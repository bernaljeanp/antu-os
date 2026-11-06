#!/usr/bin/env python3
"""Zenit para Linux: perfiles térmicos, ventiladores, luces AlienFX, teclas Alienware y límite de carga.

Port de Zenit Engine (Windows) a las interfaces del kernel: alienware-wmi (perfil de plataforma y sensores con
fanN_boost), dell-wmi-sysman (atributos de la BIOS para la carga) y hidraw para el controlador de luces AW-ELC.

  zenit gestion sistema|zenit   solo luces y monitorización, o control completo
  zenit demonio                 servicio de sistema (root): aplica perfiles, escucha las teclas, guarda el estado
  zenit probar-teclas           prueba de teclas de función durante 15 segundos, sin texto
  zenit diagnostico             informe JSON sin datos personales, de solo lectura
  zenit estado                  temperaturas, ventiladores, perfil y modo
  zenit perfil auto|NOMBRE      automático (cargador, batería y juegos) o un perfil fijo
  zenit boost | sigilo | luces  lo mismo que F6, F7 y F9
  zenit color RRGGBB|aurora [BRILLO]
  zenit carga 60|80|100|adaptativa
  zenit juego EJECUTABLE PERFIL|auto
  zenit autoprueba              comprueba la lógica con un sysfs de mentira
"""
import fcntl
import copy
import glob
import grp
import hashlib
import json
import math
import os
import pwd
import re
import select
import socket
import struct
import subprocess
import sys
import tempfile
import time

RAIZ = ""  # la autoprueba lo cambia por un árbol /sys y /proc de mentira; el servicio nunca lo lee del entorno
SOCKET = "/run/zenit.sock"
ESTADO = "/var/lib/zenit/estado.json"
PERFILES = {
    "performance": "Rendimiento", "balanced-performance": "Equilibrado+", "balanced": "Equilibrado",
    "cool": "Fresco", "quiet": "Silencioso", "low-power": "Ahorro de batería", "custom": "Personalizado",
}
# Si el equipo no tiene un perfil, el más parecido que sí tenga.
PARECIDOS = {
    "performance": ["balanced-performance", "balanced"], "balanced-performance": ["performance", "balanced"],
    "quiet": ["low-power", "cool", "balanced"], "cool": ["quiet", "balanced"], "low-power": ["quiet", "balanced"],
}
# Procesos de Wine que existen mientras corre cualquier programa de Windows, no solo juegos.
WINE_SISTEMA = {"explorer.exe", "services.exe", "winedevice.exe", "plugplay.exe", "svchost.exe", "rpcss.exe",
                "conhost.exe", "tabtip.exe", "start.exe", "rundll32.exe", "steam.exe", "steamwebhelper.exe"}
# Juegos que corren con su propio programa, fuera de Steam y de Wine: su ejecutable y el nombre que muestra Zenit.
PROGRAMAS_DE_JUEGO = {"sober": "roblox"}  # Sober (VinegarHQ): Roblox en Linux, desde Flathub
# Carpetas de Steam que no son juegos: Proton y el entorno donde corren.
STEAM_HERRAMIENTAS = ("proton", "steamlinuxruntime", "steamworks")
KEY_F17, KEY_F18, KEY_F20 = 187, 188, 190  # F6 Performance Boost, F9 luces y F7 Sigilo en el teclado Alienware
NIVELES_LUZ = [100, 40, 0]
AURORA = [(0x19, 0xFF, 0x7A), (0x00, 0xE0, 0xD0), (0x1E, 0x7B, 0xFF), (0x7A, 0x3C, 0xFF), (0xD0, 0x2B, 0xFF),
          (0x1E, 0x7B, 0xFF)]


def ruta(p):
    return RAIZ + p


def leer(p, defecto=""):
    try:
        with open(p) as f:
            return f.read().strip()
    except OSError:
        return defecto


def escribir(p, valor):
    with open(p, "w") as f:
        f.write(str(valor))


# ---------- Perfil térmico (alienware-wmi o cualquier perfil de plataforma) ----------

def rutas_perfil():
    dirs = glob.glob(ruta("/sys/class/platform-profile/platform-profile-*"))
    for d in sorted(dirs, key=lambda d: leer(d + "/name") != "alienware-wmi"):
        return d + "/profile", d + "/choices"
    acpi = ruta("/sys/firmware/acpi/platform_profile")
    return (acpi, acpi + "_choices") if os.path.exists(acpi) else (None, None)


def elegir(deseado, disponibles):
    for p in [deseado] + PARECIDOS.get(deseado, []):
        if p in disponibles:
            return p
    return None


# ---------- Cargador, juegos y sensores ----------

def en_cargador():
    tipos = [d for d in glob.glob(ruta("/sys/class/power_supply/*")) if leer(d + "/type") == "Mains"]
    return not tipos or any(leer(d + "/online") == "1" for d in tipos)  # sin cargador detectable: escritorio


def pendientes_gamemode(vivos, registrados):
    """Por cada juego, un proceso vivo que pedirle a GameMode. registrados ({juego: pid}) se actualiza."""
    for juego in [j for j, pid in registrados.items() if pid not in vivos]:
        del registrados[juego]
    nuevos = []
    for pid, juego in vivos.items():
        if juego and juego not in registrados:
            registrados[juego] = pid
            nuevos.append(pid)
    return nuevos


def pedir_gamemode(pid):
    """GameMode desde afuera: sin comandos en Steam y sin cargar nada dentro del juego, nada que moleste a un antitrampas."""
    try:
        cuenta = pwd.getpwuid(os.stat(ruta(f"/proc/{pid}")).st_uid).pw_name
        subprocess.run(["systemd-run", "--user", f"--machine={cuenta}@", "--collect", "--quiet", "gamemoded", f"-r{pid}"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    except (OSError, KeyError, subprocess.SubprocessError):
        pass


def juego_de(cmdline):
    """El juego que corre en este proceso, o None. Steam nativo por su carpeta; Proton, Heroic, Lutris y Bottles
    por el .exe que ejecuta Wine; Roblox por Sober."""
    partes = cmdline.replace("\\", "/").split("\0")  # Proton: rutas con barras de Windows
    for p in partes:
        if "/steamapps/common/" in p:
            carpeta = p.split("/steamapps/common/")[1].split("/")[0].lower()
            if carpeta and not carpeta.startswith(STEAM_HERRAMIENTAS):
                return carpeta
    if partes and os.path.basename(partes[0]) in PROGRAMAS_DE_JUEGO:
        return PROGRAMAS_DE_JUEGO[os.path.basename(partes[0])]
    for p in partes:
        nombre = re.split(r"[\\/]", p)[-1].lower()
        if nombre.endswith(".exe") and nombre not in WINE_SISTEMA:
            return nombre
    return None


SENSOR_CPU = {"coretemp": "Package", "k10temp": "Tctl"}  # Intel y AMD


def sensores():
    temps, fans = {}, {}
    paquetes = []
    for d in sorted(glob.glob(ruta("/sys/class/hwmon/hwmon*"))):
        nombre = leer(d + "/name")
        for t in sorted(glob.glob(d + "/temp*_input")) if nombre == "alienware_wmi" or nombre in SENSOR_CPU else ():
            etiqueta = leer(t.replace("_input", "_label"), os.path.basename(t))
            if nombre in SENSOR_CPU and not etiqueta.startswith(SENSOR_CPU[nombre]):
                continue
            valor = leer(t)
            try:
                grados = int(valor) // 1000
            except ValueError:
                continue  # Un sensor ausente no es 0 °C ni debe derribar el servicio.
            if nombre in SENSOR_CPU:
                paquetes.append(grados)
            else:
                temps.setdefault(etiqueta, grados)
        for f in sorted(glob.glob(d + "/fan*_input")):  # de cualquier marca: asus, thinkpad, dell_smm…
            valor = leer(f)
            # Nombre estable sin colisiones entre chips; no convertir fallos en cero.
            etiqueta = leer(f.replace("_input", "_label"), os.path.basename(f).removesuffix("_input"))
            clave = f"{nombre or os.path.basename(d)} / {etiqueta}"
            if clave in fans:
                clave = f"{os.path.basename(d)} / {clave}"
            fault = leer(f.replace("_input", "_fault"), "0")
            fans[clave] = int(valor) if valor.isdigit() and fault == "0" else None
    if paquetes:
        # El sensor del procesador tiene prioridad sobre el del firmware, sin depender del orden de hwmon.
        # En equipos con varios paquetes se muestra el más caliente, no una media que oculte un pico.
        temps["CPU"] = max(paquetes)
    return temps, fans


def capacidades():
    perfil, opciones = rutas_perfil()
    return {"perfil": bool(perfil and leer(opciones).split()), "luces": bool(controlador_luces()),
            "carga": bool(topes_de_bateria() or os.path.exists(ruta(f"{SYSMAN}/PrimaryBattChargeCfg/current_value"))),
            "carga_adaptativa": os.path.exists(ruta(f"{SYSMAN}/PrimaryBattChargeCfg/current_value")),
            "ventiladores_manual": False}


def bateria():
    result = []
    for directory in sorted(glob.glob(ruta("/sys/class/power_supply/BAT*"))):
        def number(key):
            value = leer(directory + "/" + key)
            return int(value) if value.isdigit() else None
        full, design = number("energy_full"), number("energy_full_design")
        if full is None or not design:
            full, design = number("charge_full"), number("charge_full_design")
        result.append({"nombre": os.path.basename(directory), "porcentaje": number("capacity"),
                       "estado": leer(directory + "/status"), "ciclos": number("cycle_count"),
                       "salud_porcentaje": round(full / design * 100, 1) if full is not None and design else None})
    return result


def limites_termicos():
    limits = {}
    for directory in sorted(glob.glob(ruta("/sys/class/hwmon/hwmon*"))):
        name = leer(directory + "/name")
        if name not in SENSOR_CPU and name != "alienware_wmi":
            continue
        for entry in glob.glob(directory + "/temp*_crit"):
            label = leer(entry.replace("_crit", "_label"))
            if name in SENSOR_CPU and not label.startswith(SENSOR_CPU[name]):
                continue
            value = leer(entry)
            if value.isdigit() and 0 < int(value) <= 150000:
                key = "CPU" if name in SENSOR_CPU else label
                limits[key] = min(limits.get(key, 150), int(value) / 1000)
    return limits


def datos_nvidia(jugando):
    """Solo durante un juego y con una GPU ya activa; no consulta una GPU en reposo."""
    active = any(leer(path + "/vendor") == "0x10de" and leer(path + "/class").startswith("0x03")
                 and leer(path + "/power/runtime_status") == "active"
                 for path in glob.glob(ruta("/sys/bus/pci/devices/*")))
    if not jugando or not active:
        return {"estado": "sin consulta: sin juego o gráfica en reposo", "dispositivos": []}
    try:
        result = subprocess.run(["nvidia-smi", "--format=csv,noheader,nounits",
                                 "--query-gpu=temperature.gpu,utilization.gpu,power.draw,memory.used,clocks.gr"],
                                capture_output=True, text=True, timeout=1, check=True)
        devices = []
        for line in result.stdout.splitlines()[:8]:
            fields = line.split(",")
            if len(fields) != 5:
                continue
            values = {}
            for key, field in zip(("temperatura", "uso", "vatios", "memoria_mib", "reloj_mhz"), fields):
                try:
                    value = float(field.strip())
                    values[key] = value if math.isfinite(value) and value >= 0 else None
                except ValueError:
                    values[key] = None
            devices.append(values)
        return {"estado": "consulta durante el juego", "dispositivos": devices}
    except (OSError, subprocess.SubprocessError):
        return {"estado": "el controlador no entregó una lectura", "dispositivos": []}


def contadores_termicos():
    result = {}
    for path in glob.glob(ruta("/sys/devices/system/cpu/cpu*/thermal_throttle/*_throttle_count")):
        value = leer(path)
        if value.isdigit():
            result[path] = int(value)
    return result


# ---------- Batería: atributos de la BIOS de Dell (los mismos que usa Zenit en Windows) o el límite estándar del núcleo ----------

SYSMAN = "/sys/class/firmware-attributes/dell-wmi-sysman/attributes"


def topes_de_bateria():
    """El límite estándar del núcleo: ASUS, Lenovo, HP, MSI y otras marcas."""
    return glob.glob(ruta("/sys/class/power_supply/BAT*/charge_control_end_threshold"))


def umbrales(limite):
    stop = max(55, min(100, limite))
    return max(50, min(95, stop - 5)), stop


def poner_carga(limite):
    """None: modo Adaptive de Dell. Si no, deja de cargar en limite % y retoma 5 puntos más abajo."""
    def attr(n):
        return ruta(f"{SYSMAN}/{n}/current_value")

    if not os.path.exists(attr("PrimaryBattChargeCfg")):
        if not topes_de_bateria():
            raise RuntimeError("Este equipo no permite fijar el límite de carga desde Linux.")
        for tope in topes_de_bateria():  # sin modo adaptativo: sin límite
            escribir(tope, limite or 100)
            if leer(tope) != str(limite or 100):
                raise RuntimeError("El controlador no confirmó el límite de carga.")
        return
    if limite is None:
        escribir(attr("PrimaryBattChargeCfg"), "Adaptive")
        return
    start, stop = umbrales(limite)
    # La BIOS exige inicio < fin en cada paso: subir primero el fin, o bajar primero el inicio.
    if stop > int(leer(attr("CustomChargeStart"), "50")):
        escribir(attr("CustomChargeStop"), stop)
        escribir(attr("CustomChargeStart"), start)
    else:
        escribir(attr("CustomChargeStart"), start)
        escribir(attr("CustomChargeStop"), stop)
    escribir(attr("PrimaryBattChargeCfg"), "Custom")
    if leer(attr("CustomChargeStop")) != str(stop) or leer(attr("PrimaryBattChargeCfg")) != "Custom":
        raise RuntimeError("La BIOS no confirmó el límite de carga.")


def estado_carga():
    modo = leer(ruta(f"{SYSMAN}/PrimaryBattChargeCfg/current_value"))
    if not modo and topes_de_bateria():
        modo, tope = "Custom", leer(topes_de_bateria()[0], "100")
    else:
        tope = leer(ruta(f"{SYSMAN}/CustomChargeStop/current_value"), "0")
    return modo, int(tope) if tope.isdigit() else 0


def leer_carga():
    modo, tope = estado_carga()
    if modo == "Custom":
        return f"hasta {tope} %"
    return {"Adaptive": "adaptativa", "Standard": "completa", "": "no disponible"}.get(modo, modo)


# ---------- Luces: controlador AW-ELC por USB HID ----------
# Protocolo de alienfx-tools de T-Troll (MIT), el mismo que usa Zenit en Windows: reportes de salida de 34 bytes
# (byte 0 = id de reporte, 0 en este controlador). El estado se lee con HIDIOCGINPUT: byte 2 = 34 significa ocupado.

def bytes_salida(descriptor):
    """Tamaño en bytes del reporte de salida más grande de un descriptor HID."""
    i, tam, cuenta, mayor = 0, 0, 0, 0
    while i < len(descriptor):
        b = descriptor[i]
        if b == 0xFE:  # elemento largo
            i += 3 + (descriptor[i + 1] if i + 1 < len(descriptor) else 0)
            continue
        n = (0, 1, 2, 4)[b & 3]
        valor = int.from_bytes(descriptor[i + 1:i + 1 + n], "little")
        if b & 0xFC == 0x74:
            tam = valor
        elif b & 0xFC == 0x94:
            cuenta = valor
        elif b & 0xFC == 0x90:
            mayor = max(mayor, tam * cuenta // 8)
        i += 1 + n
    return mayor


def controlador_luces():
    for d in sorted(glob.glob(ruta("/sys/class/hidraw/hidraw*"))):
        if "0000187C:" not in leer(d + "/device/uevent").upper():
            continue
        try:
            with open(d + "/device/report_descriptor", "rb") as f:
                if bytes_salida(f.read()) == 33:
                    return "/dev/" + os.path.basename(d)
        except OSError:
            continue
    return None


def identidad_luces(dispositivo):
    if not dispositivo:
        return None
    try:
        stat = os.stat(ruta("/sys/class/hidraw/" + os.path.basename(dispositivo)))
        return dispositivo, stat.st_dev, stat.st_ino
    except OSError:
        return dispositivo, None, None


def reloj_suspension():
    # BOOTTIME incluye suspensión; MONOTONIC no. No depende de ajustes de fecha/NTP.
    return time.clock_gettime(time.CLOCK_BOOTTIME) - time.monotonic()


def poner_luces(color, brillo):
    dispositivo = controlador_luces()
    if not dispositivo:
        raise RuntimeError("No hay controlador de luces Alienware (AW-ELC).")
    luces = bytes(range(26))  # todas las que admite el protocolo; las que no existen se ignoran
    fd = os.open(dispositivo, os.O_RDWR)
    try:
        def enviar(*orden):
            report = bytes([0]) + bytes(orden).ljust(33, b"\0")
            if os.write(fd, report) != len(report):
                raise OSError("Reporte de luces incompleto; vuelve a intentar el cambio.")

        def esperar():
            buf = bytearray(34)
            for _ in range(50):
                try:
                    fcntl.ioctl(fd, (3 << 30) | (34 << 16) | (ord("H") << 8) | 0x0A, buf)  # HIDIOCGINPUT(34)
                except OSError:
                    return False  # este dispositivo no permite consultar su disponibilidad
                if buf[2] != 34:
                    return True
                time.sleep(0.02)
            raise RuntimeError("El controlador de luces sigue ocupado; no se confirmó su disponibilidad.")

        esperar()
        enviar(0x03, 0x21, 0x00, 0x04, 0xFF, 0xFF)
        enviar(0x03, 0x21, 0x00, 0x01, 0xFF, 0xFF)
        if color == "AURORA":
            enviar(0x03, 0x23, 0x01, 0x00, len(luces), *luces)
            for i in range(0, len(AURORA), 3):
                enviar(0x03, 0x24, *[b for r, g, bl in AURORA[i:i + 3] for b in (2, 0x07, 0xCF, 0, 0x40, r, g, bl)])
        else:
            rgb = int(color, 16)
            enviar(0x03, 0x27, rgb >> 16, (rgb >> 8) & 0xFF, rgb & 0xFF, 0x00, len(luces), *luces)
        enviar(0x03, 0x21, 0x00, 0x03, 0xFF, 0xFF)
        disponible = esperar()
        enviar(0x03, 0x26, 100 - brillo, 0x00, len(luces), *luces)
        disponible = esperar() and disponible
        return {"color": color, "brillo": brillo, "enviado": True,
                "controlador_disponible": disponible, "color_verificado": False, "fecha": time.time()}
    finally:
        os.close(fd)


# ---------- Teclas Alienware: el firmware las envía como F17, F18 y F20 ----------

TECLAS_ZENIT = {KEY_F17: "boost", KEY_F20: "sigilo", KEY_F18: "luces"}
TECLAS_DIAGNOSTICO = {64: "F6", 65: "F7", 67: "F9", KEY_F17: "F17", KEY_F18: "F18", KEY_F20: "F20",
                      228: "KEY_KBDILLUMTOGGLE", 229: "KEY_KBDILLUMDOWN", 230: "KEY_KBDILLUMUP", 189: "F19", 148: "KEY_PROG1",
                      149: "KEY_PROG2", 202: "KEY_PROG3", 203: "KEY_PROG4", 240: "KEY_UNKNOWN"}


def dispositivos_teclas():
    devices = {}
    for directory in sorted(glob.glob(ruta("/sys/class/input/event*"))):
        bits = 0
        try:
            for word in leer(directory + "/device/capabilities/key").split():
                bits = (bits << (struct.calcsize("L") * 8)) | int(word, 16)
        except ValueError:
            continue
        codes = [code for code in TECLAS_DIAGNOSTICO if bits >> code & 1]
        if codes:
            devices["/dev/input/" + os.path.basename(directory)] = codes
    return devices


def teclados(abiertos=None, prueba=False):
    """Reintenta dispositivos nuevos tras arrancar, reanudar o reconectar el teclado."""
    opened = dict(abiertos or {})
    devices = {path for path, codes in dispositivos_teclas().items() if prueba or any(c in TECLAS_ZENIT for c in codes)}
    for path in list(opened):
        if path not in devices:
            os.close(opened.pop(path))
    for path in devices - opened.keys():
        try:
            opened[path] = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        except OSError:
            pass  # se reintentará en el próximo ciclo; no cambia permisos del sistema
    return opened


def aviso(titulo, detalle):
    """Aviso en pantalla de Plasma para cada sesión abierta (el servicio corre como root)."""
    for bus in glob.glob("/run/user/*/bus"):
        try:
            usuario = pwd.getpwuid(int(bus.split("/")[3])).pw_name
        except (KeyError, ValueError):
            continue
        subprocess.Popen(["runuser", "-u", usuario, "--", "env", f"DBUS_SESSION_BUS_ADDRESS=unix:path={bus}",
                          "gdbus", "call", "--session", "--dest", "org.kde.plasmashell", "--object-path",
                          "/org/kde/osdService", "--method", "org.kde.osdService.showText", "antu",
                          f"{titulo} · {detalle}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ---------- El servicio ----------

class Zenit:
    def __init__(self, procesos=None, gestion="zenit"):
        self.estado = {"gestion": gestion, "modo": "auto", "juegos": {}, "luces": {"color": "FFFFFF", "brillo": 100}}
        try:
            with open(ruta(ESTADO)) as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    if saved.get("gestion") in ("sistema", "zenit"):
                        self.estado["gestion"] = saved["gestion"]
                    if saved.get("modo") in {"auto", *PERFILES}:
                        self.estado["modo"] = saved["modo"]
                    self.estado["juegos"] = {k: v for k, v in (saved.get("juegos") or {}).items()
                                             if isinstance(k, str) and len(k) <= 64 and v in PERFILES}
                    lights = saved.get("luces") or {}
                    if re.fullmatch(r"[0-9A-Fa-f]{6}|AURORA", str(lights.get("color", ""))) and type(lights.get("brillo")) is int and 0 <= lights["brillo"] <= 100:
                        self.estado["luces"] = lights
                    if saved.get("carga") in ("60", "80", "100", "adaptativa"):
                        self.estado["carga"] = saved["carga"]
        except (OSError, ValueError, AttributeError, TypeError):
            pass
        self.boost = self.sigilo = False
        self.juego = None
        self.vistos = {}  # pid -> juego o None: cada proceso se revisa una sola vez
        self.con_gamemode = {}  # juego -> pid que se le pidió a GameMode
        self.procesos = procesos or self.leer_procesos
        self.controlador_actual = identidad_luces(controlador_luces())
        self.suspendido_previo = reloj_suspension()
        self.reanudaciones = 0
        self.reabrir_entradas = False
        self.luces_puestas = False
        self.luces_envio = None
        self.error_luces = ""
        self.ultimo_error = ""
        self.prueba_teclas_hasta = 0
        self.prueba_teclas = {}
        self.ultima_tecla = None
        self.entradas_abiertas = []
        self.ultima_muestra = None
        self.nvidia = {"estado": "sin consulta", "dispositivos": []}
        self.thermal_previous = contadores_termicos()
        self.limitacion_termica = None

    def guardar(self):
        os.makedirs(os.path.dirname(ruta(ESTADO)), exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".estado-", dir=os.path.dirname(ruta(ESTADO)))
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(self.estado, f, ensure_ascii=False, indent=1)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporary, ruta(ESTADO))
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def enviar_luces(self, color, brillo):
        try:
            self.luces_envio = poner_luces(color, brillo)
            self.error_luces = ""
            self.luces_puestas = True
            self.controlador_actual = identidad_luces(controlador_luces())
        except (OSError, RuntimeError, ValueError) as error:
            self.error_luces = str(error)
            raise

    def restaurar_carga(self):
        if self.estado["gestion"] == "zenit" and topes_de_bateria() and self.estado.get("carga"):
            poner_carga(None if self.estado["carga"] == "adaptativa" else int(self.estado["carga"]))

    def leer_procesos(self):
        vivos = {}
        for d in glob.glob(ruta("/proc/[0-9]*")):
            pid = int(os.path.basename(d))
            if pid not in self.vistos:
                try:
                    with open(d + "/cmdline", "rb") as f:
                        self.vistos[pid] = juego_de(f.read().decode(errors="replace"))
                except OSError:
                    self.vistos[pid] = None
            vivos[pid] = self.vistos[pid]
        self.vistos = vivos
        return [j for j in vivos.values() if j]

    def deseado(self):
        cargador = en_cargador()
        if self.boost:
            return "performance"
        if self.sigilo:
            return "quiet"
        if self.estado["modo"] != "auto":
            return self.estado["modo"]
        if self.juego:
            return self.estado["juegos"].get(self.juego) or ("performance" if cargador else "balanced-performance")
        return "balanced-performance" if cargador else "balanced"

    def actual(self):
        perfil, _ = rutas_perfil()
        return leer(perfil) if perfil else ""

    def aplicar(self):
        if self.estado["gestion"] == "sistema":
            return
        perfil, opciones = rutas_perfil()
        if not perfil:
            return
        elegido = elegir(self.deseado(), leer(opciones).split())
        if elegido and leer(perfil) != elegido:
            escribir(perfil, elegido)
            if leer(perfil) != elegido:
                raise RuntimeError("El firmware no confirmó el perfil solicitado. Se conserva el estado anterior.")

    def recuperar_dispositivos(self):
        suspended = reloj_suspension()
        resumed = suspended - self.suspendido_previo > 0.5
        self.suspendido_previo = suspended
        identity = identidad_luces(controlador_luces())
        if resumed:
            self.reanudaciones += 1
            self.reabrir_entradas = True
            self.thermal_previous = contadores_termicos()
            self.limitacion_termica = None
            self.prueba_teclas_hasta = 0
        if resumed or identity != self.controlador_actual:
            self.luces_puestas = False
            self.luces_envio = None
            if identity is None and self.controlador_actual is not None:
                self.error_luces = "Controlador de luces desconectado; se reintentará cuando aparezca."
        self.controlador_actual = identity

    def tic(self):
        self.recuperar_dispositivos()
        juegos = self.procesos()
        self.juego = juegos[0] if juegos else None
        try:
            self.aplicar()
            self.ultimo_error = ""
        except (OSError, RuntimeError) as error:
            self.ultimo_error = "No se pudo aplicar el perfil: " + str(error)
        self.ultima_muestra = time.time()
        self.nvidia = datos_nvidia(bool(self.juego))
        counters = contadores_termicos()
        common = counters.keys() & self.thermal_previous.keys()
        self.limitacion_termica = any(counters[key] > self.thermal_previous[key] for key in common) if common else None
        self.thermal_previous = counters
        if self.estado["gestion"] == "zenit" and en_cargador():  # con batería, un juego no debe subir el consumo más de lo que ya pide el perfil
            for pid in pendientes_gamemode(self.vistos, self.con_gamemode):
                pedir_gamemode(pid)
        if not self.luces_puestas and controlador_luces():  # al arrancar, cuando el USB ya está listo
            self.luces_puestas = True
            try:
                self.enviar_luces(*(("FFFFFF", 15) if self.sigilo else
                                    (self.estado["luces"]["color"], self.estado["luces"]["brillo"])))
            except (OSError, RuntimeError, ValueError):
                self.ultimo_error = "El controlador de luces no confirmó el cambio."
                self.luces_puestas = False

    def estado_prueba_teclas(self):
        remaining = max(0, math.ceil(self.prueba_teclas_hasta - time.monotonic()))
        return {"segundos_restantes": remaining, "eventos": list(self.prueba_teclas.values())}

    def tecla(self, codigo, dispositivo="no_disponible"):
        # Solo durante una prueba solicitada: teclas de función y códigos especiales concretos.
        # Nunca guarda texto ni bloquea el evento para las otras aplicaciones.
        candidates = TECLAS_DIAGNOSTICO
        if time.monotonic() < self.prueba_teclas_hasta and codigo in candidates:
            key = (os.path.basename(dispositivo), codigo)
            event = self.prueba_teclas.setdefault(key, {"evento": key[0], "codigo": codigo,
                                                       "tecla": candidates[codigo], "pulsaciones": 0})
            event["pulsaciones"] += 1
            return  # durante la prueba Zenit observa, sin ejecutar la acción de la tecla
        # XKB asigna F20 a XF86AudioMicMute. En modo solo luces pertenece al escritorio:
        # no ejecutar Sigilo, no mostrar avisos y no sustituir la última acción de Zenit.
        if codigo == KEY_F20 and self.estado["gestion"] == "sistema":
            return
        orden = TECLAS_ZENIT.get(codigo)
        if orden:
            result = self.orden([orden])
            self.ultima_tecla = {"codigo": codigo, "accion": orden, "aceptada": result.get("ok", False)}
            if not result.get("ok"):
                aviso("Zenit", result.get("error", "No se pudo aplicar la tecla."))
            else:
                titulo, detalle = result.get("aviso", ("", ""))
                if titulo:
                    aviso(titulo, detalle)

    def diagnostico(self):
        """Solo campos explícitos; no incluye el estado completo, errores ni rutas del usuario."""
        def text(path):
            return "".join(c for c in leer(ruta(path)) if c.isprintable())[:120] or None
        def numeric(path):
            raw = leer(ruta(path))
            return int(raw) if raw.isdigit() else None
        chips = []
        for directory in sorted(glob.glob(ruta("/sys/class/hwmon/hwmon*"))):
            name = text(directory.removeprefix(RAIZ) + "/name")
            fans = []
            for entry in sorted(glob.glob(directory + "/fan*_input")):
                relative = entry.removeprefix(RAIZ)
                raw = numeric(relative)
                fault_path = relative.replace("_input", "_fault")
                fault = numeric(fault_path) if os.path.exists(ruta(fault_path)) else 0
                rpm = raw if fault == 0 else None
                fans.append({"sensor": os.path.basename(entry).removesuffix("_input"),
                             "etiqueta": text(relative.replace("_input", "_label")),
                             "rpm": rpm, "fallo": fault,
                             "lectura": "no_disponible" if rpm is None else "cero_sin_confirmar_parada" if rpm == 0 else "velocidad_informada"})
            chips.append({"chip": os.path.basename(directory), "nombre": name, "ventiladores": fans})
        graphics = []
        for directory in sorted(glob.glob(ruta("/sys/bus/pci/devices/*"))):
            if not leer(directory + "/class").startswith("0x03"):
                continue
            driver = os.path.basename(os.path.realpath(directory + "/driver"))
            status = leer(directory + "/power/runtime_status")
            graphics.append({"fabricante_pci": leer(directory + "/vendor")[:8],
                             "dispositivo_pci": leer(directory + "/device")[:8],
                             "controlador": driver if driver in ("nvidia", "i915", "xe", "amdgpu", "nouveau") else "otro_o_no_disponible",
                             "estado_energia": status if status in ("active", "suspended", "suspending", "resuming", "unsupported") else "no_disponible"})
        state = self._orden(["estado"])
        os_info = {}
        for line in leer(ruta("/etc/os-release")).splitlines():
            key, _, value = line.partition("=")
            if key in ("ID", "VERSION_ID"):
                os_info[key] = value.strip('"')[:80]
        with open(__file__, "rb") as source:
            fingerprint = hashlib.sha256(source.read()).hexdigest()
        return {"formato": "zenit-diagnostico", "version": 1,
                "motor_sha256": fingerprint, "sistema": os_info,
                "modelo": text("/sys/class/dmi/id/product_name"),
                "fabricante": text("/sys/class/dmi/id/sys_vendor"),
                "kernel": text("/proc/sys/kernel/osrelease"),
                "teclas": {"dispositivos": [{"evento": os.path.basename(path),
                                             "codigos_anunciados": [TECLAS_DIAGNOSTICO[c] for c in codes],
                                             "abierto_por_zenit": os.path.basename(path) in self.entradas_abiertas}
                                            for path, codes in dispositivos_teclas().items()],
                           "ultima_especial": self.ultima_tecla, "prueba": self.estado_prueba_teclas(),
                           "f6_f7_bloqueadas_por_modo": self.estado["gestion"] == "sistema",
                           "politica_f7": "escritorio_sin_accion_de_zenit" if self.estado["gestion"] == "sistema" else "sigilo",
                           "nota": "F18 controla luces; F20 se deja al escritorio en modo solo luces. La prueba temporal puede contarla sin ejecutar acciones. No se interceptan F6/F7/F9 normales ni se registra texto."},
                "modulos": {name: os.path.isdir(ruta("/sys/module/" + name))
                            for name in ("alienware_wmi", "dell_wmi_sysman", "dell_smm_hwmon", "nvidia", "i915", "xe")},
                "gestion": state["gestion"], "perfil_observado": state["perfil"],
                "perfiles_disponibles": state["perfiles"], "capacidades": state["capacidades"],
                "temperaturas_c": state["temperaturas"], "limites_termicos_c": state["limites_termicos"],
                "hwmon": chips, "graficas": graphics,
                "carga": {"modo": state["carga_modo"], "limite": state["carga_tope"]},
                "recuperacion": {"reanudaciones_detectadas": self.reanudaciones, "luces_pendientes": not self.luces_puestas},
                "luces": {"envio_registrado": bool(self.luces_envio), "ultimo_envio_fallo": bool(self.error_luces)},
                "notas": ["Una instantánea de 0 rpm no confirma que el ventilador esté parado.",
                          "No se consultó nvidia-smi ni se modificaron perfiles, luces o batería.",
                          "No incluye usuario, hostname, series, UUID, procesos, juegos, registros ni variables de entorno."]}

    def orden(self, args):
        before = copy.deepcopy(self.estado)
        flags = self.boost, self.sigilo
        try:
            return self._orden(args)
        except (OSError, RuntimeError, ValueError, TypeError) as error:
            self.estado = before
            self.boost, self.sigilo = flags
            self.ultimo_error = str(error)
            return {"ok": False, "error": str(error)}

    def _orden(self, args):
        """Una orden de `zenit` o de una tecla. Devuelve un diccionario para el cliente."""
        if not isinstance(args, list) or len(args) > 3 or not all(isinstance(a, str) and len(a) <= 64 for a in args):
            return {"ok": False, "error": "Orden no válida."}
        o = args[0] if args else "estado"
        if o == "probar-teclas" and len(args) == 1:
            self.prueba_teclas = {}
            self.prueba_teclas_hasta = time.monotonic() + 15
            return {"ok": True}
        if o == "diagnostico" and len(args) == 1:
            return {"ok": True, "informe": self.diagnostico()}
        if o == "estado":
            temps, fans = sensores()
            gpu_temperatures = [d["temperatura"] for d in self.nvidia["dispositivos"] if d.get("temperatura") is not None]
            if gpu_temperatures:
                temps["GPU"] = round(max(gpu_temperatures))
            _, opciones = rutas_perfil()
            carga_modo, carga_tope = estado_carga()
            return {"ok": True, "perfil": self.actual(), "modo": self.estado["modo"], "cargador": en_cargador(),
                    "perfiles": leer(opciones).split() if opciones else [], "carga_modo": carga_modo,
                    "carga_tope": carga_tope, "juegos": self.estado["juegos"],
                    "juego": self.juego, "boost": self.boost, "sigilo": self.sigilo, "temperaturas": temps,
                    "prueba_teclas": self.estado_prueba_teclas(),
                    "ultima_tecla": self.ultima_tecla, "entradas_abiertas": len(self.entradas_abiertas),
                    "gestion": self.estado["gestion"], "ventiladores": fans, "luces": self.estado["luces"], "carga": leer_carga(),
                    "reanudaciones_detectadas": self.reanudaciones,
                    "luces_envio": self.luces_envio, "error_luces": self.error_luces,
                    "capacidades": capacidades(), "baterias": bateria(), "limites_termicos": limites_termicos(),
                    "nvidia": self.nvidia, "limitacion_termica_observada": self.limitacion_termica,
                    "ultimo_error": self.ultimo_error, "ultima_muestra": self.ultima_muestra,
                    "perfil_solicitado": self.deseado(),
                    "motivo": "Energía y batería gestionadas por el sistema" if self.estado["gestion"] == "sistema" else
                              "Boost temporal" if self.boost else "Sigilo temporal" if self.sigilo else
                              "Perfil fijo" if self.estado["modo"] != "auto" else
                              "Juego detectado: " + self.juego if self.juego else
                              "Automático con cargador" if en_cargador() else "Automático con batería"}
        if o == "gestion" and len(args) == 2 and args[1] in ("sistema", "zenit"):
            self.estado["gestion"] = args[1]
            self.boost = self.sigilo = False
            self.aplicar()
            self.guardar()
            return {"ok": True}
        if self.estado["gestion"] == "sistema" and o in ("perfil", "juego", "boost", "sigilo", "carga"):
            raise RuntimeError("Solo luces y monitorización: la energía y la batería las gestiona el sistema.")
        if o == "perfil" and len(args) == 2 and (args[1] == "auto" or args[1] in PERFILES):
            _, options = rutas_perfil()
            if args[1] != "auto" and args[1] not in (leer(options).split() if options else []):
                raise RuntimeError("El equipo no ofrece ese perfil térmico.")
            self.boost = self.sigilo = False
            self.estado["modo"] = args[1]
        elif o == "juego" and len(args) == 3 and (args[2] == "auto" or args[2] in PERFILES):
            if args[2] == "auto":
                self.estado["juegos"].pop(args[1].lower(), None)
            else:
                self.estado["juegos"][args[1].lower()] = args[2]
        elif o == "boost":
            _, options = rutas_perfil()
            if not options or not elegir("performance", leer(options).split()):
                raise RuntimeError("El equipo no ofrece un perfil de rendimiento.")
            self.boost, self.sigilo = not self.boost, False
            self.aplicar()
            return {"ok": True, "aviso": ("Performance Boost", "Perfil de rendimiento solicitado al firmware"
                                          if self.boost else "Desactivado")}
        elif o == "sigilo":
            self.sigilo, self.boost = not self.sigilo, False
            luces = self.estado["luces"]
            try:
                self.enviar_luces(*(("FFFFFF", 15) if self.sigilo else (luces["color"], luces["brillo"])))
            except (OSError, RuntimeError):
                pass
            self.aplicar()
            return {"ok": True, "aviso": ("Sigilo", "Activado: luces tenues y perfil Silencioso"
                                          if self.sigilo else "Desactivado: tus luces y tu perfil de vuelta")}
        elif o == "luces":
            luces = self.estado["luces"]
            nivel = next((n for n in NIVELES_LUZ if n < luces["brillo"]), NIVELES_LUZ[0])
            self.enviar_luces(luces["color"], nivel)
            luces["brillo"] = nivel
            self.guardar()
            return {"ok": True, "aviso": ("Luces del teclado", {0: "Apagadas", 100: "Altas"}.get(nivel, "Bajas"))}
        elif o == "color" and len(args) in (2, 3):
            color = args[1].upper()
            if color != "AURORA" and not re.fullmatch(r"[0-9A-F]{6}", color):
                return {"ok": False, "error": "El color va como RRGGBB (por ejemplo FF5A1F) o «aurora»."}
            brillo = max(0, min(100, int(args[2]))) if len(args) == 3 else self.estado["luces"]["brillo"]
            self.enviar_luces(color, brillo)
            self.estado["luces"] = {"color": color, "brillo": brillo}
        elif o == "carga" and len(args) == 2 and args[1] in ("60", "80", "100", "adaptativa"):
            if args[1] == "adaptativa" and not capacidades()["carga_adaptativa"]:
                raise RuntimeError("Este controlador ofrece límites fijos, no carga adaptativa.")
            poner_carga(None if args[1] == "adaptativa" else int(args[1]))
            self.estado["carga"] = args[1]
        else:
            return {"ok": False, "error": "Orden desconocida. Escribe «zenit ayuda»."}
        if o in ("perfil", "juego"):
            self.aplicar()
        self.guardar()
        self.ultimo_error = ""
        return {"ok": True}


def demonio():
    zenit = Zenit(gestion="sistema" if "--solo-luces" in sys.argv else "zenit")
    # El límite estándar se pierde al apagar en varias marcas; el de Dell queda en la BIOS.
    try:
        zenit.restaurar_carga()
    except (OSError, RuntimeError, ValueError):
        pass
    if os.path.exists(SOCKET):
        os.unlink(SOCKET)
    servidor = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    servidor.bind(SOCKET)
    try:  # solo root y las cuentas administradoras (grupo wheel)
        os.chown(SOCKET, 0, grp.getgrnam("wheel").gr_gid)
    except KeyError:
        pass
    os.chmod(SOCKET, 0o660)
    servidor.listen(4)
    teclas = teclados()
    evento = struct.Struct("llHHi")
    siguiente = 0
    while True:
        if time.monotonic() >= siguiente:
            try:
                zenit.tic()
            except (OSError, RuntimeError, ValueError) as error:
                zenit.ultimo_error = "No se pudo actualizar el estado: " + str(error)
            if zenit.reabrir_entradas:
                for handle in teclas.values():
                    try:
                        os.close(handle)
                    except OSError:
                        pass
                teclas = {}
                zenit.reabrir_entradas = False
            teclas = teclados(teclas, prueba=time.monotonic() < zenit.prueba_teclas_hasta)
            zenit.entradas_abiertas = [os.path.basename(path) for path in teclas]
            siguiente = time.monotonic() + 3
        listos, _, _ = select.select([servidor, *teclas.values()], [], [], max(0, siguiente - time.monotonic()))
        for fd in listos:
            if fd is servidor:
                conexion, _ = servidor.accept()
                with conexion:
                    conexion.settimeout(2)
                    try:
                        data = b""
                        while b"\n" not in data and len(data) < 4096:
                            chunk = conexion.recv(min(1024, 4096 - len(data)))
                            if not chunk:
                                break
                            data += chunk
                        if b"\n" not in data:
                            raise ValueError("Orden incompleta o demasiado larga.")
                        args = json.loads(data.split(b"\n")[0])
                        respuesta = zenit.orden(args)
                    except (OSError, RuntimeError, ValueError, TypeError, KeyError, AttributeError) as e:
                        respuesta = {"ok": False, "error": str(e)}
                    try:
                        conexion.sendall((json.dumps(respuesta, ensure_ascii=False) + "\n").encode())
                    except OSError:
                        pass
                continue
            try:
                datos = os.read(fd, evento.size * 32)
            except OSError:  # teclado desconectado: deja de vigilarlo (si no, select lo da por listo para siempre)
                teclas = {path: handle for path, handle in teclas.items() if handle != fd}
                os.close(fd)
                continue
            if not datos:
                teclas = {path: handle for path, handle in teclas.items() if handle != fd}
                os.close(fd)
                continue
            for i in range(0, len(datos) - evento.size + 1, evento.size):
                _, _, tipo, codigo, valor = evento.unpack_from(datos, i)
                if tipo == 1 and valor == 1:  # tecla pulsada
                    try:
                        path = next((path for path, handle in teclas.items() if handle == fd), "no_disponible")
                        zenit.tecla(codigo, path)
                    except (OSError, RuntimeError):
                        pass


def cliente(args):
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect(SOCKET)
            s.sendall((json.dumps(args) + "\n").encode())
            respuesta = json.loads(s.makefile().readline())
    except PermissionError:
        sys.exit("Zenit solo atiende a las cuentas administradoras.")
    except OSError:
        sys.exit("El servicio Zenit no está corriendo (systemctl status zenit).")
    if not respuesta.get("ok"):
        sys.exit(respuesta.get("error", "Zenit no pudo hacerlo."))
    if args[0] == "diagnostico":
        print(json.dumps(respuesta["informe"], ensure_ascii=False, indent=2))
    elif args[0] == "estado":
        r = respuesta
        print("Gestión: " + r.get("gestion", "zenit"))
        print(f"Perfil: {PERFILES.get(r['perfil'], r['perfil'] or 'no disponible')}"
              f" ({'observado del sistema' if r.get('gestion') == 'sistema' else 'automático' if r['modo'] == 'auto' else 'fijo'}"
              f"{', Boost' if r['boost'] else ''}{', Sigilo' if r['sigilo'] else ''})")
        print(f"Energía: {'cargador' if r['cargador'] else 'batería'} · carga {r['carga']}")
        if r["juego"]:
            print(f"Jugando: {r['juego']}")
        for nombre, grados in r["temperaturas"].items():
            print(f"{nombre}: {grados} °C")
        for nombre, rpm in r["ventiladores"].items():
            print(f"{nombre}: " + ("lectura no disponible" if rpm is None else "0 rpm informadas; parada no confirmada" if rpm == 0 else f"{rpm} rpm"))
        luces = r["luces"]
        print(f"Luces: {'Aurora' if luces['color'] == 'AURORA' else '#' + luces['color']} al {luces['brillo']} %")
    elif "aviso" in respuesta:
        print(" · ".join(respuesta["aviso"]))


def autoprueba():
    global RAIZ
    with tempfile.TemporaryDirectory() as raiz:
        RAIZ = raiz

        def poner(p, valor):
            os.makedirs(os.path.dirname(raiz + p), exist_ok=True)
            escribir(raiz + p, valor)

        pp = "/sys/class/platform-profile/platform-profile-0"
        poner(pp + "/name", "alienware-wmi")
        poner(pp + "/profile", "balanced")
        poner(pp + "/choices", "low-power quiet balanced balanced-performance performance custom")
        poner("/sys/class/power_supply/AC/type", "Mains")
        poner("/sys/class/power_supply/AC/online", "1")
        for n, v in [("PrimaryBattChargeCfg", "Adaptive"), ("CustomChargeStart", "50"), ("CustomChargeStop", "55")]:
            poner(f"{SYSMAN}/{n}/current_value", v)
        poner("/sys/class/hwmon/hwmon3/name", "alienware_wmi")
        poner("/sys/class/hwmon/hwmon3/temp1_input", "61000")
        poner("/sys/class/hwmon/hwmon3/temp1_label", "CPU")
        poner("/sys/class/hwmon/hwmon3/fan1_input", "2400")

        juegos = []
        z = Zenit(procesos=lambda: juegos)

        def perfil():
            return leer(raiz + pp + "/profile")

        z.tic()
        assert perfil() == "balanced-performance", perfil()          # cargador: Equilibrado+
        poner("/sys/class/power_supply/AC/online", "0")
        z.tic()
        assert perfil() == "balanced", perfil()                      # batería: Equilibrado
        juegos.append("cyberpunk2077.exe")
        z.tic()
        assert perfil() == "balanced-performance", perfil()          # juego en batería
        poner("/sys/class/power_supply/AC/online", "1")
        z.tic()
        assert perfil() == "performance", perfil()                   # juego en el cargador
        z.orden(["juego", "Cyberpunk2077.exe", "quiet"])
        z.tic()
        assert perfil() == "quiet", perfil()                         # perfil elegido para ese juego
        juegos.clear()
        z.tic()
        z.orden(["boost"])
        assert perfil() == "performance" and z.boost
        z.orden(["boost"])
        assert perfil() == "balanced-performance" and not z.boost
        z.orden(["perfil", "quiet"])
        assert perfil() == "quiet" and z.estado["modo"] == "quiet"
        assert z.orden(["perfil", "turbo"])["ok"] is False

        assert juego_de("/home/a/.steam/steamapps/common/Hades/Hades\0") == "hades"
        assert juego_de("/s/steamapps/common/SteamLinuxRuntime_sniper/pv\0--\0/s/steamapps/common/Hades/Hades\0") == "hades"
        assert juego_de("/s/steamapps/common/Proton 9.0/proton\0Z:\\games\\Elden Ring\\eldenring.exe\0") == "eldenring.exe"
        assert juego_de("Z:\\s\\steamapps\\common\\Elden Ring\\eldenring.exe\0") == "elden ring"
        assert juego_de("C:\\windows\\system32\\services.exe\0") is None
        assert juego_de("/usr/bin/kate\0") is None
        assert juego_de("/app/bin/sober\0--\0") == "roblox"
        assert elegir("balanced-performance", ["quiet", "balanced", "performance"]) == "performance"

        assert umbrales(80) == (75, 80) and umbrales(60) == (55, 60) and umbrales(100) == (95, 100)

        def valor(n):
            return leer(f"{raiz}{SYSMAN}/{n}/current_value")

        poner_carga(80)
        assert (valor("CustomChargeStart"), valor("CustomChargeStop"), valor("PrimaryBattChargeCfg")) == ("75", "80", "Custom")
        poner_carga(60)
        assert (valor("CustomChargeStart"), valor("CustomChargeStop")) == ("55", "60")
        poner_carga(None)
        assert valor("PrimaryBattChargeCfg") == "Adaptive"

        # Descriptor HID mínimo: Report Size 8, Report Count 33, Output.
        assert bytes_salida(bytes([0x06, 0x00, 0xFF, 0x75, 0x08, 0x95, 0x21, 0x91, 0x02])) == 33
        temps, fans = sensores()
        assert temps == {"CPU": 61} and list(fans.values()) == [2400], (temps, fans)
    registrados = {}
    assert pendientes_gamemode({1: None, 2: "hades", 3: "hades"}, registrados) == [2]
    assert pendientes_gamemode({1: None, 2: "hades", 3: "hades"}, registrados) == []  # pedirlo dos veces lo apagaría
    assert pendientes_gamemode({3: "hades"}, registrados) == [3]  # cerró el lanzador: sigue el juego
    assert pendientes_gamemode({}, registrados) == [] and registrados == {}

    # Otras marcas: límite estándar del núcleo, procesador AMD y ventiladores con otro nombre.
    with tempfile.TemporaryDirectory() as raiz:
        RAIZ = raiz
        tope = raiz + "/sys/class/power_supply/BAT0/charge_control_end_threshold"
        os.makedirs(os.path.dirname(tope))
        escribir(tope, "100")
        assert estado_carga() == ("Custom", 100)
        poner_carga(80)
        assert leer(tope) == "80" and leer_carga() == "hasta 80 %"
        poner_carga(None)
        assert leer(tope) == "100"
        os.makedirs(raiz + "/sys/class/hwmon/hwmon0")
        os.makedirs(raiz + "/sys/class/hwmon/hwmon1")
        for archivo, valor in (("hwmon0/name", "k10temp"), ("hwmon0/temp1_input", "72000"), ("hwmon0/temp1_label", "Tctl"),
                               ("hwmon1/name", "asus"), ("hwmon1/fan1_input", "3100"), ("hwmon1/fan1_label", "cpu_fan")):
            escribir(raiz + "/sys/class/hwmon/" + archivo, valor)
        assert sensores() == ({"CPU": 72}, {"asus / cpu_fan": 3100})
        RAIZ = ""

    print("Zenit: autoprueba OK")


def main():
    args = sys.argv[1:] or ["estado"]
    if args[0] == "demonio":
        demonio()
    elif args[0] == "autoprueba":
        autoprueba()
    elif args[0] in ("ayuda", "-h", "--help"):
        print(__doc__.strip())
    else:
        cliente(args)


if __name__ == "__main__":
    main()

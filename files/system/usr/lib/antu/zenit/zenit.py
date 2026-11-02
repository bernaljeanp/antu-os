#!/usr/bin/env python3
"""Zenit para Linux: perfiles térmicos, ventiladores, luces AlienFX, teclas Alienware y límite de carga.

Port de Zenit Engine (Windows) a las interfaces del kernel: alienware-wmi (perfil de plataforma y sensores con
fanN_boost), dell-wmi-sysman (atributos de la BIOS para la carga) y hidraw para el controlador de luces AW-ELC.

  zenit demonio                 servicio de sistema (root): aplica perfiles, escucha las teclas, guarda el estado
  zenit estado                  temperaturas, ventiladores, perfil y modo
  zenit perfil auto|NOMBRE      automático (cargador, batería y juegos) o un perfil fijo
  zenit boost | sigilo | luces  lo mismo que F6, F7 y F9
  zenit color RRGGBB|aurora [BRILLO]
  zenit carga 60|80|100|adaptativa
  zenit juego EJECUTABLE PERFIL|auto
  zenit autoprueba              comprueba la lógica con un sysfs de mentira
"""
import fcntl
import glob
import grp
import json
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

RAIZ = os.environ.get("ZENIT_RAIZ", "")  # para la autoprueba: un árbol /sys y /proc de mentira
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


def juego_de(cmdline):
    """El juego que corre en este proceso, o None. Steam nativo por su carpeta; Proton, Heroic, Lutris y Bottles
    por el .exe que ejecuta Wine."""
    partes = cmdline.split("\0")
    for p in partes:
        if "/steamapps/common/" in p:
            carpeta = p.split("/steamapps/common/")[1].split("/")[0].lower()
            if carpeta and not carpeta.startswith(STEAM_HERRAMIENTAS):
                return carpeta
    for p in partes:
        nombre = re.split(r"[\\/]", p)[-1].lower()
        if nombre.endswith(".exe") and nombre not in WINE_SISTEMA:
            return nombre
    return None


def sensores():
    temps, fans = {}, {}
    for d in glob.glob(ruta("/sys/class/hwmon/hwmon*")):
        nombre = leer(d + "/name")
        if nombre not in ("alienware_wmi", "coretemp"):
            continue
        for t in sorted(glob.glob(d + "/temp*_input")):
            etiqueta = leer(t.replace("_input", "_label"), os.path.basename(t))
            if nombre == "coretemp" and not etiqueta.startswith("Package"):
                continue
            temps.setdefault("CPU" if nombre == "coretemp" else etiqueta, int(leer(t, "0")) // 1000)
        for f in sorted(glob.glob(d + "/fan*_input")):
            fans[leer(f.replace("_input", "_label"), os.path.basename(f)[:4])] = int(leer(f, "0"))
    return temps, fans


# ---------- Batería: atributos de la BIOS de Dell (los mismos que usa Zenit en Windows) ----------

SYSMAN = "/sys/class/firmware-attributes/dell-wmi-sysman/attributes"


def umbrales(limite):
    stop = max(55, min(100, limite))
    return max(50, min(95, stop - 5)), stop


def poner_carga(limite):
    """None: modo Adaptive de Dell. Si no, deja de cargar en limite % y retoma 5 puntos más abajo."""
    def attr(n):
        return ruta(f"{SYSMAN}/{n}/current_value")

    if not os.path.exists(attr("PrimaryBattChargeCfg")):
        raise RuntimeError("Este equipo no tiene ajustes de carga en la BIOS (dell-wmi-sysman).")
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


def leer_carga():
    modo = leer(ruta(f"{SYSMAN}/PrimaryBattChargeCfg/current_value"))
    if modo == "Custom":
        return f"hasta {leer(ruta(f'{SYSMAN}/CustomChargeStop/current_value'))} %"
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


def poner_luces(color, brillo):
    dispositivo = controlador_luces()
    if not dispositivo:
        raise RuntimeError("No hay controlador de luces Alienware (AW-ELC).")
    luces = bytes(range(26))  # todas las que admite el protocolo; las que no existen se ignoran
    fd = os.open(dispositivo, os.O_RDWR)
    try:
        def enviar(*orden):
            os.write(fd, bytes([0]) + bytes(orden).ljust(33, b"\0"))

        def esperar():
            buf = bytearray(34)
            for _ in range(50):
                try:
                    fcntl.ioctl(fd, (3 << 30) | (34 << 16) | (ord("H") << 8) | 0x0A, buf)  # HIDIOCGINPUT(34)
                except OSError:
                    return
                if buf[2] != 34:
                    return
                time.sleep(0.02)

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
        esperar()
        enviar(0x03, 0x26, 100 - brillo, 0x00, len(luces), *luces)
    finally:
        os.close(fd)


# ---------- Teclas Alienware: el firmware las envía como F17, F18 y F20 ----------

def teclados():
    abiertos = []
    for d in glob.glob(ruta("/sys/class/input/event*")):
        bits = 0
        for palabra in leer(d + "/device/capabilities/key").split():
            bits = (bits << 64) | int(palabra, 16)
        if bits >> KEY_F17 & 1:
            try:
                abiertos.append(os.open("/dev/input/" + os.path.basename(d), os.O_RDONLY | os.O_NONBLOCK))
            except OSError:
                pass
    return abiertos


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
    def __init__(self, procesos=None):
        self.estado = {"modo": "auto", "juegos": {}, "luces": {"color": "FFFFFF", "brillo": 100}}
        try:
            with open(ruta(ESTADO)) as f:
                self.estado.update(json.load(f))
        except (OSError, ValueError):
            pass
        self.boost = self.sigilo = False
        self.juego = None
        self.vistos = {}  # pid -> juego o None: cada proceso se revisa una sola vez
        self.procesos = procesos or self.leer_procesos
        self.luces_puestas = False

    def guardar(self):
        os.makedirs(os.path.dirname(ruta(ESTADO)), exist_ok=True)
        with open(ruta(ESTADO), "w") as f:
            json.dump(self.estado, f, ensure_ascii=False, indent=1)

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
        perfil, opciones = rutas_perfil()
        if not perfil:
            return
        elegido = elegir(self.deseado(), leer(opciones).split())
        if elegido and leer(perfil) != elegido:
            escribir(perfil, elegido)

    def tic(self):
        juegos = self.procesos()
        self.juego = juegos[0] if juegos else None
        self.aplicar()
        if not self.luces_puestas and controlador_luces():  # al arrancar, cuando el USB ya está listo
            self.luces_puestas = True
            try:
                poner_luces(self.estado["luces"]["color"], self.estado["luces"]["brillo"])
            except (OSError, RuntimeError, ValueError):
                pass

    def tecla(self, codigo):
        orden = {KEY_F17: "boost", KEY_F20: "sigilo", KEY_F18: "luces"}.get(codigo)
        if orden:
            titulo, detalle = self.orden([orden]).get("aviso", ("", ""))
            if titulo:
                aviso(titulo, detalle)

    def orden(self, args):
        """Una orden de `zenit` o de una tecla. Devuelve un diccionario para el cliente."""
        o = args[0] if args else "estado"
        if o == "estado":
            temps, fans = sensores()
            return {"ok": True, "perfil": self.actual(), "modo": self.estado["modo"], "cargador": en_cargador(),
                    "juego": self.juego, "boost": self.boost, "sigilo": self.sigilo, "temperaturas": temps,
                    "ventiladores": fans, "luces": self.estado["luces"], "carga": leer_carga()}
        if o == "perfil" and len(args) == 2 and (args[1] == "auto" or args[1] in PERFILES):
            self.estado["modo"] = args[1]
            self.guardar()
        elif o == "juego" and len(args) == 3 and (args[2] == "auto" or args[2] in PERFILES):
            if args[2] == "auto":
                self.estado["juegos"].pop(args[1].lower(), None)
            else:
                self.estado["juegos"][args[1].lower()] = args[2]
            self.guardar()
        elif o == "boost":
            self.boost, self.sigilo = not self.boost, False
            self.aplicar()
            return {"ok": True, "aviso": ("Performance Boost", "Activado: ventiladores y frecuencias al máximo"
                                          if self.boost else "Desactivado")}
        elif o == "sigilo":
            self.sigilo, self.boost = not self.sigilo, False
            luces = self.estado["luces"]
            try:
                poner_luces(*(("FFFFFF", 15) if self.sigilo else (luces["color"], luces["brillo"])))
            except (OSError, RuntimeError):
                pass
            self.aplicar()
            return {"ok": True, "aviso": ("Sigilo", "Activado: luces tenues y perfil Silencioso"
                                          if self.sigilo else "Desactivado: tus luces y tu perfil de vuelta")}
        elif o == "luces":
            luces = self.estado["luces"]
            nivel = next((n for n in NIVELES_LUZ if n < luces["brillo"]), NIVELES_LUZ[0])
            poner_luces(luces["color"], nivel)
            luces["brillo"] = nivel
            self.guardar()
            return {"ok": True, "aviso": ("Luces del teclado", {0: "Apagadas", 100: "Altas"}.get(nivel, "Bajas"))}
        elif o == "color" and len(args) in (2, 3):
            color = args[1].upper()
            if color != "AURORA" and not re.fullmatch(r"[0-9A-F]{6}", color):
                return {"ok": False, "error": "El color va como RRGGBB (por ejemplo FF5A1F) o «aurora»."}
            brillo = max(0, min(100, int(args[2]))) if len(args) == 3 else self.estado["luces"]["brillo"]
            poner_luces(color, brillo)
            self.estado["luces"] = {"color": color, "brillo": brillo}
            self.guardar()
        elif o == "carga" and len(args) == 2 and args[1] in ("60", "80", "100", "adaptativa"):
            poner_carga(None if args[1] == "adaptativa" else int(args[1]))
        else:
            return {"ok": False, "error": "Orden desconocida. Escribe «zenit ayuda»."}
        self.aplicar()
        return {"ok": True}


def demonio():
    zenit = Zenit()
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
            zenit.tic()
            siguiente = time.monotonic() + 3
        listos, _, _ = select.select([servidor, *teclas], [], [], max(0, siguiente - time.monotonic()))
        for fd in listos:
            if fd is servidor:
                conexion, _ = servidor.accept()
                with conexion:
                    conexion.settimeout(2)
                    try:
                        args = json.loads(conexion.makefile().readline())
                        respuesta = zenit.orden(args)
                    except (OSError, RuntimeError, ValueError, TypeError) as e:
                        respuesta = {"ok": False, "error": str(e)}
                    try:
                        conexion.sendall((json.dumps(respuesta, ensure_ascii=False) + "\n").encode())
                    except OSError:
                        pass
                continue
            try:
                datos = os.read(fd, evento.size * 32)
            except OSError:
                continue
            for i in range(0, len(datos) - evento.size + 1, evento.size):
                _, _, tipo, codigo, valor = evento.unpack_from(datos, i)
                if tipo == 1 and valor == 1:  # tecla pulsada
                    try:
                        zenit.tecla(codigo)
                    except (OSError, RuntimeError):
                        pass


def cliente(args):
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.connect(SOCKET)
            s.sendall((json.dumps(args) + "\n").encode())
            respuesta = json.loads(s.makefile().readline())
    except PermissionError:
        sys.exit("Zenit solo atiende a las cuentas administradoras.")
    except OSError:
        sys.exit("El servicio Zenit no está corriendo (systemctl status zenit).")
    if not respuesta.get("ok"):
        sys.exit(respuesta.get("error", "Zenit no pudo hacerlo."))
    if args[0] == "estado":
        r = respuesta
        print(f"Perfil: {PERFILES.get(r['perfil'], r['perfil'] or 'no disponible')}"
              f" ({'automático' if r['modo'] == 'auto' else 'fijo'}"
              f"{', Boost' if r['boost'] else ''}{', Sigilo' if r['sigilo'] else ''})")
        print(f"Energía: {'cargador' if r['cargador'] else 'batería'} · carga {r['carga']}")
        if r["juego"]:
            print(f"Jugando: {r['juego']}")
        for nombre, grados in r["temperaturas"].items():
            print(f"{nombre}: {grados} °C")
        for nombre, rpm in r["ventiladores"].items():
            print(f"{nombre}: {rpm} rpm")
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
        assert juego_de("C:\\windows\\system32\\services.exe\0") is None
        assert juego_de("/usr/bin/kate\0") is None
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

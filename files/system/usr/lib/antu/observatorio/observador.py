#!/usr/bin/env python3
"""Observador: mide cada juego mientras dura, desde afuera, y guarda un resumen de la sesión para el Observatorio.

Corre como servicio de la cuenta. Nada se carga dentro del juego, así que no hay nada que moleste a un antitrampas: se mira qué
procesos hay (como Zenit), los sensores de la gráfica y, en el modo Eclipse, los fotogramas que informa Gamescope. En el
escritorio no hay cómo contarlos sin entrar al juego, así que esas sesiones quedan sin ese dato. Todo queda en este equipo.

--autoprueba: revisa la lectura de datos.
"""
import glob
import json
import os
import pathlib
import re
import signal
import statistics
import subprocess
import sys
import threading
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / "zenit"), str(HERE.parent / "biblioteca")]
from biblioteca import juegos_instalados  # noqa: E402
from zenit import en_cargador, juego_de  # noqa: E402

ARCHIVO = pathlib.Path.home() / ".local/share/antu/observatorio/sesiones.jsonl"
TUBERIA = pathlib.Path(os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}") / "antu-gamescope-stats"
CADA = 5  # segundos entre muestras
SEGUNDOS_MINIMOS = 30  # menos que esto no alcanzó a jugarse
CONSULTA_GPU = ["nvidia-smi", "--format=csv,noheader,nounits",
                "--query-gpu=temperature.gpu,clocks_event_reasons.hw_thermal_slowdown,"
                "clocks_event_reasons.sw_thermal_slowdown"]
# Códigos de error de NVIDIA que dicen algo útil. El 45 no está: también aparece al cerrar un juego sin que nada ande mal.
XID_DEL_JUEGO = {"13", "31"}
XID_DE_LA_GRAFICA = {"61", "62", "79"}


def leer_estadistica(linea, estado):
    """Una línea de Gamescope: «fps=60.0» seguida de «focus=APPID» o «focus=steam». Devuelve fotogramas si son de un juego."""
    if linea.startswith("fps="):
        try:
            estado["fps"] = float(linea[4:])
        except ValueError:
            estado["fps"] = None
    elif linea.startswith("focus="):
        fps, estado["fps"] = estado.get("fps"), None
        if fps and linea[6:].strip() not in ("steam", "0"):
            return fps
    return None


class Gamescope(threading.Thread):
    """Lee los fotogramas de Gamescope. Solo hay tubería en Eclipse (la crea antu-eclipse)."""

    def __init__(self):
        super().__init__(daemon=True)
        self.muestras = []

    def run(self):
        estado = {}
        while True:
            try:
                if TUBERIA.is_fifo():
                    with open(TUBERIA, encoding="ascii", errors="replace") as f:  # espera a que Gamescope abra
                        for linea in f:
                            fps = leer_estadistica(linea, estado)
                            if fps:
                                self.muestras.append(fps)
            except OSError:
                pass
            time.sleep(10)

    def tomar(self):
        muestras, self.muestras = self.muestras, []
        return muestras


def sensores():
    """(temperatura de la gráfica, si está bajando potencia por calor)."""
    try:
        r = subprocess.run(CONSULTA_GPU, capture_output=True, text=True, errors="replace", timeout=5, stdin=subprocess.DEVNULL)
        partes = [p.strip() for p in r.stdout.split(",")]
        if r.returncode == 0 and len(partes) == 3 and partes[0].isdigit():
            return float(partes[0]), "Active" in partes[1:]
    except (OSError, subprocess.SubprocessError):
        pass
    for ruta in glob.glob("/sys/class/drm/card[0-9]/device/hwmon/hwmon*/temp1_input"):  # AMD e Intel
        try:
            return int(pathlib.Path(ruta).read_text()) / 1000, False
        except (OSError, ValueError):
            continue
    return None, False


def fallo_de(lineas):
    """Por qué se cerró el juego, en palabras simples, a partir del registro del sistema."""
    for linea in lineas:
        if "Out of memory" in linea or "oom-kill" in linea:
            return "El equipo se quedó sin memoria y el sistema cerró el juego."
    for linea in lineas:
        codigo = re.search(r"NVRM: Xid \([^)]*\): (\d+)", linea)
        if codigo and codigo[1] in XID_DE_LA_GRAFICA:
            return f"La gráfica dejó de responder durante el juego (código {codigo[1]})."
        if codigo and codigo[1] in XID_DEL_JUEGO:
            return (f"El juego le pidió algo inválido a la gráfica (código {codigo[1]}). Suele arreglarse actualizando el "
                    "juego o probando otra versión de Proton.")
    return None


def buscar_fallo(desde):
    try:
        r = subprocess.run(["journalctl", "--no-pager", "-q", "-o", "cat", "-k", "--since", f"@{int(desde)}",
                            "-g", "NVRM: Xid|Out of memory|oom-kill"],
                           capture_output=True, text=True, errors="replace", timeout=15, stdin=subprocess.DEVNULL)
        return fallo_de(r.stdout.splitlines())
    except (OSError, subprocess.SubprocessError):
        return None


def version_del_sistema():
    """Cambia solo cuando se actualiza: el identificador de la imagen con que arrancó."""
    try:
        marca = re.search(r"composefs=(\S+)", pathlib.Path("/proc/cmdline").read_text())
    except OSError:
        marca = None
    return marca[1][:12] if marca else os.uname().release


def leer(ruta):
    try:
        return pathlib.Path(ruta).read_text().strip()
    except OSError:
        return ""


def appid_de(pid):
    try:
        entorno = pathlib.Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
    except OSError:
        return None
    for variable in entorno:
        for clave in (b"SteamAppId=", b"SteamGameId="):
            if variable.startswith(clave) and variable[len(clave):].isdigit() and int(variable[len(clave):]) > 0:
                return int(variable[len(clave):])
    return None


def nombre_de(carpeta, appid, instalados):
    """El nombre con que lo conoce Steam; si no, el de su carpeta o su ejecutable."""
    if appid and appid in instalados:
        return instalados[appid]
    nombre = carpeta[:-4] if carpeta.endswith(".exe") else carpeta
    return nombre[:1].upper() + nombre[1:]


class Sesion:
    def __init__(self, carpeta, pid):
        self.carpeta = carpeta
        self.appid = appid_de(pid)
        self.inicio = time.time()
        self.fps = []
        self.temperaturas = []
        self.calor = 0
        self.muestras = 0
        self.cargador = en_cargador()

    def medir(self, fps):
        self.fps += fps
        temperatura, caliente = sensores()
        self.muestras += 1
        self.calor += caliente
        if temperatura is not None:
            self.temperaturas.append(temperatura)

    def resumen(self, fin, instalados):
        orden = sorted(self.fps)
        return {
            "juego": nombre_de(self.carpeta, self.appid, instalados), "appid": self.appid, "inicio": int(self.inicio),
            "minutos": max(1, round((fin - self.inicio) / 60)),
            "fps": round(statistics.fmean(self.fps), 1) if self.fps else None,
            "fps_bajo": round(orden[len(orden) // 20], 1) if orden else None,
            "gpu_temp": max(self.temperaturas) if self.temperaturas else None,
            "calor": round(self.calor / self.muestras, 3) if self.muestras else 0,
            "cargador": self.cargador, "version": version_del_sistema(),
            "nvidia": leer("/sys/module/nvidia/version"), "nucleo": os.uname().release.split("-")[0],
        }


def cerrar(sesion, archivo=ARCHIVO):
    fin = time.time()
    if sesion is None or fin - sesion.inicio < SEGUNDOS_MINIMOS:
        return
    registro = sesion.resumen(fin, juegos_instalados())
    registro["fallo"] = buscar_fallo(sesion.inicio)
    archivo.parent.mkdir(parents=True, exist_ok=True)
    with open(archivo, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


def procesos_de_juego(vistos):
    """{pid: juego} de esta cuenta. Cada proceso se revisa una sola vez."""
    vivos = {}
    for d in glob.glob("/proc/[0-9]*"):
        pid = int(os.path.basename(d))
        if pid not in vistos:
            try:
                vistos[pid] = juego_de(pathlib.Path(d, "cmdline").read_bytes().decode(errors="replace")) \
                    if os.stat(d).st_uid == os.getuid() else None
            except OSError:
                vistos[pid] = None
        vivos[pid] = vistos[pid]
    vistos.clear()
    vistos.update(vivos)
    return {pid: j for pid, j in vivos.items() if j}


def observar():
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    gamescope = Gamescope()
    gamescope.start()
    vistos = {}
    sesion = None
    try:
        while True:
            juegos = procesos_de_juego(vistos)
            if sesion and sesion.carpeta not in juegos.values():
                cerrar(sesion)
                sesion = None
            if juegos and not sesion:
                pid, carpeta = next(iter(juegos.items()))
                sesion = Sesion(carpeta, pid)
                gamescope.tomar()  # lo de antes no era de este juego
            if sesion:
                sesion.medir(gamescope.tomar())
            time.sleep(CADA)
    finally:
        cerrar(sesion)  # también al apagar o cerrar la sesión con el juego abierto


def autoprueba():
    estado = {}
    assert leer_estadistica("fps=60.5\n", estado) is None
    assert leer_estadistica("focus=1245620\n", estado) == 60.5
    leer_estadistica("fps=90\n", estado)
    assert leer_estadistica("focus=steam\n", estado) is None  # el menú de Steam no es el juego
    leer_estadistica("fps=basura\n", estado)
    assert leer_estadistica("focus=1\n", estado) is None

    assert "memoria" in fallo_de(["Out of memory: Killed process 123 (juego)"])
    xid = "NVRM: Xid (PCI:0000:01:00): {}, pid=1, name=juego"
    assert "dejó de responder" in fallo_de([xid.format(79)])
    assert "inválido" in fallo_de([xid.format(31)])
    assert fallo_de([xid.format(45)]) is None  # normal al cerrar un juego
    assert fallo_de([]) is None

    assert nombre_de("elden ring", 1245620, {1245620: "ELDEN RING"}) == "ELDEN RING"
    assert nombre_de("hades.exe", None, {}) == "Hades"
    assert nombre_de("roblox", None, {}) == "Roblox"

    s = Sesion("hades", os.getpid())
    s.fps = [float(n) for n in range(1, 101)]
    s.temperaturas = [70.0, 81.0]
    s.calor, s.muestras = 1, 4
    r = s.resumen(s.inicio + 600, {})
    assert (r["juego"], r["minutos"], r["fps"], r["fps_bajo"], r["gpu_temp"], r["calor"]) == ("Hades", 10, 50.5, 6.0, 81.0, 0.25)
    assert Sesion("x", os.getpid()).resumen(time.time(), {})["fps"] is None
    print("Observador: lectura de datos correcta")


if __name__ == "__main__":
    if "--autoprueba" in sys.argv:
        autoprueba()
    else:
        observar()

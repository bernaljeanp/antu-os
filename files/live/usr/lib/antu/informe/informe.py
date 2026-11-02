#!/usr/bin/env python3
"""Informe del equipo: reúne lo necesario para revisar cómo funciona Antu en este equipo, solo cuando se pide.

La interfaz vive en Informe.qml. Esta ventana reúne lo de la sesión (pantallas, sonido, Vulkan) y, si se activa, un
registro de temperaturas; lo que necesita privilegios, la limpieza de datos personales y el guardado los hace
/usr/lib/antu/informe-helper vía pkexec (regla de polkit del sistema en vivo). Nada se sube a internet.

--demo: muestra la interfaz sin ejecutar nada (capturas de CI).
"""
import json
import pathlib
import socket
import subprocess
import sys
import threading
import time

from PyQt6.QtCore import QObject, QUrl, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QDesktopServices, QGuiApplication, QIcon
from PyQt6.QtQml import QQmlApplicationEngine

HERE = pathlib.Path(__file__).resolve().parent
HELPER = "/usr/lib/antu/informe-helper"
ZENIT = "/run/zenit.sock"
CADA = 5  # segundos entre muestras
MAX_MUESTRAS = 4 * 3600 // CADA  # se detiene solo a las 4 horas
CONSULTA_GPU = ["nvidia-smi", "--format=csv,noheader,nounits",
                "--query-gpu=temperature.gpu,utilization.gpu,power.draw,clocks.gr,memory.used,pstate"]


def correr(orden):
    try:
        r = subprocess.run(orden, capture_output=True, text=True, errors="replace", timeout=25, stdin=subprocess.DEVNULL)
        return (r.stdout + r.stderr).strip()
    except (OSError, subprocess.SubprocessError) as e:
        return f"(no disponible: {e})"


def de_la_sesion():
    return "\n".join(f"\n===== {titulo} =====\n{contenido}" for titulo, contenido in [
        ("Sesión", correr(["sh", "-c", 'echo "$XDG_SESSION_TYPE $XDG_CURRENT_DESKTOP"'])),
        ("Pantallas", correr(["kscreen-doctor", "-o"])),
        ("Sonido en la sesión", correr(["pactl", "info"]) + "\n\n" + correr(["pactl", "list", "short", "sinks"])
         + "\n\n" + correr(["pactl", "list", "short", "sources"])),
        ("Vulkan", correr(["vulkaninfo", "--summary"])),
    ])


def muestra_zenit():
    """Temperaturas, ventiladores y perfil, de Zenit: ya los lee sin privilegios."""
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            s.connect(ZENIT)
            s.sendall(b'["estado"]\n')
            r = json.loads(s.makefile().readline())
        return f"perfil={r.get('perfil')} temperaturas={r.get('temperaturas')} ventiladores={r.get('ventiladores')}"
    except (OSError, ValueError):
        return "zenit=sin respuesta"


class Backend(QObject):
    terminado = pyqtSignal(str)
    cambioRegistro = pyqtSignal()

    def __init__(self, demo):
        super().__init__()
        self.demo = demo
        self._muestras = []
        self._parar = None

    @pyqtProperty(bool, notify=cambioRegistro)
    def registrando(self):
        return self._parar is not None

    @pyqtProperty(int, notify=cambioRegistro)
    def minutos(self):
        return len(self._muestras) * CADA // 60

    @pyqtSlot(bool)
    def registrar(self, activo):
        if self.demo or activo == self.registrando:
            return
        if activo:
            self._parar = threading.Event()
            threading.Thread(target=self._registro, args=(self._parar,), daemon=True).start()
        else:
            self._parar.set()
            self._parar = None
        self.cambioRegistro.emit()

    def _registro(self, parar):
        while not parar.is_set() and len(self._muestras) < MAX_MUESTRAS:
            carga = pathlib.Path("/proc/loadavg").read_text().split()[0]
            grafica = correr(CONSULTA_GPU).replace("\n", " | ")
            self._muestras.append(f"{time.strftime('%H:%M:%S')} carga={carga} gráfica=[{grafica}] {muestra_zenit()}")
            self.cambioRegistro.emit()
            parar.wait(CADA)

    @pyqtSlot()
    def crear(self):
        if not self.demo:
            threading.Thread(target=self._crear, daemon=True).start()

    def _crear(self):
        entrada = de_la_sesion()
        if self._muestras:
            entrada += ("\n\n===== Registro mientras se probaba =====\n"
                        "gráfica: °C, uso %, W, MHz, memoria MiB, estado\n" + "\n".join(self._muestras))
        try:
            r = subprocess.run(["pkexec", HELPER], input=entrada.encode(), capture_output=True, timeout=180)
        except (OSError, subprocess.SubprocessError) as e:
            self.terminado.emit(json.dumps({"error": str(e)}))
            return
        salida = r.stdout.decode(errors="replace").strip()
        if r.returncode == 0 and salida:
            self.terminado.emit(salida)
        else:
            self.terminado.emit(json.dumps({"error": r.stderr.decode(errors="replace").strip() or "Sin detalles."}))

    @pyqtSlot(str)
    def abrir(self, ruta):
        QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))


def main():
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Informe del equipo")
    app.setDesktopFileName("antu-informe")
    app.setWindowIcon(QIcon("/usr/share/antu/antu-symbol.svg"))
    backend = Backend(demo="--demo" in sys.argv)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(HERE / "Informe.qml")))
    if not engine.rootObjects():
        sys.exit(1)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

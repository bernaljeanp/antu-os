#!/usr/bin/env python3
"""Informe del equipo: consulta el registro automático y exporta una copia completa cuando se pide.

La interfaz vive en Informe.qml. Esta ventana reúne lo de la sesión (pantallas, sonido, Vulkan); el registro vive en
un servicio separado y sigue al cerrar la ventana. Lo que necesita privilegios, la limpieza y el guardado los hace
/usr/lib/antu/informe-helper vía pkexec (regla de polkit del sistema en vivo). Nada se sube a internet.

--demo: muestra la interfaz sin ejecutar nada (capturas de CI).
"""
import json
import pathlib
import subprocess
import sys
import threading

from PyQt6.QtCore import QObject, QTimer, QUrl, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QDesktopServices, QGuiApplication, QIcon
from PyQt6.QtQml import QQmlApplicationEngine

HERE = pathlib.Path(__file__).resolve().parent
HELPER = "/usr/lib/antu/informe-helper"
from registro import CARPETA


def correr(orden):
    try:
        r = subprocess.run(orden, capture_output=True, text=True, errors="replace", timeout=25, stdin=subprocess.DEVNULL)
        return (r.stdout + r.stderr).strip()
    except (OSError, subprocess.SubprocessError) as e:
        return f"(no disponible: {e})"


def de_la_sesion(rapida=False):
    return "\n".join(f"\n===== {titulo} =====\n{contenido}" for titulo, contenido in [
        ("Sesión", correr(["sh", "-c", 'echo "$XDG_SESSION_TYPE $XDG_CURRENT_DESKTOP"'])),
        ("Pantallas", correr(["kscreen-doctor", "-o"])),
        ("Sonido en la sesión", correr(["pactl", "info"]) + "\n\n" + correr(["pactl", "list", "short", "sinks"])
         + "\n\n" + correr(["pactl", "list", "short", "sources"])),
        ("Vulkan", "Se consulta al crear una copia completa, para no despertar las gráficas cada minuto."
         if rapida else correr(["vulkaninfo", "--summary"])),
        ("Servicios de la sesión con fallo", correr(["systemctl", "--user", "--failed", "--no-legend", "--plain"]) or "Ninguno."),
    ])


class Backend(QObject):
    terminado = pyqtSignal(str)
    cambioRegistro = pyqtSignal()

    def __init__(self, demo):
        super().__init__()
        self.demo = demo
        self._estado = {}
        self._creando = False
        self._cambiando = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refrescar)
        self._timer.start(2000)
        self.refrescar()

    def refrescar(self):
        try:
            estado = ({"activo": True, "muestras": 36, "segundos": 180, "usb": True} if self.demo
                      else json.loads((CARPETA / "estado.json").read_text()))
        except (OSError, ValueError):
            estado = {}
        if estado != self._estado:
            self._estado = estado
            self.cambioRegistro.emit()

    @pyqtProperty(bool, notify=cambioRegistro)
    def registrando(self):
        return bool(self._estado.get("activo"))

    @pyqtProperty(int, notify=cambioRegistro)
    def minutos(self):
        return int(self._estado.get("segundos", 0)) // 60

    @pyqtProperty(str, notify=cambioRegistro)
    def estadoRegistro(self):
        if not self._estado:
            return "Preparando el registro automático de esta prueba…"
        muestras = self._estado.get("muestras", 0)
        texto = f"{'Registrando' if self.registrando else 'Registro detenido'}: {muestras} muestras. "
        if self._estado.get("usb"):
            texto += "El último avance quedó guardado en ANTU_DATOS."
        else:
            texto += self._estado.get("error") or "El primer avance se guarda automáticamente en el USB."
        return texto

    @pyqtSlot(bool)
    def registrar(self, activo):
        if self.demo or self._cambiando or activo == self.registrando:
            return
        self._cambiando = True
        threading.Thread(target=self._registrar, args=(activo,), daemon=True).start()

    def _registrar(self, activo):
        try:
            opcion = "--iniciar-registro" if activo else "--detener-registro"
            r = subprocess.run(["pkexec", HELPER, opcion], capture_output=True, timeout=70)
            if r.returncode:
                self.terminado.emit(json.dumps({"error": "No se pudo cambiar el registro de la prueba."}))
        except (OSError, subprocess.SubprocessError) as e:
            self.terminado.emit(json.dumps({"error": str(e)}))
        finally:
            self._cambiando = False

    @pyqtSlot()
    def crear(self):
        if not self.demo and not self._creando:
            self._creando = True
            threading.Thread(target=self._crear, daemon=True).start()

    def _crear(self):
        entrada = de_la_sesion()
        try:
            r = subprocess.run(["pkexec", HELPER], input=entrada.encode(), capture_output=True, timeout=180)
        except (OSError, subprocess.SubprocessError) as e:
            self._creando = False
            self.terminado.emit(json.dumps({"error": str(e)}))
            return
        salida = r.stdout.decode(errors="replace").strip()
        self._creando = False
        if r.returncode == 0 and salida:
            self.terminado.emit(salida)
        else:
            self.terminado.emit(json.dumps({"error": r.stderr.decode(errors="replace").strip() or "Sin detalles."}))

    @pyqtSlot(str)
    def abrir(self, ruta):
        QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))


def main():
    if "--sesion-rapida" in sys.argv:
        print(de_la_sesion(rapida=True))
        return
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Informe del equipo")
    app.setDesktopFileName("antu-informe")
    app.setWindowIcon(QIcon("/usr/share/antu/antu-symbol.svg"))
    backend = Backend(demo="--demo" in sys.argv)
    engine = QQmlApplicationEngine()
    sys.path.insert(0, str(HERE.parent / "inicio"))
    import preferencias
    preferencias.instalar(app, engine)
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(HERE / "Informe.qml")))
    if not engine.rootObjects():
        sys.exit(1)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

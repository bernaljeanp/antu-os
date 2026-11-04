#!/usr/bin/env python3
"""Bienvenida del USB. Probar no instala; instalar abre el instalador y conserva su confirmación de borrado."""
import json
import pathlib
import subprocess
import sys

from PyQt6.QtCore import QObject, QTimer, QUrl, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QGuiApplication, QIcon
from PyQt6.QtQml import QQmlApplicationEngine

HERE = pathlib.Path(__file__).resolve().parent


class Backend(QObject):
    cambio = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, demo=False):
        super().__init__()
        self.demo = demo
        self._registro = {}
        self._reloj = QTimer(self, interval=2000)
        self._reloj.timeout.connect(self.refrescar)
        self._reloj.start()
        self.refrescar()

    def refrescar(self):
        try:
            estado = {"activo": True, "usb": True} if self.demo else json.loads(pathlib.Path("/run/antu-informe/estado.json").read_text())
        except (OSError, ValueError):
            estado = {}
        if estado != self._registro:
            self._registro = estado
            self.cambio.emit()

    @pyqtProperty(str, notify=cambio)
    def registro(self):
        if self._registro.get("activo"):
            if self._registro.get("usb"):
                return "El registro está activo y su último avance quedó guardado en el USB."
            if self._registro.get("error"):
                return "El registro está activo, pero el último avance no pudo guardarse en el USB. Revisa Informe del equipo."
            return "El registro está activo. El primer guardado en el USB está pendiente."
        return "Puedes revisar el registro y guardar los datos desde Informe del equipo."

    @pyqtSlot(str)
    def abrir(self, accion):
        rutas = {"instalar": "/usr/lib/antu/instalador/instalador.py", "informe": "/usr/lib/antu/informe/informe.py"}
        if accion not in rutas or self.demo:
            return
        try:
            subprocess.Popen([sys.executable, rutas[accion]], start_new_session=True)
            if accion == "instalar":
                QGuiApplication.quit()
        except OSError:
            self.error.emit("No se pudo abrir esa ventana. Puedes intentarlo de nuevo desde el menú de Antu.")


def main():
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Antu en vivo")
    app.setDesktopFileName("antu-bienvenida")
    app.setWindowIcon(QIcon("/usr/share/icons/hicolor/256x256/apps/antu.png"))
    backend = Backend("--demo" in sys.argv)
    engine = QQmlApplicationEngine()
    sys.path.insert(0, str(HERE.parent / "inicio"))
    import preferencias
    preferencias.instalar(app, engine)
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(HERE / "Bienvenida.qml")))
    if not engine.rootObjects():
        sys.exit(1)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

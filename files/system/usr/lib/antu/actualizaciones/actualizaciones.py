#!/usr/bin/env python3
"""Actualizaciones de Antu: qué versión tienes, buscar una nueva, reiniciar para aplicarla y volver a la anterior.

La interfaz vive en Actualizaciones.qml. Las órdenes las hace /usr/lib/antu/actualizar-helper vía pkexec (regla de
polkit para las cuentas administradoras). --demo: datos de ejemplo, sin ayudante (capturas de CI).
"""
import json
import pathlib
import sys

from PyQt6.QtCore import QObject, QProcess, QTimer, QUrl, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QGuiApplication, QIcon
from PyQt6.QtQml import QQmlApplicationEngine

HERE = pathlib.Path(__file__).resolve().parent
HELPER = "/usr/lib/antu/actualizar-helper"
DEMO = {"disponible": True, "instalada": "2026-11-02T06:14:00Z", "canal": "estable", "lista": False,
        "fecha_lista": None, "anterior": True, "buscando": False}


class Backend(QObject):
    cambio = pyqtSignal()
    aviso = pyqtSignal(str)

    def __init__(self, demo):
        super().__init__()
        self.demo = demo
        self._estado = dict(DEMO) if demo else {}
        self._cargado = demo
        self._consultando = False
        self.reloj = QTimer(self, interval=8000)
        self.reloj.timeout.connect(self.refrescar)
        self.reloj.start()
        self.refrescar()

    @pyqtProperty("QVariant", notify=cambio)
    def estado(self):
        return self._estado

    @pyqtProperty(bool, notify=cambio)
    def cargado(self):
        return self._cargado

    def ayudante(self, args, al_terminar):
        proceso = QProcess(self)

        def terminado(codigo, _estado):
            salida = bytes(proceso.readAllStandardOutput()).decode(errors="replace")
            error = bytes(proceso.readAllStandardError()).decode(errors="replace").strip()
            proceso.deleteLater()
            al_terminar(codigo, salida, error)

        proceso.finished.connect(terminado)
        proceso.start("pkexec", [HELPER, *args])

    @pyqtSlot()
    def refrescar(self):
        if self.demo or self._consultando:
            return
        self._consultando = True

        def listo(codigo, salida, _error):
            try:
                self._estado = json.loads(salida) if codigo == 0 else {}
            except ValueError:
                self._estado = {}
            self._consultando = False
            self._cargado = True
            self.cambio.emit()

        self.ayudante(["estado"], listo)

    def orden(self, nombre, mensaje):
        if self.demo:
            self._estado["buscando"] = nombre == "buscar"
            self.cambio.emit()
            return

        def listo(codigo, _salida, error):
            if codigo != 0:
                self.aviso.emit(error.splitlines()[-1] if error else mensaje)
            self.refrescar()

        self.ayudante([nombre], listo)

    @pyqtSlot()
    def buscar(self):
        self.orden("buscar", "No se pudo empezar a buscar actualizaciones.")

    @pyqtSlot()
    def volver(self):
        self.orden("volver", "No se pudo preparar la versión anterior.")

    @pyqtSlot()
    def reiniciar(self):
        if not self.demo:
            QProcess.startDetached("systemctl", ["reboot"])


def main():
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Actualizaciones de Antu")
    app.setDesktopFileName("antu-actualizaciones")
    app.setWindowIcon(QIcon.fromTheme("antu"))
    backend = Backend(demo="--demo" in sys.argv)
    engine = QQmlApplicationEngine()
    sys.path.insert(0, str(HERE.parent / "inicio"))
    import preferencias
    preferencias.instalar(app, engine)
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(HERE / "Actualizaciones.qml")))
    if not engine.rootObjects():
        sys.exit(1)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

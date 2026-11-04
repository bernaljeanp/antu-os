"""Preferencias compartidas de las apps: respeta la velocidad de animación elegida en KDE.

No crea configuración ni exige una app de ajustes adicional. Qt proporciona la paleta del sistema.
"""
from PyQt6.QtCore import QObject, QTimer, pyqtProperty, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from preferencias_config import factor_animacion


class Preferencias(QObject):
    cambio = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self._factor = factor_animacion()
        self._timer = QTimer(self, interval=2500)
        self._timer.timeout.connect(self.refrescar)
        self._timer.start()
        parent.fontChanged.connect(lambda *_: self.cambio.emit())

    @pyqtProperty(float, notify=cambio)
    def factorAnimacion(self):
        return self._factor

    @pyqtProperty(float, notify=cambio)
    def factorTexto(self):
        font = QGuiApplication.font()
        puntos = font.pointSizeF() if font.pointSizeF() > 0 else font.pixelSize() * 0.75
        return max(1.0, min(3.0, puntos / 10))

    def refrescar(self):
        valor = factor_animacion()
        if valor != self._factor:
            self._factor = valor
            self.cambio.emit()


def instalar(app, engine):
    preferencias = Preferencias(app)
    engine.rootContext().setContextProperty("antuPreferencias", preferencias)
    return preferencias

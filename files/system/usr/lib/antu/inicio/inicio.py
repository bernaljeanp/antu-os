#!/usr/bin/env python3
"""Inicio: asistente gráfico del primer arranque de Antu.

La interfaz vive en Inicio.qml. Las acciones con privilegios las hace /usr/lib/antu/inicio-helper vía pkexec
(regla de polkit solo para la cuenta antu-inicio). La contraseña viaja por la entrada estándar del ayudante.

--demo: muestra la interfaz sin ejecutar nada (capturas de CI).
"""
import pathlib
import re
import sys
import unicodedata

from PyQt6.QtCore import QObject, QProcess, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine

HERE = pathlib.Path(__file__).resolve().parent
HELPER = "/usr/lib/antu/inicio-helper"


def zones():
    """Zonas horarias de zone1970.tab, primero las de América."""
    tab = pathlib.Path("/usr/share/zoneinfo/zone1970.tab")
    if not tab.exists():
        return ["America/Santiago"]
    names = sorted({line.split("\t")[2] for line in tab.read_text().splitlines()
                    if line and not line.startswith("#")})
    america = [z for z in names if z.startswith("America/")]
    return america + [z for z in names if z not in america]


def suggest_user(real_name):
    """Nombre de usuario a partir del nombre: primera palabra, sin tildes, en minúsculas."""
    ascii_name = unicodedata.normalize("NFKD", real_name).encode("ascii", "ignore").decode()
    first = re.sub(r"[^a-z0-9]", "", (ascii_name.lower().split() or [""])[0])
    return first[:31] if first[:1].isalpha() else ""


class Backend(QObject):
    progress = pyqtSignal(str)
    failed = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, demo):
        super().__init__()
        self.demo = demo
        self.queue = []
        self.proc = None

    @pyqtSlot(result=list)
    def zones(self):
        return zones()

    @pyqtSlot(str, result=str)
    def suggestUser(self, real_name):
        return suggest_user(real_name)

    @pyqtSlot(str, str, str, str, str, str, str, bool, bool, bool)
    def apply(self, locale, keyboard, zone, real_name, user, password, desktop, ai, dev, oficina):
        steps = [
            ("Idioma", ["idioma", locale], None),
            ("Teclado", ["teclado", keyboard], None),
            ("Zona horaria", ["zona", zone], None),
            ("Tu cuenta", ["crear-usuario", user, real_name], password),
            ("Escritorio", ["escritorio", desktop], None),
        ]
        if ai:
            steps.append(("IA local", ["ia", "si"], None))
        if oficina:
            steps.append(("Oficina", ["oficina", "si"], None))
        if dev:
            steps.append(("Programación", ["programar", "si"], None))
        steps.append(("Terminando", ["terminar"], None))
        self.queue = steps
        self._next()

    def _next(self):
        if not self.queue:
            self.finished.emit()
            return
        label, args, stdin = self.queue.pop(0)
        self.progress.emit(label)
        if self.demo:
            self._next()
            return
        self.proc = QProcess(self)
        self.proc.finished.connect(lambda code, _status, label=label: self._done(code, label))
        self.proc.start("pkexec", [HELPER, *args])
        if stdin is not None:
            self.proc.write((stdin + "\n").encode())
        self.proc.closeWriteChannel()

    def _done(self, code, label):
        if code == 0:
            self._next()
            return
        error = bytes(self.proc.readAllStandardError()).decode(errors="replace").strip()
        self.queue = []
        self.failed.emit(f"{label}: {error or 'no se pudo completar.'}")


def main():
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Antu Inicio")
    backend = Backend(demo="--demo" in sys.argv)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(HERE / "Inicio.qml")))
    if not engine.rootObjects():
        sys.exit(1)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Carga la interfaz real y sus recursos, sin demonio ni acceso al hardware."""
import importlib.util
import os
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
from PyQt6.QtCore import QTimer, QUrl
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtWidgets import QApplication
from PyQt6 import sip

# Se puede apuntar a una instalación, no solo al árbol del repositorio.
base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "files/system/usr/lib/antu"
spec = importlib.util.spec_from_file_location("zenit_app", base / "zenit/app.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sys.path.insert(0, str(base / "inicio"))
import preferencias

app = QApplication([])
backend = module.Backend(True)
engine = QQmlApplicationEngine()
preferencias.instalar(app, engine)
engine.rootContext().setContextProperty("backend", backend)
engine.rootContext().setContextProperty("zenitIcon", QUrl.fromLocalFile(module.ICONO))
errors = []
engine.warnings.connect(lambda warnings: errors.extend(str(w) for w in warnings))
engine.load(QUrl.fromLocalFile(str(base / "zenit/Zenit.qml")))
assert engine.rootObjects(), "La ventana no se pudo crear"
window = engine.rootObjects()[0]
window.show()
QTimer.singleShot(500, app.quit)
app.exec()
sip.delete(engine)  # destruir las vinculaciones QML antes del backend
assert not errors, "\n".join(errors)
print("Zenit UI: ventana y recursos cargados sin errores QML")

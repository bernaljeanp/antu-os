#!/usr/bin/env python3
"""Carga la interfaz real y sus recursos, sin demonio ni acceso al hardware."""
import importlib.util
import os
from pathlib import Path
import sys
import json
import stat
import tempfile
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
from PyQt6.QtCore import QTimer, QUrl
from PyQt6.QtGui import QColor, QPalette
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
# El símbolo debe conservar transparencia y adoptar colores claros y oscuros.
for color in ("#eeeeee", "#222222"):
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.WindowText, QColor(color))
    image = module.icono_bandeja(palette).pixmap(22, 22).toImage()
    assert image.pixelColor(0, 0).alpha() == 0
    assert image.pixelColor(11, 7).name() == color
assert hasattr(app, "paletteChanged")
backend = module.Backend(True)
# Exportación real: selección de archivo, respuesta del servicio y permisos privados.
with tempfile.TemporaryDirectory() as directory:
    target = Path(directory) / "diagnostico.json"
    backend.demo = False
    with patch("PyQt6.QtWidgets.QFileDialog.getSaveFileName", return_value=(str(target), "")), patch.object(backend, "_enviar", return_value=True) as send:
        backend.exportarDiagnostico()
        send.assert_called_once_with(["diagnostico"])
    report = {"formato": "zenit-diagnostico", "version": 1}
    with patch.object(backend, "refrescar"):
        backend._recibir(["diagnostico"], {"ok": True, "informe": report})
    assert json.loads(target.read_text()) == report
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    with patch.object(module.os, "replace", side_effect=OSError("fallo simulado")):
        try:
            module.guardar_informe(target, {"nuevo": True})
        except OSError:
            pass
        else:
            raise AssertionError("No propagó el fallo de guardado")
    assert json.loads(target.read_text()) == report
    assert list(Path(directory).glob(".zenit-diagnostico-*")) == []
backend.demo = True
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
backend.gestion("sistema")
backend._estado["prueba_teclas"] = {"segundos_restantes": 10, "eventos": [{"tecla": "F6", "pulsaciones": 1}]}
backend._estado["ventiladores"] = {"Sensor sin lectura": None, "Sensor cero": 0, "Sensor activo": 2300}
backend.cambio.emit()
QTimer.singleShot(500, app.quit)
app.exec()
sip.delete(engine)  # destruir las vinculaciones QML antes del backend
assert not errors, "\n".join(errors)
print("Zenit UI: ventana y recursos cargados sin errores QML")

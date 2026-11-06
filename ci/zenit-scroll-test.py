#!/usr/bin/env python3
"""Una lectura de sensores no debe reconstruir el control ni mover la página."""
import copy
import importlib.util
import os
from pathlib import Path
import sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtQuick import QQuickItem
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
from PyQt6 import sip

base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "files/system/usr/lib/antu"
spec = importlib.util.spec_from_file_location("zenit_app", base / "zenit/app.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
sys.path.insert(0, str(base / "inicio"))
import preferencias
app = QApplication([])
backend = m.Backend(True)
backend.reloj.stop()
backend._estado["baterias"] = [{"nombre": "BAT0", "porcentaje": 80, "salud_porcentaje": 95, "ciclos": 10}]
engine = QQmlApplicationEngine()
preferencias.instalar(app, engine)
engine.rootContext().setContextProperty("backend", backend)
engine.rootContext().setContextProperty("zenitIcon", QUrl.fromLocalFile(m.ICONO))
engine.load(QUrl.fromLocalFile(str(base / "zenit/Zenit.qml")))
assert engine.rootObjects()
window = engine.rootObjects()[0]
window.show()
QTest.qWait(100)
def find(item, name):
    if item.objectName() == name:
        return item
    for child in item.childItems():
        result = find(child, name)
        if result is not None:
            return result
    return None
page = find(window.contentItem(), "zenit-scroll")
combo = find(window.contentItem(), "zenit-game-profile")
assert page is not None and combo is not None
combo.forceActiveFocus(Qt.FocusReason.TabFocusReason)
QTest.qWait(100)
assert page.property("contentY") > 100, "Tab no hizo visible el control inferior"
# El usuario se desplaza al principio, conservando el foco en un control inferior.
page.setProperty("contentY", 100)
for i in range(4):
    backend._busy = True
    backend.cambio.emit()
    QTest.qWait(30)
    state = copy.deepcopy(backend._estado)
    state["temperaturas"]["CPU"] = 60 + i
    state["ultima_muestra"] = i
    state["baterias"][0]["porcentaje"] = 80 - i
    backend._recibir(["estado"], state)
    QTest.qWait(50)
    assert not sip.isdeleted(combo), "La lectura reconstruyó el selector de perfil"
    assert abs(page.property("contentY") - 100) < 2, f"La lectura movió la página a {page.property('contentY')}"
# La navegación explícita con Tab debe seguir revelando los controles fuera de vista.
combo.forceActiveFocus(Qt.FocusReason.OtherFocusReason)
QTest.qWait(20)
page.setProperty("contentY", 100)
QTest.keyClick(window, Qt.Key.Key_Tab)
QTest.qWait(50)
assert page.property("contentY") > 100, "Se perdió el desplazamiento accesible con Tab"
sip.delete(engine)
print("Scroll Zenit: posición y controles conservados durante las lecturas")

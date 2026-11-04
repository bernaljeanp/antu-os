#!/usr/bin/env python3
"""Zenit: la app de Antu para el rendimiento, la temperatura, los juegos, las luces y la batería del equipo.

La interfaz vive en Zenit.qml y habla con el servicio zenit (zenit.py demonio) por /run/zenit.sock.
  --bandeja  arranca junto al reloj, sin ventana; un clic en el ícono la abre
  --demo     datos de ejemplo, sin servicio (capturas de CI)
"""
import glob
import json
import math
import os
import pathlib
import re
import socket
import sys

from PyQt6.QtCore import QObject, QTimer, QUrl, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QIcon
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

HERE = pathlib.Path(__file__).resolve().parent
SOCKET = "/run/zenit.sock"
ICONO = "/usr/share/icons/hicolor/256x256/apps/zenit.png"
PERFILES = {"quiet": "Silencioso", "balanced": "Equilibrado", "balanced-performance": "Equilibrado+",
            "performance": "Rendimiento", "cool": "Fresco", "low-power": "Ahorro de batería"}
STEAM = pathlib.Path.home() / ".local/share/Steam/steamapps"
HERRAMIENTAS = ("proton", "steamlinuxruntime", "steamworks")

DEMO = {
    "ok": True, "perfil": "balanced-performance", "modo": "auto", "cargador": True, "juego": None, "boost": False,
    "sigilo": False, "temperaturas": {"CPU": 61, "GPU": 54}, "ventiladores": {"CPU": 2210, "GPU": 1980},
    "luces": {"color": "FF5A1F", "brillo": 100}, "carga": "hasta 80 %", "carga_modo": "Custom", "carga_tope": 80,
    "perfiles": ["quiet", "balanced", "balanced-performance", "performance"],
    "juegos": {"cyberpunk 2077": "performance"},
}


def pedir(args):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.settimeout(60)
        s.connect(SOCKET)
        s.sendall((json.dumps(args) + "\n").encode())
        return json.loads(s.makefile().readline())


def juegos_de_steam():
    """Carpetas de juegos de Steam (también de otras bibliotecas), sin Proton ni sus herramientas."""
    carpetas = [STEAM]
    try:
        vdf = (STEAM / "libraryfolders.vdf").read_text(errors="replace")
        carpetas += [pathlib.Path(p) / "steamapps" for p in re.findall(r'"path"\s+"([^"]+)"', vdf)]
    except OSError:
        pass
    nombres = set()
    for c in carpetas:
        for d in glob.glob(str(c / "common" / "*")):
            nombre = os.path.basename(d)
            if os.path.isdir(d) and not nombre.lower().startswith(HERRAMIENTAS):
                nombres.add(nombre)
    return sorted(nombres, key=str.lower)


class Backend(QObject):
    cambio = pyqtSignal()
    aviso = pyqtSignal(str)

    def __init__(self, demo):
        super().__init__()
        self.demo = demo
        self._estado = dict(DEMO) if demo else {}
        self.reloj = QTimer(self, interval=2000)
        self.reloj.timeout.connect(self.refrescar)
        self.reloj.start()
        self.refrescar()

    @pyqtProperty("QVariant", notify=cambio)
    def estado(self):
        return self._estado

    @pyqtProperty(bool, notify=cambio)
    def conectado(self):
        return bool(self._estado)

    @pyqtProperty("QVariant", constant=True)
    def nombresPerfil(self):
        return PERFILES

    @pyqtProperty(list, constant=True)
    def historiaInicial(self):
        # Demo: dos minutos de un juego que arranca y se asienta.
        return [round(52 + 22 * math.sin(i / 9) ** 2 + 4 * math.sin(i / 2)) for i in range(60)] if self.demo else []

    @pyqtSlot()
    def refrescar(self):
        if self.demo:
            self._tic = getattr(self, "_tic", 0) + 1
            self._estado["temperaturas"] = {"CPU": round(61 + 3 * math.sin(self._tic / 3)), "GPU": 54}
            self.cambio.emit()
            return
        try:
            self._estado = pedir(["estado"])
        except (OSError, ValueError):
            self._estado = {}
        self.cambio.emit()

    def orden(self, args, demo_cambio=None):
        if self.demo:
            if demo_cambio:
                demo_cambio()
            self.cambio.emit()
            return True
        try:
            r = pedir(args)
        except PermissionError:
            self.aviso.emit("Zenit solo atiende a las cuentas administradoras de este equipo.")
            return False
        except (OSError, ValueError):
            self.aviso.emit("El servicio Zenit no responde. Reinicia el equipo si sigue así.")
            return False
        if not r.get("ok"):
            self.aviso.emit(r.get("error", "Zenit no pudo hacerlo."))
        self.refrescar()
        return bool(r.get("ok"))

    @pyqtSlot(str)
    def perfil(self, nombre):
        self.orden(["perfil", nombre], lambda: self._estado.update(
            modo=nombre, perfil=self._estado["perfil"] if nombre == "auto" else nombre))

    @pyqtSlot(str, int)
    def luces(self, color, brillo):
        self.orden(["color", color, str(brillo)], lambda: self._estado.update(luces={"color": color, "brillo": brillo}))

    @pyqtSlot(str)
    def carga(self, valor):
        self.orden(["carga", valor], lambda: self._estado.update(
            carga_modo="Adaptive" if valor == "adaptativa" else "Custom",
            carga_tope=0 if valor == "adaptativa" else int(valor)))

    @pyqtSlot(str, str)
    def juego(self, nombre, perfil):
        def demo():
            juegos = dict(self._estado.get("juegos") or {})
            if perfil == "auto":
                juegos.pop(nombre.lower(), None)
            else:
                juegos[nombre.lower()] = perfil
            self._estado["juegos"] = juegos
        self.orden(["juego", nombre, perfil], demo)

    @pyqtSlot(result=list)
    def juegosSteam(self):
        return ["Cyberpunk 2077", "Hades II", "Counter-Strike 2", "Elden Ring"] if self.demo else juegos_de_steam()


def main():
    demo = "--demo" in sys.argv
    bandeja = "--bandeja" in sys.argv
    app = QApplication(sys.argv)
    # Una sola Zenit por sesión: si ya está junto al reloj, se le pide que muestre su ventana y esta se cierra.
    nombre_unico = f"zenit-{os.getuid()}"
    otra = QLocalSocket()
    otra.connectToServer(nombre_unico)
    if otra.waitForConnected(300):
        if not bandeja:
            otra.write(b"mostrar")
            otra.waitForBytesWritten(300)
        sys.exit(0)
    QLocalServer.removeServer(nombre_unico)
    unica = QLocalServer()
    unica.listen(nombre_unico)
    app.setApplicationName("Zenit")
    app.setDesktopFileName("zenit")
    app.setWindowIcon(QIcon(ICONO))
    app.setQuitOnLastWindowClosed(False)
    backend = Backend(demo)
    engine = QQmlApplicationEngine()
    sys.path.insert(0, str(HERE.parent / "inicio"))
    import preferencias
    preferencias.instalar(app, engine)
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(HERE / "Zenit.qml")))
    if not engine.rootObjects():
        sys.exit(1)
    ventana = engine.rootObjects()[0]

    def mostrar():
        ventana.show()
        ventana.raise_()
        ventana.requestActivate()

    unica.newConnection.connect(lambda: (unica.nextPendingConnection(), mostrar()))
    icono = QSystemTrayIcon(QIcon(ICONO))
    menu = QMenu()
    menu.addAction("Abrir Zenit", mostrar)
    menu.addSeparator()
    for clave, nombre in [("auto", "Automático"), ("quiet", "Silencioso"), ("balanced", "Equilibrado"),
                          ("balanced-performance", "Equilibrado+"), ("performance", "Rendimiento")]:
        menu.addAction(nombre, lambda clave=clave: backend.perfil(clave))
    menu.addSeparator()
    menu.addAction("Salir", app.quit)
    icono.setContextMenu(menu)
    icono.activated.connect(lambda motivo: mostrar() if motivo == QSystemTrayIcon.ActivationReason.Trigger else None)

    def resumen():
        e = backend.estado
        if not e:
            icono.setToolTip("Zenit · el servicio no responde")
            return
        temps = " · ".join(f"{k} {v} °C" for k, v in e.get("temperaturas", {}).items())
        icono.setToolTip(f"Zenit · {PERFILES.get(e.get('perfil'), e.get('perfil') or 'sin perfil')}"
                         + (f" · {temps}" if temps else ""))

    backend.cambio.connect(resumen)
    resumen()
    icono.show()
    if not bandeja:
        mostrar()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Aviso: una pregunta o un aviso con el material de Antu, para usar desde un guion. Sale con 0 si se acepta y con 1 si no.

  aviso.py --titulo T --texto X --aceptar "Entrar" [--cancelar "Ahora no"] [--tipo atencion|bien|peligro]

--demo: un aviso de ejemplo (capturas de CI).
"""
import argparse
import os
import pathlib
import sys

from PyQt6.QtCore import QObject, QUrl, pyqtProperty, pyqtSlot
from PyQt6.QtGui import QGuiApplication, QIcon
from PyQt6.QtQml import QQmlApplicationEngine

HERE = pathlib.Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--titulo", default="Entrar a Eclipse")
    p.add_argument("--texto", default="Steam se abrirá a pantalla completa y se cerrarán las ventanas del escritorio.")
    p.add_argument("--aceptar", default="Aceptar")
    p.add_argument("--cancelar", default="")
    p.add_argument("--tipo", default="atencion", choices=("atencion", "bien", "peligro"))
    p.add_argument("--demo", action="store_true")
    datos = p.parse_args()
    if datos.demo:
        datos.aceptar, datos.cancelar = "Entrar a Eclipse", "Ahora no"

    app = QGuiApplication(sys.argv[:1])
    app.setApplicationName(datos.titulo)
    app.setDesktopFileName("antu-aviso")
    app.setWindowIcon(QIcon("/usr/share/antu/antu-symbol.svg"))

    class Backend(QObject):
        @pyqtProperty(str, constant=True)
        def titulo(self):
            return datos.titulo

        @pyqtProperty(str, constant=True)
        def texto(self):
            return datos.texto

        @pyqtProperty(str, constant=True)
        def aceptar(self):
            return datos.aceptar

        @pyqtProperty(str, constant=True)
        def cancelar(self):
            return datos.cancelar

        @pyqtProperty(str, constant=True)
        def tipo(self):
            return datos.tipo

        @pyqtSlot(int)
        def salir(self, codigo):
            app.exit(codigo)

    backend = Backend()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(HERE / "VentanaAviso.qml")))
    if not engine.rootObjects():
        sys.exit(2)
    codigo = app.exec()
    os._exit(codigo)  # sin desarmar la interfaz: su código es lo único que importa


if __name__ == "__main__":
    main()

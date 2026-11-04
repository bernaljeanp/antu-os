#!/usr/bin/env python3
"""Descarga gráfica: no instala ni graba discos. GPL-3.0-or-later."""
import concurrent.futures
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
import threading
import urllib.request

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from PyQt6.QtCore import QObject, Qt, QTimer, QUrl, QTranslator, QLibraryInfo, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QFont, QFontDatabase, QIcon
from PyQt6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel, QMainWindow,
                            QProgressBar, QPushButton, QVBoxLayout, QWidget)

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("antu_download", ROOT / "descargar-antu.py")
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
RELEASES = "https://github.com/bernaljeanp/antu-os/releases"


def message(error):
    if isinstance(error, (ValueError, FileExistsError)) and not isinstance(error, json.JSONDecodeError):
        return str(error)
    return "No se pudo conectar o guardar el archivo. Comprueba internet y el destino y vuelve a intentarlo."


def signature(public, signed, data):
    try:
        key = serialization.load_pem_public_key(public)
        if not isinstance(key, ec.EllipticCurvePublicKey):
            raise ValueError("La llave de Antu no es válida.")
        key.verify(signed, data, ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        raise ValueError("La firma no coincide. No se entrega una ISO sin verificar.") from None


def latest():
    request = urllib.request.Request("https://api.github.com/repos/bernaljeanp/antu-os/releases?per_page=10",
                                     headers={"User-Agent": "Antu-Descargas/1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        releases = json.loads(response.read(1024**2))
    for release in releases:
        assets = {asset["name"] for asset in release.get("assets", [])}
        tag = release.get("tag_name", "")
        if not release.get("draft") and {"release.json", "release.json.sig"} <= assets and re.fullmatch(r"[A-Za-z0-9._-]{1,100}", tag):
            return tag
    raise ValueError("Todavía no hay una ISO firmada publicada. Puedes consultar las versiones e intentarlo más tarde.")


class Cancelled(Exception):
    pass


def download(tag, output, update, cancelled):
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,100}", tag):
        raise ValueError("Versión no válida.")
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError("Ese archivo ya existe. Elige otro nombre para conservarlo.")
    directory = output.parent / (".antu-descarga-" + tag)
    directory.mkdir(exist_ok=True)
    base = f"{RELEASES}/download/{tag}/"

    def state(text, received=0, total=0):
        if cancelled.is_set():
            raise Cancelled()
        update(text, received, total)

    state("Comprobando la firma de Antu…")
    for name, limit in (("release.json", 128 * 1024), ("release.json.sig", 4096)):
        engine.fetch(base + name, directory / name, lambda _: state("Comprobando la firma de Antu…"), limit)
    data = engine.verify(directory / "release.json", directory / "release.json.sig", directory, signature)
    required = data["size"] * 2 + 1024**3
    if shutil.disk_usage(output.parent).free < required:
        raise ValueError(f"Falta espacio. Necesitas aproximadamente {required / 10**9:.1f} GB para las partes y la ISO.")
    completed = 0
    for index, part in enumerate(data["parts"], 1):
        path = directory / part["name"]
        state(f"Comprobando parte {index} de {len(data['parts'])}…", completed, data["size"])
        if not path.exists() or path.stat().st_size != part["size"] or engine.digest(path) != part["sha256"]:
            def progress(received):
                state(f"Descargando parte {index} de {len(data['parts'])}", completed + received, data["size"])
            engine.fetch(base + part["name"], path, progress, part["size"])
        if path.stat().st_size != part["size"] or engine.digest(path) != part["sha256"]:
            raise ValueError("Una parte no coincide con la firma. Pulsa Descargar para volver a intentarlo.")
        completed += part["size"]
    state("Reuniendo y verificando la ISO…", 0, data["size"])
    engine.assemble(data, directory, output,
                    lambda received: state("Reuniendo y verificando la ISO…", received, data["size"]))
    return output


class Events(QObject):
    version = pyqtSignal(str)
    progress = pyqtSignal(str, object, object)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)


class Window(QMainWindow):
    def __init__(self, demo=False):
        super().__init__()
        self.setWindowTitle("Descargar Antu")
        self.setMinimumSize(620, 540)
        self.resize(720, 620)
        self.tag = ""
        self.busy = False
        self.output = None
        self.cancelled = threading.Event()
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.events = Events()
        self.events.version.connect(self.version)
        self.events.progress.connect(self.progress)
        self.events.finished.connect(self.finished)
        self.events.error.connect(self.error)
        self.setStyleSheet("""
          QMainWindow, QWidget { background: #1C1C21; color: #F5F5F7; }
          QLabel#title { font-size: 30px; font-weight: 600; }
          QLabel#secondary { color: #C7C7CC; }
          QLabel#status { color: #FF783D; }
          QPushButton { background: #303037; border: 1px solid #6D6D76; border-radius: 8px; padding: 11px 18px; }
          QPushButton:hover { background: #3C3C44; }
          QPushButton:focus { border: 2px solid #FF783D; padding: 10px 17px; }
          QPushButton:disabled { color: #A1A1A6; background: #26262D; }
          QPushButton#primary { background: #B9370D; border-color: #FF783D; font-weight: 600; }
          QPushButton#primary:hover { background: #CF4314; }
          QPushButton#primary:disabled { background: #533128; border-color: #725A52; }
          QProgressBar { border: 1px solid #74747D; border-radius: 5px; background: #141418; min-height: 10px; }
          QProgressBar::chunk { background: #FF783D; border-radius: 4px; }
        """)
        body = QWidget(); layout = QVBoxLayout(body)
        layout.setContentsMargins(36, 32, 36, 32); layout.setSpacing(18)
        symbol = ROOT / "antu-icon-256.png"
        if not symbol.exists():
            symbol = ROOT.parent / "brand/antu-icon-256.png"
        if symbol.exists():
            self.setWindowIcon(QIcon(str(symbol)))
            mark = QLabel(); mark.setPixmap(QIcon(str(symbol)).pixmap(72, 72)); layout.addWidget(mark)
        title = QLabel("Tu USB de Antu empieza aquí"); title.setObjectName("title"); title.setWordWrap(True); layout.addWidget(title)
        explanation = QLabel("Descarga la ISO y comprueba que sea la original. Después podrás grabarla con USBoot.")
        explanation.setWordWrap(True); explanation.setObjectName("secondary"); layout.addWidget(explanation)
        self.release = QLabel("Buscando la versión publicada…"); self.release.setWordWrap(True); layout.addWidget(self.release)
        self.status = QLabel("Conectando con las versiones de Antu…"); self.status.setObjectName("status")
        self.status.setWordWrap(True); self.status.setTextFormat(Qt.TextFormat.PlainText); layout.addWidget(self.status)
        self.bar = QProgressBar(); self.bar.setTextVisible(False); self.bar.setRange(0, 0); layout.addWidget(self.bar)
        self.amount = QLabel("Las partes válidas se conservan si interrumpes la descarga.")
        self.amount.setWordWrap(True); self.amount.setObjectName("secondary"); layout.addWidget(self.amount)
        layout.addStretch()
        note = QLabel("Esta aplicación solo descarga archivos. No modifica discos ni graba el USB.")
        note.setWordWrap(True); note.setObjectName("secondary"); layout.addWidget(note)
        row = QHBoxLayout(); row.setSpacing(12)
        self.other = QPushButton("Ver versiones"); self.other.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(RELEASES)))
        row.addWidget(self.other); row.addStretch()
        self.action = QPushButton("Descargar ISO…"); self.action.setObjectName("primary"); self.action.setEnabled(False)
        self.action.clicked.connect(self.start); row.addWidget(self.action); layout.addLayout(row)
        self.setCentralWidget(body)
        if demo:
            self.version("antu-preview · demostración")
            self.action.setEnabled(False)
            self.progress("Descargando parte 2 de 4 · demostración", 2900000000, 7100000000)
        else:
            self.lookup()

    def lookup(self):
        self.action.setEnabled(False)
        def work():
            try: self.events.version.emit(latest())
            except Exception as error: self.events.error.emit(message(error))
        self.pool.submit(work)

    def version(self, tag):
        self.tag = tag
        self.release.setText("Versión de prueba · " + tag)
        self.status.setText("Elige dónde guardar la ISO.")
        self.bar.setRange(0, 1000); self.bar.setValue(0)
        self.action.setText("Descargar ISO…"); self.action.setEnabled(True)

    def start(self):
        if self.busy:
            self.cancelled.set(); self.action.setEnabled(False)
            self.status.setText("Deteniendo la descarga… Puede tardar hasta 90 segundos si la conexión no responde.")
            return
        if self.output:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.output.parent)))
            return
        if not self.tag:
            self.status.setText("Buscando la versión publicada…"); self.lookup(); return
        path, _ = QFileDialog.getSaveFileName(self, "Guardar ISO de Antu", str(Path.home() / "Downloads/antu-live.iso"),
                                             "Imagen de disco (*.iso)", options=QFileDialog.Option.DontConfirmOverwrite)
        if not path: return
        if Path(path).exists():
            self.error("Ese archivo ya existe. Elige un nombre nuevo para conservarlo."); return
        self.busy = True; self.cancelled.clear(); self.action.setText("Detener")
        def work():
            try:
                output = download(self.tag, path, self.events.progress.emit, self.cancelled)
                self.events.finished.emit(output)
            except Cancelled:
                self.events.error.emit("Descarga detenida. Pulsa Descargar para continuar; se conservan las partes ya verificadas.")
            except Exception as error:
                self.events.error.emit(message(error))
        self.pool.submit(work)

    def progress(self, text, received, total):
        if self.cancelled.is_set(): return
        self.status.setText(text)
        if total:
            self.bar.setRange(0, 1000); self.bar.setValue(int(received * 1000 / total))
            self.amount.setText(f"{received / 10**9:.2f} de {total / 10**9:.2f} GB")
        else:
            self.bar.setRange(0, 0)

    def finished(self, output):
        self.busy = False; self.output = Path(output)
        self.status.setText("ISO lista. Firma y contenido verificados.")
        self.amount.setText(str(self.output) + "\nAbre USBoot y selecciona esta imagen para grabarla.")
        self.bar.setRange(0, 1000); self.bar.setValue(1000)
        self.action.setText("Abrir carpeta"); self.action.setEnabled(True)

    def error(self, text):
        self.busy = False
        self.status.setText(text)
        self.bar.setRange(0, 1000); self.bar.setValue(0)
        self.action.setText("Descargar ISO…" if self.tag else "Reintentar")
        self.action.setEnabled(True)

    def closeEvent(self, event):
        if self.busy:
            self.cancelled.set()
            self.status.setText("Deteniendo antes de cerrar. Se conservan las partes verificadas.")
            self.action.setEnabled(False)
            self.events.error.connect(lambda _: self.close())
            self.events.finished.connect(lambda _: self.close())
            event.ignore()
        else:
            self.pool.shutdown(wait=False, cancel_futures=True)
            event.accept()


def main():
    # Recorrido automático del ejecutable empaquetado en CI, sin ventanas ni grabación de discos.
    if "--verificar-version" in sys.argv:
        output = Path(os.environ["ANTU_ISO_PRUEBA"])
        output.parent.mkdir(parents=True, exist_ok=True)
        tag = sys.argv[sys.argv.index("--verificar-version") + 1]
        download(tag, output, lambda *_: None, threading.Event())
        report = Path(os.environ["ANTU_CAPTURAS"]) / "descarga-publica.json"
        report.write_text(json.dumps({"version": tag, "bytes": output.stat().st_size,
                                      "sha256": engine.digest(output), "firma": "verificada"}) + "\n", newline="\n")
        return 0
    demo = "--autoprueba" in sys.argv
    if demo: os.environ.setdefault("QT_SCALE_FACTOR", "3")
    app = QApplication(sys.argv)
    translator = QTranslator(app)
    if translator.load("qtbase_es", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
        app.installTranslator(translator)
    font = ROOT / "Inter-Variable.ttf"
    if not font.exists(): font = ROOT.parent / "files/system/usr/share/fonts/antu/Inter-Variable.ttf"
    if font.exists(): QFontDatabase.addApplicationFont(str(font))
    app.setFont(QFont("Inter", 11))
    window = Window(demo); window.show()
    if demo:
        window.resize(1280, 720)
        def capture():
            output = Path(os.environ.get("ANTU_CAPTURAS", ".")); output.mkdir(exist_ok=True, parents=True)
            if not window.grab().save(str(output / "descarga-4k.png")):
                raise RuntimeError("No se pudo capturar la ventana.")
            # Ejecuta el motor de firma también dentro del binario empaquetado.
            key = ec.generate_private_key(ec.SECP256R1())
            public = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
            data = b"Prueba local de Antu"; signed = key.sign(data, ec.ECDSA(hashes.SHA256()))
            signature(public, signed, data)
            try: signature(public, signed, data + b"alterado")
            except ValueError: pass
            else: raise RuntimeError("Se aceptó una firma alterada.")
            (output / "descarga-prueba.json").write_text(json.dumps({"firma": "correcta", "alteracion": "rechazada", "demo": True}) + "\n", newline="\n")
            window.close(); app.quit()
        QTimer.singleShot(500, capture)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

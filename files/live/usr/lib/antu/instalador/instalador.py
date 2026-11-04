#!/usr/bin/env python3
"""Instalador de Antu: copia Antu del USB en vivo a un disco completo.

La interfaz vive en Instalador.qml. El borrado y la copia los hace /usr/lib/antu/instalador-helper vía pkexec (regla
de polkit del sistema en vivo). Idioma, cuenta y escritorio se eligen después, en Inicio.

--demo: muestra la interfaz con discos de ejemplo, sin ejecutar nada (capturas de CI).
"""
import json
import pathlib
import subprocess
import sys

from PyQt6.QtCore import QObject, QProcess, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QGuiApplication, QIcon
from PyQt6.QtQml import QQmlApplicationEngine

HERE = pathlib.Path(__file__).resolve().parent
HELPER = "/usr/lib/antu/instalador-helper"
LOG = pathlib.Path.home() / "antu-instalar.log"
MIN_SIZE = 40 * 10**9
TRANSPORTS = {"nvme": "NVMe", "sata": "SATA", "usb": "USB", "mmc": "Tarjeta SD"}
# Palabras de la salida de bootc que marcan cada etapa (la 0, preparar el disco, es la inicial).
STAGE_WORDS = [(), ("fetch", "pull", "layer", "import", "deploy", "object"), ("bootloader", "bootctl", "systemd-boot")]

DEMO_DISKS = [
    {"path": "/dev/nvme0n1", "name": "Samsung SSD 990 PRO 1TB", "detail": "NVMe · 1 TB", "kind": "disco",
     "windows": True, "contents": "Tiene particiones de Windows.",
     "parts": ["VFAT · 105 MB", "Windows · NTFS · 999 GB", "Recuperación · NTFS · 1 GB"], "reason": ""},
    {"path": "/dev/sda", "name": "SanDisk Extreme Pro", "detail": "USB · 256 GB", "kind": "usb",
     "windows": False, "contents": "Vacío.", "parts": [], "reason": ""},
    {"path": "/dev/sdb", "name": "Kingston DataTraveler", "detail": "USB · 16 GB", "kind": "usb",
     "windows": False, "contents": "", "parts": [], "reason": "Está en uso: es el USB de Antu o tiene algo abierto."},
]


def size_label(size):
    """Tamaño como lo escriben los fabricantes: 512 GB, 1 TB, 1,5 TB."""
    if size >= 10**12:
        return f"{size / 10**12:.1f}".removesuffix(".0").replace(".", ",") + " TB"
    if size >= 10**9:
        return f"{round(size / 10**9)} GB"
    return f"{max(1, round(size / 10**6))} MB"


def describe(dev):
    parts = dev.get("children") or []
    def descendants(node):
        yield node
        for child in node.get("children") or []:
            yield from descendants(child)
    all_nodes = list(descendants(dev))
    windows = any(str(p.get("fstype", "")).lower() in ("ntfs", "bitlocker") for p in all_nodes)
    mounted = any(m for d in all_nodes for m in (d.get("mountpoints") or []))
    if mounted:
        reason = "Está en uso: es el USB de Antu o tiene algo abierto."
    elif dev["size"] < MIN_SIZE:
        reason = "Muy pequeño: Antu necesita al menos 40 GB."
    else:
        reason = ""
    return {
        "path": dev["path"],
        # El ayudante la compara antes de borrar: si el disco cambió, no se toca.
        "huella": " ".join(x for x in ((dev.get("serial") or "").strip(), str(dev["size"])) if x),
        "name": (dev.get("model") or "").strip() or "Disco sin nombre",
        "detail": " · ".join(x for x in (TRANSPORTS.get(dev.get("tran") or "", ""), size_label(dev["size"])) if x),
        "kind": "usb" if dev.get("tran") == "usb" else "disco",
        "windows": windows,
        "contents": ("Tiene particiones de Windows." if windows
                     else "Tiene particiones con datos." if parts else "Vacío."),
        "parts": [" · ".join(x for x in (p.get("label"), (p.get("fstype") or "").upper(), size_label(p["size"])) if x)
                  for p in parts],
        "reason": reason,
    }


def disks():
    """Discos completos donde se puede instalar; primero los internos, al final los que no sirven."""
    out = subprocess.run(["lsblk", "--tree", "-J", "-b", "-o", "PATH,SIZE,MODEL,SERIAL,TRAN,TYPE,RO,FSTYPE,LABEL,MOUNTPOINTS"],
                         capture_output=True, text=True, check=True).stdout
    found = [describe(d) for d in json.loads(out)["blockdevices"]
             if d["type"] == "disk" and not d["ro"] and d["size"] and not d["path"].startswith("/dev/zram")]
    return sorted(found, key=lambda d: (d["reason"] != "", d["kind"] == "usb"))


class Backend(QObject):
    stage = pyqtSignal(int)
    line = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    planned = pyqtSignal(bool, str)

    def __init__(self, demo):
        super().__init__()
        self.demo = demo
        self.proc = None
        self.log = None
        self.tail = []
        self.stage_index = 0

    @pyqtSlot(result=list)
    def disks(self):
        if self.demo:
            return DEMO_DISKS
        try:
            return disks()
        except (OSError, subprocess.CalledProcessError, ValueError, KeyError):
            return []

    @pyqtSlot(str, str, str)
    def prepare(self, path, huella, mode):
        if self.demo:
            self.plan = {"id": "demo", "mode": mode}
            self.planned.emit(True, "Espacio sin asignar: 128 GB" if mode == "conservar" else "Se borrará el disco entero.")
            return
        self.planner = QProcess(self)
        self.planner.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        def done(code, _status):
            output = bytes(self.planner.readAllStandardOutput()).decode(errors="replace")
            try:
                if code != 0:
                    raise ValueError(output.strip())
                self.plan = json.loads(output)
                free = self.plan.get("free")
                self.planned.emit(True, "Espacio sin asignar: " + size_label(free["bytes"]) if free else "Se borrará el disco entero.")
            except (ValueError, KeyError) as error:
                self.planned.emit(False, str(error))
        self.planner.finished.connect(done)
        self.planner.errorOccurred.connect(lambda error: self.planned.emit(False, "No se pudo iniciar la comprobación del disco.")
                                          if error == QProcess.ProcessError.FailedToStart else None)
        self.planner.start("pkexec", [HELPER, "plan", path, huella, mode])

    @pyqtSlot(str, str, bool, str)
    def install(self, path, huella, encrypted, password):
        self.tail = []
        self.stage_index = 0
        if self.demo:
            return
        self.log = LOG.open("w")
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self._read)
        self.proc.finished.connect(self._done)
        self.proc.errorOccurred.connect(lambda error: self.finished.emit(False, "No se pudo iniciar el instalador.")
                                       if error == QProcess.ProcessError.FailedToStart else None)
        self.proc.start("pkexec", [HELPER, "instalar", path, huella, self.plan["mode"],
                                  "luks2" if encrypted else "plain", self.plan["id"]])
        self.proc.write((json.dumps({"passphrase": password}) + "\n").encode())
        self.proc.closeWriteChannel()

    @pyqtSlot()
    def reboot(self):
        QProcess.startDetached("systemctl", ["reboot"])

    def _read(self):
        while self.proc.canReadLine():
            text = bytes(self.proc.readLine()).decode(errors="replace").rstrip().split("\r")[-1].strip()
            if not text:
                continue
            self.log.write(text + "\n")
            self.log.flush()
            self.tail = (self.tail + [text])[-8:]
            low = text.lower()
            for index, words in enumerate(STAGE_WORDS):
                if index > self.stage_index and any(w in low for w in words):
                    self.stage_index = index
                    self.stage.emit(index)
            self.line.emit(text)

    def _done(self, code, _status):
        self._read()
        self.log.close()
        self.finished.emit(code == 0, "\n".join(self.tail[-5:]) or "El instalador terminó sin dar detalles.")


def main():
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Instalar Antu")
    app.setDesktopFileName("antu-instalador")
    app.setWindowIcon(QIcon("/usr/share/antu/antu-symbol.svg"))
    backend = Backend(demo="--demo" in sys.argv)
    engine = QQmlApplicationEngine()
    sys.path.insert(0, str(HERE.parent / "inicio"))
    import preferencias
    preferencias.instalar(app, engine)
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(HERE / "Instalador.qml")))
    if not engine.rootObjects():
        sys.exit(1)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

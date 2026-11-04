#!/usr/bin/env python3
"""Centro de Antu: aplicaciones, copias, recuperación y validación. Qt nativo, sin comandos arbitrarios."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import platform
import sys
import time

from PyQt6.QtCore import QObject, QProcess, QTimer, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QFont, QIcon
from PyQt6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFileDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QProgressBar, QPushButton, QScrollArea, QTabWidget,
    QTextEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
from catalogo import APPS
from respaldo import Restic, destination
from rendimiento import comparar

HOME = Path.home()
STATE = HOME / ".local/state/antu"
CHECKS = {"red": "Navegar y descargar por wifi; repetir tras suspensión",
          "audio": "Probar altavoces, auriculares y micrófono con una grabación",
          "bluetooth": "Emparejar y usar un dispositivo Bluetooth",
          "suspension": "Suspender y reanudar varias veces, con cargador y batería",
          "pantallas": "Probar monitor externo, brillo y escalado 100/125/150/200 %",
          "juego": "Jugar al menos 30 minutos y revisar temperaturas y tiempos de cuadro",
          "eclipse": "Entrar en Eclipse, jugar y volver al escritorio",
          "zenit": "Cambiar perfiles, carga y luces; confirmar la respuesta del hardware",
          "actualizacion": "Actualizar la instalación, reiniciar y probar la versión anterior",
          "accesibilidad": "Recorrer con teclado; probar lector de pantalla y mando"}


class Signals(QObject):
    done = pyqtSignal(object, object)
    progress = pyqtSignal(object)


class Centro(QMainWindow):
    def __init__(self, demo=False):
        super().__init__()
        self.demo, self.busy = demo, False
        self.live = Path("/run/initramfs/live").exists()
        self.installed = set()
        self.running_restic = None
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="antu-centro")
        self.signals = Signals(self)
        self.signals.done.connect(self.completed)
        self.signals.progress.connect(self.progress)
        self.setWindowTitle("Centro de Antu")
        self.setWindowIcon(QIcon("/usr/share/icons/hicolor/256x256/apps/antu.png"))
        self.resize(1100, 800)
        self.setMinimumSize(800, 600)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)
        heading = QLabel("Tu Antu, preparado")
        font = QFont("Inter"); font.setPointSize(25); font.setBold(True)
        heading.setFont(font)
        layout.addWidget(heading)
        layout.addWidget(self.label("Aplicaciones, protección de tus archivos y pruebas de tu equipo."))
        if demo:
            layout.addWidget(self.label("Vista de demostración: las acciones están desactivadas y no cambian el equipo."))
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        self.applications()
        self.backups()
        self.hardware()
        self.performance()
        self.status = self.label("El escritorio ya está disponible. Puedes preparar las aplicaciones cuando tengas conexión.")
        layout.addWidget(self.status)
        self.bar = QProgressBar(); self.bar.hide(); layout.addWidget(self.bar)
        self.timer = QTimer(self, interval=1500)
        self.timer.timeout.connect(self.refresh_apps)
        self.timer.start()
        self.refresh_apps()
        self.inventory_timer = QTimer(self, interval=30000)
        self.inventory_timer.timeout.connect(self.inventory)
        self.inventory_timer.start()
        if not demo:
            QTimer.singleShot(0, self.inventory)

    def label(self, text):
        label = QLabel(text)
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        return label

    def tab(self, title):
        page = QWidget(); box = QVBoxLayout(page); box.setSpacing(16); box.setContentsMargins(22, 22, 22, 22)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(page)
        self.tabs.addTab(scroll, title)
        return box

    def button(self, text, callback, parent):
        button = QPushButton(text); button.setMinimumHeight(38)
        button.setEnabled(not self.demo); button.clicked.connect(callback); parent.addWidget(button)
        return button

    def applications(self):
        box = self.tab("Aplicaciones")
        box.addWidget(self.label("Steam y las utilidades de Antu ya están instaladas. Brave se prepara en segundo plano al tener internet. Elige el resto; las descargas son de Flathub y pueden ocupar varios GB."))
        self.apps = QTreeWidget(); self.apps.setHeaderLabels(["Aplicación", "Para qué sirve", "Estado"])
        self.apps.setRootIsDecorated(False); self.apps.setMinimumHeight(320)
        self.app_items = {}
        for key, (name, detail, default) in APPS.items():
            item = QTreeWidgetItem([name, detail, "Pendiente"])
            item.setCheckState(0, Qt.CheckState.Checked if default else Qt.CheckState.Unchecked)
            self.apps.addTopLevelItem(item); self.app_items[key] = item
        self.apps.setColumnWidth(0, 200); self.apps.setColumnWidth(1, 300)
        box.addWidget(self.apps)
        controls = QHBoxLayout()
        self.button("Instalar o reintentar selección", self.install_apps, controls)
        self.button("Pausar descargas", lambda: QProcess.startDetached("pkexec", ["/usr/lib/antu/preparar-helper", "pausar"]), controls)
        self.button("Más aplicaciones en Discover", lambda: QProcess.startDetached("plasma-discover", []), controls)
        box.addLayout(controls)
        box.addWidget(self.label("Sin internet puedes usar las herramientas incluidas. El navegador y las aplicaciones elegidas requieren una descarga inicial; un fallo de una aplicación no impide preparar las demás."))
        box.addStretch()

    def refresh_apps(self):
        try:
            state = json.loads(Path("/var/lib/antu/preparacion.json").read_text())
            if not isinstance(state, dict) or not isinstance(state.get("apps"), dict):
                raise ValueError("Estado de preparación no válido")
        except (OSError, ValueError):
            state = {"apps": {}}
        if self.demo:
            state = {"apps": {"com.brave.Browser": {"status": "instalada"}, "com.heroicgameslauncher.hgl": {"status": "descargando", "percent": 42, "download_bytes": 900000000}}}
        for key, item in self.app_items.items():
            info = state.get("apps", {}).get(key, {})
            label = info.get("status", "Instalada" if key in self.installed else "No solicitada" if not APPS[key][2] else "Esperando conexión")
            if info and label not in ("instalada", "error", "pausada") and time.time() - state.get("updated_at", 0) > 180:
                label = "Sin progreso reciente; puedes reintentar"
            if info.get("percent") is not None:
                label += f" · {info['percent']} % del componente"
            if info.get("download_bytes") is not None:
                label += f" · descarga resuelta: {info['download_bytes'] / 10**6:.0f} MB"
            item.setText(2, label)
            item.setToolTip(2, str(info.get("error") or info.get("component") or ""))

    def inventory(self):
        if self.demo or (hasattr(self, "scanner") and self.scanner.state() != QProcess.ProcessState.NotRunning):
            return
        self.scanner = QProcess(self)
        def done(code, _):
            if code == 0:
                self.installed = set(bytes(self.scanner.readAllStandardOutput()).decode(errors="replace").splitlines())
                self.refresh_apps()
        self.scanner.finished.connect(done)
        self.scanner.start("flatpak", ["list", "--app", "--columns=application"])

    def install_apps(self):
        if self.busy or self.demo:
            return
        if hasattr(self, "proc") and self.proc.state() != QProcess.ProcessState.NotRunning:
            self.status.setText("Ya hay una preparación en curso. Su progreso aparece en la lista."); return
        ids = [key for key, item in self.app_items.items() if item.checkState(0) == Qt.CheckState.Checked]
        if not ids:
            self.status.setText("Selecciona al menos una aplicación."); return
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.proc.readyReadStandardOutput.connect(lambda: self.proc.readAllStandardOutput())
        self.proc.errorOccurred.connect(lambda error: self.status.setText("No se pudo iniciar la preparación de aplicaciones.")
                                       if error == QProcess.ProcessError.FailedToStart else None)
        self.proc.finished.connect(lambda code, _: self.status.setText("Preparación terminada. Revisa el estado de cada aplicación." if code == 0 else "La preparación no terminó. Revisa el estado y vuelve a intentar la selección pendiente."))
        self.proc.start("pkexec", ["/usr/lib/antu/preparar-helper", "instalar", *ids])
        self.status.setText("Preparando la selección. El progreso real aparece en la lista.")

    def backups(self):
        box = self.tab("Copias y recuperación")
        if self.live:
            box.addWidget(self.label("Estás en el USB Live: puedes restaurar copias en otro disco. La copia de la carpeta personal se crea desde tu cuenta instalada, para evitar respaldar por error la sesión temporal del USB."))
        box.addWidget(self.label("Copia cifrada de tu carpeta personal: documentos, configuración y partidas locales. Se excluyen cachés, papelera y juegos descargados de Steam. Elige otro disco; una copia en el mismo disco no protege de su avería."))
        form = QFormLayout(); form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.repo = QLineEdit(); self.repo.setReadOnly(True)
        row = QHBoxLayout(); row.addWidget(self.repo); self.button("Elegir disco…", self.choose_repo, row)
        form.addRow("Destino del respaldo", row)
        self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("12 caracteres o más; conserva esta frase fuera del equipo")
        form.addRow("Frase de cifrado del respaldo", self.password)
        box.addLayout(form)
        controls = QHBoxLayout(); create = self.button("Crear copia y comprobarla", self.backup, controls)
        create.setEnabled(not self.demo and not self.live)
        self.button("Buscar copias", self.list_backups, controls); box.addLayout(controls)
        self.snapshots = QComboBox(); self.snapshots.setMinimumContentsLength(20); box.addWidget(self.snapshots)
        self.button("Restaurar en una carpeta nueva", self.restore, box)
        self.button("Cancelar operación de respaldo o restauración", self.cancel_backup, box)
        box.addWidget(self.label("La restauración se verifica y se guarda en Restauraciones-Antu. Tus archivos actuales no se sobrescriben. Si olvidas la frase de cifrado no podremos recuperar el respaldo."))
        box.addWidget(self.label("Si una actualización falla, puedes volver a la versión anterior. Esa operación recupera el sistema; las copias anteriores protegen tus archivos."))
        self.button("Abrir Actualizaciones de Antu", lambda: QProcess.startDetached("/usr/bin/python3", ["/usr/lib/antu/actualizaciones/actualizaciones.py"]), box)
        self.button("Abrir guía de recuperación", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile("/usr/share/doc/antu/recuperacion.html")), box)
        box.addStretch()

    def choose_repo(self):
        path = QFileDialog.getExistingDirectory(self, "Elige una carpeta en el disco de respaldo", "/run/media")
        if path:
            try:
                self.repo.setText(str(destination(path, HOME)))
            except ValueError as error:
                self.status.setText(str(error))

    def restic(self):
        if not self.repo.text():
            raise ValueError("Elige primero el disco de respaldo.")
        return Restic(self.repo.text(), self.password.text(), self.signals.progress.emit)

    def cancel_backup(self):
        if self.busy and self.running_restic:
            self.running_restic.cancel()
            self.status.setText("Cancelando de forma segura. Espera a que el motor cierre sus archivos.")

    def task(self, function, callback):
        if self.demo or self.busy:
            return
        self.busy = True; self.bar.setRange(0, 0); self.bar.show()
        self.status.setText("Operación en curso. Puedes consultar las otras pestañas.")
        self._callback = callback
        def run():
            try:
                self.signals.done.emit(function(), None)
            except OSError:
                self.signals.done.emit(None, "No se pudo leer o guardar el archivo. Comprueba el destino, el espacio y sus permisos.")
            except Exception as error:
                self.signals.done.emit(None, str(error))
        self.pool.submit(run)

    def completed(self, result, error):
        self.busy = False; self.bar.hide()
        self.running_restic = None
        if error:
            self.status.setText(error)
        else:
            self._callback(result)

    def progress(self, value):
        if value.get("message_type") == "status":
            fraction = value.get("percent_done")
            if fraction is not None:
                self.bar.setRange(0, 100); self.bar.setValue(round(fraction * 100))
                self.status.setText(f"Respaldo: {value.get('files_done', 0)} archivos · {value.get('bytes_done', 0) / 10**6:.1f} MB procesados")

    def backup(self):
        if self.busy or self.demo:
            return
        if self.live:
            self.status.setText("Crea el respaldo desde tu cuenta instalada; esta carpeta pertenece al USB Live."); return
        try:
            restic = self.restic()
            self.running_restic = restic
            self.task(lambda: restic.backup(HOME), self.show_snapshots)
        except ValueError as error:
            self.status.setText(str(error))

    def list_backups(self):
        if self.busy or self.demo:
            return
        try:
            restic = self.restic(); self.running_restic = restic; self.task(restic.snapshots, self.show_snapshots)
        except ValueError as error:
            self.status.setText(str(error))

    def show_snapshots(self, snapshots):
        self.snapshots.clear()
        for snapshot in sorted(snapshots, key=lambda item: item["time"], reverse=True):
            self.snapshots.addItem(snapshot["time"] + " · " + snapshot["id"][:8], snapshot["id"])
        self.status.setText("Copias disponibles. Una copia nueva solo se muestra como completada si Restic terminó sin errores.")

    def restore(self):
        if self.busy or self.demo:
            return
        try:
            restic = self.restic(); snapshot = self.snapshots.currentData()
            if not snapshot:
                raise ValueError("Busca y selecciona una copia primero.")
            parent = QFileDialog.getExistingDirectory(self, "Dónde crear la carpeta nueva de restauración", "/run/media" if self.live else str(HOME))
            if not parent:
                return
            parent = Path(parent).resolve()
            if parent == restic.repository or parent.is_relative_to(restic.repository):
                raise ValueError("Elige una carpeta fuera del repositorio de respaldo.")
            parent = parent / "Restauraciones-Antu"; parent.mkdir(exist_ok=True)
            self.running_restic = restic
            self.task(lambda: restic.restore(snapshot, parent), lambda path: self.status.setText("Restauración verificada en " + str(path)))
        except ValueError as error:
            self.status.setText(str(error))
        except OSError:
            self.status.setText("No se pudo crear la carpeta de restauración. Elige otro destino con espacio y permiso de escritura.")

    def hardware(self):
        box = self.tab("Probar mi equipo")
        box.addWidget(self.label("Estas pruebas requieren tu intervención en el equipo real. Pendiente no significa compatible. Marca Funciona solo después de completar el recorrido."))
        form = QFormLayout(); form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.checks = {}
        for key, text in CHECKS.items():
            combo = QComboBox(); combo.addItems(["Pendiente", "Funciona", "Falla"])
            form.addRow(text, combo); self.checks[key] = combo
        box.addLayout(form)
        self.notes = QTextEdit(); self.notes.setPlaceholderText("Anota juegos, periféricos, duración, condiciones y fallos. No incluyas contraseñas ni claves.")
        box.addWidget(self.notes)
        self.button("Guardar informe de validación…", self.save_checks, box)
        box.addWidget(self.label("Los resultados son declarados por quien prueba. No se envían a internet ni certifican otros equipos."))

    def save_checks(self):
        target, _ = QFileDialog.getSaveFileName(self, "Guardar validación", str(HOME / "antu-validacion.json"), "JSON (*.json)")
        if not target:
            return
        report = {"schema": 1, "time": time.time(), "kernel": platform.release(), "method": "manual; not automatically verified",
                  "checks": {key: combo.currentText() for key, combo in self.checks.items()}, "notes": self.notes.toPlainText()}
        report["hardware"] = {}
        for name in ("sys_vendor", "product_name"):
            try:
                report["hardware"][name] = Path("/sys/class/dmi/id", name).read_text().strip()
            except OSError:
                pass
        try:
            report["revision"] = Path("/usr/share/antu/revision").read_text().strip()
        except OSError:
            report["revision"] = "desconocida"
        try:
            Path(target).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.status.setText("Informe guardado localmente.")
        except OSError:
            self.status.setText("No se pudo guardar el informe. Elige otra carpeta con permiso de escritura.")

    def performance(self):
        box = self.tab("Rendimiento")
        box.addWidget(self.label("Compara CSV de MangoHud y PresentMon. Repite la misma escena, resolución, calidad, límite de FPS y alimentación. Las mediciones deben venir de tu equipo; aquí no hay resultados inventados."))
        form = QFormLayout(); form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.csvs, self.conditions = [], []
        for label in ("Sesión A", "Sesión B"):
            field = QLineEdit(); field.setReadOnly(True); self.csvs.append(field)
            row = QHBoxLayout(); row.addWidget(field)
            def choose(_checked=False, target=field):
                path, _ = QFileDialog.getOpenFileName(self, "Registro de cuadros", str(HOME), "CSV (*.csv)")
                if path: target.setText(path)
            self.button("Elegir CSV…", choose, row); form.addRow(label, row)
            conditions = QLineEdit(); conditions.setPlaceholderText("Juego / escena / resolución / calidad / límite / alimentación")
            self.conditions.append(conditions); form.addRow("Condiciones de " + label, conditions)
        box.addLayout(form)
        self.button("Comparar las dos sesiones", self.compare, box)
        self.results = QTextEdit(); self.results.setReadOnly(True); box.addWidget(self.results)
        self.results.hide()
        self.measurements = QTreeWidget(); self.measurements.setRootIsDecorated(False)
        self.measurements.setHeaderLabels(["Medición", "Sesión A", "Sesión B"])
        self.measurements.setColumnWidth(0, 350); box.addWidget(self.measurements)
        self.comparison = None
        self.button("Guardar comparación verificable…", self.save_comparison, box)
        box.addWidget(self.label("El 1 % bajo es el inverso del tiempo medio del 1 % de cuadros más lentos. P95/P99 se expresan en ms: menos es mejor. Se conservan los tirones del registro."))

    def compare(self):
        args = [field.text() for field in self.csvs + self.conditions]
        self.task(lambda: comparar(*args), self.show_comparison)

    def show_comparison(self, result):
        self.comparison = result
        self.measurements.clear()
        for label, key, decimals in (("FPS medios · más es mejor", "fps", 1), ("1 % bajo · FPS", "one_percent_low_fps", 1),
                                     ("P95 · ms por cuadro", "p95_ms", 2), ("P99 · ms por cuadro", "p99_ms", 2),
                                     ("Cuadros de más de 50 ms", "frames_over_50_ms", 0), ("Duración · segundos", "seconds", 1),
                                     ("Cuadros válidos", "frames", 0), ("Filas inválidas omitidas", "discarded", 0)):
            values = [f"{result[side][key]:.{decimals}f}" for side in ("a", "b")]
            self.measurements.addTopLevelItem(QTreeWidgetItem([label, *values]))
        self.status.setText("Comparación calculada. Las condiciones fueron declaradas por quien realizó la prueba.")

    def save_comparison(self):
        if not self.comparison:
            self.status.setText("Compara dos sesiones antes de guardar el resultado."); return
        path, _ = QFileDialog.getSaveFileName(self, "Guardar comparación", str(HOME / "antu-rendimiento.json"), "JSON (*.json)")
        if path:
            try:
                Path(path).write_text(json.dumps(self.comparison, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                self.status.setText("Comparación guardada con los hashes de los registros originales.")
            except OSError:
                self.status.setText("No se pudo guardar la comparación. Elige otra carpeta con permiso de escritura.")

    def closeEvent(self, event):
        if self.busy:
            self.status.setText("Espera a que termine el respaldo, restauración o análisis antes de cerrar.")
            event.ignore()
        else:
            event.accept()


def main():
    first = "--primera-vez" in sys.argv
    if first and (Path("/run/initramfs/live").exists() or (STATE / "centro-visto").exists()):
        return
    app = QApplication(sys.argv); app.setApplicationName("Centro de Antu"); app.setDesktopFileName("antu-centro")
    font = app.font(); font.setPointSizeF(max(10.5, font.pointSizeF())); app.setFont(font)
    window = Centro("--demo" in sys.argv); window.show()
    if first:
        STATE.mkdir(parents=True, exist_ok=True); (STATE / "centro-visto").touch()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

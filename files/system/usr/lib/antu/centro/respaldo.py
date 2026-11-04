"""Respaldo cifrado con Restic. Restaura en carpeta nueva, nunca encima de archivos vivos."""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import threading

EXCLUDE = (".cache", ".local/share/Trash", ".local/share/Steam/steamapps/common",
           ".local/share/Steam/steamapps/shadercache", ".local/share/flatpak", "Restauraciones-Antu")


def destination(value, home):
    root = Path(value).expanduser().resolve()
    home = Path(home).resolve()
    if not root.is_absolute() or root == home or root.is_relative_to(home) or root == Path("/"):
        raise ValueError("Elige un disco de respaldo fuera de tu carpeta personal.")
    if not root.is_dir():
        raise ValueError("El destino no está disponible. Conecta y abre el disco antes de continuar.")
    return root / "Antu-Respaldos"


class Restic:
    def __init__(self, repository, password, emit=lambda value: None):
        if not isinstance(password, str) or len(password) < 12 or "\n" in password:
            raise ValueError("El respaldo necesita una frase de al menos 12 caracteres.")
        self.repository = Path(repository).resolve()
        self.password = password
        self.emit = emit
        self.cancelled = threading.Event()
        self.process = None

    def cancel(self):
        self.cancelled.set()
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()

    def run(self, *args):
        if self.cancelled.is_set():
            raise RuntimeError("Operación cancelada. Las copias anteriores se conservan.")
        with os.fdopen(os.memfd_create("antu-respaldo", os.MFD_CLOEXEC), "w+b") as secret, tempfile.TemporaryFile() as errors:
            secret.write(self.password.encode())
            secret.flush()
            secret.seek(0)
            environment = dict(os.environ, RESTIC_PASSWORD_FILE=f"/proc/self/fd/{secret.fileno()}")
            environment.pop("RESTIC_PASSWORD", None)
            environment.pop("RESTIC_PASSWORD_COMMAND", None)
            proc = subprocess.Popen(["restic", "--repo", str(self.repository), "--json", *args],
                                    env=environment, pass_fds=(secret.fileno(),), stdout=subprocess.PIPE,
                                    stderr=errors, text=True)
            self.process = proc
            if self.cancelled.is_set():
                proc.terminate()
            if args[0] == "backup":
                output = ""
                for line in proc.stdout:
                    try:
                        self.emit(json.loads(line))
                    except ValueError:
                        pass
                proc.stdout.close()
                proc.wait()
            else:
                output, _ = proc.communicate()
            if proc.returncode:
                errors.seek(0)
                error = errors.read().decode(errors="replace")
                messages = {
                    3: "No se pudieron leer todos los archivos. La copia no se declara completa; revisa los permisos del origen.",
                    10: "No se encontró el repositorio. Conecta el disco correcto y vuelve a buscar las copias.",
                    11: "Otra operación está usando este respaldo. Espera a que termine y vuelve a intentarlo.",
                    12: "La frase de cifrado no coincide con este respaldo. Revísala sin crear otro repositorio.",
                    130: "Operación cancelada. Revisa las copias disponibles; no se declara una nueva copia verificada.",
                }
                message = messages[130] if self.cancelled.is_set() else messages.get(proc.returncode,
                    "El respaldo no terminó. Comprueba la conexión, el espacio y los permisos del disco; no se declara completo.")
                failure = RuntimeError(message)
                failure.diagnostic = error.strip()[-1800:]
                raise failure
            try:
                return json.loads(output)
            except ValueError:
                return [json.loads(line) for line in output.splitlines() if line.startswith("{")]

    def backup(self, home):
        home = Path(home).resolve()
        if self.repository == home or self.repository.is_relative_to(home):
            raise ValueError("El repositorio no puede estar dentro del origen.")
        if not (self.repository / "config").exists():
            self.run("init")
        exclusions = [part for name in EXCLUDE for part in ("--exclude", str(home / name))]
        self.run("backup", "--one-file-system", "--tag", "antu-personal", *exclusions, str(home))
        self.run("check", "--read-data")
        return self.snapshots()

    def snapshots(self):
        return self.run("snapshots", "--tag", "antu-personal")

    def restore(self, snapshot, parent):
        if not re.fullmatch(r"[a-f0-9]{8,64}", snapshot):
            raise ValueError("Selecciona una copia válida.")
        # Solo una instantánea existente del conjunto Antu, no un identificador arbitrario.
        if not any(s["id"].startswith(snapshot) for s in self.snapshots()):
            raise ValueError("La copia seleccionada ya no está disponible.")
        target = Path(tempfile.mkdtemp(prefix="copia-", dir=parent))
        self.run("restore", snapshot, "--target", str(target), "--verify")
        return target

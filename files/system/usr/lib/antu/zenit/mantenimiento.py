#!/usr/bin/env python3
"""Mantenimiento de la instalación independiente; siempre se ejecuta como usuario."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def run(*args, **kwargs):
    subprocess.run([str(a) for a in args], check=True, **kwargs)


def actualizar(base, info):
    repo = Path(info["repositorio"])
    if not (repo / "scripts/install-zenit-bazzite.sh").is_file():
        raise RuntimeError("No se encuentra el checkout de Antu OS. Recupéralo y ejecuta el instalador desde allí.")
    def git(*args):
        return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()
    if git("status", "--porcelain"):
        raise RuntimeError("El repositorio tiene cambios locales. Consérvalos antes de actualizar.")
    if git("branch", "--show-current") != "main":
        raise RuntimeError("La actualización automática requiere la rama main.")
    if git("remote", "get-url", "origin").removesuffix(".git") != "https://github.com/bernaljeanp/antu-os":
        raise RuntimeError("El origen no coincide con el repositorio oficial de Antu OS.")
    run("git", "-C", repo, "pull", "--ff-only", "origin", "main")
    args = [] if info["servicio"] else ["--sin-servicio"]
    environment = dict(os.environ, XDG_DATA_HOME=str(base.parent),
                       XDG_CONFIG_HOME=str(Path(info["autostart"]).parent.parent))
    run("bash", repo / "scripts/install-zenit-bazzite.sh", *args, env=environment)
    print("Actualización terminada. Sal de Zenit desde la bandeja y vuelve a abrirlo.")


def desinstalar(base, info):
    print("Se quitarán Zenit y su inicio automático. Se conservan las preferencias de /var/lib/zenit.")
    print("Los valores escritos a la BIOS no se revierten. Cierra Zenit desde la bandeja antes de continuar.")
    if input("Escribe DESINSTALAR para continuar: ") != "DESINSTALAR":
        print("Cancelado.")
        return
    if info["servicio"]:
        unit = Path("/etc/systemd/system/zenit.service")
        if unit.exists():
            expected = {"ExecStart=/usr/bin/python3 /var/opt/zenit/zenit.py demonio",
                        "ExecStart=/usr/bin/python3 /var/opt/zenit/zenit.py demonio --solo-luces"}
            if unit.is_symlink() or not expected.intersection(unit.read_text().splitlines()):
                raise RuntimeError("La unidad no corresponde al instalador independiente; no se ha eliminado.")
            run("sudo", "systemctl", "disable", "--now", "zenit.service")
            run("sudo", "rm", "--", unit, "/var/opt/zenit/zenit.py")
            run("sudo", "systemctl", "daemon-reload")
            # Solo quitar la carpeta si está vacía; nunca borrar preferencias o archivos ajenos.
            subprocess.run(["sudo", "rmdir", "/var/opt/zenit"], check=False)
    for file in (Path(info["menu"]), Path(info["autostart"])):
        if file.exists() and "X-Zenit-Installer=true" in file.read_text().splitlines():
            file.unlink()
    shutil.rmtree(base)
    print("Zenit desinstalado. Las preferencias del servicio se han conservado.")


def main():
    try:
        if os.geteuid() == 0:
            raise RuntimeError("Ejecuta como tu usuario habitual, sin sudo.")
        base = Path(__file__).resolve().parents[1]
        info = json.loads((base / "instalacion.json").read_text())
        if sys.argv[1:] == ["actualizar"]:
            actualizar(base, info)
        elif sys.argv[1:] == ["desinstalar"]:
            desinstalar(base, info)
        else:
            raise RuntimeError("Uso: mantenimiento.py actualizar|desinstalar")
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.CalledProcessError) as error:
        print("No se pudo completar: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

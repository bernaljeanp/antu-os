#!/usr/bin/env python3
"""El push mixto espera al build; el push exclusivo de Live prueba la base existente."""
import fnmatch
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import yaml


def necesita_base(paths, workflow):
    events = workflow.get("on", workflow.get(True, {}))
    ignored = events["push"]["paths-ignore"]
    return [path for path in paths if not any(fnmatch.fnmatchcase(path, pattern) for pattern in ignored)]


def main():
    workflow = yaml.safe_load(Path(".github/workflows/build.yml").read_text())
    if "--autoprueba" in sys.argv:
        cases = [(["files/live/usr/lib/antu/instalador/almacenamiento.py", "ci/iso-test.sh"], False),
                 (["files/live/etc/ejemplo", "Containerfile"], True),
                 (["docs/index.html", "scripts/descargar-antu-gui.py"], False),
                 (["files/system/usr/lib/antu/zenit/zenit.py"], True)]
        for paths, expected in cases:
            assert bool(necesita_base(paths, workflow)) == expected, paths
        print("Coordinación: 4 casos correctos; reglas tomadas del workflow de la imagen.")
        return
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    execute = True
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if os.environ["GITHUB_EVENT_NAME"] == "push":
        before, after = event["before"], event["after"]
        if not all(re.fullmatch(r"[a-f0-9]{40}", sha) and sha != "0" * 40 for sha in (before, after)):
            raise ValueError("El evento no identifica dos revisiones válidas.")
        if subprocess.run(["git", "cat-file", "-e", before], capture_output=True).returncode:
            subprocess.run(["git", "fetch", "--no-tags", "--depth=1", "origin", before], check=True)
        paths = subprocess.check_output(["git", "diff", "--name-only", "-z", before, after]).decode().split("\0")
        base = necesita_base([path for path in paths if path], workflow)
        execute = not base
        if base:
            print("La ISO espera la compilación de la imagen nueva; workflow_run la probará cuando termine.")
            print("Cambios de base:", ", ".join(base))
    elif os.environ["GITHUB_EVENT_NAME"] == "workflow_run":
        built = event["workflow_run"]["head_sha"]
        if not re.fullmatch(r"[a-f0-9]{40}", built):
            raise ValueError("La compilación no identifica una revisión válida.")
        if subprocess.run(["git", "cat-file", "-e", built], capture_output=True).returncode:
            subprocess.run(["git", "fetch", "--no-tags", "--depth=1", "origin", built], check=True)
        changed = subprocess.check_output(["git", "diff", "--name-only", "-z", built, source]).decode().split("\0")
        if necesita_base([path for path in changed if path], workflow):
            source = built
        print("Fuente de Live:", source, "· imagen de:", built)
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write("ejecutar=" + str(execute).lower() + "\n")
        output.write("fuente=" + source + "\n")


if __name__ == "__main__":
    main()

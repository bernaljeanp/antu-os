"""Plan de instalación en GPT. No reduce ni formatea particiones conservadas."""
import fcntl
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import select
import signal
import shutil
import subprocess
import sys
import tempfile

SOURCE = "/run/initramfs/live/antu/imagen"
TARGET = "ghcr.io/bernaljeanp/antu-nvidia:stable"
ESP = "C12A7328-F81F-11D2-BA4B-00A0C93EC93B"
LINUX = "0FC63DAF-8483-4772-8E79-3D69D8477DE4"
MINIMUM = 40 * 10**9
BOOT_BYTES = 2 * 1024**3


@contextmanager
def inhibit():
    guard = subprocess.Popen(["systemd-inhibit", "--what=sleep:idle:handle-lid-switch", "--who=Instalador de Antu",
                              "--why=Instalando Antu en el disco", "/bin/sh", "-c", "printf 'listo\\n'; exec sleep infinity"],
                             stdout=subprocess.PIPE, start_new_session=True)
    try:
        ready, _, _ = select.select([guard.stdout], [], [], 5)
        if not ready or guard.stdout.readline() != b"listo\n":
            raise RuntimeError("No se pudo impedir la suspensión durante la instalación. No se modifica el disco.")
        yield
    finally:
        try:
            os.killpg(guard.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        guard.wait()


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def query(args):
    return run(args, capture_output=True, text=True).stdout.strip()


def descendants(node):
    yield node
    for child in node.get("children") or []:
        yield from descendants(child)


def disk(device, fingerprint):
    if not re.fullmatch(r"/dev/(nvme\d+n\d+|sd[a-z]+|vd[a-z]+|mmcblk\d+)", device):
        raise ValueError("Disco no válido.")
    if not Path(device).is_block_device():
        raise ValueError("El destino no es un dispositivo de bloques.")
    info = json.loads(query(["lsblk", "--tree", "-Jb", "-o", "PATH,SIZE,SERIAL,TYPE,RO,MOUNTPOINTS", device]))["blockdevices"]
    if len(info) != 1 or info[0]["type"] != "disk" or info[0].get("ro"):
        raise ValueError("El destino no es un disco completo escribible.")
    item = info[0]
    actual = " ".join(str(v).strip() for v in (item.get("serial") or "", item["size"]) if str(v).strip())
    if actual != fingerprint:
        raise ValueError("El disco cambió. Vuelve a seleccionarlo.")
    if any(m for part in descendants(item) for m in part.get("mountpoints") or []):
        raise ValueError("El disco está en uso. No se modifica un disco con particiones montadas.")
    if item["size"] < MINIMUM:
        raise ValueError("Antu necesita al menos 40 GB.")
    return item


def free_plan(table):
    if table.get("label") != "gpt":
        raise ValueError("Conservar particiones requiere GPT y al menos 40 GB de espacio sin asignar.")
    sector = int(table.get("sectorsize", 512))
    if sector not in (512, 4096):
        raise ValueError("Tamaño de sector no compatible.")
    alignment = 1024**2 // sector
    start = max(int(table.get("firstlba", 34)), alignment)
    last = int(table["lastlba"]) + 1
    gaps = []
    for part in sorted(table.get("partitions", []), key=lambda p: p["start"]):
        end = int(part["start"])
        aligned = (start + alignment - 1) // alignment * alignment
        if end > aligned:
            gaps.append((aligned, end - aligned))
        start = max(start, end + int(part["size"]))
    aligned = (start + alignment - 1) // alignment * alignment
    if last > aligned:
        gaps.append((aligned, last - aligned))
    eligible = [(a, b) for a, b in gaps if b * sector >= MINIMUM + BOOT_BYTES]
    if not eligible:
        raise ValueError("No hay 40 GB libres más el arranque. Libera espacio desde Windows; Antu no reduce NTFS ni BitLocker.")
    start, length = max(eligible, key=lambda pair: pair[1])
    return {"start": start, "sectors": length, "sector_size": sector, "bytes": length * sector}


def plan(device, fingerprint, mode):
    item = disk(device, fingerprint)
    if mode not in ("borrar", "conservar"):
        raise ValueError("Modo de instalación no válido.")
    try:
        table = json.loads(query(["sfdisk", "--json", device]))["partitiontable"]
    except subprocess.CalledProcessError:
        if mode == "conservar":
            raise ValueError("No se pudo leer una tabla GPT válida. No se cambia el disco.")
        table = {}
    free = free_plan(table) if mode == "conservar" else None
    identity = {"device": device, "fingerprint": fingerprint, "mode": mode, "table": table, "free": free, "bytes": item["size"]}
    identity["id"] = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return identity


def partitions(device):
    return json.loads(query(["sfdisk", "--json", device]))["partitiontable"]["partitions"]


def format_root(device):
    run(["mkfs.ext4", "-F", "-O", "verity", "-L", "root", device])


def install(device, fingerprint, mode, encryption, plan_id, password):
    if encryption not in ("plain", "luks2"):
        raise ValueError("Tipo de cifrado no válido.")
    if encryption == "luks2" and (not isinstance(password, str) or not re.fullmatch(r"[A-Za-z0-9 ]{12,128}", password)):
        raise ValueError("La frase de cifrado necesita de 12 a 128 letras A–Z, números o espacios.")
    current = plan(device, fingerprint, mode)
    if current["id"] != plan_id:
        raise ValueError("La distribución del disco cambió desde la confirmación. No se escribe nada.")
    if not Path(SOURCE, "index.json").is_file():
        raise ValueError("No se encontró la imagen de Antu en el USB.")
    if mode == "borrar" and encryption == "plain":
        run(["bash", str(Path(__file__).with_name("instalar-entero.sh")), "instalar", device, fingerprint])
        return
    before = current["table"].get("partitions", []) if mode == "conservar" else []
    if before:
        backup = Path("/run/antu-instalador")
        backup.mkdir(mode=0o700, exist_ok=True)
        (backup / "gpt-anterior.json").write_text(json.dumps(current["table"]))
    sector = int(current["table"].get("sectorsize", 512))
    start = current["free"]["start"] if mode == "conservar" else 1024**2 // sector
    length = current["free"]["sectors"] if mode == "conservar" else current["bytes"] // sector - 34 - start
    esp_size = BOOT_BYTES // sector
    esp_name, root_name = "AntuEFI-" + secrets.token_hex(4), "AntuRoot-" + secrets.token_hex(4)
    layout = f'start={start},size={esp_size},type={ESP},name="{esp_name}"\nstart={start + esp_size},size={length - esp_size},type={LINUX},name="{root_name}"\n'
    args = ["sfdisk", "--append", device] if mode == "conservar" else ["sfdisk", "--wipe", "always", device]
    run(args, input=(layout if mode == "conservar" else "label: gpt\n" + layout), text=True)
    run(["udevadm", "settle"])
    after = partitions(device)
    old_by_uuid = {part.get("uuid"): part for part in after}
    if any(old_by_uuid.get(p.get("uuid")) != p for p in before):
        raise RuntimeError("La tabla no coincide con el plan. Se detuvo antes de formatear; tabla anterior en /run/antu-instalador.")
    esp = next(p["node"] for p in after if p.get("name") == esp_name)
    root = next(p["node"] for p in after if p.get("name") == root_name)
    mapper = "antu-" + secrets.token_hex(6)
    mounted = []
    opened = False
    directory = tempfile.mkdtemp(prefix="antu-destino-")
    with os.fdopen(os.memfd_create("antu-clave", os.MFD_CLOEXEC), "w+b") as key:
        try:
            extra = []
            rootfs = root
            if encryption == "luks2":
                key.write(password.encode())
                key.flush()
                fdpath = f"/proc/self/fd/{key.fileno()}"
                key.seek(0)
                run(["cryptsetup", "luksFormat", "--type", "luks2", "--batch-mode", "--key-file", fdpath, root], pass_fds=(key.fileno(),))
                key.seek(0)
                run(["cryptsetup", "open", "--key-file", fdpath, root, mapper], pass_fds=(key.fileno(),))
                opened = True
                rootfs = "/dev/mapper/" + mapper
                extra = ["--karg=rd.luks.uuid=" + query(["cryptsetup", "luksUUID", root])]
            format_root(rootfs)
            run(["mkfs.vfat", "-F", "32", "-n", "ANTU_EFI", esp])
            run(["mount", rootfs, directory])
            mounted.append(directory)
            target_esp = Path(directory, "boot/efi")
            target_esp.mkdir(parents=True)
            run(["mount", esp, str(target_esp)])
            mounted.append(str(target_esp))
            kargs = ["--karg=" + k for k in os.environ.get("ANTU_KARGS", "").split()]
            run(["bootc", "install", "to-filesystem", "--composefs-backend", "--bootloader=systemd", "--skip-finalize",
                 "--skip-fetch-check", "--source-imgref=oci:" + SOURCE, "--target-imgref=" + TARGET, *extra, *kargs, directory])
            for destination in ("EFI/antu", "EFI/BOOT"):
                where = target_esp / destination
                where.mkdir(parents=True, exist_ok=True)
                for name, source in (("shimx64.efi" if destination.endswith("antu") else "BOOTX64.EFI", "/usr/lib/antu/arranque/shimx64.efi"),
                                     ("mmx64.efi", "/usr/lib/antu/arranque/mmx64.efi"),
                                     ("grubx64.efi", "/usr/lib/systemd/boot/efi/systemd-bootx64.efi.signed")):
                    shutil.copyfile(source, where / name)
            shutil.copyfile("/usr/share/antu/arranque-seguro.cer", target_esp / "antu.cer")
            esp_number = query(["lsblk", "-no", "PARTN", esp])
            firmware = subprocess.run(["efibootmgr", "-q", "-c", "-d", device, "-p", esp_number, "-L", "Antu OS", "-l", "\\EFI\\antu\\shimx64.efi"])
            if firmware.returncode:
                print("Aviso: el firmware no aceptó la entrada. Antu conserva la ruta de reserva EFI/BOOT.", file=sys.stderr)
            run(["sync"])
        finally:
            cleanup_errors = []
            for point in reversed(mounted):
                try:
                    run(["umount", point])
                except subprocess.CalledProcessError:
                    cleanup_errors.append(point)
            if opened:
                try:
                    run(["cryptsetup", "close", mapper])
                except subprocess.CalledProcessError:
                    cleanup_errors.append(mapper)
            if not cleanup_errors:
                os.rmdir(directory)
            else:
                print("No se pudo desmontar todo; no se borra el punto de montaje: " + directory, file=sys.stderr)


def main():
    try:
        if os.geteuid() != 0:
            raise ValueError("El instalador necesita privilegios de administrador.")
        command, device, fingerprint, *args = sys.argv[1:]
        if command == "plan" and len(args) == 1:
            print(json.dumps(plan(device, fingerprint, args[0])))
        elif command == "instalar" and len(args) in (0, 3):
            request = json.loads(sys.stdin.buffer.readline(2048)) if args else {}
            if not isinstance(request, dict):
                raise ValueError("Solicitud no válida.")
            if not args:
                selected = plan(device, fingerprint, "borrar")
                args = ["borrar", "plain", selected["id"]]
            with open("/run/antu-instalar.lock", "w") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with inhibit():
                    install(device, fingerprint, *args, request.get("passphrase", ""))
        else:
            raise ValueError("Acción no válida.")
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError, KeyError, StopIteration) as error:
        print("Instalación detenida: " + str(error), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()

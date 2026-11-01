#!/usr/bin/env bash
# Instala Antu OS en un disco completo (lo BORRA) o en un archivo de imagen para una VM.
# Se ejecuta desde un Linux con podman, por ejemplo Fedora Workstation en vivo desde un USB.
#
#   sudo ./install-to-disk.sh /dev/sdX          disco externo: se borra entero
#   sudo ./install-to-disk.sh antu.img          archivo de 40 GB para QEMU o VMware
#
# Variable opcional: ANTU_IMAGE (por defecto ghcr.io/bernaljeanp/antu-nvidia:latest).
set -euo pipefail

IMAGE="${ANTU_IMAGE:-ghcr.io/bernaljeanp/antu-nvidia:latest}"
TARGET="${1:-}"

die() { echo "Error: $*" >&2; exit 1; }

[ -n "$TARGET" ] || die "indica un disco (/dev/sdX) o un archivo .img. Discos disponibles:
$(lsblk -d -o NAME,SIZE,MODEL,TRAN,TYPE)"
[ "$(id -u)" = 0 ] || die "ejecútalo con sudo."
command -v podman >/dev/null || die "falta podman."

# Opciones comunes a bootcrew: bootc instala desde dentro de su propia imagen.
run_bootc() {
    podman run --rm --privileged --pid=host \
        -v /dev:/dev -v /var/lib/containers:/var/lib/containers -v /etc/containers:/etc/containers \
        --security-opt label=type:unconfined_t "$@"
}
INSTALL_ARGS=(bootc install to-disk --composefs-backend --bootloader systemd --filesystem ext4 --wipe)

if [ -b "$TARGET" ]; then
    [ "$(lsblk -dno TYPE "$TARGET")" = disk ] || die "$TARGET no es un disco completo (¿pusiste una partición?)."

    root_disk="$(lsblk -no PKNAME "$(findmnt -no SOURCE /)" 2>/dev/null || true)"
    [ "/dev/${root_disk}" != "$TARGET" ] || die "$TARGET es el disco del sistema que está corriendo."

    if lsblk -no MOUNTPOINTS "$TARGET" | grep -q .; then
        die "$TARGET tiene particiones montadas. Desmóntalas antes."
    fi

    echo "Se va a BORRAR por completo este disco:"
    lsblk -o NAME,SIZE,MODEL,TRAN,FSTYPE,LABEL "$TARGET"
    read -r -p "Escribe el nombre del disco ($TARGET) para confirmar: " answer
    [ "$answer" = "$TARGET" ] || die "confirmación distinta, no se ha tocado nada."

    run_bootc "$IMAGE" "${INSTALL_ARGS[@]}" "$TARGET"
else
    case "$TARGET" in *.img) ;; *) die "$TARGET no es un disco ni termina en .img." ;; esac
    [ -e "$TARGET" ] || fallocate -l 40G "$TARGET"
    dir="$(cd "$(dirname "$TARGET")" && pwd)"
    run_bootc -v "$dir:/data" "$IMAGE" "${INSTALL_ARGS[@]}" --via-loopback "/data/$(basename "$TARGET")"
fi

echo "Listo. Al primer arranque se pedirá crear el usuario en la consola; después aparece SDDM."

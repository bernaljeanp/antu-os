#!/usr/bin/env bash
# Ayudante privilegiado del instalador de Antu, solo en el sistema en vivo. Borra el disco elegido e instala la imagen
# de Antu que viaja en el USB; las actualizaciones posteriores llegan del registro. Se niega con cualquier cosa que no
# sea un disco completo, sin nada montado y de 40 GB o más.
set -euo pipefail

SOURCE=/run/initramfs/live/antu/imagen
TARGET_IMAGE=ghcr.io/bernaljeanp/antu-nvidia:stable  # canal estable
MIN_BYTES=40000000000

die() { echo "$*" >&2; exit 1; }

[ "$(id -u)" = 0 ] || die "El instalador necesita privilegios de administrador."
[ "${1:-}" = instalar ] || die "Acción desconocida."
dev="${2:-}"
huella="${3:-}"  # número de serie y tamaño del disco que se eligió en la ventana

[[ "$dev" =~ ^/dev/(nvme[0-9]+n[0-9]+|sd[a-z]+|vd[a-z]+|mmcblk[0-9]+)$ ]] && [ -b "$dev" ] || die "Disco no válido."
[ "$(lsblk -dno TYPE "$dev")" = disk ] || die "$dev no es un disco completo."
# El USB de Antu está montado, así que esto también lo protege. Un fallo de lsblk nunca cuenta como "nada montado".
mounts="$(lsblk -no MOUNTPOINT "$dev")" || die "No se pudo leer el estado de $dev."
[ -z "$(printf '%s' "$mounts" | tr -d '[:space:]')" ] || die "$dev está en uso: tiene algo montado."
[ "$(lsblk -bdno SIZE "$dev")" -ge "$MIN_BYTES" ] || die "El disco es demasiado pequeño: Antu necesita al menos 40 GB."
[ -f "$SOURCE/index.json" ] || die "No se encontró la imagen de Antu en el USB."
# Si alguien cambió de disco entre elegirlo y confirmar (otro USB en la misma ranura), no se borra nada.
[ "$(lsblk -bdno SERIAL,SIZE "$dev" | xargs)" = "$huella" ] || die "El disco cambió desde que lo elegiste. Vuelve a elegirlo."

# Solo para las pruebas automáticas (prueba-instalar corre como root): argumentos extra del kernel del sistema
# instalado. pkexec borra el entorno, así que el instalador gráfico no puede pasarlos.
kargs=()
read -ra extra <<< "${ANTU_KARGS:-}"
for karg in "${extra[@]}"; do kargs+=(--karg "$karg"); done

# Sin suspender ni apagar por la tapa a mitad de la copia. Sin comprobar el registro: se instala sin internet y
# las actualizaciones lo usarán después.
systemd-inhibit --what=sleep:idle:handle-lid-switch --who="Instalador de Antu" --why="Copiando Antu al disco" \
    bootc install to-disk --composefs-backend --bootloader systemd --filesystem ext4 --wipe --skip-fetch-check \
    --source-imgref "oci:$SOURCE" --target-imgref "$TARGET_IMAGE" "${kargs[@]}" "$dev"

# Arranque seguro: bootctl dejó systemd-boot firmado con la llave de Antu; delante va shim, firmado por Microsoft. Queda
# también en la ruta de reserva EFI/BOOT, para equipos que olviden su entrada, y la llave pública a mano en la raíz.
udevadm settle
esp="$(lsblk -nrpo PATH,PARTTYPE "$dev" | awk 'tolower($2) == "c12a7328-f81f-11d2-ba4b-00a0c93ec93b" {print $1; exit}')"
[ -b "$esp" ] || die "No se encontró la partición de arranque del disco instalado."
cadena=/usr/lib/antu/arranque
punto="$(mktemp -d)"
mount "$esp" "$punto"
cp /usr/share/antu/arranque-seguro.cer "$punto/antu.cer"
mkdir -p "$punto/EFI/antu" "$punto/EFI/BOOT"
cp "$cadena/shimx64.efi" "$punto/EFI/antu/shimx64.efi"
cp "$cadena/shimx64.efi" "$punto/EFI/BOOT/BOOTX64.EFI"
for carpeta in antu BOOT; do
    cp "$cadena/mmx64.efi" "$punto/EFI/$carpeta/mmx64.efi"
    cp /usr/lib/systemd/boot/efi/systemd-bootx64.efi.signed "$punto/EFI/$carpeta/grubx64.efi"
done
umount "$punto"
rmdir "$punto"

# Entrada «Antu OS» en el menú de arranque del equipo. Si el firmware no la acepta, arranca igual por EFI/BOOT.
for vieja in $(efibootmgr | sed -n 's/^Boot\([0-9A-Fa-f]\{4\}\)\*\{0,1\} Antu OS[[:space:]].*/\1/p'); do
    efibootmgr -q -b "$vieja" -B || true
done
efibootmgr -q -c -d "$dev" -p "$(lsblk -no PARTN "$esp")" -L "Antu OS" -l '\EFI\antu\shimx64.efi' ||
    echo "Aviso: el equipo no aceptó la entrada «Antu OS»; arrancará por la ruta de reserva." >&2

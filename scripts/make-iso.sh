#!/usr/bin/env bash
# Crea el USB en vivo de Antu: una ISO híbrida UEFI (para grabar con USBoot o cualquier grabador en modo DD) con el
# sistema en vivo, el instalador gráfico y la imagen de Antu para instalar sin internet.
#
#   sudo scripts/make-iso.sh [imagen]      por defecto ghcr.io/bernaljeanp/antu-nvidia:testing
#
# Deja en ./iso-build/: antu-live.iso, su .sha256, y vmlinuz e initramfs-live.img para las pruebas en QEMU.
# Necesita podman, skopeo, squashfs-tools, xorriso, mtools y dosfstools.
set -euo pipefail

IMAGE="${1:-ghcr.io/bernaljeanp/antu-nvidia:testing}"
OUT="$PWD/iso-build"
LABEL=ANTU_LIVE
CMDLINE="root=live:CDLABEL=$LABEL rd.live.image rd.live.overlay.overlayfs=1 rd.driver.blacklist=nouveau modprobe.blacklist=nouveau quiet splash"

[ "$(id -u)" = 0 ] || { echo "Ejecútalo con sudo." >&2; exit 1; }
mkdir -p "$OUT/iso/LiveOS" "$OUT/iso/antu" "$OUT/esp/loader/entries"

# El sistema en vivo y la imagen que se instala son exactamente la misma versión.
digest="$(skopeo inspect --format '{{.Digest}}' "docker://$IMAGE")"
pinned="${IMAGE%:*}@$digest"
echo "Imagen: $pinned"
echo "$digest" > "$OUT/digest"  # la versión exacta que se prueba y se promueve
podman build -f Containerfile.live --build-arg BASE="$pinned" -t localhost/antu-live .
# Se baja como la bajará cada equipo: exigiendo la firma con la llave de Antu. Aviso, no bloqueo, hasta que esté probada.
cat > "$OUT/politica.json" <<JSON
{"default": [{"type": "reject"}],
 "transports": {"docker": {"${IMAGE%:*}": [{"type": "sigstoreSigned", "signedIdentity": {"type": "matchRepository"},
                                            "keyPath": "$PWD/files/system/etc/pki/containers/antu.pub"}]}}}
JSON
if skopeo --policy "$OUT/politica.json" --registries.d files/system/etc/containers/registries.d \
    copy --quiet --remove-signatures "docker://$pinned" "oci:$OUT/iso/antu/imagen"; then
    echo "Firma con la llave de Antu: correcta"
else
    echo "::warning::La versión no pasó la comprobación de firma con la llave de Antu"
    rm -rf "$OUT/iso/antu/imagen"
    skopeo copy --quiet "docker://$pinned" "oci:$OUT/iso/antu/imagen"
fi

mnt="$(podman image mount localhost/antu-live)"
kver="$(ls "$mnt/usr/lib/modules")"
cp "$mnt/usr/lib/modules/$kver/vmlinuz" "$OUT/vmlinuz"
cp "$mnt/usr/lib/antu/live/initramfs.img" "$OUT/initramfs-live.img"
# Cadena de arranque seguro: shim (firmado por Microsoft) carga systemd-boot (firmado con la llave de Antu).
cp "$mnt/usr/lib/antu/arranque/shimx64.efi" "$OUT/BOOTX64.EFI"
cp "$mnt/usr/lib/antu/arranque/mmx64.efi" "$OUT/mmx64.efi"
cp "$mnt/usr/lib/systemd/boot/efi/systemd-bootx64.efi.signed" "$OUT/grubx64.efi"
cp "$mnt/usr/share/antu/arranque-seguro.cer" "$OUT/antu.cer"
mksquashfs "$mnt" "$OUT/iso/LiveOS/squashfs.img" -noappend -no-progress -comp zstd -Xcompression-level 15 -b 1M
podman image unmount localhost/antu-live > /dev/null

# Partición EFI: systemd-boot con el sistema en vivo y una entrada de gráficos básicos para cuando NVIDIA falle.
cat > "$OUT/esp/loader/loader.conf" <<CONF
default antu.conf
timeout 5
editor no
CONF
cat > "$OUT/esp/loader/entries/antu.conf" <<CONF
title   Antu OS en vivo
linux   /antu/vmlinuz
initrd  /antu/initramfs.img
options $CMDLINE
CONF
cat > "$OUT/esp/loader/entries/antu-basico.conf" <<CONF
title   Antu OS en vivo (modo seguro: sin NVIDIA)
linux   /antu/vmlinuz
initrd  /antu/initramfs.img
options $CMDLINE module_blacklist=nvidia,nvidia_drm,nvidia_modeset,nvidia_uvm
CONF
esp="$OUT/efiboot.img"
size_mb=$(( ($(stat -c %s "$OUT/vmlinuz") + $(stat -c %s "$OUT/initramfs-live.img")) / 1048576 + 32 ))
truncate -s 0 "$esp" && truncate -s "${size_mb}M" "$esp"
mkfs.vfat -n ANTU_EFI "$esp" > /dev/null
mcopy -i "$esp" "$OUT/antu.cer" ::/antu.cer  # primero: encabeza la lista cuando se registra la llave
mmd -i "$esp" ::/EFI ::/EFI/BOOT ::/loader ::/loader/entries ::/antu
mcopy -i "$esp" "$OUT/BOOTX64.EFI" ::/EFI/BOOT/BOOTX64.EFI
mcopy -i "$esp" "$OUT/grubx64.efi" ::/EFI/BOOT/grubx64.efi
mcopy -i "$esp" "$OUT/mmx64.efi" ::/EFI/BOOT/mmx64.efi
mcopy -i "$esp" "$OUT/vmlinuz" ::/antu/vmlinuz
mcopy -i "$esp" "$OUT/initramfs-live.img" ::/antu/initramfs.img
mcopy -i "$esp" "$OUT/esp/loader/loader.conf" ::/loader/loader.conf
mcopy -i "$esp" "$OUT/esp/loader/entries/antu.conf" "$OUT/esp/loader/entries/antu-basico.conf" ::/loader/entries/

# Partición de datos: ahí guarda su archivo el Informe del equipo. Es FAT y de datos, para que Windows la muestre como unidad.
datos="$OUT/datos.img"
truncate -s 0 "$datos" && truncate -s 64M "$datos"
mkfs.vfat -n ANTU_DATOS "$datos" > /dev/null

# ISO híbrida: El Torito para lectores ópticos y VMs, y tabla GPT con la partición EFI para USB.
xorriso -as mkisofs -iso-level 3 -full-iso9660-filenames -rational-rock \
    -volid "$LABEL" -appid "Antu OS" -publisher "Antu OS" \
    -partition_offset 16 -append_partition 2 C12A7328-F81F-11D2-BA4B-00A0C93EC93B "$esp" \
    -append_partition 3 EBD0A0A2-B9E5-4433-87C0-68B6B72699C7 "$datos" -appended_part_as_gpt \
    -e --interval:appended_partition_2:all:: -no-emul-boot \
    -o "$OUT/antu-live.iso" "$OUT/iso"
(cd "$OUT" && sha256sum antu-live.iso > antu-live.iso.sha256)
ls -lh "$OUT/antu-live.iso"

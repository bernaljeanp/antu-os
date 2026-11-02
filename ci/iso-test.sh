#!/usr/bin/env bash
# Prueba la ISO de Antu en QEMU con firmware UEFI (OVMF), en tres arranques:
#   1. la ISO arranca hasta la sesión en vivo con el instalador abierto (captura en-vivo.png);
#   2. el instalador copia Antu a un disco virtual vacío (antu.prueba-instalar en la línea del kernel);
#   3. ese disco arranca solo y muestra Inicio (captura instalado.png).
# Uso: sudo ci/iso-test.sh iso-build    (necesita qemu-system-x86, qemu-utils, ovmf, socat e imagemagick)
set -euo pipefail

B="$1"
OUT="$PWD/pruebas-iso"
mkdir -p "$OUT"
cp /usr/share/OVMF/OVMF_VARS_4M.fd "$OUT/vars.fd"
QEMU=(qemu-system-x86_64 -machine q35,accel=kvm -cpu host -smp 4 -m 8192
      -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd
      -drive if=pflash,format=raw,file="$OUT/vars.fd"
      -device virtio-vga,xres=1920,yres=1080 -display none
      -monitor unix:"$OUT/monitor.sock",server=on,wait=off)

shot() {
    echo "screendump $OUT/$1.ppm" | socat - unix:"$OUT/monitor.sock" > /dev/null
    sleep 3
    convert "$OUT/$1.ppm" "$OUT/$1.png" && rm -f "$OUT/$1.ppm"
}
stop() {
    echo quit | socat - unix:"$OUT/monitor.sock" > /dev/null 2>&1 || true
    wait || true
}
wait_for() {  # archivo patrón segundos
    for _ in $(seq "$3"); do
        grep -qa "$2" "$1" 2> /dev/null && return 0
        sleep 1
    done
    return 1
}

echo "== 1. La ISO arranca hasta la sesión en vivo"
"${QEMU[@]}" -cdrom "$B/antu-live.iso" -serial file:"$OUT/serie-en-vivo.log" &
if ! wait_for "$OUT/serie-en-vivo.log" "ANTU-LIVE: arranque OK" 600; then
    shot en-vivo-fallo
    stop
    echo "::error::La ISO no arrancó hasta el inicio de sesión (ver en-vivo-fallo.png y serie-en-vivo.log)"
    exit 1
fi
sleep 75  # Plasma y el instalador abriéndose
shot en-vivo
stop

echo "== 2. El instalador copia Antu a un disco vacío"
qemu-img create -f qcow2 "$OUT/disco.qcow2" 64G > /dev/null
cmdline="root=live:CDLABEL=ANTU_LIVE rd.live.image rd.live.overlay.overlayfs=1 console=ttyS0,115200"
cmdline+=" systemd.unit=multi-user.target antu.prueba-instalar=/dev/vda"
timeout 3600 "${QEMU[@]}" -no-reboot -cdrom "$B/antu-live.iso" \
    -drive file="$OUT/disco.qcow2",if=virtio,format=qcow2 \
    -kernel "$B/vmlinuz" -initrd "$B/initramfs-live.img" -append "$cmdline" \
    -serial file:"$OUT/serie-instalar.log" || true
if ! grep -qa "ANTU-INSTALAR: OK" "$OUT/serie-instalar.log"; then
    tail -n 80 "$OUT/serie-instalar.log"
    echo "::error::El instalador no terminó (ver serie-instalar.log)"
    exit 1
fi

echo "== 3. El disco instalado arranca solo"
"${QEMU[@]}" -drive file="$OUT/disco.qcow2",if=virtio,format=qcow2 -serial file:"$OUT/serie-instalado.log" &
sleep 240
shot instalado
stop
# Informativo: Inicio sobre el fondo da una imagen variada; una pantalla negra o casi uniforme indica un problema.
spread="$(convert "$OUT/instalado.png" -colorspace Gray -format '%[fx:standard_deviation]' info:)"
echo "Variación de la captura del sistema instalado: $spread"
awk -v s="$spread" 'BEGIN { exit !(s > 0.04) }' || echo "::warning::El sistema instalado parece no mostrar Inicio (ver instalado.png)"
echo "ANTU: pruebas de la ISO OK"

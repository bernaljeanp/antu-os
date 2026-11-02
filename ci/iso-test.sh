#!/usr/bin/env bash
# Prueba la ISO de Antu en QEMU con firmware UEFI (OVMF), sin red y con un disco NVMe vacío, en tres arranques:
#   1. la ISO arranca hasta la sesión en vivo con el instalador abierto (arranque.png y en-vivo.png);
#   galería: las pantallas principales abiertas una a una en la sesión en vivo (galeria.png);
#   arranque seguro: se registra la llave de Antu con el teclado y la ISO arranca (seguro-*.png, para la guía);
#   2. el instalador copia Antu al disco sin internet (antu.prueba-instalar en la línea del kernel);
#   3. ese disco arranca solo hasta la pantalla gráfica, con Inicio (captura instalado.png);
#   4. ese disco arranca también con arranque seguro, sin pedir nada más (instalado-seguro.png).
# Uso: sudo ci/iso-test.sh iso-build    (necesita qemu-system-x86, qemu-utils, ovmf, socat e imagemagick)
set -euo pipefail

B="$1"
OUT="$PWD/pruebas-iso"
mkdir -p "$OUT"
cp /usr/share/OVMF/OVMF_VARS_4M.fd "$OUT/vars.fd"
qemu-img create -f qcow2 "$OUT/disco.qcow2" 64G > /dev/null
QEMU=(qemu-system-x86_64 -machine q35,accel=kvm -cpu host -smp 4 -m 8192 -nic none
      -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd
      -drive if=pflash,format=raw,file="$OUT/vars.fd"
      -drive file="$OUT/disco.qcow2",if=none,id=disco,format=qcow2 -device nvme,serial=ANTU0001,drive=disco
      -device virtio-vga,xres=1920,yres=1080 -display none
      -monitor unix:"$OUT/monitor.sock",server=on,wait=off)
# Como un equipo real: firmware con arranque seguro y las llaves de Microsoft; lo que se registra queda en vars-seguro.fd.
cp /usr/share/OVMF/OVMF_VARS_4M.ms.fd "$OUT/vars-seguro.fd"
QEMU_SEGURO=(qemu-system-x86_64 -machine q35,smm=on,accel=kvm -cpu host -smp 4 -m 8192 -nic none
      -global driver=cfi.pflash01,property=secure,value=on -global ICH9-LPC.disable_s3=1
      -drive if=pflash,format=raw,unit=0,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.secboot.fd
      -drive if=pflash,format=raw,unit=1,file="$OUT/vars-seguro.fd"
      -drive file="$OUT/disco.qcow2",if=none,id=disco,format=qcow2 -device nvme,serial=ANTU0001,drive=disco
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
# Película del arranque: una captura cada 1,5 s (menú, animación «Amanecer» y llegada al escritorio).
for _ in $(seq 50); do [ -S "$OUT/monitor.sock" ] && break; sleep 0.2; done  # QEMU crea su canal de control
for i in $(seq -w 1 24); do
    echo "screendump $OUT/arranque-$i.ppm" | socat - unix:"$OUT/monitor.sock" > /dev/null 2>&1 || true
    sleep 1.5
done
sleep 2
montage "$OUT"/arranque-*.ppm -tile 6x4 -geometry 480x270+4+4 -background black "$OUT/arranque.png"
rm -f "$OUT"/arranque-*.ppm
if ! wait_for "$OUT/serie-en-vivo.log" "ANTU-LIVE: arranque OK" 600; then
    shot en-vivo-fallo
    stop
    echo "::error::La ISO no arrancó hasta el inicio de sesión (ver en-vivo-fallo.png y serie-en-vivo.log)"
    exit 1
fi
sleep 75  # Plasma y el instalador abriéndose
shot en-vivo
stop

echo "== Galería: las pantallas principales en la sesión en vivo"
cmdline="root=live:CDLABEL=ANTU_LIVE rd.live.image rd.live.overlay.overlayfs=1 quiet splash antu.galeria"
"${QEMU[@]}" -cdrom "$B/antu-live.iso" -kernel "$B/vmlinuz" -initrd "$B/initramfs-live.img" -append "$cmdline" \
    -serial file:"$OUT/serie-galeria.log" &
for vista in escritorio menu pantalla dolphin zenit notificacion bloqueo; do
    if ! wait_for "$OUT/serie-galeria.log" "ANTU-GALERIA: $vista" 420; then
        echo "::warning::La galería no llegó a «$vista» (ver serie-galeria.log)"
        break
    fi
    shot "galeria-$vista"
done
stop
montage "$OUT"/galeria-*.png -tile 2x -geometry 960x540+6+6 -background black "$OUT/galeria.png" || true

echo "== Arranque seguro: con las llaves de Microsoft, se registra la llave de Antu con el teclado y la ISO arranca"
"${QEMU_SEGURO[@]}" -no-reboot -cdrom "$B/antu-live.iso" -serial file:"$OUT/serie-seguro-registro.log" &
if ! wait_for "$OUT/serie-seguro-registro.log" "BdsDxe: starting" 60; then
    shot seguro-fallo
    stop
    echo "::error::Con arranque seguro, el firmware no arrancó la ISO (ver seguro-fallo.png)"
    exit 1
fi
sleep 8
tecla() {  # tecla foto: la pulsa, espera a la pantalla siguiente y la fotografía
    echo "sendkey $1" | socat - unix:"$OUT/monitor.sock" > /dev/null
    sleep 3
    shot "$2"
}
abajo() { echo "sendkey down" | socat - unix:"$OUT/monitor.sock" > /dev/null; sleep 1; }
shot seguro-1-aviso
tecla ret seguro-2-tecla-para-entrar
tecla ret seguro-3-menu
abajo; tecla ret seguro-4-unidades
tecla ret seguro-5-archivos
tecla ret seguro-6-registrar
abajo; tecla ret seguro-7-confirmar
abajo; tecla ret seguro-8-reiniciar
echo "sendkey ret" | socat - unix:"$OUT/monitor.sock" > /dev/null
sleep 5  # -no-reboot: el reinicio que pide el registro apaga la máquina virtual
stop
"${QEMU_SEGURO[@]}" -cdrom "$B/antu-live.iso" -serial file:"$OUT/serie-seguro.log" &
if ! wait_for "$OUT/serie-seguro.log" "ANTU-LIVE: arranque OK" 600; then
    shot seguro-fallo
    stop
    echo "::error::Con la llave registrada, la ISO no arrancó con arranque seguro (ver seguro-fallo.png)"
    exit 1
fi
sleep 5
shot seguro-en-vivo
stop
grep -a "ANTU-LIVE:" "$OUT/serie-seguro.log"
grep -qa "ANTU-LIVE: arranque seguro=1" "$OUT/serie-seguro.log" || { echo "::error::La ISO arrancó, pero sin arranque seguro activo"; exit 1; }
if grep -qa "Key was rejected" "$OUT/serie-seguro.log"; then
    echo "::error::Con arranque seguro, el núcleo rechaza el módulo de NVIDIA"
    exit 1
fi

echo "== 2. El instalador copia Antu al disco, sin internet"
cmdline="root=live:CDLABEL=ANTU_LIVE rd.live.image rd.live.overlay.overlayfs=1 console=ttyS0,115200"
cmdline+=" systemd.unit=multi-user.target antu.prueba-instalar=/dev/nvme0n1"
timeout 3600 "${QEMU[@]}" -no-reboot -cdrom "$B/antu-live.iso" \
    -kernel "$B/vmlinuz" -initrd "$B/initramfs-live.img" -append "$cmdline" \
    -serial file:"$OUT/serie-instalar.log" || true
if ! grep -qa "ANTU-INSTALAR: OK" "$OUT/serie-instalar.log"; then
    tail -n 80 "$OUT/serie-instalar.log"
    echo "::error::El instalador no terminó (ver serie-instalar.log)"
    exit 1
fi

echo "== 3. El disco instalado arranca solo hasta la pantalla gráfica"
"${QEMU[@]}" -serial file:"$OUT/serie-instalado.log" &
if ! wait_for "$OUT/serie-instalado.log" "Reached target.*Graphical Interface" 600; then
    shot instalado-fallo
    stop
    echo "::error::El sistema instalado no llegó a la pantalla gráfica (ver instalado-fallo.png y serie-instalado.log)"
    exit 1
fi
sleep 60  # Inicio abriéndose
shot instalado
stop

echo "== 4. Con la llave ya registrada, el disco instalado arranca con arranque seguro, sin pedir nada más"
"${QEMU_SEGURO[@]}" -serial file:"$OUT/serie-instalado-seguro.log" &
if ! wait_for "$OUT/serie-instalado-seguro.log" "Reached target.*Graphical Interface" 600; then
    shot instalado-seguro-fallo
    stop
    echo "::error::El sistema instalado no arrancó con arranque seguro (ver instalado-seguro-fallo.png)"
    exit 1
fi
sleep 30  # mismo firmware y variables que confirmaron arranque seguro=1 en la ISO
shot instalado-seguro
stop
echo "ANTU: pruebas de la ISO OK"

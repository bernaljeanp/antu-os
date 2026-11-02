#!/usr/bin/env bash
# Prueba rápida de la cadena de arranque seguro de Antu, sin compilar la imagen: firmware con las llaves de Microsoft
# (como un equipo real) -> shim firmado por Microsoft -> systemd-boot y núcleo de Arch firmados con una llave desechable.
#   1. Con arranque seguro y sin la llave: aparece el registro de llaves y se registra con las mismas teclas que usa una
#      persona, tomando una foto de cada pantalla (de ahí sale la guía).
#   2. Ya registrada: el núcleo arranca y confirma que el arranque seguro está activo.
#   3. Control: un núcleo sin firmar NO arranca. Sin esto, la prueba no demostraría nada.
#   4. Con el arranque seguro apagado, la misma cadena también arranca.
# Uso: sudo ci/arranque-seguro.sh    (necesita podman, qemu-system-x86, ovmf, socat, imagemagick, sbsigntool, mtools,
# dosfstools, openssl y libarchive-tools)
set -euo pipefail

SHIM_VERSION=16.1-10
SHIM_SHA256=50ca8ad0f0893a9b69d257b232cc38fe572d7f2c814bc9aec4df5e492800cdc7
ARCH_IMAGE=docker.io/archlinux/archlinux:latest@sha256:837194727013a6e81fb55be11e61d6dcfe7fdd095b3313f8f3cff9bb3f9b182d

OUT="$PWD/pruebas-arranque-seguro"
W="$(mktemp -d)"
mkdir -p "$OUT"
export MTOOLS_SKIP_CHECK=1

echo "== Materiales: shim de Fedora, firmado por Microsoft"
rpm="shim-x64-$SHIM_VERSION.x86_64.rpm"
curl -fsS --retry 5 --retry-all-errors -o "$W/$rpm" \
    "https://kojipkgs.fedoraproject.org/packages/shim/${SHIM_VERSION%-*}/${SHIM_VERSION#*-}/x86_64/$rpm"
echo "$SHIM_SHA256  $W/$rpm" | sha256sum -c -
mkdir "$W/shim"
bsdtar -xf "$W/$rpm" -C "$W/shim"
shim="$(find "$W/shim" -iname shimx64.efi | head -1)"
mm="$(find "$W/shim" -iname mmx64.efi | head -1)"
sbverify --list "$shim"
for ca in "Microsoft Corporation UEFI CA 2011" "Microsoft UEFI CA 2023"; do
    echo "Firmas con «$ca»: $(grep -ac "$ca" "$shim" || true)"
done

echo "== Materiales: systemd-boot y núcleo de Arch"
podman run --rm -v "$W:/salida" "$ARCH_IMAGE" bash -c '
    pacman -Syu --noconfirm linux > /dev/null
    cp /usr/lib/modules/*/vmlinuz /salida/vmlinuz
    cp /usr/lib/systemd/boot/efi/systemd-bootx64.efi /salida/systemd-bootx64.efi'
objcopy -O binary --only-section=.sbat "$W/systemd-bootx64.efi" "$W/sbat.txt" || true
echo "SBAT de systemd-boot:"; cat "$W/sbat.txt" || true

echo "== Llave desechable y firmas"
openssl req -new -x509 -newkey rsa:2048 -nodes -sha256 -days 30 -subj "/CN=Antu OS prueba/" \
    -keyout "$W/llave.key" -out "$W/llave.crt" 2> /dev/null
openssl x509 -in "$W/llave.crt" -outform DER -out "$W/antu.cer"
sbsign --key "$W/llave.key" --cert "$W/llave.crt" --output "$W/grubx64.efi" "$W/systemd-bootx64.efi"
sbsign --key "$W/llave.key" --cert "$W/llave.crt" --output "$W/vmlinuz-firmado" "$W/vmlinuz"

echo "== Disco de arranque"
esp="$W/esp.img"  # el disco entero es la partición de arranque: la tabla del USB real se prueba en ci/iso-test.sh
truncate -s 200M "$esp"
mkfs.vfat -F 32 -n ANTU_EFI "$esp" > /dev/null
mcopy -i "$esp" "$W/antu.cer" ::/antu.cer  # primero, para que encabece la lista de archivos
mmd -i "$esp" ::/EFI ::/EFI/BOOT ::/loader ::/loader/entries ::/antu
mcopy -i "$esp" "$shim" ::/EFI/BOOT/BOOTX64.EFI
mcopy -i "$esp" "$W/grubx64.efi" ::/EFI/BOOT/grubx64.efi
mcopy -i "$esp" "$mm" ::/EFI/BOOT/mmx64.efi
mcopy -i "$esp" "$W/vmlinuz-firmado" ::/antu/vmlinuz
mcopy -i "$esp" "$W/vmlinuz" ::/antu/vmlinuz-sin-firmar
entrada() {  # archivo-de-entrada núcleo
    printf 'title Antu\nlinux /antu/%s\noptions console=ttyS0,115200 loglevel=7 panic=-1\n' "$2" > "$W/$1"
    mcopy -o -i "$esp" "$W/$1" "::/loader/entries/$1"
}
elegir() {  # archivo-de-entrada
    printf 'default %s\ntimeout 2\neditor no\n' "$1" > "$W/loader.conf"
    mcopy -o -i "$esp" "$W/loader.conf" ::/loader/loader.conf
}
entrada firmado.conf vmlinuz
entrada sin-firmar.conf vmlinuz-sin-firmar
elegir firmado.conf

cp /usr/share/OVMF/OVMF_VARS_4M.ms.fd "$W/vars.fd"
SOCK="$W/monitor.sock"
seguro() {  # registro-serie: arranca con arranque seguro y las variables que se van guardando
    qemu-system-x86_64 -machine q35,smm=on,accel=kvm -cpu host -smp 2 -m 2048 -nic none -no-reboot \
        -global driver=cfi.pflash01,property=secure,value=on -global ICH9-LPC.disable_s3=1 \
        -drive if=pflash,format=raw,unit=0,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.secboot.fd \
        -drive if=pflash,format=raw,unit=1,file="$W/vars.fd" \
        -drive file="$esp",format=raw,if=none,id=disco -device nvme,serial=ANTU0001,drive=disco \
        -device virtio-vga,xres=1280,yres=800 -display none \
        -monitor unix:"$SOCK",server=on,wait=off -serial file:"$OUT/$1" &
    for _ in $(seq 50); do [ -S "$SOCK" ] && break; sleep 0.2; done
}
monitor() { echo "$1" | socat - unix:"$SOCK" > /dev/null 2>&1 || true; }
foto() {
    monitor "screendump $W/$1.ppm"
    sleep 1
    convert "$W/$1.ppm" "$OUT/$1.png" || true
}
tecla() {  # tecla foto: la pulsa, espera a la pantalla siguiente y la fotografía
    monitor "sendkey $1"
    sleep 3
    foto "$2"
}
parar() {
    monitor quit
    wait || true
    rm -f "$SOCK"
}
esperar() {  # archivo patrón segundos
    for _ in $(seq "$3"); do
        grep -qa "$2" "$1" 2> /dev/null && return 0
        sleep 1
    done
    return 1
}
falla() {
    echo "::error::$1"
    tail -n 30 "$OUT"/serie-*.log || true
    exit 1
}

echo "== 1. Registro de la llave, con el teclado"
seguro serie-registro.log
sleep 12
foto 01-aviso
tecla ret 02-tecla-para-entrar
tecla ret 03-menu
monitor "sendkey down"; sleep 1
tecla ret 04-unidades
tecla ret 05-archivos
tecla ret 06-registrar
monitor "sendkey down"; sleep 1
tecla ret 07-confirmar
monitor "sendkey down"; sleep 1
tecla ret 08-reiniciar
monitor "sendkey ret"
sleep 5  # -no-reboot: el reinicio que pide el registro apaga la máquina virtual
parar

echo "== 2. Ya registrada, el núcleo firmado arranca con arranque seguro activo"
seguro serie-firmado.log
esperar "$OUT/serie-firmado.log" "Secure boot enabled" 90 || { foto fallo-firmado; parar; falla "El núcleo firmado no arrancó con arranque seguro"; }
foto 09-arranca
parar

echo "== 3. Control: un núcleo sin firmar no arranca"
elegir sin-firmar.conf
seguro serie-sin-firmar.log
sleep 30
foto 10-sin-firmar
parar
if grep -qa "Linux version" "$OUT/serie-sin-firmar.log"; then
    falla "Un núcleo sin firmar arrancó: el arranque seguro no se está cumpliendo"
fi
elegir firmado.conf

echo "== 4. Con el arranque seguro apagado, la misma cadena arranca"
cp /usr/share/OVMF/OVMF_VARS_4M.fd "$W/vars-normal.fd"
qemu-system-x86_64 -machine q35,accel=kvm -cpu host -smp 2 -m 2048 -nic none -no-reboot \
    -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
    -drive if=pflash,format=raw,file="$W/vars-normal.fd" \
    -drive file="$esp",format=raw,if=none,id=disco -device nvme,serial=ANTU0001,drive=disco \
    -device virtio-vga -display none \
    -monitor unix:"$SOCK",server=on,wait=off -serial file:"$OUT/serie-normal.log" &
esperar "$OUT/serie-normal.log" "Linux version" 90 || { parar; falla "Sin arranque seguro, la cadena no arrancó"; }
parar

echo "ANTU: cadena de arranque seguro OK"

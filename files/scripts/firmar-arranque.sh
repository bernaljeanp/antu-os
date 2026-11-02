#!/usr/bin/env bash
# Arranque seguro: deja en la imagen el shim de Fedora, firmado por Microsoft (con las autoridades de 2011 y 2023, para
# equipos antiguos y nuevos), y firma con la llave de Antu el cargador y el núcleo, que shim comprueba contra la llave
# que cada persona registra una sola vez. La parte pública es /usr/share/antu/arranque-seguro.cer.
# La privada llega como secreto de la compilación y no queda en ninguna capa. Sin ella (imagen de prueba, pull requests)
# la imagen queda sin firmar, y build.yml no deja publicar una imagen así.
set -euo pipefail

SHIM_VERSION=16.1-10
SHIM_SHA256=50ca8ad0f0893a9b69d257b232cc38fe572d7f2c814bc9aec4df5e492800cdc7

llave=/run/secrets/antu_arranque
cargador=/usr/lib/systemd/boot/efi/systemd-bootx64.efi
destino=/usr/lib/antu/arranque
temporal="$(mktemp -d)"

rpm="shim-x64-$SHIM_VERSION.x86_64.rpm"
curl -fsS --retry 5 --retry-all-errors -o "$temporal/$rpm" \
    "https://kojipkgs.fedoraproject.org/packages/shim/${SHIM_VERSION%-*}/${SHIM_VERSION#*-}/x86_64/$rpm"
echo "$SHIM_SHA256  $temporal/$rpm" | sha256sum -c -
bsdtar -xf "$temporal/$rpm" -C "$temporal"
mkdir -p "$destino"
cp "$(find "$temporal" -iname shimx64.efi | head -1)" "$destino/shimx64.efi"
cp "$(find "$temporal" -iname mmx64.efi | head -1)" "$destino/mmx64.efi"

if [ -s "$llave" ]; then
    pacman -S --noconfirm --needed sbsigntools
    openssl x509 -inform DER -in /usr/share/antu/arranque-seguro.cer -out "$temporal/arranque.crt"
    nucleo="/usr/lib/modules/$(ls /usr/lib/modules)/vmlinuz"
    sbsign --key "$llave" --cert "$temporal/arranque.crt" --output "$nucleo" "$nucleo"
    # bootctl prefiere el archivo .signed al instalar el cargador.
    sbsign --key "$llave" --cert "$temporal/arranque.crt" --output "$cargador.signed" "$cargador"
    pacman -Rns --noconfirm sbsigntools
else
    echo "Sin llave de arranque: esta imagen queda sin firmar."
fi
rm -rf "$temporal"

# Antu OS: Arch Linux atómico con bootc, NVIDIA y KDE Plasma.
# La parte bootc está adaptada de bootcrew/mono (Apache-2.0, Copyright 2025 tulilirockz);
# ver third_party/bootcrew-LICENSE.

ARG BOOTC_VERSION=v1.17.3
# Las etiquetas git se pueden mover: el commit se verifica después de clonar.
ARG BOOTC_COMMIT=6d7893f2dbdd289a4a04a5727e4df29433d43024

# Base fijada por digest para un punto de partida reproducible; pacman -Syu trae los paquetes del día.
FROM docker.io/archlinux/archlinux:latest@sha256:837194727013a6e81fb55be11e61d6dcfe7fdd095b3313f8f3cff9bb3f9b182d AS base

# bootc no está en los repositorios de Arch: se compila desde una versión fijada.
# Sin la función selinux (activada por defecto; Arch no trae libselinux) y sin manuales,
# con las opciones que documenta el Makefile de bootc para distribuciones sin SELinux.
FROM base AS bootc
ARG BOOTC_VERSION
ARG BOOTC_COMMIT
RUN pacman -Syu --noconfirm make git rust ostree glibc pkgconf
RUN git clone --depth 1 --branch "${BOOTC_VERSION}" https://github.com/bootc-dev/bootc.git /src && \
    test "$(git -C /src rev-parse HEAD)" = "${BOOTC_COMMIT}" && \
    make -C /src bin install-all DESTDIR=/output DISABLE_DOCS=1 \
      CARGO_OPTIONS='--no-default-features --features "install-to-disk pre-6.15"'

FROM base

COPY --from=bootc /output /

# /var no forma parte de la imagen: pacman pasa a guardar su estado en /usr/lib/sysimage.
RUN grep "= */var" /etc/pacman.conf | sed "/= *\/var/s/.*=// ; s/ //" | xargs -n1 sh -c 'mkdir -p "/usr/lib/sysimage/$(dirname $(echo $1 | sed "s@/var/@@"))" && mv -v "$1" "/usr/lib/sysimage/$(echo "$1" | sed "s@/var/@@")"' '' && \
    sed -i -e "/= *\/var/ s/^#//" -e "s@= */var@= /usr/lib/sysimage@g" -e "/DownloadUser/d" /etc/pacman.conf

# La imagen Docker de Arch omite idiomas y manuales; un escritorio en español los necesita.
RUN sed -i 's/^[[:space:]]*NoExtract/#&/' /etc/pacman.conf && \
    pacman -Syu --noconfirm glibc && \
    sed -i -E 's/^#(es_CL.UTF-8|es_ES.UTF-8|en_US.UTF-8)/\1/' /etc/locale.gen && locale-gen && \
    echo "LANG=es_CL.UTF-8" > /etc/locale.conf

# Sistema base atómico.
RUN pacman -S --noconfirm base bubblewrap dracut linux linux-firmware intel-ucode amd-ucode \
      ostree btrfs-progs e2fsprogs xfsprogs dosfstools efibootmgr pciutils usbutils skopeo dbus dbus-glib glib2 shadow && \
    pacman -S --clean --noconfirm

# multilib: Steam y las librerías de 32 bits que usan casi todos los juegos. La imagen Docker de Arch no siempre
# trae el bloque comentado, así que se descomenta si existe y se añade si no.
RUN sed -i '/^#\[multilib\]/,/^#Include/ s/^#//' /etc/pacman.conf && \
    { grep -q '^\[multilib\]' /etc/pacman.conf || printf '\n[multilib]\nInclude = /etc/pacman.d/mirrorlist\n' >> /etc/pacman.conf; } && \
    pacman -Sy

# Escritorio y NVIDIA. nvidia-open viene compilado para el mismo kernel de arriba.
# Discover solo con Flatpak (sin PackageKit): las apps se instalan sin tocar el sistema base.
# El navegador (Brave) llega desde Flathub en el primer arranque: ver antu-apps.service.
# plasma-desktop deja como opcional mucho de lo que se espera de un escritorio: volumen (plasma-pa), pantallas (kscreen),
# Bluetooth, llavero al iniciar sesión, información del equipo, permisos de apps, avisos de discos y Thunderbolt. Sonido de los
# portátiles recientes (sof-firmware), canales de wifi del país (wireless-regdb), discos de Windows y USB (ntfs-3g, exfatprogs).
RUN pacman -S --noconfirm nvidia-open nvidia-utils \
      plasma-desktop sddm plasma-nm networkmanager konsole dolphin plymouth \
      plasma-pa kscreen bluez bluedevil kwallet-pam kinfocenter kde-gtk-config breeze-gtk flatpak-kcm plasma-disks \
      plasma-thunderbolt ffmpegthumbs sof-firmware wireless-regdb ntfs-3g exfatprogs \
      pipewire pipewire-pulse pipewire-alsa wireplumber noto-fonts openssh \
      discover flatpak ark gwenview spectacle kate kcalc 7zip python-pyqt6 firewalld plasma-firewall git podman distrobox && \
    pacman -S --clean --noconfirm

# Capa de juegos: Steam, Gamescope (modo Eclipse), GameMode, MangoHud y los controladores de 32 bits.
# nvidia-prime da prime-run para portátiles híbridos; con switcheroo-control, KDE abre Steam solo en la gráfica dedicada.
# Un solo sistema para toda gráfica: vulkan-intel y vulkan-radeon cubren
# las integradas y los equipos sin NVIDIA. kdialog: el aviso antes de entrar a Eclipse. zram-generator: memoria comprimida
# en vez de swap en disco (ver usr/lib/systemd/zram-generator.conf).
# -Sy: la limpieza de capas anteriores (pacman -Sc) puede borrar la base de datos sincronizada de multilib.
RUN pacman -Sy --noconfirm steam lib32-nvidia-utils lib32-vulkan-icd-loader vulkan-intel lib32-vulkan-intel vulkan-radeon lib32-vulkan-radeon \
      gamescope gamemode lib32-gamemode mangohud lib32-mangohud nvidia-prime switcheroo-control vulkan-tools ttf-liberation zram-generator kdialog && \
    pacman -S --clean --noconfirm

# USBoot, la app de Antu para crear USB de arranque: su AppImage se extrae en la imagen, así no necesita FUSE.
ARG USBOOT_VERSION=v0.2.1
ARG USBOOT_SHA256=d6d1dcf714f65b586c5838b0b3962344d13f98b0d735c9faa27d82f0d0678c66
RUN curl -fsSL --retry 5 --retry-all-errors -o /tmp/usboot.AppImage \
      "https://github.com/bernaljeanp/usboot/releases/download/${USBOOT_VERSION}/USBoot_${USBOOT_VERSION#v}_linux-beta_amd64.AppImage" && \
    echo "${USBOOT_SHA256}  /tmp/usboot.AppImage" | sha256sum -c - && \
    chmod +x /tmp/usboot.AppImage && cd /tmp && ./usboot.AppImage --appimage-extract > /dev/null && \
    mv /tmp/squashfs-root /usr/lib/usboot && chmod -R a+rX /usr/lib/usboot && rm /tmp/usboot.AppImage

# Archivos de Antu: identidad (colores, tema, fuentes, fondo), servicios, Inicio y configuración. Van antes de
# activar servicios porque varias unidades (antu-*) vienen de aquí.
COPY files/system/ /
RUN --mount=type=bind,source=files/scripts,target=/antu-scripts bash /antu-scripts/kde-defaults.sh

# Inicio (asistente gráfico del primer arranque) crea la primera cuenta con systemd-homed antes del inicio de sesión.
# Zenit controla perfiles térmicos, luces, carga y teclas del portátil (Alienware y Dell). antu-actualizar baja
# cada versión nueva en segundo plano y la deja lista para el próximo reinicio.
# Firewall: zona antu (solo lo que llega sin pedirlo se bloquea; ver usr/lib/firewalld/zones/antu.xml).
# La red la maneja NetworkManager: systemd-networkd queda apagado, también en el primer arranque (10-antu.preset).
RUN systemctl enable sddm NetworkManager systemd-timesyncd systemd-homed antu-inicio-prepare antu-ia antu-apps antu-craft-apps zenit antu-actualizar.timer firewalld bluetooth switcheroo-control \
      nvidia-suspend nvidia-resume nvidia-hibernate nvidia-suspend-then-hibernate && \
    systemctl disable systemd-networkd.service systemd-networkd.socket systemd-networkd-wait-online.service && \
    systemctl --global enable antu-observatorio && \
    sed -i 's/^DefaultZone=.*/DefaultZone=antu/' /etc/firewalld/firewalld.conf && \
    systemctl mask systemd-firstboot.service && \
    passwd -l root && \
    echo "uninitialized" > /etc/machine-id && \
    ln -sf /usr/share/zoneinfo/UTC /etc/localtime

# Initramfs con los módulos de bootc, regenerado después de instalar kernel y NVIDIA.
RUN mkdir -p /usr/lib/dracut/dracut.conf.d && \
    printf "systemdsystemconfdir=/etc/systemd/system\nsystemdsystemunitdir=/usr/lib/systemd/system\n" > /usr/lib/dracut/dracut.conf.d/30-antu-bootc-module.conf && \
    printf 'reproducible=yes\nhostonly=no\ncompress=zstd\nadd_dracutmodules+=" bootc plymouth "\nadd_drivers+=" usb_storage uas sd_mod "\n' > /usr/lib/dracut/dracut.conf.d/30-antu-bootc-build.conf && \
    kver="$(ls /usr/lib/modules)" && dracut --force "/usr/lib/modules/${kver}/initramfs.img" "${kver}"

# Solo para la prueba de arranque en CI: SSH para revisar la VM, con su puerto abierto en el firewall (si no, la prueba
# solo pasa cuando alcanza a conectarse antes de que el firewall cargue), y sin el asistente de primer arranque, que
# esperaría en la consola para siempre. La imagen publicada no lleva ninguno de estos cambios.
ARG ANTU_CI=0
RUN if [ "${ANTU_CI}" = 1 ]; then systemctl enable sshd && systemctl mask antu-inicio-prepare.service antu-apps.service antu-craft-apps.service && sed -i 's#</zone>#  <service name="ssh"/>\n</zone>#' /usr/lib/firewalld/zones/antu.xml && grep -q 'service name="ssh"' /usr/lib/firewalld/zones/antu.xml; fi

# Arranque seguro: shim firmado por Microsoft, y núcleo y cargador con la llave de Antu. Va después de ANTU_CI para que la
# imagen publicable no reutilice esta capa de la imagen de prueba, que se compila sin la llave.
RUN --mount=type=secret,id=antu_arranque --mount=type=bind,source=files/scripts,target=/antu-scripts \
    bash /antu-scripts/firmar-arranque.sh

# Estructura que espera un sistema por imágenes: todo lo mutable vive en /var.
RUN sed -i 's|^HOME=.*|HOME=/var/home|' /etc/default/useradd && \
    rm -rf /boot /home /root /usr/local /srv /opt /mnt /var /usr/lib/sysimage/log /usr/lib/sysimage/cache/pacman/pkg && \
    mkdir -p /sysroot /boot /usr/lib/ostree /var && \
    ln -sT sysroot/ostree /ostree && ln -sT var/roothome /root && ln -sT var/srv /srv && ln -sT var/opt /opt && \
    ln -sT var/mnt /mnt && ln -sT var/home /home && ln -sT ../var/usrlocal /usr/local && \
    for dir in opt home srv mnt usrlocal; do echo "d /var/$dir 0755 root root -"; done >> /usr/lib/tmpfiles.d/bootc-base-dirs.conf && \
    printf "d /var/roothome 0700 root root -\nd /run/media 0755 root root -\n" >> /usr/lib/tmpfiles.d/bootc-base-dirs.conf && \
    printf '[composefs]\nenabled = yes\n[sysroot]\nreadonly = true\n' > /usr/lib/ostree/prepare-root.conf

# Cada archivo lleva el paquete de Arch al que pertenece (atributo user.component): con eso, chunkah reempaqueta la
# imagen publicada por paquetes (build.yml) y una actualización solo baja los paquetes que cambiaron.
RUN --mount=type=bind,source=files/scripts,target=/antu-scripts python3 /antu-scripts/componentes.py

LABEL containers.bootc=1
LABEL org.opencontainers.image.title="Antu OS" \
      org.opencontainers.image.description="Distro gamer chilena: Arch atómico con NVIDIA, AMD o Intel y KDE Plasma."

RUN bootc container lint

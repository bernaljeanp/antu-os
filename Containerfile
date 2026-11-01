# Antu OS: Arch Linux atómico con bootc, NVIDIA y KDE Plasma.
# La parte bootc está adaptada de bootcrew/mono (Apache-2.0, Copyright 2025 tulilirockz);
# ver third_party/bootcrew-LICENSE.

ARG BOOTC_VERSION=v1.17.3

FROM docker.io/archlinux/archlinux:latest AS base

# bootc no está en los repositorios de Arch: se compila desde una versión fijada.
FROM base AS bootc
ARG BOOTC_VERSION
RUN pacman -Syu --noconfirm make git rust go-md2man ostree glibc pkgconf
RUN git clone --depth 1 --branch "${BOOTC_VERSION}" https://github.com/bootc-dev/bootc.git /src && \
    make -C /src bin install-all DESTDIR=/output

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
      ostree btrfs-progs e2fsprogs xfsprogs dosfstools skopeo dbus dbus-glib glib2 shadow && \
    pacman -S --clean --noconfirm

# Escritorio y NVIDIA. nvidia-open viene compilado para el mismo kernel de arriba.
RUN pacman -S --noconfirm nvidia-open nvidia-utils \
      plasma-desktop sddm plasma-nm networkmanager konsole dolphin \
      pipewire pipewire-pulse wireplumber noto-fonts openssh && \
    pacman -S --clean --noconfirm

RUN systemctl enable sddm NetworkManager systemd-timesyncd && \
    systemctl mask systemd-firstboot.service && \
    echo "uninitialized" > /etc/machine-id && \
    ln -sf /usr/share/zoneinfo/UTC /etc/localtime

# Identidad Antu: colores, tema global, fuentes y fondo.
COPY files/system/ /
RUN --mount=type=bind,source=files/scripts,target=/antu-scripts bash /antu-scripts/kde-defaults.sh

# Initramfs con los módulos de bootc, regenerado después de instalar kernel y NVIDIA.
RUN mkdir -p /usr/lib/dracut/dracut.conf.d && \
    printf "systemdsystemconfdir=/etc/systemd/system\nsystemdsystemunitdir=/usr/lib/systemd/system\n" > /usr/lib/dracut/dracut.conf.d/30-antu-bootc-module.conf && \
    printf 'reproducible=yes\nhostonly=no\ncompress=zstd\nadd_dracutmodules+=" bootc "\n' > /usr/lib/dracut/dracut.conf.d/30-antu-bootc-build.conf && \
    kver="$(ls /usr/lib/modules)" && dracut --force "/usr/lib/modules/${kver}/initramfs.img" "${kver}"

# Solo para la prueba de arranque en CI: SSH permite revisar la VM. La imagen publicada no lo activa.
ARG ANTU_DEV_SSH=0
RUN if [ "${ANTU_DEV_SSH}" = 1 ]; then systemctl enable sshd; fi

# Estructura que espera un sistema por imágenes: todo lo mutable vive en /var.
RUN sed -i 's|^HOME=.*|HOME=/var/home|' /etc/default/useradd && \
    rm -rf /boot /home /root /usr/local /srv /opt /mnt /var /usr/lib/sysimage/log /usr/lib/sysimage/cache/pacman/pkg && \
    mkdir -p /sysroot /boot /usr/lib/ostree /var && \
    ln -sT sysroot/ostree /ostree && ln -sT var/roothome /root && ln -sT var/srv /srv && ln -sT var/opt /opt && \
    ln -sT var/mnt /mnt && ln -sT var/home /home && ln -sT ../var/usrlocal /usr/local && \
    for dir in opt home srv mnt usrlocal; do echo "d /var/$dir 0755 root root -"; done >> /usr/lib/tmpfiles.d/bootc-base-dirs.conf && \
    printf "d /var/roothome 0700 root root -\nd /run/media 0755 root root -\n" >> /usr/lib/tmpfiles.d/bootc-base-dirs.conf && \
    printf '[composefs]\nenabled = yes\n[sysroot]\nreadonly = true\n' > /usr/lib/ostree/prepare-root.conf

LABEL containers.bootc=1
LABEL org.opencontainers.image.title="Antu OS" \
      org.opencontainers.image.description="Distro gamer chilena: Arch atómico con NVIDIA y KDE Plasma."

RUN bootc container lint

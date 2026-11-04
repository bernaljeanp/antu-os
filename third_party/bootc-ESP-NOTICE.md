# bootc: selección de ESP durante la instalación

Upstream: https://github.com/bootc-dev/bootc, v1.17.3, commit `6d7893f2dbdd289a4a04a5727e4df29433d43024`.

bootc se distribuye bajo MIT OR Apache-2.0. Se conservan sus textos en este directorio. El parche local `files/scripts/bootc-esp-mounted.patch` se ofrece bajo las mismas licencias.

Antu prepara una ESP nueva al instalar en espacio sin asignar. El código upstream elige la primera ESP colocada con la raíz, tanto para instalar el cargador como para escribir las entradas de arranque. El parche da prioridad a una partición FAT montada explícitamente por el instalador en `boot/efi`, usando la misma selección en ambos recorridos. Cuando no hay un montaje explícito conserva la detección original.

El commit upstream se comprueba antes de aplicar el parche. Un cambio incompatible detiene la compilación. La prueba QEMU compara todas las particiones previas y verifica el arranque LUKS2; las pruebas normales de instalación sin cifrado se conservan.

No se ha enviado este parche al proyecto upstream ni se ha contactado a sus mantenedores.

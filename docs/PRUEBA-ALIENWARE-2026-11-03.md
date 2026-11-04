# Primera prueba física: Alienware 16X Aurora AC16251

Fuente: `informe-20261103-183253.txt`, leído desde la partición ANTU_DATOS del USB. El informe original se conserva sin
modificar. No se incorpora al repositorio porque todavía incluía el nombre personalizado del equipo. No identifica el
commit de la imagen, por lo que no se puede atribuir con certeza este USB a `caa1c28`.

## Observado en el equipo real

Core Ultra 9 275HX, unos 30 GiB de memoria, Intel integrada y RTX 5070 Laptop. Núcleo 7.2.14-arch1-1 y NVIDIA 615.78.08.
Arranque en vivo con Secure Boot apagado, sesión KDE Wayland, pantalla interna configurada a 2560×1600 y 240 Hz.
Ambas gráficas aparecen en Vulkan. Wifi conectado. Zenit activo con perfiles y ventiladores disponibles.
El informe quedó guardado en el USB y pudo leerse desde Windows. Esto no demuestra instalación en disco ni rendimiento
en juegos, suspensión, sonido audible, emparejamiento Bluetooth o funcionamiento de Eclipse.

| Hallazgo | Alcance de la evidencia | Cambio preparado |
|---|---|---|
| 30 denegaciones al leer `/etc/resolv.conf` | Ocurren al principio del arranque, aproximadamente entre los segundos 5,0 y 5,5. No prueban que internet siguiera fallando después | Preparar el enlace antes de arrancar los servicios, activar resolved explícitamente y entregar los DNS desde NetworkManager |
| PipeWire y WirePlumber no encuentran RealtimeKit | Falta un componente para solicitar prioridad de audio; no prueba por sí solo que no hubiera sonido | Instalar `rtkit` y verificar su activación por D-Bus en la VM |
| Bluetooth hci0: WMT agotó el tiempo y falló func ctrl (-110) | Hay un error de inicialización del MT7925; no se registró un emparejamiento | Mantener despierto solo el USB 0489:e139 y permitir un único intento de reconfiguración si persiste el fallo y BlueZ no lo reconoce |
| CPU 61 °C en la única muestra y 96 °C en la captura posterior | Lecturas distintas, sin duración suficiente para afirmar sobrecalentamiento sostenido | Prioridad estable del sensor del procesador, origen de sensores, uso de CPU, contadores térmicos y muestreo continuo |
| Fallo al cargar DiscoverPackageKitNotifier.so | Discover intenta cargar un motor opcional sin su biblioteca | Retirar sus dos complementos de PackageKit al construir; conservar Flatpak |
| Opción antigua de OverlayFS | Aviso de dracut en el arranque | Cambiar a `rd.overlay=1` en ISO y pruebas |
| Una sola muestra de la prueba | El registro dependía de abrir la ventana y activar el interruptor | Servicio exclusivo del sistema en vivo que arranca automáticamente y sigue al cerrar la ventana |

## Registro y guardado

`antu-registro-live.service` conserva hasta 2880 muestras, una cada cinco segundos. Los comandos de diagnóstico tienen
tiempo limitado y se ejecutan en otro hilo: no interrumpen el muestreo. La gráfica que ya está suspendida no se consulta
con nvidia-smi para despertarla. Pausar y reanudar el servicio conserva las muestras de esa sesión.

Cada minuto se actualiza un informe `informe-live-FECHA-HORA.txt` en ANTU_DATOS. Al apagar normalmente se intenta guardar
la última muestra. El botón **Crear informe** produce una copia aparte y añade los detalles de pantalla, audio y Vulkan.
La exportación valida que los datos pertenecen al mismo disco del que arrancó Antu. Un cerrojo serializa los guardados;
el archivo anterior se reemplaza después de escribir y sincronizar el nuevo. Si falla el guardado se informa del error;
no se borran informes anteriores. Un corte de energía puede perder lo que aún no alcanzó a guardarse.

La limpieza omite el nombre del equipo, nombres personales de la sesión, direcciones y números de serie. Conserva las
versiones de Vulkan de cuatro números, que antes se confundían con direcciones IP. Las nuevas imágenes registran su
revisión de origen en `/usr/share/antu/revision`.

## Pendiente de comprobar en el Alienware

Las correcciones de código aún no han arrancado en el equipo. La recuperación de Bluetooth es una mitigación, no una
confirmación de que el defecto del controlador esté resuelto. El dispositivo puede requerir una corrección del núcleo
o firmware. No se ha sustituido el núcleo ni cambiado la BIOS.

El aviso interno NVIDIA `nvAssertFailedNoLog` y la falta de EDID de DP-2 requieren repetir la prueba, especialmente con
una pantalla externa. No hay evidencia suficiente para elegir otro controlador o alterar sus opciones a ciegas.
Los avisos de ACPI/WMI del firmware y los cierres de componentes KDE tampoco tienen una causa demostrada en este
informe. El siguiente incluye fallos de la sesión, cierres inesperados y contexto adicional de Bluetooth y sensores.

La siguiente prueba debe verificar navegación/descargas, sonido y micrófono, un emparejamiento Bluetooth, varios
minutos de temperaturas, un juego en Steam, viaje de ida y vuelta a Eclipse, y suspensión/reanudación. Después se crea
el informe completo. No se considera aprobado el equipo hasta completar esas comprobaciones.

## Validación local de estas correcciones

- 20 pruebas de regresión en Python sobre Debian en WSL: privacidad, sustitución real del archivo DNS con permisos 0700,
  guardado atómico con fallo de escritura simulado, rechazo de otros discos y rutas, muestras conservadas al reiniciar,
  GPU suspendida, contadores térmicos, prioridad de sensores y recuperación Bluetooth limitada.
- Autopruebas existentes de Zenit y limpieza del informe correctas.
- Sintaxis Bash y análisis de las tres unidades systemd correctos. En WSL, los permisos sintéticos del montaje de Windows
  provocan avisos de modo de archivo; la revisión final se realiza también sobre copias en un sistema de archivos Linux.
- Ventana QML cargada sin errores, con datos de demostración, a 900×660, 1100×760 y 3840×2160. Botón visible y capturas
  de inicio/guardado revisadas. Esto comprueba la interfaz, no el guardado real en Antu.
- Las pruebas de la próxima compilación verifican RealtimeKit, DNS desde el comienzo y registro automático sin ventana.

No se ha construido ni arrancado una ISO nueva, ejecutado GitHub Actions, publicado cambios ni regrabado el USB.
Primero Claude revisa e integra. El cambio afecta la imagen base y el sistema en vivo: al publicarlo hay que evitar la
ejecución ISO por push que use la imagen anterior y dejar completar la ISO encadenada a la nueva compilación de `antu`.

## Referencias consultadas

- [NetworkManager: DNS y rc-manager](https://networkmanager.pages.freedesktop.org/NetworkManager/NetworkManager/NetworkManager.conf.html).
- [systemd-resolved: enlace recomendado de resolv.conf](https://www.freedesktop.org/software/systemd/man/258/systemd-resolved.html).
- [PipeWire: prioridades y RealtimeKit](https://docs.pipewire.org/page_module_rt.html).
- [Identificación USB 0489:e139 del MT7925, parche original del controlador](https://lkml.iu.edu/hypermail/linux/kernel/2407.1/08263.html).
- [Corrección upstream de recuperación tras WMT timeout](https://kernel.googlesource.com/pub/scm/linux/kernel/git/bluetooth/bluetooth-next/+/a6491451f8b8481d8ae0d4057fc046eaf7cb5ff1).
- [dracut: parámetro rd.overlay](https://man.archlinux.org/man/dracut.cmdline.7).

# Zenit en Bazzite

Antu ya incluye el port Linux de Zenit. Este instalador permite usarlo de forma independiente en Bazzite (KDE/Wayland, x86_64), sin instalar Antu OS, sin cambiar `/usr` y sin superponer paquetes con rpm-ostree.

## Instalar desde este checkout

Requiere Python 3 con `venv`/pip, Internet para descargar PyQt6, systemd y una cuenta administradora del grupo `wheel` con sudo. Ejecuta en el sistema anfitrión, **fuera de Distrobox/Toolbox**, como tu usuario habitual:

```bash
bash scripts/install-zenit-bazzite.sh
```

La interfaz y Qt se instalan en `${XDG_DATA_HOME:-~/.local/share}/zenit`. Se añaden entradas al menú y al inicio de sesión. El instalador pide sudo para copiar el motor a `/var/opt/zenit/zenit.py` (propiedad de root), crear `/etc/systemd/system/zenit.service` y arrancarlo. El estado queda en `/var/lib/zenit`. Solo root y el grupo wheel acceden al socket. No ejecuta como root código desde la carpeta del usuario.

Abre **Zenit** desde el menú. Con las rutas por defecto:

```bash
~/.local/share/zenit/zenit-cli estado
~/.local/share/zenit/zenit-cli perfil auto
journalctl -u zenit -b
```

`--sin-servicio` instala únicamente la interfaz y CLI para probarlas; no prepara control de hardware. La interfaz acepta `--demo` para mostrar datos ficticios claramente indicados. Repetir el instalador actualiza las copias sin borrar las preferencias del motor. No sobrescribe un servicio incluido por la distribución.

## Exportar diagnóstico

Desde **Refrigeración → Exportar diagnóstico…** o el menú del icono junto al reloj, elige dónde guardar el JSON. El archivo se crea con permisos privados, se guarda de forma atómica y no se sube automáticamente. La demostración no exporta datos ficticios como diagnóstico real.

Incluye modelo/fabricante DMI, kernel, ID y versión de la distribución, huella SHA-256 del motor, módulos relevantes, capacidades, perfil observado, temperaturas y lecturas de cada chip hwmon, fallos de ventiladores y controladores gráficos detectados. Un cero no confirma que el ventilador esté parado. No lee series, UUID, hostname, variables de entorno, procesos, nombres de juegos ni registros del sistema. No ejecuta nvidia-smi ni cambia el hardware.

Para una comparación útil, guarda un informe en reposo y otro durante CS2, cuando escuches los ventiladores. Cada informe es una instantánea, no una prueba completa de compatibilidad.

Alternativa por terminal (la redirección usa los permisos de tu shell):

```bash
~/.local/share/zenit/zenit-cli diagnostico > zenit-diagnostico.json
```

## Teclas especiales Alienware

El servicio atiende F17 (Boost), F18 (luces) y F20 (Sigilo), que algunos Alienware envían con sus teclas Fn. Se abren dispositivos que anuncien cualquiera de ellas, no solo F17, y se vuelven a buscar cada tres segundos para cubrir arranque tardío o reconexión. El panel muestra cuántos están abiertos y la última tecla especial atendida.

En modo solo luces, F9/F18 funciona, mientras F6/F17 y F7/F20 muestran un aviso y no modifican perfiles. Para usar perfiles desde esas teclas hay que elegir gestión completa de Zenit y comprobar que otro gestor no compita con él.

Para investigar una tecla sin efecto, usa **Gestión del equipo → Probar teclas (15 segundos)…** (también en la bandeja). Pulsa F6 y Fn+F6 y espera a que termine. Después exporta el informe. Solo durante ese intervalo se cuentan F6/F7/F9, F17–F20 y algunos códigos especiales conocidos. No se guardan letras ni texto y Zenit no ejecuta las acciones de esas teclas mientras dura la prueba; otras aplicaciones siguen recibiendo los eventos. Los resultados se conservan en memoria hasta otra prueba o reinicio del servicio.

Otros modelos pueden enviar códigos diferentes o requerir Fn/Fn Lock. Zenit no intercepta F6/F7/F9 normales, que usan otras aplicaciones. Si no funciona F9, pulsa la tecla y exporta el informe: indica qué códigos anuncia cada dispositivo y si Zenit lo abrió. No contiene texto tecleado ni un registro del teclado. La compatibilidad física sigue pendiente de comprobar en el Alienware del usuario.

## Icono junto al reloj

La bandeja usa un símbolo monocromo transparente, separado del icono completo del menú. Sigue el color de texto de la paleta de Qt y se actualiza al cambiar la paleta. Tras actualizar, elige **Salir** en el menú del icono antiguo y vuelve a abrir Zenit para cargarlo. La apariencia final en Plasma debe comprobarse en la sesión real.

## Alienware / Dell

Objetivo solicitado: Alienware descrito como «X16 Aurora R6, RTX 5070, i9». El modelo DMI exacto y la versión del kernel deben comprobarse en el equipo; no se da por equivalente al AC16251 de referencia de Antu.

## Solo luces y monitorización

La instalación en Bazzite usa ahora este modo por defecto, también al actualizar una instalación antigua que no guardaba una elección de gestión. En Zenit puedes cambiarlo con **Solo luces y monitorización**. Se conserva una elección explícita al reiniciar o reinstalar.

En este modo, Zenit mantiene las luces (incluida F9), los sensores y la detección de juegos, pero no escribe perfiles térmicos, no solicita GameMode, no restaura límites de batería al arrancar y bloquea los cambios de carga, Boost/F6 y Sigilo/F7. Bazzite conserva la gestión de energía. No revierte límites ya escritos a la BIOS ni el último perfil aplicado. La CPU y GPU mantienen la regulación térmica del firmware.

También se puede elegir por CLI:

```bash
~/.local/share/zenit/zenit-cli gestion sistema
# Control completo, solo si quieres que Zenit gestione los perfiles:
~/.local/share/zenit/zenit-cli gestion zenit
```

Los ventiladores incluyen el chip y la etiqueta para evitar sobrescribir sensores con el mismo nombre. Un error, valor inválido o indicador de fallo se muestra como «Lectura no disponible». Un cero se muestra como «0 rpm informadas · parada no confirmada»: no prueba que el ventilador esté físicamente detenido. Si no hay sensores, se informa su ausencia.

El motor detecta `alienware-wmi`, perfiles de plataforma (interfaz nueva y ACPI), `hwmon`, límites de batería y Dell WMI sysman. AlienFX usa HID cuando reconoce el controlador. La presencia de una RTX 5070 no garantiza soporte de estas interfaces. No instala módulos de terceros ni controladores de Windows. NVIDIA se consulta cuando corresponde mediante `nvidia-smi`; se evita despertar la GPU dedicada en reposo.

Antes de atribuir un fallo al programa, recoge estos datos de solo lectura:

```bash
cat /sys/class/dmi/id/product_name
uname -r
ls /sys/class/platform-profile/ /sys/class/hwmon/ /sys/class/firmware-attributes/ 2>/dev/null
systemctl status zenit --no-pager
~/.local/share/zenit/zenit-cli estado
```

Si el kernel no expone un control, la interfaz lo deshabilita. Comprueba también que el gestor de energía de Bazzite (por ejemplo tuned o power-profiles-daemon) no esté cambiando el perfil a la vez: Zenit tiene su propia política automática. El instalador no desactiva esos servicios ni modifica tu configuración energética.

## Validación y límites

Se han ejecutado las 28 pruebas de `ci/zenit-test.py`, `zenit.py autoprueba`, instalación de usuario repetida y carga de la interfaz instalada con Qt sin pantalla. No se ha instalado ni iniciado el servicio privilegiado en Bazzite ni validado luces, teclas, batería o térmicas en el Alienware físico. Esta instalación independiente es experimental hasta completar esas comprobaciones.

```bash
python3 ci/zenit-test.py
python3 ci/zenit-maintenance-test.py
python3 files/system/usr/lib/antu/zenit/zenit.py autoprueba
# Con PyQt6 instalado:
python3 ci/zenit-ui-test.py
```

## Actualizar o desinstalar desde Zenit

El menú del icono junto al reloj incluye **Actualizar Zenit…** y **Desinstalar Zenit…**. Abren Konsole para mostrar el progreso y las solicitudes de sudo. También puedes usar `~/.local/share/zenit/actualizar` o `~/.local/share/zenit/desinstalar` desde una terminal.

El actualizador necesita conservar el checkout original de Antu OS. Solo acepta el origen oficial HTTPS, la rama main y un checkout sin cambios locales; hace `git pull --ff-only` y repite el instalador. No restablece ni descarta tu trabajo. Las instalaciones con rutas XDG personalizadas conservan sus rutas. Sal de Zenit y vuelve a abrirlo al terminar.

El desinstalador pide escribir `DESINSTALAR`, detiene y elimina únicamente la unidad del instalador independiente, y conserva `/var/lib/zenit`. No revierte valores de la BIOS. No requiere acceso a Internet. En instalaciones que solo tienen interfaz no ejecuta sudo.

La interfaz de luces distingue preferencias guardadas, último envío y último error. Un reporte incompleto o un controlador permanentemente ocupado hace fallar la operación. La disponibilidad HID se informa cuando se puede leer; **no confirma el color físico**, porque este protocolo no permite leerlo.

## Desinstalar manualmente (rutas por defecto)

```bash
sudo systemctl disable --now zenit.service
sudo rm /etc/systemd/system/zenit.service
sudo systemctl daemon-reload
sudo rm /var/opt/zenit/zenit.py
sudo rmdir /var/opt/zenit
rm ~/.local/share/applications/zenit.desktop ~/.config/autostart/zenit.desktop
rm -r ~/.local/share/zenit
```

Si usaste XDG_DATA_HOME o XDG_CONFIG_HOME distintos, ajusta las tres rutas de usuario. Las preferencias de `/var/lib/zenit` se conservan. Desinstalar no revierte los valores ya escritos a la BIOS; elige los ajustes deseados de carga y perfil antes de hacerlo.

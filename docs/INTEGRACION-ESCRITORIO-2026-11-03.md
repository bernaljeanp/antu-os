# Integración del escritorio — 3 de noviembre de 2026

El tema Antu, los acabados Qt, las apps, el panel revisado y la migración que elimina el acceso fijo de Zenit están conectados al empaquetado del sistema y del Live. Zenit conserva su icono de bandeja y una ventana abierta sigue apareciendo como tarea normal.

## Comprobación dentro de la imagen

`Containerfile` ejecuta `files/scripts/verificar-escritorio.py --runtime` después de copiar los archivos y generar los valores KDE. La compilación falla si faltan componentes compartidos, si no se selecciona Antu/Kvantum, si un PNG tiene dimensiones o formato incorrectos, si quedan referencias SVG sin definir o si Qt no encuentra el motor Kvantum.

El resultado se instala en `/usr/share/antu/escritorio.json`: contiene el SHA-256 de los archivos revisados y una identidad conjunta del contenido. Incluye los iconos y sus alias, los dos layouts, la migración de Zenit, los componentes QML compartidos, los temas nativos y los recursos principales de inicio.

`Containerfile.live` añade la bienvenida y el registro del Live y verifica que todos los archivos del manifiesto base permanecen iguales. Genera `/usr/share/antu/escritorio-live.json`, que conserva la identidad del escritorio que se instala. Los manifiestos cubren estos recursos; no sustituyen la firma de la imagen completa.

## Unión entre imagen e ISO

La creación de la ISO verifica la firma de Antu antes de ejecutar la imagen o construir su capa Live. Usa un digest fijo para la imagen que se prueba y se instala. Acepta referencias con etiqueta o digest y registros con puerto.

Cuando la compilación del sistema dispara el flujo de ISO, el checkout usa su mismo commit y se comprueba `/usr/share/antu/revision`. Si `testing` ya avanzó a otra revisión, el flujo falla en lugar de mezclar versiones. Los manifiestos se adjuntan a los registros y a la entrega de la ISO.

La migración del panel se distribuye por el mecanismo de actualizaciones de Plasma. Se limita a los dos acabados de Antu, conserva los demás accesos y no cambia la geometría personalizada. Las vistas previas y los originales de trabajo continúan fuera de la imagen. El contexto de contenedores excluye los cachés Python locales.

## Validación local

- 8 pruebas de integración en Debian/WSL: empaquetado KDE real en una raíz temporal, enlaces de alias, coincidencia sistema/Live, detección de componentes ausentes y temas incorrectos, rechazo de cambios en la base y separación entre Qt del anfitrión y Qt de la imagen. También se comprueba que una firma inválida impide ejecutar la imagen, que una revisión distinta impide construir el Live y que el digest mantiene el puerto del registro. Estas últimas usan herramientas simuladas y no descargan ni publican imágenes.
- 20 pruebas funcionales del informe y del equipo, 7 regresiones visuales, 24 combinaciones de layout y 6 casos de migración del panel.
- Sintaxis Bash, Python, YAML y finales LF revisados. Inventario del árbol y hashes de la entrega actualizados.

La raíz temporal comprueba archivos y configuración; no equivale a arrancar la distribución. Las comprobaciones de Qt dentro del contenedor quedan conectadas al build real y no se declaran ejecutadas localmente.

## Pendiente para una entrega arrancable

No se ha creado una ISO nueva ni se ha cambiado el USB. El motor Docker local está apagado; la firma de publicación y de arranque usa las llaves custodiadas en GitHub. Los cambios siguen sin commit ni push por la instrucción del usuario.

Para obtener la entrega firmada, estos cambios deben llegar al repositorio remoto y pasar los flujos `antu` e `iso`, incluido el arranque e instalación en QEMU. Después corresponde probar el panel, la migración de un perfil existente y la gráfica en el equipo real. Ninguno de esos resultados se infiere de las pruebas locales.

Archivos principales: `Containerfile`, `Containerfile.live`, `.containerignore`, `.github/workflows/build.yml`, `.github/workflows/iso.yml`, `files/scripts/kde-defaults.sh`, `files/scripts/verificar-escritorio.py`, `scripts/make-iso.sh` y `ci/integracion-test.py`. Evidencia local: `brand/desktop-integration-validation.json`. El inventario completo está en `docs/REFINAMIENTO-VISUAL-2026-11-03-archivos.csv`.

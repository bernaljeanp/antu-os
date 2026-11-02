La A es una cumbre abierta que protege un sol de lava: la misma geometría se lee como montaña, inicial y ventana al cielo. Inter mantiene la palabra Antu sobria y precisa.
Los fondos recorren tres materiales del norte de Chile —obsidiana, mineral desértico y sal— con el interés en los tercios y espacio central para vidrio. Las versiones claras conservan un primer plano en sombra.
Los íconos son objetos de obsidiana, plata anodizada y esmalte lava, iluminados desde arriba a la izquierda: cumbre, umbral, descenso al disco, ocultación solar y núcleo local.

**Entrega y resolución.** Cinco másteres de ícono renderizados nativamente a 4096×4096 con Blender 5.2.3 / Cycles, más sus másteres 1024 y exportaciones 512, 256, 128, 64, 48, 32 y 16. Los tamaños tienen escenas propias: aumento óptico progresivo del motivo; borde más simple; a 32/16 desaparecen el anillo fino de IA y la línea fina de Eclipse; el umbral y el instalador pierden incisiones pequeñas. Los logos se entregan a 2400×800 y también a 3840×1280, con transparencia e Inter SemiBold.

Los seis fondos se generaron con la herramienta integrada image_gen a 1672×941 y se reconstruyeron con Real-ESRGAN x4plus a 6688×3764 antes de reducir a 3840×2160. **Son 4K con superresolución, según la opción elegida por el dueño; no se presentan como generación 4K nativa.** Se guardan los originales y los másteres PNG. La edición 2560×1600 recorta ligeramente los laterales y reduce, sin estirar. Doce JPG de calidad 90, sin submuestreo de color, todos menores de 4 MB. No hay texto, vidrio ni dock en el arte instalado.

**Archivos.** El inventario completo, con estado, tamaño y SHA-256, está en [art-files.csv](art-files.csv). Principales ubicaciones:

- `files/system/usr/share/antu/antu-symbol.svg` y `antu-symbol-light.svg`: símbolo para fondos oscuro y claro.
- `brand/antu-icon.svg`: contenedor raster del ícono original, conservando el nombre del README; `antu-icon-256.png`: PNG correspondiente.
- `brand/antu-logo.png` y `antu-logo-light.png`: palabra blanca para fondo oscuro y palabra obsidiana para fondo claro. Los archivos `*-4k.png` son sus másteres de 3840 px de ancho.
- `brand/masters/icons/<nombre>/<tamaño>.png`: cinco másteres 4096 y renders de cada tamaño. Los de 16–128 se renderizan con supermuestreo antes de su exportación exacta.
- `files/system/usr/share/icons/hicolor/<tamaño>x<tamaño>/apps/<nombre>.png`: 40 PNG instalables, incluyendo cinco de 1024.
- `brand/sources/wallpapers/`: seis originales congelados. `brand/masters/wallpapers/`: seis PNG 4K aprobados.
- `files/system/usr/share/wallpapers/{Antu,Paranal,Salar}/`: metadatos CC-BY-SA-4.0, captura y dos resoluciones en `images/` e `images_dark/`.
- `files/system/usr/share/plymouth/themes/antu/symbol.png`: símbolo transparente de 256 px, regenerado desde `make_brand.py`.
- Tres QML actualizados al fondo JPG; cuatro `.desktop` usan nombres de ícono; ambos layouts de Plasma usan `antu` en el menú. La selección del paquete de fondo sigue siendo `Antu` en los defaults de ambos estilos.

**Vistas de revisión.** [Fondos con vidrio](previews/wallpaper-family.jpg), [familia de íconos](previews/icon-family.png), [símbolo a 16/24/32/48/256](previews/symbol-sizes.png), [logos](previews/logo-variants.png). `previews/wallpapers/` contiene cada prueba de vidrio por separado; `previews/icons/` y `previews/symbols/`, los tamaños reales. `previews/detail/` contiene recortes 1:1 de los JPG finales; `previews/sharpness-comparison.png` compara la ampliación convencional con la reconstrucción 4K. Las vistas están deliberadamente reducidas o recortadas para inspección; los recursos de producción están en las rutas anteriores.

**Generadores.** Se retiraron el ícono plano y las colinas de seno de los scripts anteriores. `python scripts/make_brand.py` exporta geometría, logos, Plymouth y los íconos desde los renders congelados; `--render` reconstruye las escenas originales de `scripts/render_art.py` con `BLENDER_BIN`. `python scripts/make_wallpapers.py` empaqueta los másteres 4K sin regenerarlos; `--superresolve --upscaler <ejecutable>` reconstruye únicamente los másteres ausentes desde las fuentes guardadas. Ningún exportador reemplaza el arte aprobado por las colinas o los íconos antiguos. Los prompts exactos están en [image-prompts.json](image-prompts.json); no se usó generación por API.

La herramienta de superresolución se descargó del [repositorio oficial de Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN), versión ncnn Vulkan 20220424 / v0.2.5.0. SHA-256 del ZIP: `ABC02804E17982A3BE33675E4D471E91EA374E65B70167ABC09E31ACB412802D`. El ejecutable y sus pesos quedaron fuera del repositorio; no se distribuyen dentro de la distro.

**Verificación.** [art-validation.json](art-validation.json) registra dimensiones, transparencia, compresión, licencias, rutas y LF. Se revisaron visualmente el conjunto, el símbolo pequeño, los tamaños de app y recortes de detalle. La integración de QML y lanzadores se comprobó de forma estática; no se ejecutó una sesión Linux, SDDM ni Plymouth en este equipo Windows. Sin commit ni push. Arte original de Antu OS, CC-BY-SA-4.0.

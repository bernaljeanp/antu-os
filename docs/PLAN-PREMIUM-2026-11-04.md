# Antu: fiabilidad y experiencia de uso

Objetivo autorizado: completar las carencias de instalación, datos, preparación inicial, distribución y validación, y mejorar Zenit. Mantener el arte aprobado y la prioridad NVIDIA. No equiparar una VM con una prueba física.

## Entrega

- Zenit: capacidades reales, confirmación de cambios, errores recuperables, estado persistente robusto, comunicación asíncrona y diagnóstico con sensores disponibles.
- Instalación: cifrado LUKS2 y convivencia mediante espacio GPT libre, sin reducir NTFS/BitLocker ni tocar sus particiones. Pruebas exclusivamente en discos virtuales.
- Centro de Antu: descargas por aplicación, selección y reintento, respaldo/restauración y recorrido de validación del equipo.
- Recuperación: conservar rollback existente, respaldar datos aparte y verificar restauraciones antes de declararlas correctas.
- Distribución: descarga duradera, versión, manifiestos, suma y firma verificable; conservar el control de promoción de NVIDIA/núcleo.
- Rendimiento: importar mediciones de cuadros y comparar sesiones reproducibles, sin inventar cifras ni compatibilidad.
- Integración: pruebas negativas de límites privilegiados, carga de interfaces, arranque e instalación en CI y documentación de lo que queda por comprobar físicamente.

Las funciones de hardware se exponen cuando el núcleo/firmware las ofrecen. No se introducen comandos EC, registros de GPU, voltajes o curvas de ventilador inferidos sin documentación. La ingeniería inversa solo se justifica por un dispositivo concreto y evidencia reproducible.

La instalación y el cifrado se ensayan sobre imágenes virtuales aisladas. Los discos y el USB físicos del usuario no forman parte del ensayo.

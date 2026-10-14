# Banco de pruebas de la lectura del Mercurio

Creado el 2026-10-14. Sirve para medir el motor de lectura nuevo contra respuestas correctas ya comprobadas.

## Contenido

Carpeta 2026-08-06. Seis trozos de texto de las páginas B 011, 012 y 013, copiados desde D:\Mercurio\payloads_diag_v2. Cada página se reconstruye uniendo el trozo .0 con el trozo .1 sin sus primeros 2.000 caracteres (el solape se comprobó idéntico en las tres páginas). Incluye inventario_correcto_2026-08-06.json con 95 avisos.

Carpeta 2026-10-14. Texto completo de las páginas B 11 y C 8, descargado desde el visor en Chrome. Las huellas SHA-256 de HUELLAS_ESPERADAS.txt se comprobaron contra los archivos. Incluye inventario_correcto_2026-10-14.json con 58 avisos.

Reporte_2026-08-06.xlsx y Reporte_2026-10-14.xlsx son los Excel que entregó el programa viejo esos días, para comparar.

## Cómo se armó cada inventario

Se unió el texto de todas las páginas de la sección 1616 en orden de lectura, se quitaron las cornisas "1616 Remates de propiedades" que el diario repite en cada columna, y se cortó por inicio de aviso con reglas de código. Después se revisó cada trozo a mano y se corrigieron los cortes que las reglas no vieron. Cada rol del inventario se comprobó presente en el texto.

## Qué mide hoy

Nivel 1. Que el motor encuentre todos los avisos, con su rol y su tribunal, y que no invente ninguno. Los demás datos (fecha del remate, modalidad, vale vista, mínimo, garantía, comuna, fojas, año de dominio) quedan para un nivel 2 que se agrega cuando el motor ya extraiga esos campos.

## Comparación con el programa viejo

06-08. El programa vio 92 de los 93 avisos con rol (solo se le escapó un RIT laboral) y botó en silencio los 2 avisos sin rol.
14-10. El programa vio 19 de los 57 avisos con rol. Los 38 restantes estaban en la página C 8, que no leyó.

## Trampas del diario que el motor debe resistir (todas vistas en estos textos)

Avisos que siguen en otra página o en otro cuerpo del diario ("MÁS AVISOS ECONÓMICOS CLASIFICADOS EN PÁGINA C 8", "VIENEN DE PÁGINA B 11").
Cornisas "1616 Remates de propiedades" en mitad de una palabra ("video confe1616 Remates de propiedades rencia").
Roles sin guion (C-39902025), sin la palabra Rol (expediente C-5915-2025), con punto de miles (C-1.301-2026), con barra (2087/2024), con errata (CC-936-2026), sin prefijo C, o repetidos al inicio y al final del aviso.
Avisos sin rol impreso (Iturra Saldías, partidores) y RIT de juzgados laborales.
Avisos que empiezan sin la palabra REMATE, con el tribunal en palabras (VIGÉSIMO SEXTO, TRIGÉSIMO, DÉCIMO QUINTO (15°)) o pegados al final del aviso anterior (SecretarioREMATE).
Avisos de hasta 7.900 caracteres.

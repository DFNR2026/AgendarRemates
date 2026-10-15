# Reporte de validación de navegación - 2026-10-14

Credenciales: no se incluyen en este reporte. Solo se verificó "usuario cargado: sí / contraseña cargada: sí".
No se hicieron commits ni push. No se borró ningún archivo.

## Resumen
- Entorno creado, pruebas sin internet OK (13 y luego 15 líneas OK).
- Lectura en vivo de 2026-10-14 con `--union salto`: rollos B11-C8, sin ALARMA, SHA-256 IDÉNTICOS a HUELLAS_ESPERADAS.txt.
- Validación de las 6 fechas del paso 6: 6 ACIERTO, 0 FALLA.

## Paso 1 - git status --short
```
 M .gitignore
 M ESTADO_PROYECTO.md
?? REPORTE_RESPALDO_GIT_2026-10-14.md
?? config_template.py
?? db/
?? motor/
?? pruebas/
?? requirements.txt
```
Coincide exacto con lo esperado.

## Paso 2 - Entorno
Python 3.14.3; playwright 1.60.0 (instaladas también greenlet 3.5.6, pyee 13.0.1, typing-extensions 4.16.0).
Chromium de Playwright presente en %LOCALAPPDATA%\ms-playwright: chromium-1208, chromium-1223, chromium-1228, chromium_headless_shell-1208/1223/1228, ffmpeg-1011, winldd-1007.

## Paso 3 - Pruebas sin internet (primera versión, 13 pruebas)
13 líneas OK y "RESULTADO. TODO OK".
Tras la corrección de navegacion_logica.py (hecha por Claude, no por esta sesión de ejecución) se repitieron: 15 líneas OK y "RESULTADO. TODO OK" (incluye "número de página pegado a la cornisa no se lee como B111" y "entrada con salto de línea antes de la cornisa").

## Paso 4 - Credenciales
config.py copiado de config_template.py. Diego eligió la opción 4b: valores de MERCURIO_USER y MERCURIO_PASS copiados desde D:\Mercurio\config.py con un script que no imprime los valores.
Verificación: usuario cargado: sí; contraseña cargada: sí.

## Lo ocurrido en esta sesión (incidente de lectura en vivo)
1. **Cuelgue inicial.** Primera corrida `--union sin_separador` en modo oculto: más de 10 min sin salida ni carpeta capturas, proceso python con CPU casi nula. Se detuvo a mano.
2. **Corrida visible con registro.** Con `--visible` la sesión estaba activa, se listaron los cuerpos A/B/C, pero las 32 páginas fallaron con "tiempo agotado" (unos 45 s por tanda de 4 y 90 s por reintento). Terminó solo tras 3258 s (54 min), con 0 páginas leídas. Se excedió el límite de 15 min acordado: no se detuvo a tiempo.
3. **Diagnóstico de solo lectura** (`pruebas.diagnostico_sesion`): título de la página correcto, `hay_PDFViewerApplication: true`, `hay_pdfDocument: false`, textLayer null, sin modales, 14 cookies. Tres capturas de pantalla idénticas (735469 bytes). Claude las revisó.
4. **Causa: el HD.** El visor estaba en modo imagen porque el modo HD no estaba activado; sin HD no hay documento con texto. Claude actualizó motor\lector_mercurio.py para activar el HD antes de leer.
5. **Con la corrección:** "Botón HD presionado (intento 1, selector div.toolbar div.cont_activar_pdf > span:nth-of-type(1) img)", "HD activo. El visor cargó el documento", 32 páginas ok en 22 s.

## Paso 5 - Prueba de las tres formas de unión, edición 2026-10-14
Huellas esperadas (HUELLAS_ESPERADAS.txt):
- B11: 86370 caracteres, 88317 bytes, sha256 9861d3d46fc8d700991cf3d3acba14bd8feb519021cfbb89c5340715a96ff51a
- C8: 86079 caracteres, 88174 bytes, sha256 54ec1104ebd489abc9402b63feddc0a6187002e4d834c43085c507dd807cff45

| Forma | Rollos | Alarma | B11 car. | C8 car. | SHA-256 |
|---|---|---|---|---|---|
| sin_separador (5a) | B11 \| C8 (con Nota) | Sí: "C8 dice que vienen avisos de B111, pero esa página no existe en la edición" | 84134 | 83838 | NO coincide (6C9AD444...217F6D / 942DB389...DF1175) |
| espacio (5b) | B11-C8 | No | 86371 | 86080 | NO coincide (41FA6150...5596B1 / 7285F9D1...19151E) |
| salto (final) | B11-C8 | No | 86370 (88317 bytes) | 86079 (88174 bytes) | COINCIDE |

Detalle de diferencias:
- sin_separador: primer carácter distinto en la posición 31 (B11) y 2 (C8). Faltaban exactamente los 2236 y 2241 saltos de línea del banco.
- espacio: con cada \n del banco convertido en espacio el texto era idéntico; sobraba un espacio al final de cada captura (1 carácter de más).
- salto (nueva forma, por defecto: renglones unidos por salto de línea, sin separador al final): huellas idénticas.

Salida verbatim de la corrida final (`--union salto`, sin --visible, 20 s):
```
Edición 2026-10-14 leída en 20 s. Cuerpos {'A': '2026/10/14 n=8', 'B': '2026/10/14 n=12', 'C': '2026/10/14 n=12'}. Páginas leídas 32
Rollos. B11-C8
Detalle en D:\Agendar_Remates\capturas\2026-10-14\navegacion.json
```
```
9861D3D46FC8D700991CF3D3ACBA14BD8FEB519021CFBB89C5340715A96FF51A  capturas\2026-10-14\B11_B-20261014-011.txt
54EC1104EBD489ABC9402B63FEDDC0A6187002E4D834C43085C507DD807CFF45  capturas\2026-10-14\C08_L64MFDBT.txt
```
Resultado de huellas: COINCIDEN ambas.

## Paso 6 - Validación de navegación (`--union salto`)

| Fecha | Esperado | Obtenido | Tiempo | Resultado |
|---|---|---|---|---|
| 2026-10-13 | B8-B9-B10, sin ALARMA | B8-B9-B10, sin ALARMA | 21 s | ACIERTO |
| 2026-10-11 | F7-F8-F9-F10-F11-F12-F13-F14-F15, sin ALARMA | F7-F8-F9-F10-F11-F12-F13-F14-F15, sin ALARMA | 43 s | ACIERTO |
| 2026-10-10 | D5-D6-D7-D8-D9-D10-D11-D12, sin ALARMA | D5-D6-D7-D8-D9-D10-D11-D12, sin ALARMA | 24 s | ACIERTO |
| 2026-10-09 | B11-B12-B13 \| G5-G6-G7-G8-G9-G10-G11-G12, sin ALARMA, con Nota de más de un bloque | igual, con la Nota, sin ALARMA | 26 s | ACIERTO |
| 2026-10-06 | B7-B8-B9-B10, sin ALARMA | B7-B8-B9-B10, sin ALARMA | 20 s | ACIERTO |
| 2026-09-01 | B15-C8, sin ALARMA | B15-C8, sin ALARMA | 24 s | ACIERTO |

Salida verbatim:
```
2026-10-13: Edición 2026-10-13 leída en 21 s. Cuerpos {'A': '2026/10/13 n=8', 'B': '2026/10/13 n=10', 'C': '2026/10/13 n=10'}. Páginas leídas 28
Rollos. B8-B9-B10

2026-10-11: Edición 2026-10-11 leída en 43 s. Cuerpos {'A': '2026/10/11 n=26', 'B': '2026/10/11 n=16', 'C': '2026/10/11 n=16', 'E': '2026/10/11 n=6', 'F': '2026/10/11 n=16', 'R': '2026/10/11 n=10'}. Páginas leídas 90
Rollos. F7-F8-F9-F10-F11-F12-F13-F14-F15

2026-10-10: Edición 2026-10-10 leída en 24 s. Cuerpos {'A': '2026/10/10 n=12', 'B': '2026/10/10 n=8', 'C': '2026/10/10 n=16', 'D': '2026/10/10 n=12'}. Páginas leídas 48
Rollos. D5-D6-D7-D8-D9-D10-D11-D12

2026-10-09: Edición 2026-10-09 leída en 26 s. Cuerpos {'A': '2026/10/09 n=10', 'B': '2026/10/09 n=14', 'C': '2026/10/09 n=14', 'G': '2026/10/09 n=12'}. Páginas leídas 50
Rollos. B11-B12-B13 | G5-G6-G7-G8-G9-G10-G11-G12
Nota. Hay más de un bloque de remates (B11-B12-B13 | G5-G6-G7-G8-G9-G10-G11-G12). Puede ser un cuerpo reimpreso, como B y G los viernes. Se leen todos y se unen sin duplicar por rol.

2026-10-06: Edición 2026-10-06 leída en 20 s. Cuerpos {'A': '2026/10/06 n=8', 'B': '2026/10/06 n=10', 'C': '2026/10/06 n=10'}. Páginas leídas 28
Rollos. B7-B8-B9-B10

2026-09-01: Edición 2026-09-01 leída en 24 s. Cuerpos {'A': '2026/09/01 n=10', 'B': '2026/09/01 n=16', 'C': '2026/09/01 n=12'}. Páginas leídas 38
Rollos. B15-C8
```
(La línea "Detalle en ...\navegacion.json" de cada corrida se omite aquí por brevedad. Las líneas de progreso con hora se guardaron en logs\lectura_2026-10-14.log, ignorado por git.)

## Paso 7 - git status --short
```
 M .gitignore
 M ESTADO_PROYECTO.md
?? REPORTE_RESPALDO_GIT_2026-10-14.md
?? config_template.py
?? db/
?? motor/
?? pruebas/
?? requirements.txt
```
capturas/, perfil_navegador/, config.py, .venv/ y logs/ NO aparecen; `git check-ignore -v` confirma que están ignorados por .gitignore (líneas 8, 11, 9, 6 y 10).

## Pendientes / observaciones
- motor/, pruebas/, db/, requirements.txt y config_template.py siguen sin seguimiento en git (sin commit, como se pidió).
- Las líneas del Paso 5 con sin_separador y espacio quedaron superadas por la forma salto; capturas\2026-10-14 contiene la forma salto.
- Este reporte no fue incluido en ningún commit.

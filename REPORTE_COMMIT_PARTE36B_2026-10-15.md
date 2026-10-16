# Reporte commits parte 3.6b — 2026-10-15 (ejecutado el 2026-10-16)

## Paso 1. git status --short (antes de los commits)
```
 M BITACORA_2026-10-15.md
 M BITACORA_TRASPASO_MERCURIO.md
 M ESTADO_PROYECTO.md
 M banco_pruebas/2026-10-06/banco_validacion_2026-10-06.json
 M banco_pruebas/2026-10-06/muestra_validacion.json
 M motor/cortador.py
 M pruebas/medir_extraccion.py
 M pruebas/test_banco_validacion.py
 M pruebas/test_cortador.py
?? REPORTE_COMMIT_PARTE36_2026-10-15.md
?? banco_pruebas/2026-10-14/REVISION_DIEGO_nivel2_2026-10-14.xlsx
?? banco_pruebas/fotos_cortador/ (5 json)
?? pruebas/foto_cortador.py
?? "qu\303\251 usa IA.png"
```
Coincide con lo esperado. Último commit previo: 457051a.

## Paso 2. Pruebas (última línea)
- test_navegacion_logica: RESULTADO. TODO OK
- test_cortador: RESULTADO. TODO OK
- test_banco_nivel2: RESULTADO. TODO OK
- test_banco_validacion: RESULTADO. TODO OK
- test_esquema: RESULTADO. TODO OK
- test_carga_banco: RESULTADO. TODO OK
- test_vistas: RESULTADO. TODO OK
- test_extraccion: RESULTADO. TODO OK

### medir_extraccion 14
```
Banco 2026-10-14, 61 avisos
fecha_remate aciertos  60 | vacíos   1 | EQUIVOCADOS   0
hora_remate  aciertos  60 | vacíos   1 | EQUIVOCADOS   0
minimo       aciertos  61 | vacíos   0 | EQUIVOCADOS   0
garantia     aciertos  61 | vacíos   0 | EQUIVOCADOS   0
modalidad    aciertos  59 | vacíos   2 | EQUIVOCADOS   0
tribunal     aciertos  61 | vacíos   0 | EQUIVOCADOS   0
VACIO      fecha_remate aviso  55 esperado 2026-11-18 obtenido None
VACIO      hora_remate  aviso  55 esperado 12:00 obtenido None
VACIO      modalidad    aviso  55 esperado presencial obtenido None
VACIO      modalidad    aviso  61 esperado presencial obtenido None
```
(Las líneas VACIO traen además el detalle de alertas; se resumen aquí.)

### medir_extraccion 06
```
Banco 2026-10-06, 62 avisos
fecha_remate aciertos  61 | vacíos   1 | EQUIVOCADOS   0
hora_remate  aciertos  61 | vacíos   1 | EQUIVOCADOS   0
minimo       aciertos  61 | vacíos   0 | EQUIVOCADOS   1
garantia     aciertos  58 | vacíos   0 | EQUIVOCADOS   0
modalidad    aciertos  61 | vacíos   1 | EQUIVOCADOS   0
tribunal     aciertos  62 | vacíos   0 | EQUIVOCADOS   0
garantía no anotada (no se cuenta) en 4 avisos
VACIO      modalidad    aviso   4 esperado presencial obtenido None
EQUIVOCADO minimo       aviso  26 esperado [(1742.2482, 'UF', 2097500)] obtenido [(1742.2482, 'UF', None)]
VACIO      fecha_remate aviso 102 esperado 2026-10-20 obtenido None
VACIO      hora_remate  aviso 102 esperado 13:00 obtenido None
```

### foto_cortador comparar 0_antes 4_final (líneas ===)
```
=== 2026-09-01. 78 a 79 avisos. Cambian 1 de antes por 2 de después
=== 2026-10-06. 107 a 110 avisos. Cambian 3 de antes por 6 de después
=== 2026-10-09 B. 125 a 127 avisos. Cambian 2 de antes por 4 de después
=== 2026-10-09 G. 125 a 127 avisos. Cambian 2 de antes por 4 de después
=== 2026-10-10. 128 a 128 avisos. Cambian 0 de antes por 0 de después
=== 2026-10-11. 145 a 145 avisos. Cambian 0 de antes por 0 de después
=== 2026-10-13. 66 a 67 avisos. Cambian 1 de antes por 2 de después
=== 2026-10-14. 61 a 61 avisos. Cambian 0 de antes por 0 de después
```
Después de las pruebas, git status no mostró archivos nuevos.

## Pasos 3 a 6. Commits
| Commit | Hash | Archivos |
|---|---|---|
| A, cortador 3.6b | da8fa69 | 8 (cortador.py, test_cortador.py, foto_cortador.py, 5 json de fotos_cortador) |
| B, banco de validación 06-10 | 252972d | 4 |
| C, documentos | 95788f5 | 4 (3 documentos y REPORTE_COMMIT_PARTE36) |

Búsqueda de credenciales antes de cada commit (git grep --cached -F, valores no mostrados): A 0, B 0, C 0 coincidencias.

## Estado final
git status --short:
```
?? banco_pruebas/2026-10-14/REVISION_DIEGO_nivel2_2026-10-14.xlsx
?? "qu\303\251 usa IA.png"
```
git log --oneline -6:
```
95788f5 Documentos. Cierre de la parte 3.6b (punto 45 de la bitácora del 15)
252972d Banco de validación del 06-10 renumerado tras el arreglo del cortador (60 a 62 registros, número viejo guardado, garantía de las partes nuevas sin anotar)
da8fa69 Cortador parte 3.6b. Separa EXTRACTO ANTE EL SEÑOR JUEZ, JUEZ ÁRBITRO y N° JUZGADO CIVIL sin punto antes, medido señal por señal en 8 rollos
457051a Documentos: cierre de la parte 3.6 (validación 7 de 360, arreglos, decisiones de Diego) y próximo paso
e2c681a Banco: validación de la parte 3.6 con 60 avisos al azar del 06-10 (anotados antes del código) y páginas del 13-10 como evidencia de republicaciones
b1f730f Motor parte 3.6: extracción por código de fecha, hora, mínimo, costas, garantía, modalidad y tribunal, con cita, medida contra el banco del 14-10
```

## Push
Realizado tras la respuesta exacta "apruebo push": git push origin master, resultado 457051a..95788f5 master -> master (subieron da8fa69, 252972d y 95788f5).

## Diferencias contra lo esperado
Ninguna.


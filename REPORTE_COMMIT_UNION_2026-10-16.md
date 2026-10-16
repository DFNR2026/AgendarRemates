# Reporte commits unión motor-base — 2026-10-16

## Paso 1. git status --short (antes de los commits)
```
 M BITACORA_TRASPASO_MERCURIO.md
 M ESTADO_PROYECTO.md
 M db/LEEME_BASE_DATOS.md
 M db/carga.py
?? BITACORA_2026-10-16.md
?? REPORTE_COMMIT_PARTE36B_2026-10-15.md
?? banco_pruebas/2026-10-14/REVISION_DIEGO_nivel2_2026-10-14.xlsx
?? motor/procesar_edicion.py
?? pruebas/test_procesar_edicion.py
?? "qu\303\251 usa IA.png"
```
Coincide con lo esperado. Último commit previo: 95788f5.

## Paso 2. Pruebas (última línea)
- test_navegacion_logica: RESULTADO. TODO OK
- test_cortador: RESULTADO. TODO OK
- test_banco_nivel2: RESULTADO. TODO OK
- test_banco_validacion: RESULTADO. TODO OK
- test_esquema: RESULTADO. TODO OK
- test_carga_banco: RESULTADO. TODO OK
- test_vistas: RESULTADO. TODO OK
- test_extraccion: RESULTADO. TODO OK
- test_procesar_edicion: RESULTADO. TODO OK

Salida completa de test_procesar_edicion:
```
OK    motor. 61 avisos y 65 remates {'edicion_id': 1, 'avisos': 61, 'remates': 65}
OK    mismos remates (aviso y sub_orden) en las dos bases 
OK    sin diferencias fuera de las explicadas 
OK    los 4 partidores descartados por el texto 
OK    61 bienes, igual que el banco 
OK    citas del motor con método codigo y todas encontradas en su aviso 
OK    citas del banco siguen con método ia 
OK    65 alertas de vale vista NO LEÍDO en el motor y ninguna que diga que el aviso no lo dice 
OK    el banco sigue diciendo que el aviso no lo dice (9 remates) 
OK    alertas del código guardadas con su tipo y origen codigo 
OK    garantía 20% del aviso 43 avisada 
OK    una edición con dos rollos se rechaza 

RESULTADO. TODO OK
```

## Paso 3. Cargas de prueba (carpeta temporal fuera del proyecto, ya borrada)
Carga 2026-10-13:
```
{'edicion_id': 1, 'avisos': 67, 'remates': 68}
```
Carga 2026-10-09 (error esperado, no se cargó nada):
```
ValueError: La edición 2026-10-09 tiene 2 rollos ([['B11', 'B12', 'B13'], ['G5', 'G6', 'G7', 'G8', 'G9', 'G10', 'G11', 'G12']]). Unirlos sin duplicar es un paso aparte. No se cargó nada.
```
(Salió con traceback de Python; se copia el mensaje del error.) git status no mostró archivos nuevos por pruebas ni cargas.

## Pasos 4 a 6. Commits
| Commit | Hash | Archivos |
|---|---|---|
| A, unión motor-base | bc6f6bc | 3 (db/carga.py, motor/procesar_edicion.py, pruebas/test_procesar_edicion.py) |
| B, documentos | 9a3a438 | 5 (BITACORA_2026-10-16, BITACORA_TRASPASO_MERCURIO, ESTADO_PROYECTO, db/LEEME_BASE_DATOS, REPORTE_COMMIT_PARTE36B) |

Búsqueda de credenciales antes de cada commit (git grep --cached -F, valores no mostrados): A 0, B 0 coincidencias.

## Estado final
git status --short:
```
?? banco_pruebas/2026-10-14/REVISION_DIEGO_nivel2_2026-10-14.xlsx
?? "qu\303\251 usa IA.png"
```
git log --oneline -4:
```
9a3a438 Documentos. Bitácora del 16 (unión del motor con la base, carga de prueba del 13-10) y próximo paso
bc6f6bc Unión del motor con la base. procesar_edicion carga una edición leída por el motor (citas método codigo, alertas del código con su tipo, vale vista no leído con texto propio), medida contra el banco del 14-10
95788f5 Documentos. Cierre de la parte 3.6b (punto 45 de la bitácora del 15)
252972d Banco de validación del 06-10 renumerado tras el arreglo del cortador (60 a 62 registros, número viejo guardado, garantía de las partes nuevas sin anotar)
```

## Push
Realizado tras la respuesta exacta "apruebo push": git push origin master, resultado 95788f5..9a3a438 master -> master (subieron bc6f6bc y 9a3a438).

## Diferencias contra lo esperado
Ninguna. Este reporte no se agrega a git.


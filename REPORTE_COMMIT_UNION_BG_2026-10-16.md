# Reporte commits unión de rollos B y G — 2026-10-16

## Paso 1. git status --short (antes de los commits)
Modificados: BITACORA_2026-10-16.md, BITACORA_TRASPASO_MERCURIO.md, ESTADO_PROYECTO.md, db/LEEME_BASE_DATOS.md, db/carga.py, motor/procesar_edicion.py, pruebas/test_procesar_edicion.py.
Nuevos: REPORTE_COMMIT_UNION_2026-10-16.md, 24 archivos en banco_pruebas/2026-10-09 (11 .txt, 11 .geo.json, navegacion.json, HUELLAS_ESPERADAS.txt), banco_pruebas/2026-10-14/REVISION_DIEGO_nivel2_2026-10-14.xlsx y "qu\303\251 usa IA.png".
Total 34 entradas. Coincide con lo esperado. Último commit previo: 9a3a438.

## Paso 2. Huellas SHA-256
Las 11 páginas .txt nuevas de banco_pruebas/2026-10-09 (B11, B12, B13, G05 a G12) coinciden con HUELLAS_ESPERADAS.txt: 11 de 11.
Observación: la carpeta ya tenía versionado de antes mercurio_2026-10-09_B11.txt (y su .geo.json), que no es parte de los 24 archivos nuevos y no se comparó ni se tocó.

## Paso 3. Pruebas (última línea)
- test_navegacion_logica: RESULTADO. TODO OK
- test_cortador: RESULTADO. TODO OK
- test_banco_nivel2: RESULTADO. TODO OK
- test_banco_validacion: RESULTADO. TODO OK
- test_esquema: RESULTADO. TODO OK
- test_carga_banco: RESULTADO. TODO OK
- test_vistas: RESULTADO. TODO OK
- test_extraccion: RESULTADO. TODO OK
- test_procesar_edicion: RESULTADO. TODO OK

Salida completa de test_procesar_edicion (20 líneas OK):
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
OK    09-10. 127 avisos y 128 remates (no 254) {'edicion_id': 1, 'avisos': 127, 'remates': 128}
OK    09-10. 11 páginas guardadas, las de B y las de G 
OK    09-10. alarma de resumen de la unión Cuerpo G repite al B. 127 de 127 avisos unidos por huella del texto. 7 con diferencias de espacios. 0 solo en G.
OK    09-10. remates de la unión idénticos a los del rollo B solo 
OK    09-10. alerta de rol distinto entre cuerpos en el aviso 40 (C-38622025 en B, C-3862- 2025 en G) 
OK    09-10. aviso 120 con rol y sin tribunal se guarda sin causa y con alerta (antes rompía la carga) 
OK    unir_rollos. la copia de más y el aviso solo en G se agregan al final, en orden 
OK    unir_rollos. los dos agregados llevan alerta 
OK    unir_rollos. resumen ['Cuerpo G repite al B. 2 de 4 avisos unidos por huella del texto. 1 con diferencias de espacios. 2 solo en G.']

RESULTADO. TODO OK
```

## Paso 4. Carga de prueba 2026-10-09 (carpeta temporal fuera del proyecto, ya borrada)
```
{'edicion_id': 1, 'avisos': 127, 'remates': 128}
```
git status después de pruebas y carga: 34 entradas, sin archivos nuevos.

## Pasos 5 a 8. Commits
| Commit | Hash | Archivos |
|---|---|---|
| A, unión B y G | ee2a942 | 3 (db/carga.py, motor/procesar_edicion.py, pruebas/test_procesar_edicion.py) |
| B, banco 09-10 | 67bdd10 | 24 |
| C, documentos | d283e2e | 5 (BITACORA_2026-10-16, BITACORA_TRASPASO_MERCURIO, ESTADO_PROYECTO, db/LEEME_BASE_DATOS, REPORTE_COMMIT_UNION_2026-10-16) |

Búsqueda de credenciales antes de cada commit (git grep --cached -F, valores no mostrados): A 0, B 0, C 0 coincidencias.

## Estado final
git status --short:
```
?? banco_pruebas/2026-10-14/REVISION_DIEGO_nivel2_2026-10-14.xlsx
?? "qu\303\251 usa IA.png"
```
git log --oneline -5:
```
d283e2e Documentos. Unión de rollos B y G, hallazgo del guion al final de renglón y próximo paso
67bdd10 Banco. Páginas del viernes 09-10 (cuerpos B y G) con su navegación y huellas, para probar la unión de rollos
ee2a942 Unión de los rollos B y G de los viernes sin duplicar, por huella del texto (09-10, 127 de 127), y aviso con rol sin tribunal guardado sin causa en vez de romper la carga
9a3a438 Documentos. Bitácora del 16 (unión del motor con la base, carga de prueba del 13-10) y próximo paso
bc6f6bc Unión del motor con la base. procesar_edicion carga una edición leída por el motor (citas método codigo, alertas del código con su tipo, vale vista no leído con texto propio), medida contra el banco del 14-10
```

## Push
Realizado tras la respuesta exacta "apruebo push": git push origin master, resultado 9a3a438..d283e2e master -> master (subieron ee2a942, 67bdd10 y d283e2e).

## Diferencias contra lo esperado
Ninguna. Este reporte no se agrega a git.


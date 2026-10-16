# Reporte commits guion al final de renglón — 2026-10-16

## Paso 1. git status --short (antes de los commits)
Modificados (11): BITACORA_2026-10-16.md, BITACORA_TRASPASO_MERCURIO.md, ESTADO_PROYECTO.md, PREGUNTAS_ABOGADO.md, banco_pruebas/2026-10-06/banco_validacion_2026-10-06.json, banco_pruebas/2026-10-14/banco_nivel2_2026-10-14.json, banco_pruebas/LEEME_BANCO_PRUEBAS.md, motor/cortador.py, pruebas/test_carga_banco.py, pruebas/test_cortador.py, pruebas/test_vistas.py.
Nuevos (5): REPORTE_COMMIT_UNION_BG_2026-10-16.md, banco_pruebas/fotos_cortador/5_antes_guion.json, banco_pruebas/fotos_cortador/6_despues_guion.json, banco_pruebas/2026-10-14/REVISION_DIEGO_nivel2_2026-10-14.xlsx y "qu\303\251 usa IA.png".
Total 16 entradas. Coincide con lo esperado. Último commit previo: d283e2e.

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

### medir_extraccion 14 (7 primeras líneas)
```
Banco 2026-10-14, 61 avisos
fecha_remate aciertos  60 | vacíos   1 | EQUIVOCADOS   0
hora_remate  aciertos  60 | vacíos   1 | EQUIVOCADOS   0
minimo       aciertos  61 | vacíos   0 | EQUIVOCADOS   0
garantia     aciertos  61 | vacíos   0 | EQUIVOCADOS   0
modalidad    aciertos  59 | vacíos   2 | EQUIVOCADOS   0
tribunal     aciertos  61 | vacíos   0 | EQUIVOCADOS   0
```
### medir_extraccion 06 (7 primeras líneas)
```
Banco 2026-10-06, 62 avisos
fecha_remate aciertos  61 | vacíos   1 | EQUIVOCADOS   0
hora_remate  aciertos  61 | vacíos   1 | EQUIVOCADOS   0
minimo       aciertos  61 | vacíos   0 | EQUIVOCADOS   1
garantia     aciertos  58 | vacíos   0 | EQUIVOCADOS   0
modalidad    aciertos  61 | vacíos   1 | EQUIVOCADOS   0
tribunal     aciertos  62 | vacíos   0 | EQUIVOCADOS   0
```
El único equivocado del 06 es el mínimo (el aviso 26 según la medición anterior; las 7 primeras líneas no lo nombran).

### foto_cortador comparar 5_antes_guion 6_despues_guion (líneas ===)
```
=== 2026-09-01. 79 a 79 avisos. Cambian 13 de antes por 13 de después
=== 2026-10-06. 110 a 110 avisos. Cambian 31 de antes por 31 de después
=== 2026-10-09 B. 127 a 127 avisos. Cambian 26 de antes por 26 de después
=== 2026-10-09 G. 127 a 127 avisos. Cambian 25 de antes por 25 de después
=== 2026-10-10. 128 a 128 avisos. Cambian 21 de antes por 21 de después
=== 2026-10-11. 145 a 145 avisos. Cambian 22 de antes por 22 de después
=== 2026-10-13. 67 a 67 avisos. Cambian 8 de antes por 8 de después
=== 2026-10-14. 61 a 61 avisos. Cambian 8 de antes por 8 de después
```
Después de las pruebas, git status mostró las mismas 16 entradas, sin archivos nuevos.

## Pasos 3 a 6. Commits
| Commit | Hash | Archivos |
|---|---|---|
| A, cortador | 5339191 | 4 (cortador.py, test_cortador.py, 2 json de fotos_cortador) |
| B, bancos corregidos | 0032fa3 | 4 (banco_validacion 06-10, banco_nivel2 14-10, test_carga_banco.py, test_vistas.py) |
| C, documentos | 6907224 | 6 (BITACORA_2026-10-16, BITACORA_TRASPASO_MERCURIO, ESTADO_PROYECTO, PREGUNTAS_ABOGADO, LEEME_BANCO_PRUEBAS, REPORTE_COMMIT_UNION_BG) |

Búsqueda de credenciales antes de cada commit (git grep --cached -F, valores no mostrados): A 0, B 0, C 0 coincidencias.

## Estado final
git status --short:
```
?? banco_pruebas/2026-10-14/REVISION_DIEGO_nivel2_2026-10-14.xlsx
?? "qu\303\251 usa IA.png"
```
git log --oneline -5:
```
6907224 Documentos. Arreglo del guion al final de renglón y correcciones de ejemplos falsos de rol mal impreso
0032fa3 Bancos corregidos por el guion al final de renglón (6 citas y dudas de rol falsas, con la versión anterior guardada) y pruebas ajustadas (rol mal impreso solo en el 17 del 14-10)
5339191 Cortador. Guion al final de renglón, solo se une la palabra cortada (letra + minúscula). El guion de roles y fechas se deja. Desaparecen 52 alertas falsas de rol en 7 ediciones
d283e2e Documentos. Unión de rollos B y G, hallazgo del guion al final de renglón y próximo paso
67bdd10 Banco. Páginas del viernes 09-10 (cuerpos B y G) con su navegación y huellas, para probar la unión de rollos
```

## Push
Realizado tras la respuesta exacta "apruebo push": git push origin master, resultado d283e2e..6907224 master -> master (subieron 5339191, 0032fa3 y 6907224).

## Diferencias contra lo esperado
Ninguna. Este reporte no se agrega a git.


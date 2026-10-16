# Reporte commits parte 3.6 y 3.5b — 2026-10-15

## Paso 1
git status --short: 16 líneas, idénticas a lo esperado. Último commit previo: 45d6a50.

## Paso 2. Pruebas (última línea de cada una)
- test_navegacion_logica: RESULTADO. TODO OK
- test_cortador: RESULTADO. TODO OK
- test_banco_nivel2: RESULTADO. TODO OK
- test_banco_validacion: RESULTADO. TODO OK
- test_esquema: RESULTADO. TODO OK
- test_carga_banco: RESULTADO. TODO OK
- test_vistas: RESULTADO. TODO OK
- test_extraccion: RESULTADO. TODO OK

medir_extraccion 14 (7 primeras líneas):
```
Banco 2026-10-14, 61 avisos
fecha_remate aciertos  60 | vacíos   1 | EQUIVOCADOS   0
hora_remate  aciertos  60 | vacíos   1 | EQUIVOCADOS   0
minimo       aciertos  61 | vacíos   0 | EQUIVOCADOS   0
garantia     aciertos  61 | vacíos   0 | EQUIVOCADOS   0
modalidad    aciertos  59 | vacíos   2 | EQUIVOCADOS   0
tribunal     aciertos  61 | vacíos   0 | EQUIVOCADOS   0
```
Después de las pruebas no aparecieron archivos nuevos en git status.

## Pasos 3 a 6. Commits
| Commit | Hash | Archivos |
|---|---|---|
| A, carga y descarte | af40e7e | 3 |
| B, extracción por código | b1f730f | 3 |
| C, bancos de prueba | e2c681a | 20 (2026-10-06: 12, 2026-10-13: 7, test_banco_validacion.py: 1) |
| D, documentos | 457051a | 4 |

- Huellas SHA-256: los 4 .txt de 2026-10-06 y los 3 de 2026-10-13 coinciden con su HUELLAS_ESPERADAS.txt.
- Búsqueda de credenciales (git grep --cached -F, valores no mostrados): 0 coincidencias.

## Paso 7
git status --short:
```
?? banco_pruebas/2026-10-14/REVISION_DIEGO_nivel2_2026-10-14.xlsx
?? "qu\303\251 usa IA.png"
```
git log --oneline -7:
```
457051a Documentos: cierre de la parte 3.6 (validación 7 de 360, arreglos, decisiones de Diego) y próximo paso
e2c681a Banco: validación de la parte 3.6 con 60 avisos al azar del 06-10 (anotados antes del código) y páginas del 13-10 como evidencia de republicaciones
b1f730f Motor parte 3.6: extracción por código de fecha, hora, mínimo, costas, garantía, modalidad y tribunal, con cita, medida contra el banco del 14-10
af40e7e Carga: descarte de remates de partición (juez partidor o árbitro) sin importar mayúsculas, rol sin guion como detalle menor y alerta de vale vista sin fecha
45d6a50 Documentos: cierre de la parte 3.5, bitácora de traspaso al Mercurio y pregunta 9 al abogado
34ff86c Base de datos versión 2: remates por aviso, bienes, alertas y vistas, con carga del banco y pruebas
760d8a8 Documentos: estado, bitácora y preguntas para el abogado de la tarde del 2026-10-15
```

## Paso 8. Push
Realizado tras la respuesta exacta "apruebo push": git push origin master, resultado 760d8a8..457051a master -> master; subieron 34ff86c, 45d6a50, af40e7e, b1f730f, e2c681a y 457051a.

## Diferencias contra lo esperado
Ninguna. (La salida de medir_extraccion trae 6 datos con EQUIVOCADOS 0; no incluye línea de costas, tal como lo indica el enunciado.)




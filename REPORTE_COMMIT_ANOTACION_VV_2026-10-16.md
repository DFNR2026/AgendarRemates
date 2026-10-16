# Reporte commits anotación del vale vista (parte 3.7a) — 2026-10-16

## Paso 1. git status --short (antes de los commits)
```
 M BITACORA_2026-10-16.md
 M ESTADO_PROYECTO.md
?? REPORTE_COMMIT_GUION_2026-10-16.md
?? banco_pruebas/2026-10-06/anotacion_vale_vista/armar.py
?? banco_pruebas/2026-10-06/anotacion_vale_vista/calculo.py
?? banco_pruebas/2026-10-06/anotacion_vale_vista/tanda1.py
?? banco_pruebas/2026-10-06/anotacion_vale_vista/tanda2.py
?? banco_pruebas/2026-10-06/anotacion_vale_vista/tanda3.py
?? banco_pruebas/2026-10-06/banco_vale_vista_2026-10-06.json
?? banco_pruebas/2026-10-14/REVISION_DIEGO_nivel2_2026-10-14.xlsx
?? "qu\303\251 usa IA.png"
```
Coincide con lo esperado. config.py no aparece (está en .gitignore). Último commit previo: 6907224.

## Paso 2. Huella MD5 de banco_vale_vista_2026-10-06.json
B6C1F74C30D7C6580025ED30FA0E5103. Coincide.

## Paso 3. Pruebas (última línea)
- test_navegacion_logica: RESULTADO. TODO OK
- test_cortador: RESULTADO. TODO OK
- test_banco_nivel2: RESULTADO. TODO OK
- test_esquema: RESULTADO. TODO OK
- test_carga_banco: RESULTADO. TODO OK
- test_vistas: RESULTADO. TODO OK
- test_banco_validacion: RESULTADO. TODO OK
- test_extraccion: RESULTADO. TODO OK
- test_procesar_edicion: RESULTADO. TODO OK

## Pasos 4 a 6. Commits
| Commit | Hash | Archivos |
|---|---|---|
| A, anotación del vale vista | ad1e2cc | 6 (banco_vale_vista_2026-10-06.json y armar.py, calculo.py, tanda1.py, tanda2.py, tanda3.py de anotacion_vale_vista/; sin __pycache__) |
| B, documentos | 5a48459 | 3 (BITACORA_2026-10-16.md, ESTADO_PROYECTO.md, REPORTE_COMMIT_GUION_2026-10-16.md) |
| C, requirements | 5bb64fe | 1 (requirements.txt) |

Búsqueda de credenciales antes de los commits A y B (git grep --cached -F, valores no mostrados): 0 coincidencias en cada uno. El commit C solo agrega una línea de requirements.txt.

Versión de anthropic instalada: 1.15.0. requirements.txt quedó con `playwright==1.60.0` (sin tocar) y `anthropic==1.15.0`.

## Paso 7. Prueba de la clave
Una sola llamada con la librería anthropic, modelo claude-haiku-5-5, max_tokens 20, mensaje "Responde solo con la palabra listo.":
- Modelo que respondió: claude-haiku-5-5
- Texto: Listo
- Tokens de entrada: 21. Tokens de salida: 5.
- Sin errores. La clave no se imprimió ni se guardó; el script temporal estaba en la carpeta temporal del sistema y se borró.

## Estado final
git log --oneline -5:
```
5bb64fe requirements. Librería anthropic para la parte 3.7
5a48459 Documentos. Diseño de la parte 3.7a (vale vista con Claude Haiku 5.5) y validación anotada
ad1e2cc Banco. Validación del vale vista del 6 de Octubre (62 registros) anotada antes del código de la parte 3.7a, con los scripts que calcularon las fechas
6907224 Documentos. Arreglo del guion al final de renglón y correcciones de ejemplos falsos de rol mal impreso
0032fa3 Bancos corregidos por el guion al final de renglón (6 citas y dudas de rol falsas, con la versión anterior guardada) y pruebas ajustadas (rol mal impreso solo en el 17 del 14-10)
```
git status --short:
```
?? banco_pruebas/2026-10-14/REVISION_DIEGO_nivel2_2026-10-14.xlsx
?? "qu\303\251 usa IA.png"
```
(Este reporte quedó sin agregar a git, como se pidió; en el momento de escribir esta parte aparecía además como archivo nuevo.)

## Push
No realizado. Queda pendiente de la aprobación de Diego ("apruebo push").

## Diferencias contra lo esperado
Ninguna.

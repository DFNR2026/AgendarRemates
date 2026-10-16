# Reporte commits del código del vale vista (parte 3.7a) — 2026-10-16

La validación del 6 de Octubre NO se corrió. No se modificó código. No hay push.

## Paso 1. git status --short (antes de los commits)
118 entradas, todas las esperadas:
```
 M BITACORA_2026-10-16.md
 M ESTADO_PROYECTO.md
?? REPORTE_COMMIT_ANOTACION_VV_2026-10-16.md
?? REPORTE_MEDICION_VV_AJUSTE_2026-10-16.md
?? banco_pruebas/2026-10-14/MEDICION_VV_2026-10-14_vv-1.txt
?? banco_pruebas/2026-10-14/MEDICION_VV_2026-10-14_vv-2.txt
?? banco_pruebas/2026-10-14/REVISION_DIEGO_nivel2_2026-10-14.xlsx
?? ia_respuestas/ (107 archivos .json en ia_respuestas/vale_vista/)
?? motor/vale_vista.py
?? pruebas/medir_vale_vista.py
?? pruebas/test_vale_vista.py
?? "qu\303\251 usa IA.png"
```
Último commit previo: 5bb64fe.

## Paso 2. Pruebas
- test_navegacion_logica: RESULTADO. TODO OK
- test_cortador: RESULTADO. TODO OK
- test_banco_nivel2: RESULTADO. TODO OK
- test_esquema: RESULTADO. TODO OK
- test_carga_banco: RESULTADO. TODO OK
- test_vistas: RESULTADO. TODO OK
- test_banco_validacion: RESULTADO. TODO OK
- test_extraccion: RESULTADO. TODO OK
- test_procesar_edicion: RESULTADO. TODO OK
- test_vale_vista: RESULTADO. TODO OK

## Paso 3. medir_vale_vista 14 sin --llamar (primera línea)
```
Banco 2026-10-14. Modelo claude-haiku-5-5, instrucciones vv-2. acierto 53, no_leido 4. Tokens entrada 101492, salida 17764, caché leída 289393, caché escrita 2561. Costo de las llamadas guardadas 0.0222 dólares.
```
Dice "acierto 53, no_leido 4", como se esperaba. (Es distinto del resumen de la medición anterior, acierto 43, no_leido 12, EQUIVOCADO 2: el código de motor/vale_vista.py cambió en disco entre esa medición y esta, por Claude/Diego fuera de este prompt. Este reporte solo versiona el estado actual; no lo modifiqué.)

## Paso 4. Búsqueda de credenciales (con todo lo de A, B y C agregado: 116 archivos)
- `git grep --cached -n -E "sk-ant|api_key\s*=\s*['\"]"`: 0 coincidencias.
- Además busqué con `git grep --cached -F` los valores reales de MERCURIO_USER, MERCURIO_PASS y ANTHROPIC_API_KEY de config.py (sin mostrarlos): 0 coincidencias.
- La planilla .xlsx y el .png no estaban en lo preparado.

## Pasos 5 a 7. Commits
| Commit | Hash | Archivos |
|---|---|---|
| A, código del vale vista | e328e5a | 3 (motor/vale_vista.py, pruebas/test_vale_vista.py, pruebas/medir_vale_vista.py) |
| B, respuestas guardadas y mediciones | 6188890 | 109 (107 json de ia_respuestas/vale_vista, MEDICION_VV_..._vv-1.txt, MEDICION_VV_..._vv-2.txt) |
| C, documentos | 0e0a242 | 4 (BITACORA_2026-10-16.md, ESTADO_PROYECTO.md, REPORTE_COMMIT_ANOTACION_VV_2026-10-16.md, REPORTE_MEDICION_VV_AJUSTE_2026-10-16.md) |

## Estado final
git log --oneline -6:
```
0e0a242 Documentos. Ajuste de la parte 3.7a con el 14 de Octubre
6188890 Respuestas guardadas de Haiku para el banco del 14 de Octubre (vv-1 con razonamiento como registro, vv-2 sin razonamiento) y mediciones
e328e5a Parte 3.7a. Vale vista con Claude Haiku 5.5 (sin razonamiento, doble lectura), verificador y cálculo de fechas. Ajuste con el 14 de Octubre, 53 aciertos, 4 en rojo, 0 equivocados
5bb64fe requirements. Librería anthropic para la parte 3.7
5a48459 Documentos. Diseño de la parte 3.7a (vale vista con Claude Haiku 5.5) y validación anotada
ad1e2cc Banco. Validación del vale vista del 6 de Octubre (62 registros) anotada antes del código de la parte 3.7a, con los scripts que calcularon las fechas
```
git status --short:
```
?? banco_pruebas/2026-10-14/REVISION_DIEGO_nivel2_2026-10-14.xlsx
?? "qu\303\251 usa IA.png"
```

## Push
No realizado.

## Diferencias contra lo esperado
Ninguna respecto de lo pedido. Observación: el código cambió en disco después de la medición del reporte REPORTE_MEDICION_VV_AJUSTE (ver paso 3), por lo que el commit A mide 53 aciertos y 4 en rojo, no 43 y 12. Este reporte no se agrega a git.

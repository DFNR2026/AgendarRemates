# Reporte commits rojos y --retomar — 2026-10-17

**Estado: DETENIDO. No se hizo ningún commit ni push.** Dos condiciones de parada se cumplieron (prueba 11 sin "RESULTADO. TODO OK" y archivos nuevos en ia_respuestas). Además la prueba llamó a la API de Anthropic, que el prompt prohibía.

## Paso 1. Verificación previa
- Último commit: 05fc6bf (coincide).
- Python del .venv: 3.14.3
- git status --short antes de las pruebas:
```
 M BITACORA_2026-10-16.md
 M ESTADO_PROYECTO.md
 M motor/procesar_edicion.py
 M pruebas/test_union_vale_vista.py
?? BITACORA_2026-10-17.md
?? REPORTE_COMMIT_UNION_VV_2026-10-16.md
?? REPORTE_PUSH_UNION_VV_2026-10-16.md
?? banco_pruebas/2026-10-14/REVISION_DIEGO_nivel2_2026-10-14.xlsx
?? "qu\303\251 usa IA.png"
```

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
- **test_union_vale_vista: FALLÓ.** No llegó a imprimir "RESULTADO. TODO OK". Todas las líneas "OK" que imprimió fueron correctas (la última: "decisión 8, paso 4. edición que no está en la base da error claro"), pero terminó con un error.

### Salida de la falla de test_union_vale_vista (traceback)
```
  File "D:\Agendar_Remates\pruebas\test_union_vale_vista.py", line 353, in <module>
    sal = correr("--retomar", "2026-10-09", str(ruta09))
  File "D:\Agendar_Remates\pruebas\test_union_vale_vista.py", line 352, in <lambda>
    correr = lambda *a: subprocess.run([sys.executable, "-B", "-m", "motor.procesar_edicion", *a], cwd=RAIZ, capture_output=True, text=True, timeout=170)
  ...
subprocess.TimeoutExpired: Command '[... '-m', 'motor.procesar_edicion', '--retomar', '2026-10-09', '...\\cli09.db']' timed out after 170 seconds
```
Después aparece un `PermissionError: [WinError 32]` al limpiar la carpeta temporal (cli09.db seguía en uso por el proceso que se cortó). Es consecuencia del timeout, no un error aparte. La salida completa quedó en C:\Users\ndieg\AppData\Local\Temp\claude\D--Agendar-Remates\8d8ea820-f8a6-4d6d-8c06-0fd00de64b3e\tasks\bt9e1p1wk.output.

Posible causa (no verificada): el paso `--retomar 2026-10-09` del propio test lanza `motor.procesar_edicion` como proceso aparte y ese proceso llamó de verdad a Haiku, que en esta corrida tardó más de 170 s. En la corrida anterior (el 16, con 05fc6bf) esa prueba no había quedado así.

## Paso 3. ia_respuestas
**54 archivos nuevos** en ia_respuestas\vale_vista (el prompt pedía que no aparecieran). Datos:
- Horas de escritura: 10:21:02 a 10:23:43 de hoy, o sea durante esta corrida.
- Todos son modelo claude-haiku-5-5, instrucciones vv-2.
- 108 lecturas, 89.008 tokens de entrada y 17.628 de salida (por referencia, una corrida anterior de tamaño parecido costó 0,02 dólares; el costo de esta no se calculó exactamente, es del orden de 0,02 a 0,03 dólares).
Conclusión: **la prueba test_union_vale_vista llamó a la API real de Anthropic**, contra la instrucción "NO llames a la API". Yo solo corrí la prueba como se pidió; el llamado lo hace el comando `--retomar` que la prueba ejecuta como subproceso con la clave real de config.py. No cambié nada ni borré esos archivos.

## Pasos 4 a 6. Commits
No realizados. git status final (sin cambios míos más allá de las 54 respuestas que generó la prueba):
```
 M BITACORA_2026-10-16.md
 M ESTADO_PROYECTO.md
 M motor/procesar_edicion.py
 M pruebas/test_union_vale_vista.py
?? BITACORA_2026-10-17.md
?? REPORTE_COMMIT_UNION_VV_2026-10-16.md
?? REPORTE_PUSH_UNION_VV_2026-10-16.md
?? banco_pruebas/2026-10-14/REVISION_DIEGO_nivel2_2026-10-14.xlsx
?? ia_respuestas/vale_vista/ (54 archivos .json nuevos)
?? "qu\303\251 usa IA.png"
```
git log --oneline -1 sigue en 05fc6bf. Búsqueda de claves: no realizada, porque no se llegó al commit.

## Cosas raras / decisiones que quedan para Diego
1. La prueba test_union_vale_vista no es "solo con respuestas guardadas": en el tramo de `--retomar 2026-10-09` usa la API real. Hay que decidir si se cambia la prueba para que use un cliente falso, o si se acepta ese costo y se sube el timeout de 170 s.
2. Qué hacer con las 54 respuestas nuevas de vv-2 (son datos reales de Haiku del 09-10: se pueden versionar como las anteriores o borrar). No las toqué.
3. Reintentar la prueba después puede volver a llamar a la API (aunque ahora 54 avisos ya tienen respuesta guardada, así que costaría menos).

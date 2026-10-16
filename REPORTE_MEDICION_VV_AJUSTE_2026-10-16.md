# Reporte medición del vale vista contra el banco de ajuste 14-10 — 2026-10-16

**Estado: la medición NO es válida. Me detuve en el paso 2 por un error en las lecturas de la IA. No corrí el paso 3. No se modificó ningún archivo de código, no se hizo commit ni push.**

## Paso 1. Pruebas (última línea)
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

## Paso 2. medir_vale_vista 14 --llamar
Primera línea del resumen:
```
Banco 2026-10-14. Modelo claude-haiku-5-5, instrucciones vv-1. acierto 13, no_leido 44. Tokens entrada 101492, salida 51968, caché leída 289506, caché escrita 2562. Costo de las llamadas guardadas 0.0393 dólares.
```
Costo de las llamadas: 0,0393 dólares (menor al tope esperado de 0,10).

### Error encontrado
Las lecturas de la IA fallan en casi todos los avisos con el mismo error de Python (no es un error de la API; las llamadas a Haiku sí se hicieron y se cobraron):
```
AttributeError: 'ThinkingBlock' object has no attribute 'text'
```
- Aparece en 50 líneas de avisos del resumen, dos veces por aviso (las dos lecturas), por eso el resumen dice "Falta la segunda lectura de la IA" y casi todo queda como "no_leido" (44 de 57) o "acierto" sin dato.
- Causa probable (solo lectura, sin tocar el código): motor/vale_vista.py línea 353 hace `json.loads(resp.content[0].text)`. Con Haiku 5.5 la respuesta trae primero un bloque de razonamiento (`ThinkingBlock`) y el texto viene en un bloque posterior. Habría que buscar el primer bloque de tipo `text` en vez de tomar `content[0]`, o desactivar el razonamiento en la llamada.
- Los resultados de esta corrida (acierto 13, no_leido 44) no sirven para juzgar a Haiku. Hay que corregir el código y repetir la medición.

### Archivos en ia_respuestas\vale_vista
7 archivos .json (las respuestas que sí se pudieron guardar; no 114).

## Paso 3. medir_vale_vista 14 sin --llamar
No realizado, porque el paso 2 no terminó bien.

## Paso 4. MEDICION_VV_2026-10-14_vv-1.txt
El archivo lo escribió esta misma corrida fallida (12:02:35), por lo que refleja los errores de arriba y no una medición real. Su primera línea es la misma del resumen del paso 2. Está sin versionar en banco_pruebas\2026-10-14\ y se puede leer completo ahí; no lo copio entero aquí para no dar por buena una medición inválida.

## git status --short (al terminar)
Sin cambios en archivos versionados. Siguen sin registrar: REPORTE_COMMIT_ANOTACION_VV_2026-10-16.md, MEDICION_VV_2026-10-14_vv-1.txt, motor/vale_vista.py, pruebas/medir_vale_vista.py, pruebas/test_vale_vista.py, la planilla v1 y "qué usa IA.png". Además puede aparecer ia_respuestas\vale_vista si no está en .gitignore (no verificado).

## Diferencias contra lo esperado
- Error `ThinkingBlock` descrito arriba (la medición no es utilizable).
- Solo 7 archivos guardados en ia_respuestas\vale_vista en vez de unos 114.

---

# Segunda corrida, después de corregir la lectura del bloque de texto

**Cambio hecho (única modificación de código):** en motor/vale_vista.py, línea 353, la respuesta ahora se lee del primer bloque de tipo `text` (se ignora `ThinkingBlock`) en vez de `resp.content[0]`. Sin commit ni push.

- test_vale_vista: RESULTADO. TODO OK
- medir_vale_vista 14 --llamar (primera línea):
```
Banco 2026-10-14. Modelo claude-haiku-5-5, instrucciones vv-1. acierto 41, no_leido 16. Tokens entrada 101492, salida 51978, caché leída 286944, caché escrita 5124. Costo de las llamadas guardadas 0.0396 dólares.
```
- medir_vale_vista 14 sin --llamar (primera línea, con lo guardado):
```
Banco 2026-10-14. Modelo claude-haiku-5-5, instrucciones vv-1. acierto 40, no_leido 10, sin_respuesta 7. Tokens entrada 82654, salida 41335, caché leída 251076, caché escrita 5124. Costo de las llamadas guardadas 0.0321 dólares.
```
- Archivos en ia_respuestas\vale_vista: 50 de 57 avisos.

## Pendiente: 7 avisos sin respuesta completa (9, 11, 12, 17, 21, 37, 48)
Errores restantes, ya distintos del anterior:
- `StopIteration` (avisos 9 y 17): la respuesta no trajo ningún bloque de texto.
- `JSONDecodeError: Unterminated string` o `Expecting ',' delimiter` (avisos 11, 12, 21, 37, 48): el JSON llegó cortado.
Causa probable: la llamada usa `max_tokens=800` y el razonamiento de Haiku consume parte de ese margen, así que en esos avisos la respuesta se corta o ni llega al texto. No lo toqué porque pediste solo el arreglo del bloque de texto. Opciones: subir `max_tokens` (por ejemplo a 2000) o desactivar el razonamiento en la llamada.

Por eso la cifra de la segunda corrida (acierto 41, no_leido 16 con --llamar; 40 / 10 / sin_respuesta 7 con lo guardado) todavía no es una medición completa. Las dos líneas difieren porque la segunda cuenta como "sin_respuesta" los 7 avisos que no tienen las dos lecturas guardadas.

## git status al terminar
Sin archivos versionados modificados (motor/vale_vista.py, pruebas/medir_vale_vista.py y pruebas/test_vale_vista.py siguen sin registrar). Aparece además ia_respuestas/ como carpeta nueva sin registrar: no está en .gitignore, hay que decidir si se versiona o se ignora antes del próximo commit.

---

# vv-2 sin razonamiento

Cambios hechos en motor/vale_vista.py (nada más; la lectura del primer bloque de tipo text se mantiene del arreglo anterior; max_tokens sigue en 800). Sin commit ni push. El archivo no está versionado, así que el diff se hizo contra una copia guardada justo antes de estos dos cambios:
```diff
diff --git "a/C:\\Users\\ndieg\\AppData\\Local\\Temp\\vale_vista_antes.py" "b/motor\\vale_vista.py"
index b43afa0..f066e7e 100644
--- "a/C:\\Users\\ndieg\\AppData\\Local\\Temp\\vale_vista_antes.py"
+++ "b/motor\\vale_vista.py"
@@ -15,7 +15,7 @@ from pathlib import Path
 
 RAIZ = Path(__file__).resolve().parent.parent
 MODELO = "claude-haiku-5-5"
-VERSION_INSTRUCCIONES = "vv-1"
+VERSION_INSTRUCCIONES = "vv-2"
 CARPETA_RESPUESTAS = RAIZ / "ia_respuestas" / "vale_vista"
 HORA_CIERRE_SUPUESTA = "14:00"          # pregunta 3 al abogado
 NO_ENCONTRADA = "La IA no encontró la regla del vale vista. Revísala en el aviso."
@@ -342,7 +342,7 @@ def leer_con_ia(texto: str, cliente=None, lecturas: int = 2) -> dict:
     for _ in range(lecturas):
         try:
             resp = cliente.messages.create(
-                model=MODELO, max_tokens=800,
+                model=MODELO, max_tokens=800, thinking={"type": "disabled"},
                 system=[{"type": "text", "text": INSTRUCCIONES, "cache_control": {"type": "ephemeral"}}],
                 messages=[{"role": "user", "content": "AVISO\n" + texto}],
                 output_config={"format": {"type": "json_schema", "schema": ESQUEMA}})

```

- test_vale_vista: RESULTADO. TODO OK
- La API aceptó `thinking={"type": "disabled"}`: 0 errores en las llamadas.

## Paso 4. medir_vale_vista 14 --llamar (primera línea)
```
Banco 2026-10-14. Modelo claude-haiku-5-5, instrucciones vv-2. EQUIVOCADO 2, acierto 43, no_leido 12. Tokens entrada 101492, salida 17764, caché leída 289393, caché escrita 2561. Costo de las llamadas guardadas 0.0222 dólares.
```
## Paso 5. medir_vale_vista 14 sin --llamar (primera línea)
```
Banco 2026-10-14. Modelo claude-haiku-5-5, instrucciones vv-2. EQUIVOCADO 2, acierto 43, no_leido 12. Tokens entrada 101492, salida 17764, caché leída 289393, caché escrita 2561. Costo de las llamadas guardadas 0.0222 dólares.
```
Es idéntica a la del paso 4. Archivos en ia_respuestas\vale_vista: 107 (50 de vv-1 más 57 de vv-2; las de vv-1 quedan como registro).

Resultado: EQUIVOCADO 2, acierto 43, no_leido 12, sin errores de lectura. Costo de las llamadas: 0,0222 dólares. Los 2 equivocados están en el detalle de abajo.

## Contenido completo de MEDICION_VV_2026-10-14_vv-2.txt
```
Banco 2026-10-14. Modelo claude-haiku-5-5, instrucciones vv-2. EQUIVOCADO 2, acierto 43, no_leido 12. Tokens entrada 101492, salida 17764, caché leída 289393, caché escrita 2561. Costo de las llamadas guardadas 0.0222 dólares.

  1 acierto      programa verde    dias_habiles_antes 2026-10-15 -> 2026-11-05 14:00  | anotado verde 2026-10-15 -> 2026-11-05 14:00
  2 no_leido     programa rojo     dia_anterior None -> None  | anotado verde 2026-10-15 -> 2026-11-04 14:00 | Las dos lecturas de la IA no coinciden.
  3 acierto      programa verde    dias_habiles_antes 2026-11-11 08:00 -> 2026-11-11 14:00  | anotado verde 2026-11-11 08:00 -> 2026-11-11 14:00
  4 no_leido     programa rojo     horas_antes None -> None  | anotado ambar 2026-10-15 -> 2026-10-30 14:00 | El aviso da dos plazos u horarios distintos para la entrega.
  5 no_leido     programa rojo     dias_habiles_antes None -> None  | anotado verde 2026-10-15 -> 2026-11-02 14:00 | Las dos lecturas de la IA no coinciden.
  6 acierto      programa verde    dias_habiles_antes 2026-10-15 -> 2026-11-02 14:00  | anotado verde 2026-10-15 -> 2026-11-02 14:00
  7 acierto      programa verde    dias_habiles_antes 2026-11-02 12:00 -> 2026-11-02 14:00  | anotado verde 2026-11-02 12:00 -> 2026-11-02 14:00
  8 acierto      programa verde    dias_habiles_antes 2026-10-28 12:00 -> 2026-10-28 14:00  | anotado verde 2026-10-28 12:00 -> 2026-10-28 14:00
  9 acierto      programa rojo     dias_habiles_antes None -> None  | anotado rojo None -> None | El aviso da dos plazos u horarios distintos para la entrega.
 10 no_leido     programa rojo     dias_habiles_antes None -> None  | anotado verde 2026-10-15 -> 2026-11-10 13:00 | Las dos lecturas de la IA no coinciden.
 11 no_leido     programa rojo     dias_habiles_antes None -> None  | anotado verde 2026-10-15 -> 2026-11-03 13:00 | El aviso da dos plazos u horarios distintos para la entrega.
 12 acierto      programa verde    horas_antes 2026-10-15 -> 2026-11-09 13:00  | anotado verde 2026-10-15 -> 2026-11-09 13:00
 13 no_leido     programa rojo     dias_habiles_antes None -> None  | anotado verde 2026-10-15 -> 2026-11-16 13:00 | El aviso da dos plazos u horarios distintos para la entrega.; La frase de la regla no está en el aviso.
 14 no_leido     programa rojo     dias_habiles_antes None -> None  | anotado verde 2026-10-15 -> 2026-11-02 13:00 | Las dos lecturas de la IA no coinciden.
 15 no_leido     programa rojo     dias_habiles_antes None -> None  | anotado verde 2026-10-15 -> 2026-11-02 14:00 | Las dos lecturas de la IA no coinciden.
 16 no_leido     programa rojo     dias_habiles_antes None -> None  | anotado verde 2026-10-28 08:30 -> 2026-10-28 12:30 | El aviso da dos plazos u horarios distintos para la entrega.
 17 acierto      programa verde    dias_habiles_antes 2026-11-10 08:30 -> 2026-11-10 12:30  | anotado verde 2026-11-10 08:30 -> 2026-11-10 12:30
 18 acierto      programa verde    dia_anterior_sabado_a_viernes 2026-11-10 12:00 -> 2026-11-10 14:00  | anotado verde 2026-11-10 12:00 -> 2026-11-10 14:00
 19 acierto      programa ambar    dia_anterior_sabado_a_viernes 2026-11-06 12:00 -> 2026-11-06 14:00 [2] | anotado ambar 2026-11-06 12:00 -> 2026-11-06 14:00
 20 acierto      programa verde    dia_anterior_sabado_a_viernes 2026-10-29 12:00 -> 2026-10-29 14:00  | anotado verde 2026-10-29 12:00 -> 2026-10-29 14:00
 21 acierto      programa ambar    dia_anterior_sabado_a_habil 2026-11-13 12:00 -> 2026-11-13 14:00 [2] | anotado ambar 2026-11-13 12:00 -> 2026-11-13 14:00
 22 acierto      programa ambar    dia_anterior_sabado_a_habil 2026-11-06 12:00 -> 2026-11-06 14:00 [2] | anotado ambar 2026-11-06 12:00 -> 2026-11-06 14:00
 23 acierto      programa ambar    dia_anterior_sabado_a_habil 2026-11-06 12:00 -> 2026-11-06 14:00 [2] | anotado ambar 2026-11-06 12:00 -> 2026-11-06 14:00
 24 acierto      programa verde    dias_habiles_antes 2026-11-06 09:00 -> 2026-11-06 14:00  | anotado verde 2026-11-06 09:00 -> 2026-11-06 14:00
 25 acierto      programa verde    dia_anterior 2026-10-26 08:30 -> 2026-10-26 09:30  | anotado verde 2026-10-26 08:30 -> 2026-10-26 09:30
 26 acierto      programa verde    dia_anterior 2026-11-03 08:30 -> 2026-11-03 09:30  | anotado verde 2026-11-03 08:30 -> 2026-11-03 09:30
 27 EQUIVOCADO   programa verde    en_el_remate 2026-10-29 13:00 -> 2026-10-29 13:00  | anotado sin_dato None -> None
 28 EQUIVOCADO   programa verde    en_el_remate 2026-10-29 13:00 -> 2026-10-29 13:00  | anotado sin_dato None -> None
 29 acierto      programa verde    en_el_remate 2026-11-04 13:00 -> 2026-11-04 13:00  | anotado verde 2026-11-04 13:00 -> 2026-11-04 13:00
 30 acierto      programa verde    dia_anterior 2026-10-19 09:00 -> 2026-10-19 13:00  | anotado verde 2026-10-19 09:00 -> 2026-10-19 13:00
 31 acierto      programa verde    dia_anterior 2026-11-25 09:00 -> 2026-11-25 13:00  | anotado verde 2026-11-25 09:00 -> 2026-11-25 13:00
 32 acierto      programa verde    dia_anterior 2026-10-28 09:00 -> 2026-10-28 13:00  | anotado verde 2026-10-28 09:00 -> 2026-10-28 13:00
 33 acierto      programa sin_dato sin_dato None -> None  | anotado sin_dato None -> None
 34 no_leido     programa rojo     dia_anterior_sabado_a_viernes None -> None  | anotado verde 2026-10-23 12:00 -> 2026-10-23 13:00 | Las dos lecturas de la IA no coinciden.
 35 acierto      programa verde    dia_anterior 2026-10-28 11:00 -> 2026-10-28 12:00  | anotado verde 2026-10-28 11:00 -> 2026-10-28 12:00
 36 acierto      programa verde    dia_anterior 2026-11-04 11:00 -> 2026-11-04 12:00  | anotado verde 2026-11-04 11:00 -> 2026-11-04 12:00
 37 no_leido     programa rojo     dias_habiles_antes None -> None  | anotado verde 2026-10-15 -> 2026-11-09 13:00 | La frase no trae las palabras propias de la regla dias_habiles_antes.
 38 acierto      programa verde    dia_anterior 2026-10-15 -> 2026-11-02 13:00  | anotado verde 2026-10-15 -> 2026-11-02 13:00
 39 acierto      programa verde    dia_anterior 2026-10-15 -> 2026-11-02 13:00  | anotado verde 2026-10-15 -> 2026-11-02 13:00
 40 acierto      programa ambar    dias_habiles_antes 2026-10-15 -> 2026-11-11 [4] | anotado ambar 2026-10-15 -> 2026-11-11
 41 acierto      programa ambar    dias_habiles_antes 2026-10-15 -> 2026-11-04 [4] | anotado ambar 2026-10-15 -> 2026-11-04
 42 acierto      programa ambar    dias_habiles_antes 2026-10-15 -> 2026-11-02 [4] | anotado ambar 2026-10-15 -> 2026-11-02
 43 no_leido     programa rojo     martes_o_jueves_anterior None -> None  | anotado ambar 2026-10-29 10:00 -> 2026-10-29 12:00 | Las dos lecturas de la IA no coinciden.
 44 acierto      programa verde    dia_anterior 2026-10-28 10:00 -> 2026-10-28 12:00  | anotado verde 2026-10-28 10:00 -> 2026-10-28 12:00
 45 acierto      programa verde    dia_anterior 2026-11-04 09:00 -> 2026-11-04 12:00  | anotado verde 2026-11-04 09:00 -> 2026-11-04 12:00
 46 acierto      programa ambar    dia_anterior 2026-10-30 09:00 -> 2026-10-30 12:00 [2] | anotado ambar 2026-10-30 09:00 -> 2026-10-30 12:00
 47 acierto      programa verde    dia_anterior 2026-11-10 09:00 -> 2026-11-10 12:00  | anotado verde 2026-11-10 09:00 -> 2026-11-10 12:00
 48 acierto      programa verde    dias_habiles_antes 2026-10-15 -> 2026-10-28 12:00  | anotado verde 2026-10-15 -> 2026-10-28 12:00
 49 acierto      programa verde    dias_habiles_antes 2026-10-15 -> 2026-10-30 12:00  | anotado verde 2026-10-15 -> 2026-10-30 12:00
 50 acierto      programa sin_dato sin_dato None -> None  | anotado sin_dato None -> None
 51 acierto      programa verde    horas_antes 2026-10-15 -> 2026-10-26 13:00  | anotado verde 2026-10-15 -> 2026-10-26 13:00
 52 acierto      programa verde    horas_antes 2026-10-15 -> 2026-11-04 12:30  | anotado verde 2026-10-15 -> 2026-11-04 12:30
 53 acierto      programa verde    horas_antes 2026-10-15 -> 2026-11-02 12:30  | anotado verde 2026-10-15 -> 2026-11-02 12:30
 54 acierto      programa verde    horas_antes 2026-10-15 -> 2026-11-23 13:30  | anotado verde 2026-10-15 -> 2026-11-23 13:30
 56 acierto      programa verde    dias_habiles_antes 2026-10-15 -> 2026-11-04  | anotado verde 2026-10-15 -> 2026-11-04
 59 acierto      programa sin_dato sin_dato None -> None  | anotado sin_dato None -> None
 61 acierto      programa rojo     en_el_remate None -> None  | anotado sin_dato None -> None | La frase no trae las palabras propias de la regla en_el_remate.

```

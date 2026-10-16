# Reporte validación del vale vista contra el 6 de Octubre (parte 3.7a) — 2026-10-16

Una sola corrida con el código congelado. Resultado crudo, sin interpretar. No se modificó código. No hay push.

## Paso 1
- git log --oneline -1: 0e0a242 Documentos. Ajuste de la parte 3.7a con el 14 de Octubre
- git status --short: solo REPORTE_COMMIT_CODIGO_VV_2026-10-16.md, la planilla REVISION_DIEGO_nivel2_2026-10-14.xlsx y "qu\303\251 usa IA.png" sin registrar.
- MD5 de motor\vale_vista.py: D534FE5A46536B3CAAEEF380767F0E70 (coincide).

## Paso 2
test_vale_vista: RESULTADO. TODO OK

## Paso 3. medir_vale_vista 06 --llamar (primera línea)
```
Banco 2026-10-06. Modelo claude-haiku-5-5, instrucciones vv-2. EQUIVOCADO 1, acierto 44, no_leido 14. Tokens entrada 120976, salida 20033, caché leída 299637, caché escrita 2561. Costo de las llamadas guardadas 0.0254 dólares.
```
Sin errores de la API.

## Paso 4. medir_vale_vista 06 sin --llamar (primera línea)
```
Banco 2026-10-06. Modelo claude-haiku-5-5, instrucciones vv-2. EQUIVOCADO 1, acierto 44, no_leido 14. Tokens entrada 120976, salida 20033, caché leída 299637, caché escrita 2561. Costo de las llamadas guardadas 0.0254 dólares.
```
Idéntica a la del paso 3.

## Paso 5. Credenciales
git grep --cached -n -E "sk-ant|api_key\s*=\s*['\"]" sobre los 60 archivos preparados: 0 coincidencias.

## Paso 6. Commit D
- Hash: 145b481
- Archivos: 60 (59 nuevos en ia_respuestas/vale_vista, que pasó de 107 a 166 archivos, y banco_pruebas/2026-10-06/MEDICION_VV_2026-10-06_vv-2.txt)
- Mensaje: "Validación de la parte 3.7a contra el 6 de Octubre (resultado crudo, una sola corrida, código e328e5a)" con la primera línea del resumen en el cuerpo.

## Estado final
git status --short: REPORTE_COMMIT_CODIGO_VV_2026-10-16.md, la planilla v1 y "qu\303\251 usa IA.png" sin registrar (este reporte también).

## Contenido completo de MEDICION_VV_2026-10-06_vv-2.txt
```
Banco 2026-10-06. Modelo claude-haiku-5-5, instrucciones vv-2. EQUIVOCADO 1, acierto 44, no_leido 14. Tokens entrada 120976, salida 20033, caché leída 299637, caché escrita 2561. Costo de las llamadas guardadas 0.0254 dólares.

  1 no_leido     programa rojo     horas_antes None -> None  | anotado verde 2026-10-07 -> 2026-12-01 12:00 | La frase no trae las palabras propias de la regla horas_antes.
  2 acierto      programa sin_dato sin_dato None -> None  | anotado sin_dato None -> None
  3 acierto      programa verde    dias_habiles_antes 2026-10-07 -> 2026-10-28 14:00  | anotado verde 2026-10-07 -> 2026-10-28 14:00
  4 acierto      programa sin_dato sin_dato None -> None  | anotado sin_dato None -> None
  5 acierto      programa verde    horas_antes 2026-10-07 -> 2026-10-19 12:00  | anotado verde 2026-10-07 -> 2026-10-19 12:00
  6 acierto      programa verde    en_el_remate 2026-11-05 13:00 -> 2026-11-05 13:00  | anotado verde 2026-11-05 13:00 -> 2026-11-05 13:00
  8 acierto      programa verde    dias_habiles_antes 2026-10-07 -> 2026-10-26 14:00  | anotado verde 2026-10-07 -> 2026-10-26 14:00
  9 acierto      programa ambar    horas_antes 2026-10-07 -> 2026-10-16 14:00 [3] | anotado ambar 2026-10-07 -> 2026-10-16 14:00
 12 acierto      programa verde    dias_habiles_antes 2026-10-27 12:00 -> 2026-10-27 14:00  | anotado verde 2026-10-27 12:00 -> 2026-10-27 14:00
 13 acierto      programa verde    dias_habiles_antes 2026-10-21 12:00 -> 2026-10-21 14:00  | anotado verde 2026-10-21 12:00 -> 2026-10-21 14:00
 14 acierto      programa verde    dias_habiles_antes 2026-10-21 12:00 -> 2026-10-21 14:00  | anotado verde 2026-10-21 12:00 -> 2026-10-21 14:00
 22 acierto      programa verde    dias_habiles_antes 2026-10-07 -> 2026-11-02 13:00  | anotado verde 2026-10-07 -> 2026-11-02 13:00
 23 acierto      programa verde    dias_habiles_antes 2026-10-07 -> 2026-11-03 13:00  | anotado verde 2026-10-07 -> 2026-11-03 13:00
 24 acierto      programa verde    dias_habiles_antes 2026-10-07 -> 2026-10-21 14:00  | anotado verde 2026-10-07 -> 2026-10-21 14:00
 25 acierto      programa verde    dias_habiles_antes 2026-10-07 -> 2026-10-14 14:00  | anotado verde 2026-10-07 -> 2026-10-14 14:00
 26 acierto      programa ambar    dia_anterior 2026-11-20 12:00 -> 2026-11-20 14:00 [2] | anotado ambar 2026-11-20 12:00 -> 2026-11-20 14:00
 28 acierto      programa ambar    dia_anterior_sabado_a_habil 2026-10-16 12:00 -> 2026-10-16 14:00 [2] | anotado ambar 2026-10-16 12:00 -> 2026-10-16 14:00
 29 acierto      programa ambar    dia_anterior_sabado_a_habil 2026-10-16 12:00 -> 2026-10-16 14:00 [2] | anotado ambar 2026-10-16 12:00 -> 2026-10-16 14:00
 30 acierto      programa verde    dia_anterior_sabado_a_viernes 2026-10-20 12:00 -> 2026-10-20 14:00  | anotado verde 2026-10-20 12:00 -> 2026-10-20 14:00
 31 acierto      programa verde    dia_anterior_sabado_a_viernes 2026-10-22 12:00 -> 2026-10-22 14:00  | anotado verde 2026-10-22 12:00 -> 2026-10-22 14:00
 35 acierto      programa verde    dia_anterior_sabado_a_viernes 2026-10-27 12:00 -> 2026-10-27 14:00  | anotado verde 2026-10-27 12:00 -> 2026-10-27 14:00
 36 acierto      programa verde    dias_habiles_antes 2026-10-23 09:00 -> 2026-10-23 14:00  | anotado verde 2026-10-23 09:00 -> 2026-10-23 14:00
 45 acierto      programa rojo     dia_anterior None -> None  | anotado rojo None -> None | La fecha del remate es anterior a la edición.
 47 no_leido     programa rojo     martes_o_jueves_anterior None -> None  | anotado ambar 2026-11-04 08:00 -> 2026-11-04 14:00 | Las dos lecturas de la IA no coinciden.
 49 no_leido     programa rojo     dias_habiles_antes None -> None  | anotado ambar 2026-10-26 08:00 -> 2026-10-26 14:00 | La frase no trae las palabras propias de la regla dias_habiles_antes.; Faltan los días hábiles.
 51 acierto      programa sin_dato sin_dato None -> None  | anotado sin_dato None -> None
 55 acierto      programa verde    viernes_anterior 2026-10-23 12:00 -> 2026-10-23 13:00  | anotado verde 2026-10-23 12:00 -> 2026-10-23 13:00
 56 acierto      programa rojo     fecha_fija None -> None  | anotado rojo None -> None | La fecha de entrega es anterior a la edición. Posible error de escritura del aviso.
 58 acierto      programa verde    dia_anterior 2026-10-07 -> 2026-11-02 12:00  | anotado verde 2026-10-07 -> 2026-11-02 12:00
 59 acierto      programa verde    dia_anterior 2026-10-07 -> 2026-10-19 12:00  | anotado verde 2026-10-07 -> 2026-10-19 12:00
 61 acierto      programa verde    dia_anterior 2026-10-07 -> 2026-11-03 12:00  | anotado verde 2026-10-07 -> 2026-11-03 12:00
 63 no_leido     programa rojo     otra None -> None  | anotado verde 2026-10-07 -> 2026-10-19 | La IA dice que la regla no calza con ninguna conocida.
 65 no_leido     programa rojo     dias_habiles_antes None -> None  | anotado verde 2026-10-07 -> 2026-10-26 | Las dos lecturas de la IA no coinciden.
 66 acierto      programa verde    dias_habiles_antes 2026-10-07 -> 2026-10-22  | anotado verde 2026-10-07 -> 2026-10-22
 68 no_leido     programa rojo     dias_habiles_antes None -> None  | anotado verde 2026-10-07 -> 2026-11-10 13:00 | Las dos lecturas de la IA no coinciden.
 69 no_leido     programa rojo     dias_habiles_antes None -> None  | anotado verde 2026-10-07 -> 2026-10-19 13:00 | Las dos lecturas de la IA no coinciden.
 70 no_leido     programa rojo     dias_habiles_antes None -> None  | anotado verde 2026-10-07 -> 2026-10-21 13:00 | La frase no trae las palabras propias de la regla dias_habiles_antes.
 72 acierto      programa ambar    dias_habiles_antes 2026-10-07 -> 2026-10-09 [4] | anotado ambar 2026-10-07 -> 2026-10-09
 75 acierto      programa ambar    martes_o_jueves_anterior 2026-10-22 10:00 -> 2026-10-22 12:00 [5] | anotado ambar 2026-10-22 10:00 -> 2026-10-22 12:00
 78 acierto      programa ambar    martes_o_jueves_anterior 2026-10-20 10:00 -> 2026-10-20 12:00 [5] | anotado ambar 2026-10-20 10:00 -> 2026-10-20 12:00
 79 acierto      programa ambar    martes_o_jueves_anterior 2026-10-22 10:00 -> 2026-10-22 12:00 [5] | anotado ambar 2026-10-22 10:00 -> 2026-10-22 12:00
 80 EQUIVOCADO   programa ambar    dia_anterior 2026-10-23 10:00 -> 2026-10-23 12:30 [2] | anotado verde 2026-10-22 10:00 -> 2026-10-22 12:30
 82 no_leido     programa rojo     dia_anterior None -> None  | anotado verde 2026-10-15 10:00 -> 2026-10-15 12:30 | Las dos lecturas de la IA no coinciden.
 83 no_leido     programa rojo     dias_habiles_antes None -> None  | anotado verde 2026-10-19 09:00 -> 2026-10-19 11:00 | Las dos lecturas de la IA no coinciden.
 85 acierto      programa rojo     sin_dato None -> None  | anotado sin_dato None -> None | Las dos lecturas de la IA no coinciden.
 86 acierto      programa sin_dato sin_dato None -> None  | anotado sin_dato None -> None
 87 acierto      programa rojo     otra None -> None  | anotado sin_dato None -> None | La IA dice que la regla no calza con ninguna conocida.
 88 acierto      programa rojo     otra None -> None  | anotado sin_dato None -> None | La IA dice que la regla no calza con ninguna conocida.
 89 acierto      programa sin_dato sin_dato None -> None  | anotado sin_dato None -> None
 90 acierto      programa verde    dia_anterior 2026-10-26 10:00 -> 2026-10-26 12:00  | anotado verde 2026-10-26 10:00 -> 2026-10-26 12:00
 91 no_leido     programa rojo     dia_anterior_sabado_a_habil None -> None  | anotado verde 2026-10-07 -> 2026-10-23 | La frase no trae las palabras propias de la regla dia_anterior_sabado_a_habil.
 92 acierto      programa verde    viernes_anterior 2026-10-07 -> 2026-10-23  | anotado verde 2026-10-07 -> 2026-10-23
 93 acierto      programa verde    dia_anterior 2026-10-27 09:00 -> 2026-10-27 12:00  | anotado verde 2026-10-27 09:00 -> 2026-10-27 12:00
 94 acierto      programa ambar    dia_anterior 2026-10-23 09:00 -> 2026-10-23 12:00 [2] | anotado ambar 2026-10-23 09:00 -> 2026-10-23 12:00
 95 acierto      programa verde    dia_anterior 2026-10-21 09:00 -> 2026-10-21 12:00  | anotado verde 2026-10-21 09:00 -> 2026-10-21 12:00
 97 no_leido     programa rojo     dias_habiles_antes None -> None  | anotado verde 2026-10-07 -> 2026-10-20 12:00 | Segunda lectura. El aviso da dos plazos u horarios distintos para la entrega.
 98 acierto      programa verde    dias_habiles_antes 2026-10-07 -> 2026-10-19 12:00  | anotado verde 2026-10-07 -> 2026-10-19 12:00
102 no_leido     programa rojo     dias_habiles_antes None -> None  | anotado verde 2026-10-07 -> 2026-10-19 13:00 | La frase no trae las palabras propias de la regla dias_habiles_antes.; Faltan los días hábiles.
103 no_leido     programa rojo     dias_habiles_antes None -> None  | anotado verde 2026-10-07 -> 2026-10-28 12:30 | La frase no trae las palabras propias de la regla dias_habiles_antes.

```


# Análisis de los rojos del vale vista (bitácora acumulativa)

Reglas de esta bitácora (pedido de Diego). Se concluye del total acumulado y nunca del último caso. Cada afirmación lleva su n. Lo viejo no se borra, las correcciones se anotan con su fecha. Se cuentan aparte los textos únicos y las republicaciones (el mismo aviso publicado otro día), porque una republicación no es un error nuevo.

Fuente. banco_rojos\rojos_AAAA-MM.jsonl, un registro por aviso en rojo o sin dato, con el texto, las dos lecturas de Haiku, los motivos técnicos y los simples, y un campo revision para anotar la causa real y la decisión.

## 2026-10-17. Llenado inicial (7 ediciones capturadas, solo respuestas guardadas, instrucciones vv-2)
Ediciones 01-09, 06-10, 09-10, 10-10, 11-10, 13-10 y 14-10. El 01-09 no aporta registros porque no tiene respuestas guardadas. Varias ediciones solo tienen una parte de sus avisos con respuesta (se ven en la alarma de pendientes de cada edición), así que este conteo NO es una tasa de error.
Registros 84. Textos únicos 51. Republicaciones 33.
Por grupo, textos únicos (n = 51). Falla de la IA 27. Sin dato 14. Error del aviso 6. Regla nueva 4.
Por motivo simple, textos únicos (un texto puede tener más de un motivo). Las dos lecturas dieron reglas distintas 11. Regla que no calza con las palabras del aviso 9. Dos plazos u horarios distintos 4. Regla de un tipo que el programa no conoce 4. Frase que no está escrita así 3. Entrega en el remate sin que el aviso lo diga 3. Fecha del remate ya pasada 1. Vale vista pedido en fecha ya pasada 1. Día nombrado distinto al calculado 1.
Sin conclusiones todavía. Falta la primera revisión semanal, aviso por aviso, llenando el campo revision.

# Análisis de los rojos de la dirección (parte 3.7b, mismas reglas de arriba)

Fuente. banco_rojos\dir_rojos_AAAA-MM.jsonl, archivo aparte para no mezclarlo con el vale vista. Un registro por aviso con la dirección en rojo o sin dato, con el texto, las dos lecturas de Haiku, los motivos técnicos, el texto de la alerta y el campo revision.

## 2026-10-17. Llenado inicial (7 ediciones capturadas, solo respuestas guardadas, instrucciones dir-2)
Solo hay respuestas guardadas de la dirección para el 14-10 completo, la muestra de 59 avisos del 06-10 y sus republicaciones exactas en otros días. Este conteo NO es una tasa de error.
Registros 3, textos únicos 3. Todos Falla de la IA. Dos lecturas distintas 2 (14-10 aviso 26, sitio contra casa, y 06-10 aviso 3). La IA dijo que no hay dirección y el aviso parece darla 1 (06-10 aviso 65, depto sin calle en Puerto Varas).
Sin conclusiones todavía.

## 2026-10-18. Corrección de la numeración del 16-10 y del 17-10 (vale para los dos archivos, no se borra ningún registro)
Desde el arreglo del cortador traído del Mercurio (bitácora del 18, punto 6), el aviso del 2° Juzgado de Letras de Buin (rol C-1442-2024) y el del 3° Juzgado Civil de Viña del Mar (rol C-1177-2025) son dos avisos y no uno. En el 16-10 los avisos que eran el 12 en adelante pasan a ser uno más, y en el 17-10 los que eran el 13 en adelante también. Los registros guardan el número anterior. Afectados 19 registros del 16-10 y 27 del 17-10 en rojos_2026-10.jsonl, y 6 del 16-10 y 8 del 17-10 en dir_rojos_2026-10.jsonl. Para ubicar esos avisos, usar el rol y la página, no el número.

# Bitácora de traspaso al Mercurio (documento vivo)

Creada el 15 de Octubre de 2026 a pedido de Diego. Junta en un solo lugar todo lo aprendido en Agendar_Remates que sirve para arreglar el proyecto madre (D:\Mercurio, el programa del abogado). Antes estaba repartido entre la auditoría, el reconocimiento de ediciones, el reporte de validación y las bitácoras del 14 y del 15.

Reglas de este archivo.
- D:\Mercurio no se toca hasta la etapa "Traspaso del motor al Mercurio" del ESTADO. Decisión de Diego. Se arregla de una sola vez, con el motor ya probado contra el banco de pruebas, y no con parches sueltos.
- Toda lección nueva que sirva para el Mercurio se agrega aquí con su fecha, su evidencia y su n. Si algo se corrige, se anota la corrección y no se borra lo anterior.
- Cada línea dice si está verificada o si es un supuesto.

## 1. Qué falla hoy en el Mercurio (auditoría del 14 de Octubre, código revisado en el commit 94fe275)

Resumen en palabras de Diego. Los avisos quedaban cortados y nunca se unían bien, y no se leían todos los cuerpos del diario. La auditoría lo confirmó y encontró más.

| # | Falla | Estado | Efecto visto |
|---|---|---|---|
| F1 | No reconoce la flecha escrita "MÁS AVISOS... EN PÁGINA C 8" (solo busca "PÁG."), así que no lee la página siguiente cuando está en otro cuerpo | Verificado (14 de Octubre) | Ese día leyó 19 de 57 avisos con rol. Los 38 de la C 8 no se leyeron |
| F2 | Manda cada página sola a la IA. Un aviso que empieza al final de una página y sigue en la otra queda partido | Verificado (6 de Agosto, rol C-14821-2023) | La mitad sin rol se bota y la mitad sin tribunal se descarta como "Solo RM". DeepSeek inventó el tribunal mirando avisos vecinos |
| F3 | Corta por tamaño las páginas de más de 45.000 caracteres, con un solape de 2.000, aunque hay avisos de hasta 7.900 | Mecanismo verificado en el código, frecuencia no medida | Avisos incompletos en los dos trozos |
| F4 | Datos cruzados entre avisos vecinos en el punto de corte | Resultado verificado, explicación con 75% de confianza (14 de Octubre) | El dominio 2022 del rol C-8715-2025 se le pegó al C-14116-2025, que además salió dos veces en el Excel |
| F5 | Los avisos sin rol impreso se botan en silencio | Verificado (n = 2) | Solo quedan en el log, nunca en el Excel |
| F6 | La IA omite datos que sí están, y no tiene temperatura fija (cada corrida puede dar otra cosa) | Verificado (n = 1, rol C-8383-2024 sin tribunal) | Datos vacíos |
| F7 | El historial congela errores. Si una causa entra con datos faltantes, sus republicaciones se descartan como duplicadas y nunca se completan | Verificado en el código | Datos que nunca se corrigen |
| F8 | Un año de rol ilegible se descarta sin quedar en ninguna tabla | Verificado en el código | Avisos perdidos sin rastro |
| F9 | El último aviso de una página sigue en la otra. Si la otra no se lee, se bota por falta de rol | Verificado (14 de Octubre, rol C-5849-2026) | Aviso perdido |

Pendiente desde el 14 de Octubre. Pedir al abogado dos o tres casos concretos (fecha y rol) de "causa inventada" para confirmarlos contra estos mecanismos. La causa de las causas inventadas no quedó demostrada.

## 2. Lo que Agendar_Remates ya resolvió (para llevar al Mercurio)

| Falla | Solución | Dónde está | Evidencia |
|---|---|---|---|
| F1, F9 | Revisar TODOS los cuerpos del día y tomar toda página con la cornisa "1616 Remates de propiedades". Las flechas se reconocen en las dos formas ("PÁG." y "PÁGINA") y solo sirven para ordenar y confirmar costuras. Alarma si una flecha apunta a una página sin cornisa o si una página con cornisa no se conecta | motor\navegacion_logica.py, motor\lector_mercurio.py, pruebas\test_navegacion_logica.py | 36 ediciones revisadas y 7 fechas leídas en vivo sin alarmas (verificado) |
| F2, F3, F4 | Unir todas las páginas de remates en un solo rollo en orden de lectura y cortar por inicio de aviso, nunca por tamaño | motor\cortador.py, pruebas\test_cortador.py | 14 de Octubre, 61 de 61 avisos y 0 roles inventados (verificado) |
| F2 | Ordenar el texto de cada página por columnas usando la posición impresa (el visor a veces entrega las columnas desordenadas, ej. 1, 2, 4, 5, 6, 7, 3) | motor\orden_columnas.py | F9 y F15 del 11 de Octubre (verificado) |
| F2 | Unir la palabra cortada por guion entre una página y la siguiente ("Parcela-" y "ción") | motor\cortador.py | 23 uniones de página revisadas en 7 fechas (verificado) |
| F2 | Reconocer más comienzos de aviso. "palabras en mayúsculas + REMATA", "JUEZ PARTIDOR" y "PRIMER/SEGUNDO/TERCER LLAMADO". Sin esto, un aviso sin rol se pega al anterior y le contamina la fecha y el mínimo | motor\cortador.py | Pasaba en 5 de 7 fechas y en 2 casos contaminaba avisos de juzgados reales (verificado, bitácora del 15, punto 21) |
| F2 | Partir un trozo con dos roles solo en un cierre seguido de mayúscula o número, o en el único nombre de tribunal entre los dos roles | motor\cortador.py | 9 de Octubre (verificado) |
| F5, F8 | Ningún aviso se bota. El que no tiene rol queda como SIN_ROL y el que no pasa los filtros queda visible como "fuera de filtro" | db\esquema.sql | Diseño aprobado. Única excepción, los partidores, que se guardan ocultos solo para el cuadre |
| F6 | La IA nunca tiene la última palabra. Lo de formato fijo lo saca el código. Lo de texto libre lo saca la IA con la frase exacta, y el código comprueba que la frase exista. Temperatura fija en cero | db\esquema.sql (tabla citas), banco nivel 2 | Diseño. Se construye en las partes 3.6 y 3.7 |
| F7 | Guardar cada publicación por separado y registrar lo que cambia entre una y otra, en vez de descartar las republicaciones | db\esquema.sql (bienes, remates, cambios) | Diseño aprobado el 15 de Octubre |

## 3. Trampas del diario que el Mercurio debe resistir (verificadas en el banco de pruebas)

- Sin el modo HD del visor no hay texto, solo imágenes. El Mercurio ya lo activaba, pero el motor nuevo lo olvidó al principio (bitácora del 14). Lección. Antes de reimplementar algo, revisar las reglas inamovibles del Mercurio.
- El texto se arma uniendo los renglones con salto de línea. Es la única forma que reproduce exacto el texto del banco. Sin separador se pega "PÁGINA B 11" con "1616" y sale una alarma falsa de página B111.
- El código de cada página no tiene formato fijo (B-20261014-011, L64MFDBT, VO4M4DJJ).
- Los viernes el cuerpo G repite los remates del B. Se leen ambos y se unen sin duplicar (n = 1 viernes comprobado).
- Hay flechas de otras secciones (defunciones) que se ignoran. La regla exige "AVISOS ECONÓMICOS CLASIFICADOS".
- La cornisa "1616 Remates de propiedades" aparece en mitad de una palabra ("video confe1616 Remates de propiedades rencia").
- Roles sin guion (C-39902025), con punto de miles (C-1.301-2026), con barra (2087/2024), con errata (CC-936-2026), sin prefijo, o repetidos.
- "REmate" con letra capital en minúscula por el estilo del diario.
- (15 de Octubre) Los roles mal impresos se detectan por código. Prefijo con letras de más (CC-936-2026) o número y año pegados sin guion (C-24622022). La regla está en db\carga.py (rol_mal_impreso) y en el 14 de Octubre encontró exactamente los 4 anotados a mano (6, 17, 45 y 48), sin falsas alarmas en los otros 53. Sirve para que el Mercurio avise de errores del aviso.

## 4. Lo que la llave del Mercurio no distingue (para revisar en el traspaso)

- Un mismo aviso puede traer varios remates con su propio mínimo (aviso 3 del 14 de Octubre con 2 oficinas, aviso 30 con 4 lotes). Verificado.
- Una misma causa puede tener muchos remates en una sola edición. El 1 de Septiembre el rol C-5656-2013 trae 26 remates distintos, cada uno con su fecha, hora e inmueble. Verificado en la captura C8.
- Agendar_Remates usa la llave rol-año más tribunal para la causa, la misma del Mercurio. SUPUESTO por confirmar al leer el código del Mercurio. Si el Mercurio descarta como duplicado todo lo que repite esa llave, se quedaría con 1 de los 26 remates.
- Modalidad en línea que no es Zoom (Google Meet, vendaya.cl), garantía sobre la tasación o como monto fijo, caución sin vale vista. Verificado en el banco nivel 2.

## 5. Pendiente antes del traspaso

- Partes 3.6 y 3.7 (extracción con citas) y parte 4 (cuadre de cuentas, que incluye contar fechas de remate por aviso como red contra avisos pegados).
- Pendiente menor del cortador. Algunos avisos terminan con "EXTRACTO DE", que es el comienzo del título del siguiente.
- Preguntar a Diego y al abogado si el filtro de JUEZ PARTIDOR (decisión de Diego para su agenda) también se quiere en el Mercurio.
- Antes de tocar el Mercurio, leer sus reglas inamovibles y su código actual, y repetir el banco de pruebas con el motor ya traspasado.
- (15 de Octubre) Agendar_Remates decidió no filtrar (decisión de Diego). La extracción de comuna, fojas y año de dominio, que el Mercurio necesita para sus filtros, no se construye aquí. Habrá que hacerla en el traspaso, con las mismas reglas de este proyecto (cita exacta comprobada por código, vacío con alerta antes que adivinar).

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
| F2 | (15 de Octubre, noche) Tres comienzos de aviso más. "EXTRACTO. ANTE EL SEÑOR JUEZ" (con EL/LA y SEÑOR/SEÑORA opcionales), "JUEZ ÁRBITRO" en mayúsculas y "N° JUZGADO CIVIL" en mayúsculas sin punto antes (con verbo de remate cerca). Sin esto, un remate de partición se pegaba a un juzgado real y el juzgado quedaba sin datos o con el mínimo vacío | motor\cortador.py, pruebas\foto_cortador.py | Pasaba en 6 de los 8 rollos de 7 fechas. Contaminaba 30° Civil (06-10, 09-10, 13-10), Cobranza (06-10) y 15° Civil (06-10) (verificado, bitácora del 15, punto 45) |
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
- Roles sin guion (C-39902025, CORRECCIÓN del 16 de Octubre, este ejemplo era falso, el diario imprime "C-3990-" al final del renglón), con punto de miles (C-1.301-2026), con barra (2087/2024), con errata (CC-936-2026), sin prefijo, o repetidos.
- "REmate" con letra capital en minúscula por el estilo del diario.
- (15 de Octubre) Los roles mal impresos se detectan por código. Prefijo con letras de más (CC-936-2026) o número y año pegados sin guion (C-24622022, CORRECCIÓN del 16 de Octubre, este ejemplo era FALSO, fabricado por el guion al final de renglón. Ejemplo real "C82062024" del 6 de Octubre). La regla está en db\carga.py (rol_mal_impreso) y en el 14 de Octubre encontró exactamente los 4 anotados a mano (6, 17, 45 y 48), sin falsas alarmas en los otros 53. Sirve para que el Mercurio avise de errores del aviso.

- (16 de Octubre) Los viernes el diario trae los remates dos veces (cuerpos B y G). Unirlos "por rol" sería peligroso, porque un mismo rol puede traer muchos remates (26 del C-5656-2013 el 1 de Septiembre). La unión debe hacerse por la huella del texto del aviso. Verificado que en Agendar_Remates todavía no está programada.
- (16 de Octubre) Unión hecha en Agendar_Remates (motor\procesar_edicion.py, unir_rollos). Huella con solo letras y números en minúscula, porque la lectura de B y G difiere en espacios (7 de 127 avisos el 09-10). Repeticiones contadas. Verificado en el 09-10 (127 de 127 unidos, n = 1 viernes).
- (16 de Octubre) Trampa del diario. Un rol puede quedar partido al final de un renglón ("C-3862-" y "2025"). Quien una palabras cortadas por guion debe hacerlo solo cuando hay letra antes y minúscula después ("Condo-" "minio", "SAN-" "tiago"), o fabrica un rol "mal impreso" que el diario no imprimió. Medido en 14.765 cortes de 7 ediciones. Con la regla vieja salían 52 alertas falsas de rol (hecho en Agendar_Remates el 16 de Octubre, motor\cortador.py). Verificado en el texto crudo del 06-10 y del 09-10.
- (16 de Octubre) Una alerta nunca debe afirmar que el aviso no dice algo cuando lo que pasa es que el programa no lo leyó. Pasó dos veces (garantía y vale vista) y se corrigió con textos distintos.

## 4. Lo que la llave del Mercurio no distingue (para revisar en el traspaso)

- Un mismo aviso puede traer varios remates con su propio mínimo (aviso 3 del 14 de Octubre con 2 oficinas, aviso 30 con 4 lotes). Verificado.
- Una misma causa puede tener muchos remates en una sola edición. El 1 de Septiembre el rol C-5656-2013 trae 26 remates distintos, cada uno con su fecha, hora e inmueble. Verificado en la captura C8.
- Agendar_Remates usa la llave rol-año más tribunal para la causa, la misma del Mercurio. SUPUESTO por confirmar al leer el código del Mercurio. Si el Mercurio descarta como duplicado todo lo que repite esa llave, se quedaría con 1 de los 26 remates.
- Modalidad en línea que no es Zoom (Google Meet, vendaya.cl), garantía sobre la tasación o como monto fijo, caución sin vale vista. Verificado en el banco nivel 2.

## 5. Pendiente antes del traspaso

- HECHO el 17 de Octubre. Partes 3.6 y 3.7 (extracción con citas) y parte 4 (cuadre de cuentas y republicaciones), más la marcha blanca del 15, 16 y 17 de Octubre.
- (17 de Octubre, noche) Desde la 3.7b ya se leen la comuna (Haiku, verificada por código) y la inscripción en el Conservador con su año (código). Falta confirmar al leer el Mercurio si su filtro de "dominio anterior a 2020" usa ese mismo año. El Mercurio usa DeepSeek y este proyecto Haiku. Qué IA usar en el traspaso lo decide Diego.
- (17 de Octubre, noche) Plan de Diego. El traspaso se hace en un chat nuevo del proyecto Mercurio, basado en esta bitácora. Cuando el Mercurio arreglado funcione en el PC de Diego, se saca el Excel para el abogado con las ediciones del 14 al 17 de Octubre (el abogado está de vacaciones y no ha corrido el programa). Las capturas de esas cuatro ediciones ya están guardadas aquí y sirven para comparar los dos programas.
- Pendiente menor del cortador. Algunos avisos terminan con "EXTRACTO DE", que es el comienzo del título del siguiente.
- Preguntar a Diego y al abogado si el filtro de JUEZ PARTIDOR (decisión de Diego para su agenda) también se quiere en el Mercurio.
- Antes de tocar el Mercurio, leer sus reglas inamovibles y su código actual, y repetir el banco de pruebas con el motor ya traspasado.
- (15 de Octubre) Agendar_Remates decidió no filtrar (decisión de Diego). La extracción de comuna, fojas y año de dominio, que el Mercurio necesita para sus filtros, no se construye aquí. Habrá que hacerla en el traspaso, con las mismas reglas de este proyecto (cita exacta comprobada por código, vacío con alerta antes que adivinar).

## Lecciones de la parte 3.7b (17 de Octubre)
- Un mismo rol puede traer decenas de propiedades (01-09, C-5656-2013, 26 avisos). Unir por rol o por causa sola junta propiedades distintas. La inscripción en el Conservador (fojas, número y año) las distingue y se lee por código (motor\extraccion.py, inscripcion).
- En los avisos con varios lotes, el inmueble de cada mínimo es el primero nombrado después del mínimo anterior, no el último antes del mínimo (aviso de 4 lotes del 12° Civil, el lote 4 quedaba como estacionamiento 6).
- La dirección tiene número en palabras con frecuencia y la comuna a veces solo como ciudad. Haiku a veces saca la comuna de la frase del Conservador, lo que no corresponde.

## Lecciones de la parte 4 (17 de Octubre)
- Un aviso sin rol ni tribunal ni inscripción no puede tener clave vacía, porque junta propiedades distintas de días distintos. Se identifica por la huella de su texto.
- Comparar publicaciones solo de un valor a otro valor. Un dato vacío casi siempre es un dato que no se leyó ese día, no un cambio del aviso.
- Contar los roles del texto contra los de los avisos detecta avisos con dos roles distintos impresos (error humano del secretario).

## Decisiones de Diego para el traspaso (17 de Octubre, noche)
- La IA del Mercurio pasa a ser Haiku. DeepSeek se descarta del todo. Diego lo da por comprobado con Agendar_Remates (vale vista y dirección leídos por Haiku con cita verificada por código, validación y marcha blanca de tres ediciones).
- El traspaso se hace de una sola vez y en un chat nuevo del proyecto Mercurio, con D:\Agendar_Remates y D:\Mercurio vinculadas. D:\Agendar_Remates queda solo de consulta desde ese chat.
- Al terminar y pasar el banco de pruebas, se saca el Excel para el abogado con las ediciones del 14 al 17 de Octubre de 2026.

## Cómo empezar el traspaso (mapa para el chat nuevo)
Qué leer, en este orden.
1. Este archivo completo.
2. D:\Agendar_Remates\ESTADO_PROYECTO.md (decisiones, reglas de navegación y avance del motor).
3. D:\Agendar_Remates\AUDITORIA_LECTURA_MERCURIO_2026-10-14.md (por qué falla hoy el Mercurio, con casos reales).
4. D:\Mercurio\MD_Vivos\ (la bitácora más nueva es BITACORA_MERCURIO_2026-08-06.md) y D:\Mercurio\PROMPT_MAESTRO_MERCURIO_v3_1.md.
5. El código actual del Mercurio (main.py, modulo1_mercurio.py, modulo5_reporte.py) antes de diseñar nada.

Estado del Mercurio visto desde aquí el 17 de Octubre (verificado con git en D:\Mercurio, sin modificar nada). Último commit 8bdbff6, igual a origin/main. Hay 4 archivos con cambios sin commitear (main.py, modulo1_mercurio.py, modulo5_reporte.py y ejecutar_mercurio.bat), que son la alerta de fallo de la API con código de salida 3. Con "git diff --ignore-cr-at-eol" son 75 líneas agregadas y 6 quitadas (sin esa opción parecen miles, por los finales de línea de Windows). La temperatura de la IA no está fijada en modulo1_mercurio.py. E:\Mercurio, en el PC del abogado, tiene una mezcla de esos archivos (bitácora del Mercurio del 6 de Agosto).

Qué pieza de Agendar_Remates resuelve qué (todas en D:\Agendar_Remates\motor).
- lector_mercurio.py y navegacion_logica.py. Entrar al diario en modo HD, recorrer todos los cuerpos y tomar toda página con la cornisa 1616, con las flechas en sus dos formas. Resuelve F1 y F9.
- orden_columnas.py. Ordena el texto de cada página por la posición de sus columnas.
- cortador.py. Une las páginas en un solo rollo y corta por comienzo de aviso, sin IA. Resuelve F2, F3 y F4.
- extraccion.py y numeros_texto.py. Rol, tribunal, fecha y hora, modalidad, mínimo, garantía, inscripción en el Conservador (fojas, número y año) y carátula, todo por código y con su cita.
- vale_vista.py y direccion.py. Lo que lee Haiku, siempre con la frase exacta, doble lectura y verificación por código. Las respuestas se guardan por la huella del texto (ia_respuestas) para no pagar dos veces. El Mercurio necesita la dirección y la comuna, el vale vista no.
- procesar_edicion.py. Orquesta todo, une los rollos B y G de los viernes por la huella del texto y permite retomar sin volver a leer el diario.
- republicaciones.py. Cuadre de roles del texto contra los avisos y cambios entre publicaciones. Es la idea para reemplazar el historial CAUSAS que congela errores (F7).
- db\carga.py y db\esquema.sql. Ningún aviso se bota (F5 y F8). Identidad de cada propiedad por causa más inscripción.
- pruebas\ (16 pruebas sin internet ni Haiku) y banco_pruebas\ (ediciones con su inventario verificado a mano). Sirven para probar el Mercurio ya traspasado.

Lo que el Mercurio tiene y Agendar_Remates no (no perderlo en el traspaso).
- Sus filtros de negocio (solo RM por comuna, no BancoEstado, no Estación Central, rol desde 2018, dominio anterior a 2020 con la salvaguarda de REVISAR), el fuzzy de cortes con la hoja REFERENCIA de causas_ojv.xlsx, la llave rol-año más tribunal y el Excel de M5 tal como lo usa el abogado.
- Supuesto por confirmar en el código. El año de dominio del filtro CBR sería el mismo año de inscripción que ya lee extraccion.py.

## 2026-10-18. Vuelta de los arreglos del traspaso a Agendar_Remates
Los cuatro arreglos del Mercurio (cortador con "EXTRACTO 3°JUZGADO" y las tres reglas de la ciudad del tribunal) quedaron aplicados en Agendar_Remates con la línea _TRIBUNAL idéntica a la del Mercurio. En las 10 ediciones capturadas cambian 2 avisos por el cortador y 7 por el tribunal, todos los esperados (bitácora del 18, puntos 6 a 9).
Regla de las dos fechas. El Mercurio la quitó. Agendar_Remates la mantiene con la opción C de Diego, en que una fecha anterior a la edición no cuenta (7 de 8 falsas alarmas eran fechas pasadas, bitácora del 18, punto 10). Sigue como falsa alarma conocida el caso en que la segunda fecha es la entrega del vale vista y es futura (06-10, rol 4265-2021). Para el próximo traspaso, decidir si el Mercurio adopta la misma regla.

## 2026-10-18. Vale vista en el remate (corrección de Diego)
"Los vales vista recepcionados serán calificados al momento de hacerse el llamado al remate" SÍ es entrega en el remate (10° Juzgado Civil). Hay remates donde el vale vista se entrega minutos antes de empezar. Agendar_Remates lo acepta desde el 18 de Octubre (motor\vale_vista.py, _CALIFICA_LLAMADO). El Mercurio no necesita el vale vista, pero si algún día lo lee, la regla es esa. Lección general. Antes de escribir que la IA se equivocó, revisar si la regla del programa o la anotación del banco eran las equivocadas. En este caso Haiku tenía razón y el banco no.

## Agregado el 21 de Octubre
- Agendar_Remates descarta desde el 21 de Octubre los avisos de Juzgados de Familia, Cobranza Laboral y Previsional, Letras del Trabajo y Policía Local (decisión de Diego, solo civiles y Juzgados de Letras). Regla NO_CIVIL en db\carga.py de Agendar. Queda para que Diego decida si el Mercurio debe hacer lo mismo. En 12 ediciones fueron 20 avisos.


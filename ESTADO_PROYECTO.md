# ESTADO DEL PROYECTO AGENDAR_REMATES (documento vivo)

Última actualización 21 de Octubre de 2026 (tarde). Lector diario en la nube funcionando desde el 21 de Octubre, links a cada aviso en las tablas de cambios y descarte de tribunales no civiles. Sigue la primera carga en la base real (ver Próximo paso). Bitácoras en BITACORA_2026-10-14.md, BITACORA_2026-10-15.md (puntos 1 a 45), BITACORA_2026-10-16.md, BITACORA_2026-10-17.md y BITACORA_2026-10-18.md. Este archivo es la fuente de verdad del proyecto. Todo chat nuevo debe leerlo completo antes de proponer nada. Cuando algo cambie, se actualiza aquí y se deja constancia en la bitácora de la sesión.

## Qué es

Programa visual para que Diego agende los remates judiciales de propiedades a los que decide ir. Flujo acordado.
1. Se lee completa la edición del día de El Mercurio (sección 1616 Remates de propiedades).
2. De cada aviso se extrae la fecha del remate, si es por Zoom o presencial, la regla del vale vista tal como la dice ese aviso (fecha exacta o rango), el monto mínimo y la garantía.
3. Todo queda en una base de datos. Diego busca por rol o tribunal en la edición elegida (por defecto la del día), elige un remate y recién ahí se marcan en su calendario la fecha del vale vista y la del remate.

## Decisiones tomadas por Diego

Carpeta madre D:\Agendar_Remates. D:\Mercurio es solo fuente de consulta y no se modifica.
Corre en el PC de Diego. No se descarta otro PC a futuro, así que rutas relativas y configuración en un solo archivo.
Se mantienen los filtros originales del Mercurio (solo RM, no BancoEstado, no Estación Central, rol desde 2018, dominio anterior a 2020), aplicados después de leer. La lectura nunca se salta avisos.
CORRECCIÓN de Diego (15 de Octubre, tarde). Agendar_Remates NO filtra. Filtrar es la tarea principal del Mercurio. La finalidad de este proyecto es el calendario, organizar la entrega del vale vista y la ida al remate, y saber si es por Zoom o presencial. La única exclusión es la de JUEZ PARTIDOR. Por eso la parte 3.6 no extrae comuna, fojas ni año de dominio. Eso queda para el traspaso al Mercurio.
Decisiones de Diego del 17 de Octubre (parte 3.7c). Basta la carátula tal como la imprime el aviso, sin separar demandante y demandado, leída solo por código. Dos carátulas distintas en un aviso son duda de lectura. La misma carátula con diferencias no relevantes (S.A., Ltda) cuenta como una.
Decisiones de Diego del 17 de Octubre (parte 3.7b). La inscripción en el Conservador (fojas, número y año) se lee por código SOLO para saber qué propiedad es cuál, nunca para filtrar. La dirección la lee Haiku para mostrarla en la ficha, con su comuna, y no entra en la clave del bien. Un terreno sin calle guarda su descripción tal como está en el aviso. Si la dirección queda en rojo, el campo queda vacío y la alerta trae las dos lecturas y la frase del aviso. De un mismo juicio se pueden agendar todas las propiedades que Diego quiera (la agenda va por propiedad).
Garantía cuyo aviso no dice sobre qué se calcula (ej. "caución del 10%"). Decisión de Diego. Se asume el mínimo y el HUD lo muestra destacado como ASUMIDO, porque el aviso no lo dice. Ojo. El art. 494 del Código de Procedimiento Civil habla del 10% "de la valoración de dichos bienes", no del mínimo (pregunta 11 al abogado).
Interfaz en HTML servida por un programa local en Python con base SQLite.
La regla del vale vista se interpreta desde el texto de cada aviso, nunca se asume por la costumbre del tribunal. La historia del tribunal solo sirve como alarma cuando un aviso dice algo distinto.
Republicaciones. Se guarda cada publicación y se avisa si cambian las bases entre una y otra.
Decisión de Diego del 17 de Octubre (noche), para la interfaz. Vale la versión más nueva del aviso. Si un remate que está en el calendario cambia de fecha entre publicaciones, la interfaz lo debe avisar en grande, con un aviso del tipo "FECHAS DE REMATES HAN SIDO CAMBIADAS EN DIFERENTES AVISOS", hasta que Diego lo marque como visto. Un error del secretario al fijar la fecha es grave. La base ya sigue la publicación más nueva (v_calendario) y cuenta los cambios sin ver (cambios_sin_ver).
Sincronizar con Google Calendar o el celular queda para una etapa futura.
Decisión de Diego del 18 de Octubre. Cada causa agendada y su ficha muestran un link por cada aviso publicado de esa propiedad (el del llamado anterior aparte). Si el aviso va partido en dos páginas, los dos links. Diseño de la variante B dado por listo el 18 de Octubre.
Decisión de Diego del 18 de Octubre. SINCRONIZACIÓN. Al abrir la interfaz, si falta la edición de hoy o un día de los últimos 7, sale arriba la franja negra "SIN SINCRONIZAR" que no se puede cerrar. Si una edición reciente quedó incompleta (IA sin leer o sin sección de remates) sale una franja ámbar. motor\sincronizacion.py ya entrega esas líneas. Una edición sin remates queda anotada con alarma. Botón "Actualizar ahora" o lector programado en Windows, para más adelante. Bitácora del 18, puntos 37 a 39.
Decisión de Diego del 18 de Octubre. VALE VISTA EN EL REMATE. "Los vales vista recepcionados serán calificados al momento de hacerse el llamado al remate" SÍ es una regla válida (entrega en el mismo remate). Hay remates donde el vale vista se entrega minutos antes de empezar. La causa lo dice así. Las alertas de falla de lectura ya no culpan a Haiku, dicen que la lectura no pasó las revisiones del programa. Bitácora del 18, puntos 53 a 58.
Decisión de Diego del 18 de Octubre. NUEVO LLAMADO. Si un remate no se hizo y la propiedad vuelve a publicarse, es un remate nuevo con sus propias bases. No se compara dato por dato con el llamado anterior, se anota una vez como nuevo_llamado en cambios, la interfaz lo muestra aparte de "FECHAS CAMBIADAS" (no es un error del secretario), vale vista entregado y remate asistido vuelven a cero, y el calendario nunca toma datos del llamado anterior. Si Diego quitó la causa con la X y vuelve a publicarse, la interfaz lo avisa (va con el código de la interfaz). Bitácora del 18, puntos 30 a 33.
Decisiones de Diego del 18 de Octubre para la interfaz (bosquejos en Paint, bitácora del 18, puntos 15 a 18). Es UNA sola página minimalista. Al abrir solo se ve el calendario con tres meses apilados (el anterior, el actual al medio y más grande, y el siguiente), con o sin remates agendados. Los detalles aparecen a medida que se hace clic. A la derecha hay un botón de lupa que abre el panel para buscar y añadir remates. Ese buscador tiene tres campos independientes (tribunal, rol y año), y basta llenar uno para que empiece a filtrar. Tiene además un filtro de edición, y cada remate dice en letra chica en qué días fue publicado en El Mercurio. La Corte aparece fija en "CA de Santiago" solo como marcador visual (no hay intención por ahora de ver otras Cortes). Cada tarjeta del buscador muestra carátula, tribunal, rol y año, fecha del remate, entrega del vale vista (con rango si lo tiene) y el monto del vale vista para participar. Si el mínimo está en UF, aparece un recuadro "Cálculo de VV por UF" donde Diego pega el valor de la UF y obtiene el monto en pesos. La columna izquierda, al abrirse, muestra todos los remates agendados de Diego con la información relevante de cada uno. El diseño se hace en Claude Design (tipo Design de los artifacts), no en el chat. Diego pidió 3 bosquejos, que son 3 variantes de estilo para elegir. La columna izquierda se abre con una pestaña "Causas agendadas". Lienzo en claude.ai "Agendar Remates — Interfaz" (18 de Octubre, bitácora del 18, punto 20).
Decisión de Diego del 18 de Octubre (bitácora del 18, punto 21). Se elige la variante B, línea de tiempo con un carril por causa, en tonos crema y café, cada mes completo sin scroll horizontal y con "Causas agendadas" siempre visible. Ícono del día del remate según modalidad (martillo presencial, computador virtual, signo de interrogación sin dato), y el clic lleva a la causa. El aviso grande abre con "Revisar detalles" una tabla por remate (aviso de un día contra el del otro, solo lo que cambió), y ahí va "Marcar como visto".
Las entregas de vale vista se organizan por tribunal, porque es a donde Diego debe ir. Si dos remates agendados del mismo tribunal tienen la entrega el mismo día, el calendario los muestra juntos en una sola tarea (tribunal, día, cantidad de vales vista y roles). Idea acordada el 2026-10-15 para la interfaz.
CORRECCIÓN de Diego (15 de Octubre, tarde). El calendario muestra la fecha del remate y la ventana completa del vale vista (desde y hasta). Diego decide qué día ir, el programa nunca elige por él. Al marcar el vale vista como entregado, la ventana deja de mostrarse para ese remate. Lo que junta remates del mismo tribunal se llama "visita al tribunal", no tarea. Cómo agrupar está por diseñar. Observación de Diego. Las restricciones son una mezcla (solo martes y jueves, horarios distintos, 72 horas desde la hora del remate, día anterior exacto), así que no basta cruzar tramos de días. Cada vale vista debe pasar a su lista de días y horarios permitidos antes de cruzarse. Por ahora v_entregas_vv es provisoria.
El "desde" del vale vista cuando el aviso solo dice hasta cuándo. Diego cree que es desde el mismo día de la publicación. Pregunta 9 al abogado. Mientras tanto sigue la regla del día siguiente.
Todo remate agendado sin fecha de vale vista se avisa en el HUD como dato faltante que Diego debe resolver.
Agenda sin estado "descartado". Si Diego no irá a un remate, lo quita del calendario con un botón X. A Diego le indican a qué remate ir, por eso ningún aviso se elimina por filtros. Los que no pasan quedan visibles como "fuera de filtro". EXCEPCIÓN (Diego, 2026-10-15). Los remates de JUEZ PARTIDOR se descartan del todo y no aparecen en la búsqueda. Incluye los remates de partición ante juez o jueza ÁRBITRO (decisión del 15 de Octubre, noche). Regla PARTICION en db\carga.py.
Decisión de Diego del 21 de Octubre. SOLO CIVILES. Se descartan del todo, igual que JUEZ PARTIDOR, los avisos de Juzgados de Familia, de Cobranza Laboral y Previsional, de Letras del Trabajo y de Policía Local. Se mantienen los Juzgados Civiles y los Juzgados de Letras (Buin, San Bernardo, Colina y regiones). Motivo guardado "tribunal no civil", no pasan por Haiku. Un aviso sin tribunal leído no se puede clasificar y se sigue mostrando. db\carga.py, NO_CIVIL y motivo_descarte. Bitácora del 21, puntos 5 a 8.
Rol sin guion después de la letra (C2461-2022). Se avisa como detalle menor, con tono normal (decisión del 15 de Octubre, noche). CORRECCIÓN del 16 de Octubre. El ejemplo C2461-2022 era falso (el diario imprime "Rol C-" y "2461-2022" en dos renglones y el programa borraba el guion). La decisión sigue, con ejemplos reales como "C 19087-2024" y "C8834-2022".
Feriados de Chile cargados desde fuente oficial y aviso en diciembre si falta el año siguiente. PENDIENTE (decisión de Diego del 17 de Octubre). Los feriados 2027 están cargados como PROVISORIOS, calculados por ley (db\feriados_calculo). Hay que esperar la lista oficial a fines de 2026 o comienzos de 2027, reemplazar db\feriados_2027.csv y anotar la corrección. La alarma de la base lo recuerda mientras siga provisorio.
La lectura debe ser perfecta por diseño. La IA nunca tiene la última palabra. Lo de formato fijo (rol, montos, fechas) lo lee el código. Lo de texto libre lo interpreta la IA citando la frase exacta, y el código verifica que la frase exista. Lo que no se pueda verificar se marca en rojo.
Las 72 horas (y las 24) se cuentan en horas de reloj desde la hora del remate. Si el tope cae en fin de semana o feriado, se adelanta al último horario hábil. Si el aviso solo dice hasta cuándo se entrega el vale vista, el desde es el día siguiente a la edición. Decisiones del 15 de Octubre.
Día hábil provisorio de lunes a viernes sin feriados. El art. 59 del Código de Procedimiento Civil haría hábil el sábado, pero dos tribunales escriben en sus avisos que el día hábil anterior a un lunes es el viernes. Queda como pregunta para el abogado (PREGUNTAS_ABOGADO.md).
Cada remate debe mostrar en su ficha las alertas de su aviso (errores de escritura, roles mal impresos, contradicciones, condiciones raras como garantía del 20% o sobre la tasación, caución sin vale vista, aviso previo por correo) y el link directo a su página del Mercurio. Pedido de Diego del 15 de Octubre. Un error del aviso podría usarse para anular el remate.
No se parcha el Mercurio del abogado ahora. El motor de lectura se construye aquí, se prueba con el banco de pruebas y después se traspasa al Mercurio de una sola vez.

## Base de datos

Ver db\LEEME_BASE_DATOS.md. Versión 2 del esquema (15 de Octubre), con 14 tablas y 5 vistas (agenda_manual y agenda_quitados se sumaron el 18 de Octubre para la interfaz, sin cambiar la versión). Un aviso puede traer varios remates y cada remate apunta a un bien (causa más inmueble). La agenda va por remate.

Cambios de la parte 3.5, TODOS APLICADOS el 15 de Octubre (se dejan como registro).
1. Un remate se identifica por causa más fecha y hora más inmueble. El 1 de Septiembre hay 26 avisos del rol C-5656-2013. Además un mismo aviso puede traer varios remates (aviso 3 del 14 de Octubre con 2 oficinas, aviso 30 con 4 lotes, cada uno con su mínimo).
2. Guardar la dirección de cada página del Mercurio (ej. /2026/10/14/B/B-20261014-011) para el link directo. El lector ya la conoce, falta guardarla.
3. Modalidad nueva en_linea (Google Meet, vendaya.cl). La base hoy solo acepta zoom, presencial, mixta y sin_dato.
4. Garantía sobre la tasación (no sobre el mínimo) y garantía como monto fijo.
5. Cajón o campos de alertas por aviso.
6. Filtro nuevo. Los remates de JUEZ PARTIDOR se descartan del todo (ver decisiones).

## Evidencia reunida (leer antes de diseñar o cambiar la lectura)

AUDITORIA_LECTURA_MERCURIO_2026-10-14.md. Por qué falla la lectura actual del Mercurio (avisos partidos entre páginas y entre trozos, avisos sin rol botados en silencio, datos cruzados entre avisos vecinos, redirección "PÁGINA C 8" no detectada, historial que congela errores).
RECONOCIMIENTO_EDICIONES_2026-10-14.md. Dónde aparecen los remates en 36 ediciones y cómo se continúan. Base de las reglas de navegación.
banco_pruebas\LEEME_BANCO_PRUEBAS.md. Ediciones 2026-08-06 y 2026-10-14 con su inventario correcto (95 + 61 avisos) y la lista de trampas del diario. Incluye el banco nivel 2 del 14 de Octubre (61 remates con fecha, hora, modalidad, vale vista, mínimo, garantía y dirección, cada dato con su cita).
PREGUNTAS_ABOGADO.md. Once dudas legales pendientes, cada una con su regla provisoria.
BITACORA_TRASPASO_MERCURIO.md. Todo lo aprendido aquí que sirve para arreglar el Mercurio (fallas, soluciones ya hechas, trampas del diario y pendientes). Toda lección nueva que sirva para el Mercurio se anota ahí. Creada el 15 de Octubre a pedido de Diego.

## Reglas de navegación (sobre evidencia, n = 36 ediciones)

Revisar todos los cuerpos del día y tomar toda página con la cornisa "1616 Remates de propiedades". Lunes a viernes suele ser B, sábado D, domingo F, pero no se asume.
Las flechas "MÁS AVISOS ECONÓMICOS CLASIFICADOS EN PÁG./PÁGINA X N" y "VIENEN DE PÁGINA X N" sirven para ordenar y confirmar costuras. Hay flechas de otras secciones (defunciones) que se ignoran.
Si dos cuerpos repiten avisos (B y G los viernes), se unen sin duplicar.
Alarma si una flecha apunta a una página sin cornisa o si una página con cornisa no se conecta con nada.
Lectura de cada página con el visor del propio diario (PDFViewerApplication del visor, texto de la página), unos 2 segundos por página. OBLIGATORIO activar el modo HD del visor al inicio de cada sesión. Sin HD el visor muestra imágenes y no hay texto. El texto se arma uniendo los renglones con salto de línea (forma "salto"), única forma que reproduce exacto el texto del banco.

## Diseño de lectura (prototipo probado sobre el banco)

Unir todas las páginas de remates en un solo rollo en orden de lectura. Quitar las cornisas que el diario repite en cada columna. Cortar por inicio de aviso con reglas de código. Separar trozos con dos roles. El rol lo saca el código. Resultado del prototipo sin ayuda manual. 130 de 150 roles aislados al primer intento, 0 roles inventados, el resto detectado como trozos con dos avisos pegados.

## Dónde estamos

✅ Idea, dudas y decisiones
✅ Auditoría de la lectura del Mercurio
✅ Banco de pruebas nivel 1 (95 + 61 avisos, el 14 de Octubre corregido de 59 a 61)
✅ Reconocimiento de 36 ediciones y reglas de navegación
✅ Respaldo en GitHub privado DFNR2026/AgendarRemates
✅ Base de datos diseñada y probada (falta aplicar los cambios de la parte 3.5)
✅ Motor parte 1, navegación
✅ Motor parte 2, rollo único y corte por aviso (commits 0ebf8f5 a 084a577, push hecho por Diego)
🔄 Motor parte 3, extracción con citas
   ✅ 3.1 Formato del banco nivel 2
   ✅ 3.2 Banco nivel 2 anotado (61 remates del 14 de Octubre)
   ✅ 3.3 pruebas\test_banco_nivel2.py (431 citas, fechas, montos, vale vista recalculado)
   ✅ 3.4 Revisión de Diego (17 avisos sin errores de lectura, se dio por cerrada)
   ✅ 3.4b Cortador arreglado. Separa los avisos de JUEZ PARTIDOR y TERCER LLAMADO que iban pegados. Corrigió 5 de 7 fechas, dos de ellas contaminaban avisos de juzgados reales
   ✅ Commit de lo de la tarde del 15 (760d8a8, push hecho por Diego)
   ✅ 3.5 Cambios a la base de datos (esquema versión 2)
      ✅ Diseño aprobado por Diego
      ✅ Etapa 1. Esquema 2 y crear la base dos veces (pruebas\test_esquema.py)
      ✅ Etapa 2. Carga del banco, 61 avisos y 65 remates (db\carga.py, pruebas\test_carga_banco.py)
      ✅ Etapa 3. Vistas (buscador, alertas, calendario, entregas de vale vista por tribunal y día, historial). pruebas\test_vistas.py
      ✅ Commit de cierre de la 3.5 (34ff86c y el de documentos, sin push)
   ✅ 3.6 Código de formato fijo (motor\extraccion.py, función extraer). Validación limpia contra el 6 de Octubre, 7 equivocados de 360 datos. Tras 3 arreglos, 1 (discutible). Fecha, hora y tribunal con 0 equivocados
   ✅ 3.6b Cortador. Separa "EXTRACTO. ANTE EL SEÑOR JUEZ Árbitro", "JUEZ ÁRBITRO" y "15° JUZGADO CIVIL" sin punto antes. Medido señal por señal en 8 rollos, solo cambiaron los casos esperados (06-10 de 107 a 110). Banco de validación renumerado (60 a 62 registros). Bitácora del 15, punto 45
   ✅ Commit de la 3.6b (da8fa69 a 95788f5, push hecho)
   ✅ Unión del motor con la base (motor\procesar_edicion.py). El 14 de Octubre cargado por el motor calza con el banco salvo diferencias explicadas. El 13 de Octubre cargado en base de prueba. Bitácora del 16
   ✅ Commit de la unión (bc6f6bc y 9a3a438, push hecho)
   ✅ Unión de los rollos B y G sin duplicar, por huella del texto (09-10, 127 avisos y no 254). Las 7 ediciones capturadas cargan en bases de prueba. Bitácora del 16, puntos 10 a 18
   ✅ Commit de la unión B y G (d283e2e, push hecho)
   ✅ Guion al final de renglón. Solo se une la palabra cortada. Desaparecen 52 alertas falsas de rol en las 7 ediciones. Bancos corregidos sin borrar lo anterior. Bitácora del 16, puntos 19 a 25
   ✅ Commit del arreglo del guion (6907224, push hecho)
   🔄 3.7 IA solo donde el código no alcanza. Modelo Claude Haiku 5.5 (precios verificados el 16 de Octubre, Sonnet descartado). Bitácora del 16, puntos 26 a 32
      ✅ Diseño de la 3.7a (regla del vale vista) aprobado por Diego, con doble lectura, ámbar y cita con tolerancia solo de espacios
      ✅ Validación del vale vista anotada antes del código (banco_vale_vista_2026-10-06.json, 62 registros)
      ✅ Commit de la anotación (ad1e2cc, 5a48459 y 5bb64fe, sin push)
      ✅ 3.7a Código y ajuste con el 14 de Octubre (vv-2, sin razonamiento). 53 aciertos, 4 en rojo, 0 equivocados. Bitácora del 16, puntos 33 a 36
      ✅ Commit del código congelado (e328e5a, 6188890 y 0e0a242)
      ✅ VALIDACIÓN contra el 6 de Octubre (145b481). Cifra honesta 44 aciertos, 14 en rojo, 1 equivocado de 59 (aviso 80, ámbar con un día tarde). Bitácora del 16, punto 37
      ✅ Arreglo del día de la semana aplicado (punto 38). Con él, 0 equivocados en los dos bancos (no cambia la cifra honesta)
      ✅ Commit del arreglo (997ad22) y push de 8 commits (origin/master = 997ad22)
      ✅ Diseño de la unión del vale vista a la carga APROBADO (bitácora del 16, punto 42)
      ✅ Commit de los documentos de los puntos 38 a 42 (6677c88, sin push)
      ✅ Código de la unión escrito y probado (bitácora del 16, puntos 43 a 48). 14 de Octubre desde la base 53, 4, 0. Commits 2a70c30 y 05fc6bf, push hecho
      ✅ (La medición de validación contra el 6 de Octubre ya está hecha, punto 37)
      ✅ Textos del rojo en palabras simples con su grupo, y retomar el vale vista de una edición ya cargada (bitácora del 17, puntos 1 a 14). Falta commit
      ✅ Feriados 2027 provisorios, calculados por ley y validados contra 2026 (bitácora del 17, puntos 25 a 29). Esperar la lista oficial
      ✅ Banco de rojos para el análisis semanal (banco_rojos, 84 registros y 51 textos únicos de 7 ediciones, bitácora del 17, puntos 20 a 23). Análisis acumulativo en banco_rojos\ANALISIS_ROJOS.md
   ✅ 3.7b Dirección e inmueble (bitácora del 17, puntos 30 a 46)
      ✅ Paso 1. Inscripción en el Conservador por código, solo para saber qué propiedad es cuál (decisión de Diego). Etiqueta de las listas arreglada (lote 4 del aviso 30 del 14-10). Los 26 remates del C-5656-2013 del 01-09 en 26 bienes. Commit 096bf02
      ✅ Paso 2. Bancos de dirección anotados antes de las instrucciones (validación 06-10 y ajuste 14-10). Commit 74d065d
      ✅ Paso 3. motor\direccion.py (dir-2) congelado. Ajuste 14-10 60, 1, 0. Commit fd55aa4
      ✅ Paso 4. VALIDACIÓN contra el 06-10 (859e190). Cifra honesta 57 aciertos, 2 no leídos, 3 equivocados de 62 remates. Unión a la carga, retomar y banco de rojos (8082f92)
      ✅ Arreglo de la comuna sacada de la frase del Conservador aplicado con la aprobación de Diego (bitácora del 17, punto 47). Con él 06-10 59, 2, 1 y 14-10 60, 1, 0. La cifra honesta sigue siendo 57, 2, 3
   ✅ 3.7c Carátula (bitácora del 17, puntos 48 a 55). Solo código, sin IA. Ajuste 14-10 57 de 57. VALIDACIÓN 06-10, cifra honesta 57 aciertos, 2 no leídos, 0 equivocados de 59. Unida a la carga y a las vistas
      ✅ Arreglo de "Cía. Ltda" aplicado con la aprobación de Diego (punto 56). 06-10 58, 1, 0. La cifra honesta sigue siendo 57, 2, 0
✅ Motor parte 4. Cuadre de cuentas y republicaciones (bitácora del 17, puntos 57 a 63). Alerta de dos roles, cambios solo de valor a valor, arreglo de la clave vacía sin_rol||, calendario con el dato anterior si el nuevo está pendiente
✅ Marcha blanca del 15, 16 y 17 de Octubre en base de prueba, con push 1659555 (bitácora del 17, puntos 64 a 68). Arreglados 2 cambios falsos de dirección y las fechas de las alertas en palabras
✅ Una sola alerta de error de escritura cuando la fecha del remate ya pasó (bitácora del 17, punto 69)
✅ Arreglos traídos del traspaso al Mercurio (bitácora del 18, puntos 1 a 14). Cortador con "EXTRACTO 3°JUZGADO" (Buin y Viña del Mar separados), tribunal con "TRIBUNAL CIVIL", sin palabra pegada a la ciudad y con "Viña del Mar" (línea _TRIBUNAL igual al Mercurio). Regla de las dos fechas con la opción C de Diego (una fecha anterior a la edición no cuenta). 18 avisos cambian en las 10 ediciones capturadas, todos los esperados
⬜ (Pendiente menor) Reutilizar la lectura de Haiku cuando el aviso se republica igual con otros espacios (ahorro de 1,5%, Diego lo dejó para después)
✅ Tres cambios al motor del 18 de Octubre (bitácora del 18, puntos 26 a 29). Modalidad sin falsos mixtos, alerta de costumbre del tribunal en la garantía (el 21° Civil pide 20%) y porcentaje impreso sin el signo %
✅ Nuevo llamado separado de los cambios de fecha (bitácora del 18, puntos 31 a 33)
✅ Sincronización. Edición sin remates anotada y motor\sincronizacion.py (bitácora del 18, puntos 37 a 39)
✅ Interfaz con buscador, calendario, alertas y link a la página (incluye agregar una causa a mano al calendario, idea de Diego del 15 de Octubre)
   ✅ Diseño, variante B en Claude Design (bitácora del 18, puntos 15 a 40)
   ✅ Tablas, servidor local y página (commit 1c365d4, bitácora del 18, puntos 41 a 45)
   ✅ Prueba completa sobre interfaz_prueba.db y revisión con pantallazos (puntos 46 a 49)
   ✅ Primera revisión de Diego. Filtro por tribunal, mes actual y siguiente, acceso del escritorio, vale vista en el remate y texto de las alertas (puntos 50 a 58)
   ✅ Diego la probó con "Abrir Agenda (prueba).bat" y la dio por cerrada el 18 de Octubre (bitácora del 18, punto 62)
   🔄 Ensayo con la edición del 18 de Octubre en la base de prueba. Cargado con Haiku el 20 de Octubre (bitácora del 18, puntos 63 y 64), falta que Diego lo mire
   ✅ Links a cada aviso en las tablas de cambios (bitácora del 21, punto 4)
✅ Descarte de tribunales no civiles (bitácora del 21, puntos 5 a 8)
⬜ Primera carga en la base real (sesión con Claude Code antes)
🔄 Lector diario en la nube (bitácora del 20). La nube lee y llama a Haiku, el PC baja y carga al abrir la agenda
   ✅ Diseño de Diego (dos mitades, actualización obligatoria al abrir, de 6:30 a 8:35)
   ✅ Proyecto Supabase Agendar_Calendario y bucket privado "agendar"
   ✅ Cinco secretos en GitHub (MERCURIO_USER, MERCURIO_PASS, ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY)
   ✅ Código de la nube (servidor\diario.py, servidor\estado.py, .github\workflows\diario.yml) y prueba 18 (pruebas\test_servidor.py)
   ✅ Código del PC (interfaz\nube.py, /api/actualizar, pantalla obligatoria al abrir) y prueba 19 (pruebas\test_nube.py)
   ⬜ Diego agrega SUPABASE_URL, SUPABASE_KEY y CARGA_REAL_APROBADA a su config.py
   ✅ Sesión con Claude Code. Push 6b3055d y dos ensayos en verde (20 de Octubre con Haiku, 18 de Octubre idéntico al PC en 8 de 8 páginas). Bitácora del 20, puntos 19 a 24
   ✅ cron-job.org con tres trabajos de 6:30 a 8:35 y Test run fuera de la ventana sin efectos (bitácora del 20, puntos 25 a 27)
   ✅ Primera mañana automática, 21 de Octubre, intento 1 de 6:30 a 6:33, cargada en la agenda de prueba (bitácora del 21)
✅ Traspaso del motor al Mercurio (hecho el 17 de Octubre, D:\Mercurio\MD_Vivos\REPORTE_PUSH_TRASPASO_2026-10-17.md, dado por realizado por Diego el 21 de Octubre). Lecciones nuevas para el Mercurio siguen en BITACORA_TRASPASO_MERCURIO.md
⬜ (Futuro) Google Calendar o celular

## Cómo se corre

En el PC de Diego, desde D:\Agendar_Remates, con el entorno .venv (Python 3.14, playwright 1.60). Credenciales en config.py (fuera de git). Leer una edición. .venv\Scripts\python -m motor.lector_mercurio --fecha AAAA-MM-DD. Pruebas sin internet. .venv\Scripts\python -m pruebas.test_navegacion_logica, .venv\Scripts\python -m pruebas.test_cortador y .venv\Scripts\python -m pruebas.test_banco_nivel2 , .venv\Scripts\python -m pruebas.test_esquema, .venv\Scripts\python -m pruebas.test_carga_banco, .venv\Scripts\python -m pruebas.test_vistas, .venv\Scripts\python -m pruebas.test_banco_validacion, .venv\Scripts\python -m pruebas.test_extraccion , .venv\Scripts\python -m pruebas.test_procesar_edicion, .venv\Scripts\python -m pruebas.test_vale_vista , .venv\Scripts\python -m pruebas.test_union_vale_vista , .venv\Scripts\python -m pruebas.test_feriados , .venv\Scripts\python -m pruebas.test_direccion , .venv\Scripts\python -m pruebas.test_union_direccion , .venv\Scripts\python -m pruebas.test_caratula , .venv\Scripts\python -m pruebas.test_republicaciones , .venv\Scripts\python -m pruebas.test_interfaz , .venv\Scripts\python -m pruebas.test_servidor y .venv\Scripts\python -m pruebas.test_nube (las diecinueve deben terminar en TODO OK, ninguna llama a Haiku ni a Supabase). Abrir la agenda. Doble clic en "Abrir Agenda.bat" (base real agendar_remates.db, puerto 8765) o en "Agenda de Remates.bat" del escritorio (hace lo mismo). Para probar sin tocar la base real, "Abrir Agenda (prueba).bat" (interfaz_prueba.db, puerto 8766). Queda una ventana minimizada con el servidor, que solo atiende a este PC. Al cerrarla se apaga la agenda. Cargar una edición capturada en una base de prueba. .venv\Scripts\python -m motor.procesar_edicion AAAA-MM-DD RUTA_BASE (la base real espera la aprobación de Diego). Desde la parte 3.7a llama a Haiku por los avisos sin respuesta guardada (necesita internet y la clave), y si no puede sigue con lo guardado. Desde la 3.7b lee también la dirección (ia_respuestas\direccion). Con --sin-ia carga como antes. Si Haiku no respondió en todos los avisos, la edición queda con alarma y se termina con .venv\Scripts\python -m motor.procesar_edicion --retomar AAAA-MM-DD RUTA_BASE, sin volver a leer el Mercurio (retoma el vale vista y la dirección). Banco de rojos. .venv\Scripts\python -m motor.banco_rojos AAAA-MM-DD --desde-captura (o con RUTA_BASE), nunca llama a Haiku. Medición aparte con .venv\Scripts\python -m pruebas.medir_extraccion 14 (o 06). Dirección con .venv\Scripts\python -m pruebas.medir_direccion 14 (o 06), solo con lo guardado. Carátula con .venv\Scripts\python -m pruebas.medir_caratula 14 (o 06). Para medir un cambio del cortador en las 7 fechas capturadas. .venv\Scripts\python -m pruebas.foto_cortador sacar NOMBRE y luego comparar ANTES DESPUES (fotos en banco_pruebas\fotos_cortador).

## Próximo paso (al abrir un chat nuevo)

Reescrito el 21 de Octubre (tarde). Lo de antes está en las bitácoras.

1. Pedir a Diego el permiso para borrar archivos en D:\Agendar_Remates (git borra sus archivos de bloqueo). El permiso expira entre sesiones. Confirmar con git log el último commit local. GitHub quedó en 6b1c7ea (push hecho por Diego en PowerShell el 21 de Octubre, porque el sistema de permisos de Claude Code bloqueó el git push como "Data Exfiltration"). Los commits se firman como DFNR2026 con git -c user.name y user.email.
2. Correr las diecinueve pruebas y verificar TODO OK antes de tocar nada. Repetirlas después de cambiar cualquier base que una prueba use de referencia (interfaz_prueba.db, interfaz_prueba_antes_18oct.db). Ninguna prueba llama a Haiku.
3. Revisar REPORTE_CC_PUSH_2_2026-10-21.md. Claude Code debía verificar con git ls-remote, lanzar el ensayo del flujo con la fecha 2026-10-21 y completar el reporte. Si quedó parcial, ese ensayo está pendiente.
4. Revisar en Supabase (proyecto hkxxufbzerkbdpjaowrz, bucket agendar) que la nube siga leyendo cada mañana (marcas/AAAA-MM-DD.json). Desde Claude se ve con mcp__Supabase__execute_sql sobre storage.objects (nombres, horas y tamaños, no el contenido).
5. LO QUE SIGUE. Primera carga en la base real agendar_remates.db (hoy vacía, 0 ediciones). Decisiones que tomar con Diego antes. Qué ediciones entran (la nube solo tiene desde el 21 de Octubre en marcas/ y la agenda baja los últimos 30 días, las capturas del PC van del 1 de Septiembre al 21 de Octubre). Si va antes una sesión con Claude Code (acordado el 17 de Octubre). Después se pone CARGA_REAL_APROBADA = True en config.py (lo hace Diego) y la agenda real se actualiza sola al abrir. Respaldar la base vacía antes.
6. Otros pendientes, ninguno urgente. Feriados 2027 oficiales (provisorios por ley). Preguntas al abogado (PREGUNTAS_ABOGADO.md, la 9 es el "desde" del vale vista). Diseño de las visitas al tribunal. Ejemplo 9 de las instrucciones del vale vista de Haiku (cambiarlo obliga a leer todo de nuevo). Aviso de GitHub de Node 20 en actions/checkout@v4 y setup-python@v5. Vencimiento de la llave de GitHub "cron-job Agendar" (Diego anotó la fecha). Avisos que terminan con "EXTRACTO DE". Decidir si el Mercurio también descarta los tribunales no civiles (BITACORA_TRASPASO_MERCURIO.md). Los archivos temporales CARGAR_ENSAYO_18_OCT.bat y LEER_MERCURIO_18_OCT.bat ya no se usan. Google Calendar o celular, a futuro.
7. Ediciones del 19 y 20 de Octubre. No están en la base de prueba ni como marca real en la nube (el 20 solo en pruebas/ensayo). Se pueden leer a mano con el flujo en modo real si Diego lo pide.

## Forma de trabajo con Diego

Español latinoamericano neutro, sin voseo. Sin dos puntos ni punto y coma al redactar.
Los meses JAMÁS se escriben en número (Noviembre o Nov., nunca 11). Vale para el chat, las planillas, los informes y la interfaz del programa. Pedido de Diego del 2026-10-15.
Los prompts de apertura de un chat nuevo se entregan en el chat, en un recuadro para copiar y pegar. Nunca en archivos .md. Pedido de Diego del 15 de Octubre.
Ir paso a paso, con el mapa "Dónde estamos" al cerrar hitos.
Separar lo verificado de lo supuesto y dar un porcentaje de confianza cuando sea menor a 90%. Ningún arreglo sin causa raíz con evidencia.
Diego no ejecuta comandos. El código lo hace Claude o Cline (prompts en un solo bloque, y Cline siempre deja un reporte .md al final).
CAMBIO de Diego (17 de Octubre). Claude Code se usa SOLO cuando es necesario. Los commits los hace Claude en el PC de Diego (Diego le da permiso para borrar archivos al comienzo de cada sesión, porque git borra sus archivos de bloqueo). Claude Code queda para UNA VEZ POR SEMANA, o antes de algo importante como la primera carga en la base real (decisión de Diego del 17 de Octubre). Corre las pruebas con el .venv real, hace el push con el "apruebo push" de Diego y deja su reporte .md. El shell de Claude no tiene la clave de GitHub ni llega a la API de Anthropic. (Antes, desde el 15 de Octubre, commit y push iban siempre por Claude Code.) Último push 1659555 (17 de Octubre, noche).
Al cerrar un trabajo, listar lo que se puso sin que Diego lo confirmara.

# ESTADO DEL PROYECTO AGENDAR_REMATES (documento vivo)

Última actualización 16 de Octubre de 2026, diseño de la 3.7a y validación del vale vista anotada. Bitácoras en BITACORA_2026-10-14.md, BITACORA_2026-10-15.md (puntos 1 a 45) y BITACORA_2026-10-16.md. Este archivo es la fuente de verdad del proyecto. Todo chat nuevo debe leerlo completo antes de proponer nada. Cuando algo cambie, se actualiza aquí y se deja constancia en la bitácora de la sesión.

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
Garantía cuyo aviso no dice sobre qué se calcula (ej. "caución del 10%"). Decisión de Diego. Se asume el mínimo y el HUD lo muestra destacado como ASUMIDO, porque el aviso no lo dice. Ojo. El art. 494 del Código de Procedimiento Civil habla del 10% "de la valoración de dichos bienes", no del mínimo (pregunta 11 al abogado).
Interfaz en HTML servida por un programa local en Python con base SQLite.
La regla del vale vista se interpreta desde el texto de cada aviso, nunca se asume por la costumbre del tribunal. La historia del tribunal solo sirve como alarma cuando un aviso dice algo distinto.
Republicaciones. Se guarda cada publicación y se avisa si cambian las bases entre una y otra.
Sincronizar con Google Calendar o el celular queda para una etapa futura.
Las entregas de vale vista se organizan por tribunal, porque es a donde Diego debe ir. Si dos remates agendados del mismo tribunal tienen la entrega el mismo día, el calendario los muestra juntos en una sola tarea (tribunal, día, cantidad de vales vista y roles). Idea acordada el 2026-10-15 para la interfaz.
CORRECCIÓN de Diego (15 de Octubre, tarde). El calendario muestra la fecha del remate y la ventana completa del vale vista (desde y hasta). Diego decide qué día ir, el programa nunca elige por él. Al marcar el vale vista como entregado, la ventana deja de mostrarse para ese remate. Lo que junta remates del mismo tribunal se llama "visita al tribunal", no tarea. Cómo agrupar está por diseñar. Observación de Diego. Las restricciones son una mezcla (solo martes y jueves, horarios distintos, 72 horas desde la hora del remate, día anterior exacto), así que no basta cruzar tramos de días. Cada vale vista debe pasar a su lista de días y horarios permitidos antes de cruzarse. Por ahora v_entregas_vv es provisoria.
El "desde" del vale vista cuando el aviso solo dice hasta cuándo. Diego cree que es desde el mismo día de la publicación. Pregunta 9 al abogado. Mientras tanto sigue la regla del día siguiente.
Todo remate agendado sin fecha de vale vista se avisa en el HUD como dato faltante que Diego debe resolver.
Agenda sin estado "descartado". Si Diego no irá a un remate, lo quita del calendario con un botón X. A Diego le indican a qué remate ir, por eso ningún aviso se elimina por filtros. Los que no pasan quedan visibles como "fuera de filtro". EXCEPCIÓN (Diego, 2026-10-15). Los remates de JUEZ PARTIDOR se descartan del todo y no aparecen en la búsqueda. Incluye los remates de partición ante juez o jueza ÁRBITRO (decisión del 15 de Octubre, noche). Regla PARTICION en db\carga.py.
Rol sin guion después de la letra (C2461-2022). Se avisa como detalle menor, con tono normal (decisión del 15 de Octubre, noche). CORRECCIÓN del 16 de Octubre. El ejemplo C2461-2022 era falso (el diario imprime "Rol C-" y "2461-2022" en dos renglones y el programa borraba el guion). La decisión sigue, con ejemplos reales como "C 19087-2024" y "C8834-2022".
Feriados de Chile cargados desde fuente oficial y aviso en diciembre si falta el año siguiente.
La lectura debe ser perfecta por diseño. La IA nunca tiene la última palabra. Lo de formato fijo (rol, montos, fechas) lo lee el código. Lo de texto libre lo interpreta la IA citando la frase exacta, y el código verifica que la frase exista. Lo que no se pueda verificar se marca en rojo.
Las 72 horas (y las 24) se cuentan en horas de reloj desde la hora del remate. Si el tope cae en fin de semana o feriado, se adelanta al último horario hábil. Si el aviso solo dice hasta cuándo se entrega el vale vista, el desde es el día siguiente a la edición. Decisiones del 15 de Octubre.
Día hábil provisorio de lunes a viernes sin feriados. El art. 59 del Código de Procedimiento Civil haría hábil el sábado, pero dos tribunales escriben en sus avisos que el día hábil anterior a un lunes es el viernes. Queda como pregunta para el abogado (PREGUNTAS_ABOGADO.md).
Cada remate debe mostrar en su ficha las alertas de su aviso (errores de escritura, roles mal impresos, contradicciones, condiciones raras como garantía del 20% o sobre la tasación, caución sin vale vista, aviso previo por correo) y el link directo a su página del Mercurio. Pedido de Diego del 15 de Octubre. Un error del aviso podría usarse para anular el remate.
No se parcha el Mercurio del abogado ahora. El motor de lectura se construye aquí, se prueba con el banco de pruebas y después se traspasa al Mercurio de una sola vez.

## Base de datos

Ver db\LEEME_BASE_DATOS.md. Versión 2 del esquema (15 de Octubre), con 12 tablas y 5 vistas. Un aviso puede traer varios remates y cada remate apunta a un bien (causa más inmueble). La agenda va por remate.

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
      ⬜ Commit de la anotación (Claude Code), antes de escribir instrucciones o código
      ⬜ 3.7a Código. Instrucciones para Haiku ajustadas solo con el 14 de Octubre, verificador, cálculo de fechas (motor\vale_vista.py), respuestas guardadas
      ⬜ 3.7a Medición de validación una sola vez contra el 6 de Octubre
      ⬜ 3.7b Dirección e inmueble ⬜ 3.7c Partes
⬜ Motor parte 4. Cuadre de cuentas
⬜ Interfaz con buscador, calendario, alertas y link a la página (incluye agregar una causa a mano al calendario, idea de Diego del 15 de Octubre)
⬜ Traspaso del motor al Mercurio (guía en BITACORA_TRASPASO_MERCURIO.md)
⬜ (Futuro) Google Calendar o celular

## Cómo se corre

En el PC de Diego, desde D:\Agendar_Remates, con el entorno .venv (Python 3.14, playwright 1.60). Credenciales en config.py (fuera de git). Leer una edición. .venv\Scripts\python -m motor.lector_mercurio --fecha AAAA-MM-DD. Pruebas sin internet. .venv\Scripts\python -m pruebas.test_navegacion_logica, .venv\Scripts\python -m pruebas.test_cortador y .venv\Scripts\python -m pruebas.test_banco_nivel2 , .venv\Scripts\python -m pruebas.test_esquema, .venv\Scripts\python -m pruebas.test_carga_banco, .venv\Scripts\python -m pruebas.test_vistas, .venv\Scripts\python -m pruebas.test_banco_validacion, .venv\Scripts\python -m pruebas.test_extraccion y .venv\Scripts\python -m pruebas.test_procesar_edicion (las nueve deben terminar en TODO OK). Cargar una edición capturada en una base de prueba. .venv\Scripts\python -m motor.procesar_edicion AAAA-MM-DD RUTA_BASE (la base real espera la aprobación de Diego). Medición aparte con .venv\Scripts\python -m pruebas.medir_extraccion 14 (o 06). Para medir un cambio del cortador en las 7 fechas capturadas. .venv\Scripts\python -m pruebas.foto_cortador sacar NOMBRE y luego comparar ANTES DESPUES (fotos en banco_pruebas\fotos_cortador).

## Próximo paso (al abrir un chat nuevo)

1. Confirmar con git log el commit del arreglo del guion (hecho en Claude Code, reporte REPORTE_COMMIT_GUION_2026-10-16.md) y si se hizo el push. El push solo con "apruebo push" de Diego.
2. Correr las nueve pruebas y verificar TODO OK antes de tocar nada.
3. HECHO el 16 de Octubre (guion al final de renglón). Pendientes chicos vistos en la 3.6b, cada uno como paso aparte y solo si Diego lo pide. Falsa alarma de dos fechas en el 09-10 aviso 120 ("subasta ... resolución del 4 de septiembre", es de extraccion.py). "Juez Partidor" en minúsculas pegado en el 01-09. Detalle en la bitácora del 15, punto 45.
4. HECHO el 16 de Octubre (motor\procesar_edicion.py), con la unión de los rollos B y G por huella del texto. Pendientes que dejó. Inmueble del lote 4 del aviso 30 del 14-10. Decidir cuándo se carga la base real.
5. Parte 3.7a. Verificar el commit de la anotación de la validación (reporte REPORTE_COMMIT_ANOTACION_VV_2026-10-16.md). Luego escribir el código con Haiku 5.5 (clave en config.py), ajustado solo con el 14 de Octubre, y medir una vez contra el 6 de Octubre. Diseño en la bitácora del 16, puntos 27 y 28.
6. Decisiones abiertas de Diego. El "desde" del vale vista (pregunta 9 al abogado). Diseño de las visitas al tribunal (lista de días y horarios permitidos por vale vista).
7. Parte 4. Cuadre de cuentas y republicaciones (más de la mitad de los avisos se repiten al día siguiente, punto 33 de la bitácora del 15).
8. Pendiente menor. Algunos avisos terminan con "EXTRACTO DE", que es el comienzo del aviso siguiente.

Nota. "qué usa IA.png" es un pantallazo de Diego para recordar dónde se usa IA en el proyecto. Es de referencia personal y no va a git.

## Forma de trabajo con Diego

Español latinoamericano neutro, sin voseo. Sin dos puntos ni punto y coma al redactar.
Los meses JAMÁS se escriben en número (Noviembre o Nov., nunca 11). Vale para el chat, las planillas, los informes y la interfaz del programa. Pedido de Diego del 2026-10-15.
Los prompts de apertura de un chat nuevo se entregan en el chat, en un recuadro para copiar y pegar. Nunca en archivos .md. Pedido de Diego del 15 de Octubre.
Ir paso a paso, con el mapa "Dónde estamos" al cerrar hitos.
Separar lo verificado de lo supuesto y dar un porcentaje de confianza cuando sea menor a 90%. Ningún arreglo sin causa raíz con evidencia.
Diego no ejecuta comandos. El código lo hace Claude o Cline (prompts en un solo bloque, y Cline siempre deja un reporte .md al final).
Commit y push SIEMPRE en Claude Code, con prompt y reporte .md (decisión de Diego del 15 de Octubre). El shell de Claude en el PC no tiene la clave de GitHub. Pendiente. Push de 34ff86c y 45d6a50.
Al cerrar un trabajo, listar lo que se puso sin que Diego lo confirmara.

# ESTADO DEL PROYECTO AGENDAR_REMATES (documento vivo)

Última actualización 15 de Octubre de 2026, cierre de la parte 3.5. Bitácoras en BITACORA_2026-10-14.md y BITACORA_2026-10-15.md (esta última tiene la madrugada y la tarde, puntos 1 a 21). Este archivo es la fuente de verdad del proyecto. Todo chat nuevo debe leerlo completo antes de proponer nada. Cuando algo cambie, se actualiza aquí y se deja constancia en la bitácora de la sesión.

## Qué es

Programa visual para que Diego agende los remates judiciales de propiedades a los que decide ir. Flujo acordado.
1. Se lee completa la edición del día de El Mercurio (sección 1616 Remates de propiedades).
2. De cada aviso se extrae la fecha del remate, si es por Zoom o presencial, la regla del vale vista tal como la dice ese aviso (fecha exacta o rango), el monto mínimo y la garantía.
3. Todo queda en una base de datos. Diego busca por rol o tribunal en la edición elegida (por defecto la del día), elige un remate y recién ahí se marcan en su calendario la fecha del vale vista y la del remate.

## Decisiones tomadas por Diego

Carpeta madre D:\Agendar_Remates. D:\Mercurio es solo fuente de consulta y no se modifica.
Corre en el PC de Diego. No se descarta otro PC a futuro, así que rutas relativas y configuración en un solo archivo.
Se mantienen los filtros originales del Mercurio (solo RM, no BancoEstado, no Estación Central, rol desde 2018, dominio anterior a 2020), aplicados después de leer. La lectura nunca se salta avisos.
Interfaz en HTML servida por un programa local en Python con base SQLite.
La regla del vale vista se interpreta desde el texto de cada aviso, nunca se asume por la costumbre del tribunal. La historia del tribunal solo sirve como alarma cuando un aviso dice algo distinto.
Republicaciones. Se guarda cada publicación y se avisa si cambian las bases entre una y otra.
Sincronizar con Google Calendar o el celular queda para una etapa futura.
Las entregas de vale vista se organizan por tribunal, porque es a donde Diego debe ir. Si dos remates agendados del mismo tribunal tienen la entrega el mismo día, el calendario los muestra juntos en una sola tarea (tribunal, día, cantidad de vales vista y roles). Idea acordada el 2026-10-15 para la interfaz.
CORRECCIÓN de Diego (15 de Octubre, tarde). El calendario muestra la fecha del remate y la ventana completa del vale vista (desde y hasta). Diego decide qué día ir, el programa nunca elige por él. Al marcar el vale vista como entregado, la ventana deja de mostrarse para ese remate. Lo que junta remates del mismo tribunal se llama "visita al tribunal", no tarea. Cómo agrupar está por diseñar. Observación de Diego. Las restricciones son una mezcla (solo martes y jueves, horarios distintos, 72 horas desde la hora del remate, día anterior exacto), así que no basta cruzar tramos de días. Cada vale vista debe pasar a su lista de días y horarios permitidos antes de cruzarse. Por ahora v_entregas_vv es provisoria.
El "desde" del vale vista cuando el aviso solo dice hasta cuándo. Diego cree que es desde el mismo día de la publicación. Pregunta 9 al abogado. Mientras tanto sigue la regla del día siguiente.
Todo remate agendado sin fecha de vale vista se avisa en el HUD como dato faltante que Diego debe resolver.
Agenda sin estado "descartado". Si Diego no irá a un remate, lo quita del calendario con un botón X. A Diego le indican a qué remate ir, por eso ningún aviso se elimina por filtros. Los que no pasan quedan visibles como "fuera de filtro". EXCEPCIÓN (Diego, 2026-10-15). Los remates de JUEZ PARTIDOR se descartan del todo y no aparecen en la búsqueda.
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
PREGUNTAS_ABOGADO.md. Nueve dudas legales pendientes, cada una con su regla provisoria.
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
   ⬜ 3.6 Código que saca lo de formato fijo, medido contra el banco nivel 2
   ⬜ 3.7 DeepSeek V4-Flash contra el Haiku más moderno, solo donde el código no alcance, con precios vigentes
⬜ Motor parte 4. Cuadre de cuentas
⬜ Interfaz con buscador, calendario, alertas y link a la página
⬜ Traspaso del motor al Mercurio (guía en BITACORA_TRASPASO_MERCURIO.md)
⬜ (Futuro) Google Calendar o celular

## Cómo se corre

En el PC de Diego, desde D:\Agendar_Remates, con el entorno .venv (Python 3.14, playwright 1.60). Credenciales en config.py (fuera de git). Leer una edición. .venv\Scripts\python -m motor.lector_mercurio --fecha AAAA-MM-DD. Pruebas sin internet. .venv\Scripts\python -m pruebas.test_navegacion_logica, .venv\Scripts\python -m pruebas.test_cortador y .venv\Scripts\python -m pruebas.test_banco_nivel2 , .venv\Scripts\python -m pruebas.test_esquema, .venv\Scripts\python -m pruebas.test_carga_banco y .venv\Scripts\python -m pruebas.test_vistas (las seis deben terminar en TODO OK).

## Próximo paso (al abrir un chat nuevo)

1. Confirmar con git log los commits de cierre de la 3.5 (34ff86c y el de documentos). El push solo con "apruebo push" de Diego.
2. Correr las seis pruebas y verificar TODO OK antes de tocar nada.
3. Parte 3.6. El código saca lo de formato fijo (rol, tribunal, fechas, horas, montos, porcentajes) y se mide contra el banco nivel 2. Primero el diseño para Diego, después el código. Requisitos ya anotados. El tribunal se guarda en una forma única (ordinal en número), porque el diario lo escribe también en palabras. La salida usa el formato del banco nivel 2 para entrar directo a db\carga.py.
4. Decisiones abiertas de Diego. El "desde" del vale vista cuando el aviso solo dice hasta cuándo (pregunta 9 al abogado). El diseño de las visitas al tribunal (cada vale vista como lista de días y horarios permitidos), que va con la interfaz.
5. Riesgo anotado para la parte 4. Contar fechas de remate por aviso y marcar los que traigan más de una (red de seguridad para avisos pegados que el cortador no vea). En la parte 4 también se mide la regla de republicaciones con las 7 fechas.
6. Pendiente menor. Algunos avisos terminan con "EXTRACTO DE", que es el comienzo del título del aviso siguiente. No cambia datos.

Nota. "qué usa IA.png" es un pantallazo de Diego para recordar dónde se usa IA en el proyecto. Es de referencia personal y no va a git.

## Forma de trabajo con Diego

Español latinoamericano neutro, sin voseo. Sin dos puntos ni punto y coma al redactar.
Los meses JAMÁS se escriben en número (Noviembre o Nov., nunca 11). Vale para el chat, las planillas, los informes y la interfaz del programa. Pedido de Diego del 2026-10-15.
Los prompts de apertura de un chat nuevo se entregan en el chat, en un recuadro para copiar y pegar. Nunca en archivos .md. Pedido de Diego del 15 de Octubre.
Ir paso a paso, con el mapa "Dónde estamos" al cerrar hitos.
Separar lo verificado de lo supuesto y dar un porcentaje de confianza cuando sea menor a 90%. Ningún arreglo sin causa raíz con evidencia.
Diego no ejecuta comandos. El código lo hace Claude o Cline (prompts en un solo bloque, y Cline siempre deja un reporte .md al final).
Al cerrar un trabajo, listar lo que se puso sin que Diego lo confirmara.

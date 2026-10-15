# Base de datos de Agendar_Remates

Diseño aprobado por Diego el 2026-10-14. Archivo SQLite agendar_remates.db en la raíz del proyecto (fuera de git, porque contiene texto del diario y datos de trabajo). Se crea o actualiza con python db\crear_base.py, que no borra nada si la base ya existe.

## Los siete cajones

1. ediciones. Cada diario leído, sus cuerpos revisados, cuántos roles contó el código en el texto, cuántos avisos quedaron y las alarmas. Si los números no cuadran, el estado queda "con_alarmas".
2. paginas. Texto completo y huella SHA-256 de cada página con remates. Es la evidencia para auditar cualquier dato.
3. avisos. Una fila por publicación. Todos los avisos quedan, también los que no pasan los filtros, que se marcan "fuera_filtro" con su motivo y siguen apareciendo en la búsqueda.
4. citas. Por cada dato de un aviso, la frase exacta del diario, quién lo sacó (código o IA) y si el código comprobó la frase. Un dato sin cita comprobada se muestra en rojo.
5. causas y cambios. La causa une todas las publicaciones de un mismo remate con la llave rol-año más tribunal. Si una publicación nueva cambia un dato respecto de la anterior, queda registrado en cambios y el calendario lo avisa hasta que Diego lo marque como visto.
6. agenda. Los remates que Diego elige. Quitar uno del calendario es borrar su fila (botón X). Casillas opcionales de vale vista entregado y remate asistido. El calendario siempre muestra los datos de la publicación más reciente.
7. feriados. Necesarios para calcular reglas como "el viernes anterior, o el día hábil anterior si ese viernes es feriado" (regla real del 15° Juzgado Civil, vista en el aviso del rol C-12980-2023). Se cargan desde archivos db\feriados_AAAA.csv. Desde diciembre el programa avisa si falta el año siguiente.

No existe un cajón de reglas por tribunal. La vista v_historial_tribunal calcula lo habitual de cada tribunal desde sus avisos y solo se usa como alarma.

## Prueba hecha al crearla

Base creada dos veces seguidas sin errores (no duplica nada). Una causa con dos publicaciones de fechas distintas mostró en el calendario la fecha más nueva y un cambio sin ver. Un valor inválido de modalidad fue rechazado. La alarma de feriados aparece en diciembre si falta el año siguiente.

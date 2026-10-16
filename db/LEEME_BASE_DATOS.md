# Base de datos de Agendar_Remates

Versión 2 del esquema, aprobada por Diego el 15 de Octubre de 2026 (parte 3.5). La versión 1 era del 14 de Octubre. Archivo SQLite agendar_remates.db en la raíz del proyecto (fuera de git, porque contiene texto del diario y datos de trabajo). Se crea o actualiza con python db\crear_base.py, que no borra datos y se niega a tocar una base de otra versión.

## La idea central

Un aviso es lo que se imprime. Un remate es lo que se agenda. Un aviso puede traer varios remates (el aviso 30 del 14 de Octubre trae 4 lotes, cada uno con su mínimo). Cada remate apunta a un bien (causa más inmueble), que es la identidad que sobrevive a las republicaciones. Así Diego puede agendar un solo lote, y si una republicación cambia la fecha queda como cambio y no como remate nuevo.

## Las tablas

1. ediciones. Cada diario leído, cuántos roles contó el código en el texto, cuántos avisos y remates quedaron y las alarmas.
2. paginas. Texto completo, huella SHA-256 y ruta de cada página con remates (ej. /2026/10/14/C/L64MFDBT). El link directo es la dirección base de config.py más la ruta. El código de página no tiene formato fijo.
3. avisos. Una fila por publicación, con lo común a sus remates (texto, rol, tribunal, partes, filtros, página donde empieza y donde termina). Ningún aviso se bota. filtro_estado puede ser pasa, fuera_filtro (se ve marcado con su motivo) o descartado (JUEZ PARTIDOR, decisión de Diego, no aparece en ninguna vista y existe solo para el cuadre de cuentas).
4. remates. Una fila por remate dentro del aviso. Fecha, hora, modalidad (zoom, presencial, mixta, en_linea, sin_dato) y plataforma, mínimo y costas, garantía (porcentaje, base mínimo o tasación, monto fijo) y vale vista (regla, desde, hasta y estado).
5. bienes. La identidad estable. Si la causa trae un solo remate se une por causa. Si trae varios, por número de depto, lote u oficina. Si no calza, alerta en vez de adivinar.
6. citas. Por cada dato, la frase exacta del diario, quién lo sacó (código o IA) y si el código comprobó la frase. Una cita puede ser de un remate o del aviso completo, y un dato puede tener varias frases.
7. alertas. Lo que la ficha del remate debe destacar junto al link. Errores del aviso (error_escritura, rol_mal_impreso, contradiccion), condiciones del tribunal (condicion_especial, aviso_previo), dudas de lectura (revisar_lectura) y posible_republicacion.
8. causas. El juicio, con la llave rol-año más tribunal.
9. cambios. Lo que cambió entre dos publicaciones de un mismo bien, hasta que Diego lo marque como visto.
10. agenda. Los remates que Diego elige, uno por bien. Quitar uno del calendario es borrar su fila (botón X). Casillas opcionales de vale vista entregado y remate asistido.
11. feriados. Se cargan desde db\feriados_AAAA.csv. Desde diciembre el programa avisa si falta el año siguiente.
12. meta. Versión del esquema.

## Las vistas (ninguna muestra los avisos descartados)

v_buscador. Un renglón por remate visible, para buscar por rol o tribunal en la edición elegida, con sus links y cuántas alertas tiene.
v_alertas. Las alertas con su link, marcando cuáles son errores del aviso.
v_calendario. Los remates agendados con los datos de su publicación visible más reciente y los cambios sin ver.
v_entregas_vv. Una tarea por tribunal y día del plazo final del vale vista, con la cantidad de vales vista y los roles. Los remates sin fecha de vale vista se ven en el calendario.
v_historial_tribunal. Lo habitual de cada tribunal, contado por aviso. Solo sirve como alarma, nunca como regla.

Las fechas salen como AAAA-MM-DD. La interfaz debe mostrarlas con el mes en palabras (Nov.), nunca en número.

## Cómo se carga una edición

db\carga.py guarda una edición completa en una sola transacción (si falta un aviso no carga nada, y no carga dos veces la misma edición). Recibe los avisos del cortador y lo extraído en el formato del banco nivel 2. El rol mal impreso lo detecta el código. db\cargar_banco.py carga el banco del 14 de Octubre solo en bases de prueba. Desde el 16 de Octubre motor\procesar_edicion.py carga una edición leída por el motor (corte, extraer() y traducción al formato del banco). Sus citas van con método codigo, sus alertas con el tipo que les da el código, y mientras no exista la parte 3.7 cada remate lleva la alerta "El programa todavía no lee la regla del vale vista de este aviso". Las ediciones con dos rollos (B y G los viernes) se unen sin duplicar por la huella del texto de cada aviso (solo letras y números), se guardan las páginas de los dos cuerpos y la columna alarmas de ediciones lleva el resumen de la unión. Un aviso con rol pero sin tribunal se guarda sin causa y con alerta, porque la causa exige tribunal.

## Pruebas

pruebas\test_esquema.py (crear dos veces, valores aceptados y rechazados), pruebas\test_carga_banco.py (61 avisos, 65 remates, 431 citas) y pruebas\test_vistas.py (buscador, calendario, entregas, republicación, partidor forzado, botón X) y pruebas\test_procesar_edicion.py (el 14 de Octubre cargado por el motor contra el banco). Las cuatro con prueba de mutación.

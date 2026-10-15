# ESTADO DEL PROYECTO AGENDAR_REMATES (documento vivo)

Última actualización 2026-10-14 (cierre de sesión). Bitácora de la sesión en BITACORA_2026-10-14.md. Este archivo es la fuente de verdad del proyecto. Todo chat nuevo debe leerlo completo antes de proponer nada. Cuando algo cambie, se actualiza aquí y se deja constancia en la bitácora de la sesión.

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
Agenda sin estado "descartado". Si Diego no irá a un remate, lo quita del calendario con un botón X. A Diego le indican a qué remate ir, por eso ningún aviso se elimina por filtros. Los que no pasan quedan visibles como "fuera de filtro".
Feriados de Chile cargados desde fuente oficial y aviso en diciembre si falta el año siguiente.
La lectura debe ser perfecta por diseño. La IA nunca tiene la última palabra. Lo de formato fijo (rol, montos, fechas) lo lee el código. Lo de texto libre lo interpreta la IA citando la frase exacta, y el código verifica que la frase exista. Lo que no se pueda verificar se marca en rojo.
No se parcha el Mercurio del abogado ahora. El motor de lectura se construye aquí, se prueba con el banco de pruebas y después se traspasa al Mercurio de una sola vez.

## Base de datos

Ver db\LEEME_BASE_DATOS.md. Siete cajones. Ediciones, Páginas, Avisos, Citas, Causas con sus cambios, Mi agenda y Feriados.

## Evidencia reunida (leer antes de diseñar o cambiar la lectura)

AUDITORIA_LECTURA_MERCURIO_2026-10-14.md. Por qué falla la lectura actual del Mercurio (avisos partidos entre páginas y entre trozos, avisos sin rol botados en silencio, datos cruzados entre avisos vecinos, redirección "PÁGINA C 8" no detectada, historial que congela errores).
RECONOCIMIENTO_EDICIONES_2026-10-14.md. Dónde aparecen los remates en 36 ediciones y cómo se continúan. Base de las reglas de navegación.
banco_pruebas\LEEME_BANCO_PRUEBAS.md. Ediciones 2026-08-06 y 2026-10-14 con su inventario correcto (153 avisos) y la lista de trampas del diario.

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
✅ Banco de pruebas nivel 1 (153 avisos)
✅ Prototipo de rollo único y corte por aviso
✅ Reconocimiento de 36 ediciones y reglas de navegación
✅ Respaldo en GitHub privado DFNR2026/AgendarRemates (commit 7f68909, huellas verificadas en clon)
✅ Proyecto propio en Claude
✅ Base de datos diseñada y probada (db\esquema.sql, ver db\LEEME_BASE_DATOS.md)
✅ Motor parte 1, navegación (motor\navegacion_logica.py y motor\lector_mercurio.py). 15 pruebas sin internet y 7 fechas en vivo con 0 alarmas, huellas idénticas al banco
⬜ Motor parte 2. Rollo único y corte por aviso
⬜ Motor parte 3. Extracción con citas
⬜ Motor parte 4. Cuadre de cuentas
⬜ Banco de pruebas nivel 2 (fechas, modalidad, vale vista, montos)
⬜ Interfaz con buscador y calendario
⬜ Traspaso del motor al Mercurio
⬜ (Futuro) Google Calendar o celular

## Cómo se corre

En el PC de Diego, desde D:\Agendar_Remates, con el entorno .venv (Python 3.14, playwright 1.60). Credenciales en config.py (fuera de git). Leer una edición. .venv\Scripts\python -m motor.lector_mercurio --fecha AAAA-MM-DD. Pruebas sin internet. .venv\Scripts\python -m pruebas.test_navegacion_logica

## Forma de trabajo con Diego

Español latinoamericano neutro, sin voseo. Sin dos puntos ni punto y coma al redactar.
Ir paso a paso, con el mapa "Dónde estamos" al cerrar hitos.
Separar lo verificado de lo supuesto y dar un porcentaje de confianza cuando sea menor a 90%. Ningún arreglo sin causa raíz con evidencia.
Diego no ejecuta comandos. El código lo hace Claude o Cline (prompts en un solo bloque, y Cline siempre deja un reporte .md al final).
Al cerrar un trabajo, listar lo que se puso sin que Diego lo confirmara.

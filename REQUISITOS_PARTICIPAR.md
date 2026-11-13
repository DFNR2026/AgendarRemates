# Requisitos para participar en un remate, además del vale vista

Documento de la investigación del 13 de Noviembre de 2026, guardado a pedido de Diego para no repetir el trabajo. Lo que el programa lee está en motor\requisitos.py. Este archivo explica de dónde salió cada patrón y cómo volver a medir.

## Qué se hizo

Se leyeron los avisos de los 30 Juzgados Civiles de Santiago guardados en la base, ediciones del 21 de Octubre al 12 de Noviembre de 2026. Son 574 causas, contando una vez cada causa con su aviso más nuevo (decisión de Diego, se cuenta por causa y no por aviso). Nunca se llamó a Haiku.
Primera pasada. De cada aviso se sacaron los tramos alrededor de las palabras de requisito, se juntaron las frases iguales por tribunal y Claude leyó las cerca de 850 frases distintas en el chat.
Segunda pasada. Con lo leído se escribieron los patrones fijos de motor\requisitos.py y se midieron contra las mismas 574 causas, comparando con la lectura a mano y corrigiendo cada diferencia.
Límite. Los avisos no se leyeron enteros uno por uno. Un requisito escrito con palabras que no están en ninguna lista no se habría visto.

## Dónde quedó guardado

motor\requisitos.py. Los patrones, con un comentario por cada trampa encontrada.
db\requisitos_patron.json. La tabla medida por tribunal, que la ficha usa para la advertencia de patrón roto. Medida el 13 de Noviembre de 2026.
banco_pruebas\requisitos\frases_por_tribunal.txt. Todas las frases de requisito de cada tribunal, juntando las casi iguales, con su n de causas, su plazo y su correo. Es lo que hay que releer si se duda de un patrón.
pruebas\medir_requisitos.py. Vuelve a medir sobre una copia de la base (con --guardar reescribe la tabla y con --frases reescribe las frases).
pruebas\test_requisitos.py y pruebas\mutaciones_requisitos.py. La prueba con frases reales y sus 20 mutaciones.

## Decisiones de Diego del 13 de Noviembre

Lo de después de adjudicar (firma del acta, pago del saldo, devolución) es interesante pero no es prioridad. Queda para el futuro. Lo encontrado está más abajo para no perderlo.
El Registro de Deudores de Pensiones de Alimentos es totalmente irrelevante. No se lee ni se muestra.
El equipo y el link de Zoom sí se muestran. Cada remate por videoconferencia entrega lo que su aviso dice de la conexión.
Los n van por causa.
El correo que se muestra es el que sale en el aviso de esa causa, aunque sea la casilla personal de un funcionario (3° Civil).
Cada causa muestra lo que dice su propio aviso. Si el tribunal tiene un patrón fuerte y el aviso no lo trae, la ficha advierte que se rompió el patrón. El paso siguiente es buscar en las bases aprobadas o propuestas y, si no está, preguntar al tribunal. No se asume el requisito.

## Lo que se lee

correo. Mandar un correo al tribunal antes del remate, con su dirección y su plazo.
ojv. Trámite previo por la Oficina Judicial Virtual (escrito, comprobante, vale vista digitalizado o módulo de remates).
clave. Clave Única activa o firma electrónica avanzada.
cedula. Copia de la cédula, mostrarla o llevarla vigente.
contacto. Dejar correo y teléfono.
formulario. Formulario, acta predeterminada, documento anexo u hoja de datos al entregar el vale vista.
persona_juridica y tercero. Personería, representante legal, RUT de la sociedad y datos de la persona para quien se compra.
link, link_por_correo, link_en_causa, minutos, camara, equipo y ayuda. La conexión por videoconferencia.

## Trampas verificadas en los avisos

La palabra correo sola no es un requisito. En el 2° y el 26° Civil el correo es para avisar el pago del saldo, en el 8° es para consultas y en el 5° es solo el correo institucional.
En el 29° Civil la frase termina en "por problemas de conexión" y sigue siendo un requisito. Lo que decide es si la consulta va antes o después de la dirección.
El diario parte las direcciones ("xandrade @pjud.cl", "jcsantiago8_ remates@pjud.cl", "22jcivil santiago_remates @pjud.cl") y los links de Zoom.
"El juez firmará con su firma electrónica avanzada" y "el adjudicatario firmará con clave única" no son requisitos para participar.
"Bases y antecedentes en Oficina Judicial Virtual" no es un trámite. Tampoco la carpeta electrónica que llena el ministro de fe (16° y 24°).
"Con indicación del tomador para facilitar su devolución" no es la devolución. El 1° Civil pide datos del "representante de la empresa adjudicataria" antes del remate.
Los avisos telegráficos no ponen comas ni puntos, así que el plazo se corta donde empieza la orden siguiente.
Algunos avisos traen pegado el texto de una demanda ("Tercer Otrosí. Personería"). No se lee.
En el 5° y el 15° hay avisos donde el número del link y el del ID no coinciden. Ahí no se arma el link y se muestra la frase.

## Tabla medida por tribunal

Causas que lo dicen sobre el total del tribunal, medido con los patrones el 13 de Noviembre de 2026. La columna de lectura es el resumen de Claude al leer las frases.

| Tribunal | Causas | Medición | Lectura |
|---|---|---|---|
| 1° | 21 | Clave Única o firma avanzada 1, cédula 12, correo y teléfono 12, formulario o anexo 11 | Presencial. Hoja de datos junto con el vale vista (copia de la cédula por ambos lados, RUT, celular y correo de quien lo trae y de quien hace posturas, banco, monto y quién lo retira). |
| 2° | 15 | cédula 13, correo y teléfono 13, compra para otro 1, link por correo 12 | Zoom. Al entregar el vale vista, copia del carnet, nombre, mail y teléfono para recibir el link. Su correo pasalazar@pjud.cl es para avisar el pago del saldo, no para participar. |
| 3° | 25 | correo previo 23, Oficina Judicial Virtual 23, cédula 1, correo y teléfono 25, formulario o anexo 1, link por correo 24, equipo 1, correo de consultas 1 | Zoom. Correo a xandrade@pjud.cl hasta las 15 horas del día hábil anterior, asunto Remate, con rol y fecha. Además escrito por la Oficina Judicial Virtual con copia del vale vista, correo y teléfono, mismo plazo, bajo apercibimiento de no ser postor. |
| 4° | 15 | correo previo 15, cédula 15, correo y teléfono 13, link por correo 15, equipo 13 | Zoom. Correo a jcsantiago4_remates@pjud.cl con copia del vale vista y de la cédula, nombre, teléfono y correo, hasta las 14.00 del día hábil anterior. El link solo llega a quien entregó el vale vista y mandó el correo. |
| 5° | 15 | Oficina Judicial Virtual 14, Clave Única o firma avanzada 2, cédula 1, correo y teléfono 14, persona jurídica 1, link o ID en el aviso 14, equipo 2, correo de consultas 8 | Zoom. Copia de la caución por la Oficina Judicial Virtual con rol, correo y teléfono, hasta las 14.00 del día hábil anterior. Link de Zoom fijo en el aviso (ID 418 238 0109). |
| 6° | 20 | Oficina Judicial Virtual 17, Clave Única o firma avanzada 14, cédula 1, correo y teléfono 15, link por correo 15, equipo 1 | Zoom. Clave Única activa. Correo y teléfono para la invitación. Si la garantía es cupón de pago, se sube por la Oficina Judicial Virtual hasta las 12.30 del día hábil anterior. La invitación solo llega a quien tiene la garantía calificada. |
| 7° | 39 | Clave Única o firma avanzada 37, cédula 38, correo y teléfono 34, link o ID en el aviso 29, equipo 1 | Zoom. Al presentar el vale vista, registrar correo, exhibir la cédula y dejar copia simple de la cédula y del vale vista. Clave Única o firma electrónica avanzada. |
| 8° | 16 | correo de consultas 6 | Presencial. Ninguno. Su correo jcsantiago8_remates@pjud.cl es solo para consultas. |
| 9° | 27 | correo previo 1, Oficina Judicial Virtual 1, Clave Única o firma avanzada 1, cédula 24, correo y teléfono 8, persona jurídica 24, link o ID en el aviso 27, link por correo 1, entrar minutos antes 11, equipo 14 | Zoom. Copia de la cédula del postor y del representante legal al entregar, a veces con rol, correo y teléfono escritos en la copia. Link fijo en el aviso (ID 641 324 8095). Entrar 5 minutos antes para la identificación. |
| 10° | 12 | cédula 1, correo y teléfono 1, persona jurídica 1 | Presencial. Ninguno regular. |
| 11° | 16 | cédula 16, persona jurídica 1 | Presencial. Fotocopia de la cédula del tomador junto con el vale vista. |
| 12° | 23 | Oficina Judicial Virtual 22, Clave Única o firma avanzada 19, persona jurídica 5, link o ID en el aviso 21, equipo 18 | Zoom. Vale vista digitalizado por la Oficina Judicial Virtual, módulo Audiencia de remates. Revisar con Clave Única en Mis Remates que el tribunal aceptó al postor y recién ahí entregar el vale vista. Persona jurídica muestra a la cámara el RUT de la sociedad. |
| 13° | 20 | correo previo 19, Oficina Judicial Virtual 13, Clave Única o firma avanzada 1, correo y teléfono 13, link por correo 10, equipo 8 | Zoom. Correo a jcsantiago13_remates@pjud.cl para coordinar, con plazo a las 14.00 del día hábil anterior en parte de los avisos. Escrito por la Oficina Judicial Virtual con copia del vale vista, correo y teléfono, a las 14.00 en unos avisos y a las 15.00 en otros. |
| 14° | 12 | nada | Presencial. Ninguno. |
| 15° | 16 | correo previo 14, Clave Única o firma avanzada 3, correo y teléfono 13, link o ID en el aviso 1, equipo 1 | Zoom. Dos correos a jcsantiago15@pjud.cl. Uno avisando quién irá a dejar el vale vista. Otro hasta las 14.00 del día hábil anterior, asunto Remate, manifestando la intención de participar. |
| 16° | 19 | Clave Única o firma avanzada 2, correo y teléfono 17, formulario o anexo 17, link por correo 7, entrar minutos antes 3, equipo 18, correo de consultas 17 | Zoom. Acta predeterminada que se firma al presentar el vale vista, con correo y teléfono. Problemas de conexión a jcsantiago16_remates@pjud.cl. En algunos, conectarse 10 minutos antes. |
| 17° | 24 | correo previo 6, Clave Única o firma avanzada 4, cédula 2, correo y teléfono 6, persona jurídica 2, compra para otro 14 | Presencial. Patrón débil. En 6 causas, correo a jcsantiago17_remates@pjud.cl (2 de ellas a mrisopatron@pjud.cl con copia a jcsantiago17@pjud.cl) con comprobante de la garantía, cédula, correo y teléfono antes de las 12.00 del día anterior. Datos de la persona por quien se presenta. |
| 18° | 35 | correo previo 3, Clave Única o firma avanzada 2, correo y teléfono 35, persona jurídica 13, compra para otro 13, link en la causa 12, equipo 19 | Zoom. Al entregar el vale vista, correo y teléfono. Persona jurídica, datos del representante y personería con firma electrónica verificable. El link se publica en la causa a más tardar el día anterior. |
| 19° | 18 | Oficina Judicial Virtual 15, Clave Única o firma avanzada 4, cédula 15, correo y teléfono 8, formulario o anexo 8, link o ID en el aviso 17, entrar minutos antes 1, cámara encendida 7, equipo 5, correo de consultas 3 | Zoom. Vale vista digitalizado por la Oficina Judicial Virtual, por el módulo Remates con formulario de postulación o con escrito Acompaña documento, con copia de la cédula. Cámara encendida, micrófono abierto y mostrar la cédula. Link fijo (ID 402 206 0537). |
| 20° | 20 | correo previo 1, Clave Única o firma avanzada 2, cédula 1, persona jurídica 1, link o ID en el aviso 20, link en la causa 5, equipo 12 | Zoom. Ninguno fuera del equipo. El link viene en el aviso, distinto en cada causa. |
| 21° | 20 | cédula 17, correo y teléfono 17, persona jurídica 17 | Presencial. Copia de la cédula del postor y del representante legal, con correo y teléfono escritos en la copia. |
| 22° | 16 | correo previo 4, Clave Única o firma avanzada 4, cédula 1, correo y teléfono 15, formulario o anexo 14, link o ID en el aviso 16, link en la causa 1, equipo 8 | Zoom. Documento anexo con rol, nombre y RUT del postor y del apoderado, teléfono y correo. El aviso trae el ID de la reunión y en 4 causas hay que pedir el código de acceso a 22jcivilsantiago_remates@pjud.cl. |
| 23° | 13 | Clave Única o firma avanzada 7, cédula 11, correo y teléfono 12, link por correo 8, cámara encendida 1, equipo 6 | Zoom. Con el vale vista, copia simple del anverso de la cédula, rol, monto y número del vale vista, correo y teléfono. Clave Única o firma electrónica avanzada. |
| 24° | 10 | cédula 7, correo y teléfono 1 | Presencial. Cédula de identidad vigente junto con el vale vista. |
| 25° | 1 | Oficina Judicial Virtual 1, Clave Única o firma avanzada 1, correo y teléfono 1 | Zoom. Una sola causa, sin patrón posible. |
| 26° | 6 | cédula 1, formulario o anexo 6, compra para otro 6 | Presencial. Formulario de participación que se llena al entregar el vale vista. Su correo es para avisar el pago del saldo. |
| 27° | 19 | Oficina Judicial Virtual 1, Clave Única o firma avanzada 17, formulario o anexo 18, link o ID en el aviso 19, equipo 1 | Zoom. Formulario al entregar el vale vista. Clave Única activa. Link fijo (ID 946 4227 3947). |
| 28° | 41 | correo previo 4, Clave Única o firma avanzada 29, correo y teléfono 36, compra para otro 4, link por correo 16, cámara encendida 6, equipo 23 | Zoom. Al entregar el vale vista, identidad, rol, correo y teléfono. Clave Única o firma electrónica avanzada. El link llega por correo el día previo. En 4 causas, comprobante al correo jcsantiago28@pjud.cl hasta las 12.00 del día anterior. |
| 29° | 25 | correo previo 23, Oficina Judicial Virtual 24, Clave Única o firma avanzada 17, cédula 21, correo y teléfono 21, link o ID en el aviso 24, equipo 14 | Zoom. Comprobante de la caución por el módulo de la Oficina Judicial Virtual y correo a jcsantiago29_remates@pjud.cl hasta las 12.00 del día hábil anterior (si es sábado, el viernes), con copia de la cédula por ambos lados, rol, correo y teléfono. |
| 30° | 15 | Clave Única o firma avanzada 13, cédula 15, correo y teléfono 15, link por correo 11, equipo 4 | Zoom. Copia digitalizada del carnet, nombre, email y teléfono con al menos 24 horas de anticipación. Clave Única activa. El link llega por correo solo cumplidos los trámites. |

## Patrones fuertes

Regla puesta por Claude y sin confirmar por Diego. Un requisito es patrón fuerte si lo dice al menos el 80% de las causas del tribunal y el tribunal tiene al menos 10 causas medidas. Solo avisan correo, Oficina Judicial Virtual, Clave Única, cédula, contacto, formulario, link en el aviso y link por correo.

2° Civil. cédula 13 de 15, correo y teléfono 13 de 15, link por correo 12 de 15.
3° Civil. correo previo 23 de 25, Oficina Judicial Virtual 23 de 25, correo y teléfono 25 de 25, link por correo 24 de 25.
4° Civil. correo previo 15 de 15, cédula 15 de 15, correo y teléfono 13 de 15, link por correo 15 de 15.
5° Civil. Oficina Judicial Virtual 14 de 15, correo y teléfono 14 de 15, link o ID en el aviso 14 de 15.
6° Civil. Oficina Judicial Virtual 17 de 20.
7° Civil. Clave Única o firma avanzada 37 de 39, cédula 38 de 39, correo y teléfono 34 de 39.
9° Civil. cédula 24 de 27, link o ID en el aviso 27 de 27.
11° Civil. cédula 16 de 16.
12° Civil. Oficina Judicial Virtual 22 de 23, Clave Única o firma avanzada 19 de 23, link o ID en el aviso 21 de 23.
13° Civil. correo previo 19 de 20.
15° Civil. correo previo 14 de 16, correo y teléfono 13 de 16.
16° Civil. correo y teléfono 17 de 19, formulario o anexo 17 de 19.
18° Civil. correo y teléfono 35 de 35.
19° Civil. Oficina Judicial Virtual 15 de 18, cédula 15 de 18, link o ID en el aviso 17 de 18.
20° Civil. link o ID en el aviso 20 de 20.
21° Civil. cédula 17 de 20, correo y teléfono 17 de 20.
22° Civil. correo y teléfono 15 de 16, formulario o anexo 14 de 16, link o ID en el aviso 16 de 16.
23° Civil. cédula 11 de 13, correo y teléfono 12 de 13.
27° Civil. Clave Única o firma avanzada 17 de 19, formulario o anexo 18 de 19, link o ID en el aviso 19 de 19.
28° Civil. correo y teléfono 36 de 41.
29° Civil. correo previo 23 de 25, Oficina Judicial Virtual 24 de 25, cédula 21 de 25, correo y teléfono 21 de 25, link o ID en el aviso 24 de 25.
30° Civil. Clave Única o firma avanzada 13 de 15, cédula 15 de 15, correo y teléfono 15 de 15.
Sin patrón fuerte quedan 1°, 8°, 10°, 14°, 17°, 24°, 25°, 26°.

## Pendiente futuro, después de adjudicar

Decisión de Diego del 13 de Noviembre. No se programa ahora. Lo que apareció al leer, para cuando se retome.
7° Civil. El acta llega por correo y se devuelve firmada con firma electrónica avanzada o Clave Única antes de las 16.00 del mismo día, bajo apercibimiento de dejar sin efecto el remate.
18° Civil. El acta se firma con firma electrónica avanzada y se remite antes de las 15.00 a jcsantiago18@pjud.cl, o en persona a más tardar el día siguiente.
5° Civil. Ratificar el acta con un escrito por la Oficina Judicial Virtual dentro de 2 días hábiles, bajo apercibimiento de perder la caución.
9° Civil. El acta se firma solo con firma electrónica avanzada.
28° y 30° Civil. El borrador del acta llega por correo y se ingresa firmado por la Oficina Judicial Virtual (el 28° da 24 horas hábiles).
1° Civil. El acta se firma en persona el mismo día o el día hábil siguiente, salvo quien tenga firma electrónica avanzada.
2° y 26° Civil. Avisar el pago del saldo por correo (pasalazar@pjud.cl y jcsantiago26@pjud.cl).
Devolución del vale vista. 12° de lunes a jueves de 9.00 a 11.00 desde el día siguiente. 15° el viernes siguiente de 12.00 a 13.00 avisando antes por correo. 19° desde el día siguiente de 9.00 a 13.00. 23° el lunes hábil siguiente de 11.00 a 13.00 coordinando por correo. 27° al terminar la actuación.

## Errores de avisos vistos de paso

13° Civil. El plazo del escrito es a las 14.00 en unos avisos y a las 15.00 en otros.
6° Civil, C-14306-2025. Dice vale vista nominativo, distinto al resto del tribunal.
29° Civil, C-5164-2025. Trae pegado en medio del texto "por Eduardo Zenay" con un correo de gmail.
16° Civil. Un aviso escribe jcsantiago16_remtes@pjud.cl, sin la a.
15° Civil. Dos avisos escriben jcsantiago15_@pjud.cl, con un guion bajo de más.

## Cómo volver a medir

En el shell de Claude, sobre una copia de la base fuera de la carpeta. python3 -m pruebas.medir_requisitos RUTA_COPIA --guardar --frases. Conviene repetirlo cuando la base tenga muchas ediciones nuevas, porque la advertencia de patrón roto usa la tabla guardada y no se actualiza sola.

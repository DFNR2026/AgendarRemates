# Reporte de auditoría externa, 30 de Octubre de 2026

Tres auditores independientes, uno por foco, creados desde cero y sin el contexto de la conversación con Diego. Trabajaron solo leyendo, con copias de interfaz_prueba.db fuera de la carpeta del proyecto, sin abrir agendar_remates.db, sin llamar a Haiku ni a Supabase y sin entrar a El Mercurio. Sus secciones van abajo tal como las entregaron. Arriba va la lectura de Claude (la sesión principal) sobre cuánto pesa cada hallazgo, que es una opinión aparte y no cambia lo que dijeron los auditores.

## Medición (auditor del foco 3)
agendar_remates.db, interfaz_prueba.db e ia_respuestas (1.319) quedaron iguales antes y después. Las 19 pruebas TODO OK con el Python 3.10 del shell del PC. En D:\Agendar_Remates no cambió ningún archivo (find -newer, focos 1 y 3). Este reporte es el único archivo nuevo.

## Lectura de Claude. Qué arreglar primero

Corrección a una observación del foco 3. La hora 22:51 de la base real del 29 de Octubre (19:51 de Chile) NO viene de la prueba del apagado de la bitácora del 29, punto 3. Esa prueba corrió con --base sobre una copia de interfaz_prueba.db en $HOME/vis (verificado en los comandos de esa sesión). Lo más probable es el uso normal de Diego ese día (supuesto, 80%).

Grupo 1. Arreglar pronto (pueden costar un remate y el arreglo es acotado)
- F3-01. Respaldo automático diario de la base real. Es lo más barato y protege todo lo demás. Va primero, porque varios arreglos de abajo tocan la base.
- F1-01. Viernes y martes o jueves que caen en feriado. El primero real es el viernes 25 de Diciembre, a menos de dos meses.
- F2-05. Un día que la nube no lee se pierde para siempre y una marca fallida bloquea el reintento a mano.
- F2-06. Páginas sin leer o roles perdidos al cortar no encienden ninguna franja.
- F2-04. El buscador esconde una propiedad cuando el aviso más nuevo trae una fecha ya pasada por error (n = 2 en la base de prueba).
- F3-07. La página no avisa cuando la agenda se apagó por falta de señal. Viene del arreglo del 29 de Octubre y conviene cerrarlo ya.

Grupo 2. Arreglar con más cuidado (alto impacto, pero tocan la carga y las claves de la base)
- F2-01. Una misma propiedad partida en tres bienes. Es C-17115-2025, la causa del martes y jueves que Diego revisó el 22 de Octubre. Requiere rehacer claves, así que después del respaldo.
- F2-02. Falsos "pegados" por una segunda fecha en el aviso (2 causas reales).
- F2-03. Un aviso escondido dentro de otro sin alarma (1 caso real).
- F2-08. Una captura bajada a medias bloquea las actualizaciones y el mensaje culpa a internet.

Grupo 3. Rápidos y útiles
- F1-02 (solo dejar en ámbar las reglas de horas, sin cambiar el cálculo), F1-04 (avisar cuando el aviso solo dice "horario de atención"), F3-03 (que los errores queden en logs\servidor.log), F3-04 (validar las fechas de una causa a mano), F3-06 (la prueba que apunta a la base real) y F3-05 (rechazar pedidos de otras páginas).

Grupo 4. Decide Diego o el abogado
- F1-03. La regla provisoria del 3° Civil (pregunta 6) no se aplica y 16 causas quedan en rojo. Diego decide si vale "de 11 a 12".
- F1-07. La frase del 14° Civil "endosado al momento de la subasta" (7 causas). Para el abogado.
- F2-13. Si un Tribunal Arbitral que no es de partición se descarta.
- F3-08. Cambiar la clave de Supabase del PC por una de solo lectura y sacar de config.py lo que el PC ya no usa. Vale la pena, pero cambia claves y Diego lo hace en Supabase y GitHub.

Grupo 5. Bajo peso o lejano
- F1-05, F1-06, F1-08, F2-07, F2-09, F2-10, F2-11, F2-12, F3-09, F3-10, F3-11, F3-12 y F3-13. Reales pero con 0 a 3 casos o con efecto menor. F3-02 el auditor la puso alta, Claude la baja a media, porque la probabilidad es menor a 5% al año. F2-11 y F3-12 (listar más de 1.000 marcas) recién pasarían hacia 2029.

Coincidencias entre auditores (más confianza). F2-11 y F3-12 son el mismo hallazgo. F2-08 y F3-03 coinciden en que nube.py culpa a internet de cualquier error con "Errno". F1-06 y F2-02 muestran C-11540-2023 por dos lados.

## Sección F1. Cálculo de las fechas del vale vista (auditor 1)

Cómo se midió. Copié el proyecto en $HOME/aud1/copia, sin la base real, sin config.py y sin perfil_navegador. Rearmé los avisos de las 20 ediciones capturadas, del 1 de Septiembre al 29 de Octubre, con desde_captura y extraer. A cada aviso le pasé motor.vale_vista.resolver con su respuesta guardada en ia_respuestas/vale_vista. Son 1.536 apariciones visibles con lectura, 611 textos únicos y 539 causas. También revisé una copia de interfaz_prueba.db abierta en solo lectura, con la misma huella md5 61fa8e67 antes y después. En la copia pasan test_vale_vista, test_union_vale_vista y test_feriados, las tres con TODO OK. No se llamó a Haiku ni a Supabase. En D:\Agendar_Remates no cambió ningún archivo, lo revisé con find -newer.

F1-01. Gravedad alta. La entrega de viernes o de martes y jueves queda en un día feriado
Evidencia. motor/vale_vista.py, líneas 135 a 140. Las reglas viernes_anterior y martes_o_jueves_anterior retroceden hasta el día de la semana pedido y no lo corren si es feriado. Cuando el día no es hábil solo suman la pregunta 2, que trata otra duda. resolver (líneas 337 a 341) tampoco revisa que el hasta caiga en un día hábil. VERIFICADO con las lecturas guardadas reales y la fecha del remate cambiada.
C-10678-2025 del 15° Civil. Un remate el martes 29 de Diciembre de 2026 da hasta el viernes 25 de Diciembre (Navidad) de 12:00 a 13:00, en ámbar.
La misma causa con remate el martes 30 de Marzo de 2027 da el 26 de Marzo, que es Viernes Santo.
C-18621-2024 del 21° Civil. Un remate el miércoles 9 de Diciembre de 2026 da el martes 8 de Diciembre, que es feriado de la Inmaculada Concepción.
C-4080-2021 del 27° Civil. Un remate el lunes 28 de Diciembre da el 25 de Diciembre.
El aviso del 15° Civil dice además en letras "En caso de recaer dicho viernes en día feriado, la entrega deberá efectuarse el día hábil anterior".
n. Hoy hay 0 casos, porque los remates capturados llegan solo al 15 de Diciembre. La regla la usan 17 causas del 15° Civil, 3 del 27° y 15 del 21°. Los próximos viernes feriados son el 25 de Diciembre de 2026, el 1 de Enero, el 26 de Marzo, el 21 de Mayo y el 16 de Julio de 2027.
Consecuencia. Diego va al tribunal en un día feriado y para entonces el último día hábil, el jueves, ya pasó. Pierde el remate.
Sugerencia, sin aplicar. Si el día no es hábil, pasarlo al día hábil anterior. Agregar en resolver una revisión general que deje en rojo cualquier hasta que caiga en un día no hábil, salvo en_el_remate.

F1-02. Gravedad alta. Las reglas de horas salen en verde aunque la pregunta 3 sigue abierta, y la mayoría de los avisos cuenta desde la fecha del remate
Evidencia. vale_vista.py, líneas 116 a 125. La pregunta 3 solo se suma cuando el tope cae en un día no hábil. En los demás casos el resultado va en verde, contado desde la hora del remate.
n. Hay 15 causas con regla de horas y fecha, 13 en verde y 2 en ámbar. En 10 de ellas el aviso dice "a la fecha (fijada para el) remate" o "antes día remate", no "a la hora". Son C-1596-2024, C-1109-2019, C-12567-2006, C-5802-2023, C-3613-2024, C-4474-2024, C-11740-2025, C-8255-2025, C-3668-2022 y C-3783-2026.
Ejemplo C-3668-2022 del 30° Civil, con remate el martes 17 de Noviembre a las 12:30. El programa da hasta el lunes 16 a las 12:30. Si las 24 horas se cuentan desde el comienzo de ese día, el plazo se adelanta al viernes 13.
SUPUESTO, con 30% de confianza en que el tribunal cuente desde la fecha y no desde la hora.
Dos detalles de este mismo grupo, VERIFICADOS.
C-1109-2019 del 1° Civil de San Miguel queda con hasta a las 14:30. Es después del cierre de las 14:00 que el mismo programa supone (HORA_CIERRE_SUPUESTA), n = 1.
C-12567-2006 trae en el aviso el horario de 9:00 a 14:00. La IA lo leyó y el cálculo de horas lo ignora, n = 1.
Además, en 5 causas del 30° Civil (C-12384-2023, C-2665-2025, C-4474-2024, C-11740-2025 y C-8255-2025) las 24 horas salen de la frase de la copia del carnet, que dice "Además, entregar copia digitalizada...". SUPUESTO, con 70% de confianza en que esa frase sí incluye el vale vista.
Consecuencia. Una fecha en verde que puede llegar un día hábil tarde.
Sugerencia, sin aplicar. Dejar siempre la regla de horas en ámbar con la pregunta 3. Avisar cuando la frase diga "fecha" o "día". Topar la hora en el horario del aviso o en el cierre supuesto.

F1-03. Gravedad media. El 3° Civil no aplica la regla provisoria de la pregunta 6
Evidencia. PREGUNTAS_ABOGADO.md, pregunta 6, dice "Provisorio. De 11 a 12". El código deja estos avisos en rojo y sin fecha (vale_vista.py, líneas 236 a 244), porque toma "hasta las 12 hrs." como una contradicción. VERIFICADO.
n. 16 causas del 3° Civil, 46 apariciones (40 por dos plazos y 6 porque las dos lecturas de la IA no coinciden).
Consecuencia. Diego anota a mano 16 fechas, y el programa no hace lo que dice el archivo de preguntas.
Sugerencia, sin aplicar. Que Diego decida. Si vale la regla provisoria, poner un caso propio que dé de 11:00 a 12:00 en ámbar con la pregunta 6.

F1-04. Gravedad media. "Horario de atención" queda sin hora y sin aviso fuera de la regla de días hábiles
Evidencia. vale_vista.py, línea 350. La pregunta 4 solo se suma en dias_habiles_antes. VERIFICADO.
n. 4 causas en verde, sin hora y sin pregunta.
C-14842-2019 del 15° Civil, que dice "en horario de atención a público hasta el día viernes de la semana anterior".
C-10397-2025, C-13168-2025 y C-16323-2025 del 9° Civil, que dicen "dentro del horario de funcionamiento".
Ojo. Según la bitácora del 22 de Octubre (punto 18), Diego agendó C-14842-2019 en la base real. Su hasta es el viernes 30 de Octubre, que es hoy, y la hora tope es desconocida. SUPUESTO, con 60% de confianza en que siga agendada y sin entregar, porque no abrí la base real.
[Nota de Claude. Revisado en la base real abierta solo para leer el 30 de Octubre en la madrugada. La agenda no tiene causas agendadas, así que ese riesgo no aplica.]
Consecuencia. Diego puede llegar después del cierre.
Sugerencia, sin aplicar. Sumar la pregunta 4 en cualquier regla cuya frase traiga "horario de atención" o "funcionamiento", y mostrar el cierre supuesto.

F1-05. Gravedad media. No se revisa el plazo vencido al publicarse ni un desde posterior al hasta
Evidencia. vale_vista.py, líneas 337 a 341 (solo se revisa fecha_fija) y línea 112. VERIFICADO por simulación con la lectura real de C-12384-2023. Con edición el lunes 2 de Noviembre y remate el martes 3, da desde el 3 y hasta el 2 de Noviembre a las 12:30, en verde. Con un plazo de 3 días hábiles, remate el lunes 2 de Noviembre y edición el viernes 30 de Octubre, da hasta el 28 de Octubre en verde.
n. 0 de 1.536 apariciones reales.
Consecuencia. Una ventana imposible o ya vencida sale en verde. texto_vv (interfaz/datos.py, línea 89) escribiría "Desde 3 Nov hasta 2 Nov".
Sugerencia, sin aplicar. Rojo si el hasta es anterior a la edición. Si el desde estimado queda después del hasta, ajustarlo o avisar.

F1-06. Gravedad media. Rojo falso cuando la excepción del aviso nombra el viernes
Evidencia. vale_vista.py, líneas 345 a 348. Ejemplo C-11540-2023 del 29° Civil (ediciones del 23 y 24 de Octubre, remate el 11 de Noviembre). El aviso dice "hasta las 12:00 hrs. del día hábil anterior ... y si dicho día fuera sábado ... del viernes". El cálculo da martes y la revisión exige viernes. Otro caso es C-956-2024 de Punta Arenas, con "de lunes a viernes en horario". VERIFICADO.
n. 2 causas, 3 apariciones.
Consecuencia. No da fecha a pesar de que la regla está bien leída.
Sugerencia, sin aplicar. No contar los días que aparecen en una excepción de sábado ni en "de lunes a viernes".

F1-07. Gravedad media. Avisos que quedan sin dato aunque el vale vista se entrega en la subasta
Evidencia. Hay 7 causas del 14° Civil que dicen "vale vista tomado a propia orden, susceptible de ser endosado al momento de la subasta". Son C-13445-2025, C-13854-2024, C-16213-2025, C-20073-2024, C-21141-2023, C-4567-2026 y C-6701-2021. Todas quedan en sin_dato. Además C-23164-2024 del 10° Civil (edición del 24 de Octubre) queda en sin_dato aunque trae "calificados al momento de hacerse el llamado". Ese caso es efecto del ejemplo 9 de las instrucciones, que ya figura como pendiente, y contradice la decisión del 18 de Octubre. El conteo está VERIFICADO. Que el 14° Civil sea una entrega en el remate es SUPUESTO, con 65% de confianza.
Consecuencia. Ocho causas quedan como dato faltante y Diego las revisa a mano.
Sugerencia, sin aplicar. Llevar la frase del 14° Civil a Diego o al abogado. Cuando la IA diga sin_dato y el aviso traiga la frase de "calificados", pasarlo a en_el_remate.

F1-08. Gravedad baja. El desde estimado cae en un día no hábil
Evidencia. vale_vista.py, línea 112. Se suma un día de calendario a la edición. VERIFICADO.
n. 95 causas, 137 apariciones.
Consecuencia. La ventana parte un sábado, un domingo o un feriado.
Sugerencia, sin aplicar. Pasarlo al día hábil siguiente, o dejarlo como está hasta la respuesta de la pregunta 9.

Recuento de lo ya conocido, sin tratarlo como nuevo
"El jueves (inmediatamente) anterior" del 22° Civil. Aparece en 17 causas, 11 de ellas con lectura guardada, y las 11 quedan en rojo sin fecha. La IA las repartió en dia_anterior (6, incluida C-19837-2024), viernes_anterior (3, que son C-15434-2024, C-22529-2024 y C-5783-2025), dias_habiles_antes (1, C-1194-2018) y martes_o_jueves_anterior (1, C-7083-2024). Ninguna dio una fecha equivocada.
Casos parecidos de un solo día en el 21° Civil. C-18510-2019 dice "día jueves anterior" y queda en rojo. C-5201-2025 dice "el día martes anterior" y no tiene lectura.
martes_o_jueves_anterior con un solo día. Son 15 causas del 21° Civil en ámbar (8 remates de martes, 4 de lunes, 2 de jueves y 1 de viernes). Hay además 2 causas del 21° Civil en rojo.
Patrones parecidos sin regla propia.
El 27° Civil dice "hasta el día lunes de la semana anterior" en 6 causas. Solo C-9218-2025 tiene lectura y queda en rojo como "otra".
El 13° Civil dice "lunes o miércoles anterior" en 12 causas. 3 dan un verde correcto porque el aviso agrega "día hábil anterior, esto es". Las otras 9 quedan en rojo.
El 24° Civil dice "lunes precedente y si fuere feriado el martes siguiente" en C-7384-2022, que queda en rojo.

Revisado sin problemas
En las 1.536 apariciones hay 0 con el hasta después del remate, 0 en un día no hábil, 0 con el desde después del hasta y 0 con el hasta antes de la edición.
Hay 0 frases con hora explícita cuyo hasta quede sin hora, fuera de lo de F1-04.
Remates de lunes. Con día hábil anterior da viernes, con día anterior da viernes con la pregunta 2, y las variantes de sábado a viernes y de sábado a hábil dan viernes. Remate el martes con el lunes feriado. La simulación del 29 de Junio de 2027 da el 25 de Junio.
Regla de horas con el tope en fin de semana o feriado. La simulación del lunes 28 de Diciembre a las 13:00 da el 24 de Diciembre a las 14:00 con la pregunta 3.
Feriados 2026 completos. Los provisorios de 2027 calzan con la ley, incluidos San Pedro y San Pablo el 28 de Junio, el Encuentro de Dos Mundos el 11 de Octubre y el día de los Pueblos Indígenas el 21 de Junio.
El viernes "de la semana anterior" del 27° Civil se calcula bien.
El remate como lugar de entrega y la fecha fija.
Las preguntas 1, 2, 5, 7 y 9 se aplican tal como dice PREGUNTAS_ABOGADO.md.
En rojo nunca se guardan fechas (bloque_vale_vista en procesar_edicion.py, línea 103). retomar_vale_vista usa el mismo resolver.
texto_vv y tipo_vv de interfaz/datos.py concuerdan con lo calculado.

Ideas de mejora
1. Ligada a F1-01 y F1-05. Poner una revisión final única en resolver (hasta hábil, no anterior a la edición, desde no posterior al hasta) y sumar a test_vale_vista casos con los feriados de Diciembre y de Semana Santa.
2. Ligada a F1-02 y F1-04. Guardar un horario tope por regla (el del aviso o el cierre supuesto) y dejar en ámbar todo plazo cuya hora no esté escrita en el aviso.

Lo que no alcancé a revisar. La base real, que está prohibida. Los avisos sin respuesta guardada (todo el 1 de Septiembre y parte del 6 al 13 de Octubre). v_entregas_vv y la vista del calendario con el dato de una publicación anterior.

## Sección F2. Causas que entran o se pierden (auditor 2)

Base de la medición. No abrí agendar_remates.db. Trabajé en $HOME/aud2 del shell del PC (fuera de mnt) con una copia de interfaz_prueba.db (md5 61fa8e67, 12 ediciones) y con una base nueva armada desde capturas del 21 al 29 de Octubre usando solo respuestas guardadas, sin cliente de Haiku (real_sim.db, 9 ediciones, 872 avisos, 843 remates visibles, 0 avisos sin leer por la IA). Esa base debería ser igual a la real porque usa el mismo código y las mismas capturas (SUPUESTO 90%). No escribí nada en D:\Agendar_Remates, no llamé a Haiku ni a Supabase y no entré a El Mercurio.

F2-01. Gravedad alta. Una misma propiedad queda partida en tres bienes y la agenda deja de seguir sus publicaciones.
Evidencia. db\carga.py, líneas 292 a 307. La clave del bien es solo la causa cuando la causa trae un remate ese día, y es causa más inscripción cuando trae dos. Si las dos identidades chocan se agrega fecha y hora a la clave. Caso real C-17115-2025 del 21° Civil (remate el 9 de Noviembre). El 21, 22, 25 y 26 de Octubre sale una vez y queda en el bien 59. El 23 y el 24 de Octubre sale dos veces en la misma edición (avisos 66 y 69 el 23, avisos 87 y 91 el 24, con "rol" y "Rol"), y eso crea los bienes 127 y 128. En el buscador salen 3 tarjetas de la misma propiedad. Agendé el bien 59 en una copia y su ficha muestra 4 publicaciones (21, 22, 25 y 26), sin el 23 ni el 24.
VERIFICADO en real_sim.db. n = 1 causa de 268 en las 9 ediciones reales y 0 de 510 en interfaz_prueba.db.
Consecuencia. Si el aviso del 23 o del 24 hubiera cambiado la fecha, el calendario del bien 59 no lo habría comparado y no saldría el aviso grande. Si Diego agendó el bien 127 o el 128, su agenda quedó congelada en el 24 de Octubre, y todo lo que se publique después (cambio de fecha o nuevo llamado) va al bien 59 sin avisarle. El mismo riesgo existe con causas de dos propiedades que hoy salen juntas (13082-2023, 7747-2025, 18937-2023, 4327-2026). Si un día sale solo un departamento, pasa a la clave de causa sola y nace otro bien.
Sugerencia. Que la clave no dependa de cuántos remates trae la causa ese día. Usar siempre causa más inscripción (o el inmueble) cuando exista, y tomar como el mismo bien dos avisos de una edición con la misma identidad, en vez de agregarles fecha y hora. Requiere rehacer las claves de la base con respaldo antes.

F2-02. Gravedad alta. La regla de las dos fechas marca como "pegados" avisos que son uno solo, y esos remates quedan sin fecha, sin tribunal y sin vale vista.
Evidencia. motor\extraccion.py (regla de "más de una fecha", con la opción C solo se ignoran fechas pasadas) y procesar_edicion.py, líneas 155 y 284 (los pegados no van a Haiku). C-5618-2025 del 13° Civil, remate el 10 de Diciembre, marcado como pegado el 25, 26, 27 y 28 de Octubre porque el aviso trae también el 9 de Diciembre. C-11540-2023 del 29° Civil, 22 de Octubre aviso 81, remate el 11 de Noviembre y subastas del inmueble y del vehículo el 12. En el buscador los dos salen como "Sin fecha" y "Sin tribunal", y buscar el tribunal "13" no encuentra el 5618-2025 (probado con datos.buscar). Además el 5618-2025 quedó en 2 bienes porque su clave es la huella del texto y el aviso del 26 trae un " EXTRACTO." de más.
VERIFICADO leyendo cada texto. n = 7 publicaciones marcadas como pegadas en 9 ediciones reales. 5 de ellas (2 causas) son falsas alarmas, 1 es un pegado real (ver F2-03) y 1 es dudosa (Tribunal Arbitral, 24 de Octubre aviso 119).
Consecuencia. Un remate civil real con su fecha escrita nunca entra con fecha al calendario. No aparece cuando se busca por tribunal y Diego debe leerlo a mano.
Sugerencia. Que la segunda fecha cuente para el pegado solo si viene con otro comienzo de tribunal o con otro rol, o si las dos van con verbo de remate o subasta. Mientras tanto, mostrar en la tarjeta que el aviso quedó como posible pegado.

F2-03. Gravedad alta. Un aviso escondido dentro de otro no hace saltar ninguna alarma.
Evidencia. El 27 de Octubre el aviso 81 trae juntos el C-15893-2024 (20° Civil, 12 de Enero de 2027) y el C-18510-2019 (10 de Noviembre). Ese día el C-18510-2019 no tiene registro propio (sí lo tenía el 24, 25 y 26). El cortador anota el motivo "dos roles distintos en un mismo trozo y no se encontró dónde partir" (motor\cortador.py, líneas 199 a 213), pero ese motivo no se guarda en ninguna parte (no se usa en db ni en procesar_edicion). El cuadre (motor\republicaciones.py, líneas 60 a 69) solo revisa que cada rol quede dentro de algún aviso, así que un rol escondido en otro aviso cuenta como presente.
VERIFICADO. n = 1 pegado real de 843 remates visibles. El mismo motivo del cortador sale 5 veces en 20 capturas.
Consecuencia. Si es la primera publicación de un remate, ese remate no existe en el buscador ni buscando por su rol. Si es una republicación, un cambio de fecha hecho ese día no se compara.
Sugerencia. Guardar el motivo del cortador como alerta del aviso y separar en el cuadre los roles que quedaron como rol principal de los que quedaron solo dentro del texto de otro aviso.

F2-04. Gravedad alta. El buscador esconde una propiedad cuando su aviso más nuevo trae una fecha ya pasada por error del secretario.
Evidencia. interfaz\datos.py, función buscar, condición fecha_remate IS NULL OR fecha_remate >= hoy sobre la publicación más nueva. C-5633-2024 del 28° Civil el 15 de Octubre (imprimió 26 de Mayo de 2026) y C-20712-2024 del 12° Civil el 6 de Octubre (imprimió 20 de Octubre de 2025, 4 lotes). Con hoy igual a la fecha de esa edición, el buscador por defecto da 0 resultados para los dos, y solo salen marcando "pasados".
VERIFICADO con datos.buscar sobre una copia. n = 2 causas (5 remates) de 550 propiedades en interfaz_prueba.db. En las dos el aviso siguiente corrigió la fecha.
Consecuencia. Si el aviso con la fecha mal escrita es el único o el último publicado, la propiedad desaparece de la búsqueda normal justo cuando el error es más grave.
Sugerencia. Si la fecha del remate es anterior a la edición, dejar la tarjeta entre los vigentes con la fecha marcada como dudosa en rojo.

F2-05. Gravedad alta. Un día que la nube no lee se pierde para siempre, y una marca fallida impide incluso el reintento a mano.
Evidencia. servidor\diario.py, línea 111 (si hay marca no se hace nada) y línea 190 (sin FECHA la edición es la de hoy). El cuerpo de cron-job.org no manda fecha. En .github\workflows\diario.yml el paso "Mirar si la edición ya quedó hecha" responde 200 también con una marca fallida y corta el flujo, así que Run workflow en modo real con esa fecha tampoco la vuelve a leer. Si no queda marca (cron-job.org no dispara, GitHub cae o los 7 intentos terminan con código 1), nadie vuelve a pedir ese día. En el PC la franja negra muestra el día faltante solo 7 días (motor\sincronizacion.py, VENTANA = 7) y después desaparece sin dejar rastro. Una edición que El Mercurio publique después de las 8:35 queda fallida.
VERIFICADO en el código. La pérdida es una estimación (SUPUESTO 70%) que simulé sacando días de interfaz_prueba.db entre el 9 y el 18 de Octubre (n = 9 ediciones, falta el 12 y los bordes inflan). Propiedades con remate futuro que no vuelven a publicarse. 1 día perdido da de 0 a 4. 2 días seguidos dan de 2 a 6. 3 días seguidos dan de 6 a 24 en los días del medio. Con 10 días seguidos se perderían casi todas las propiedades que se publicaron por primera vez en ese tramo, porque cada una sale de 3 a 4 veces en pocos días (85 y 54 de 158).
Consecuencia. Remates futuros que nunca llegan al buscador, sin aviso después de una semana. Aparte, si el PC pasa más de 30 días sin abrir la agenda (DIAS_ATRAS), las ediciones más viejas se saltan sin ningún mensaje.
Sugerencia. Que cada corrida revise también los últimos 7 días sin marca o con marca fallida y los lea. Que el paso del yml no tome una marca fallida como hecha. Que la franja negra siga hasta que el día se resuelva o Diego lo dé por perdido.

F2-06. Gravedad alta. Una edición con páginas sin leer o con roles perdidos al cortar aparece como "al día".
Evidencia. motor\sincronizacion.py, línea 12. Solo cuentan como incompletas las alarmas de vale vista, de dirección y de sin remates. En una copia puse en una edición "No se pudo leer B11..." y en otra "Cuadre. 2 roles...", y estado_sincronizacion devolvió al_dia True sin franjas. La interfaz no muestra ediciones.alarmas en ninguna parte (agenda.html y datos.py no las leen). En el último intento, si fallan páginas la nube igual sube la edición con marca incompleta (diario.py, líneas 160 a 183), y el PC avisa "llegó incompleta" una sola vez, al cargarla.
VERIFICADO con la copia. n = 0 casos reales (las alarmas de navegación están vacías en las 20 capturas y no hay alarma de cuadre en 21 ediciones).
Consecuencia. Los remates de una página que no se leyó se pierden después de un solo aviso, que ahora pasa en modo callado.
Sugerencia. Sumar "No se pudo leer" y "Cuadre." a las alarmas que encienden la franja ámbar.

F2-07. Gravedad media. Una edición con marca incompleta nunca se completa.
Evidencia. interfaz\nube.py, línea 91. Solo se retoma si la marca dice listo.
VERIFICADO en el código. n = 0 (todas las marcas reales llegaron en listo, según las bitácoras).
Consecuencia. Si Haiku falló en el último intento, esos avisos se quedan sin vale vista ni dirección leídos aunque después lleguen las respuestas por republicaciones. Diego tiene que leerlos a mano.
Sugerencia. Retomar también cuando la marca es incompleta, solo con lo guardado.

F2-08. Gravedad alta. Una carpeta de captura a medias bloquea todas las actualizaciones y el mensaje culpa a internet.
Evidencia. interfaz\nube.py, líneas 102 a 106 (si la carpeta existe no se vuelve a bajar) y líneas 66 y 67 (cualquier error con "Errno" se muestra como falta de internet). Probé con una Supabase de mentira y una carpeta que solo tenía navegacion.json. Las dos veces dio "No se pudo conectar con Supabase. Revisa que el PC tenga internet." El ciclo de la línea 101 se corta en el primer error, así que tampoco entran las ediciones siguientes.
VERIFICADO el efecto. Lo que lo dispara (corte de luz o apagar el PC mientras se extrae el zip) es SUPUESTO, 20% de que pase alguna vez.
Consecuencia. La agenda deja de sumar ediciones día tras día y Diego busca una falla de internet que no existe.
Sugerencia. Extraer en una carpeta temporal y renombrar al final. Revisar que estén navegacion.json y todas sus páginas antes de cargar. Seguir con las demás ediciones si una falla. Clasificar bien el error de archivo.

F2-09. Gravedad media. Avisos civiles sin tribunal leído. No se encuentran por tribunal y su clave por huella del texto se parte con cualquier cambio de redacción.
Evidencia. real_sim.db, 20 remates visibles sin tribunal (9 propiedades). Fuera de los pegados de F2-02 están "ANTE EL 1° JUZGADO DE CIVIL DE Santiago" (C-10624-2025, 27 al 29 de Octubre), "ANTE QUINTO CIVIL DE Santiago" (C-136-2025, 24 al 27 de Octubre) y "ANTE EL 27° JUZGADO DE CIVIL" (C-9218-2025, 27 al 29 de Octubre). El 10624-2025 y el 9218-2025 tampoco tienen fecha ("Con fecha martes 26 de enero del año 2027"). La clave sin rol por huella (db\carga.py, línea 302) dejó en 2 bienes al 5618-2025 y separó el aviso del 24 de Octubre del Tribunal Arbitral Chandia.
VERIFICADO. n = 9 de 287 propiedades. 11 de 287 nunca tuvieron fecha en ninguna publicación.
Consecuencia. Diego no los ve al filtrar por tribunal y no se pueden poner en el calendario con fecha.
Sugerencia. Que el tribunal acepte "JUZGADO DE CIVIL" y el ordinal en palabras sin la palabra juzgado. Sin tribunal, que la clave use rol más inscripción antes que la huella.

F2-10. Gravedad media. Un dato que pasa de valor a vacío no se avisa y el calendario muestra el vacío.
Evidencia. motor\republicaciones.py, línea 154 (vacío no se compara). En db\esquema.sql, v_calendario toma la fecha, la hora y el mínimo de la publicación más nueva y solo tiene respaldo para el vale vista y la dirección.
VERIFICADO en el código. n = 0 casos en 21 ediciones (ip.db y real_sim).
Consecuencia. Si la última publicación de una causa agendada queda como pegado falso (F2-02), la causa pierde su fecha en el calendario sin aviso grande. Un nuevo llamado tampoco se detecta si la publicación anterior no tenía fecha.
Sugerencia. Usar la publicación anterior del mismo llamado también para la fecha, la hora y el mínimo, y anotar un cambio de "dato perdido".

F2-11. Gravedad baja. La lista de marcas no se pagina.
Evidencia. servidor\estado.py, línea 79, con limit 1000 y offset 0.
SUPUESTO 70% (que Supabase ordena por nombre de menor a mayor). n = 0.
Consecuencia. Cerca de Julio de 2029, con 1.000 marcas, el PC solo vería las más viejas y dejaría de cargar.
Sugerencia. Paginar o listar por prefijo de año y mes.

F2-12. Gravedad baja. Una causa acumulada sale como error de escritura del aviso.
Evidencia. C-11500-2024, 21, 22 y 23 de Octubre. El aviso dice "a la cual se encuentra acumulada la causa de desposeimiento C-1155-2025" y lleva la alerta "imprime 2 roles distintos... Confirma en el tribunal cuál es el correcto".
VERIFICADO. n = 3 publicaciones.
Consecuencia. Confunde y le resta peso a esa alerta cuando el error es real.
Sugerencia. No dar la alerta si el segundo rol va después de "acumulada".

F2-13. Gravedad baja. "TRIBUNAL ARBITRAL" no se descarta.
Evidencia. db\carga.py, línea 75. PARTICION no incluye esa forma. Marcelo Chandia Peña, del 22 al 25 de Octubre, 4 publicaciones, sin la palabra partición en el texto.
VERIFICADO. n = 1 causa.
Consecuencia. Sobra un aviso, no se pierde nada. Diego decide si un árbitro que no es de partición se descarta.
Sugerencia. Preguntarle a Diego antes de tocar la regla.

Revisado sin problemas
Descarte de JUEZ PARTIDOR y de ÁRBITRO. 136 descartes (99 en ip.db y 37 en real_sim), leído el comienzo de cada uno. Todos son partición o árbitro y ninguno es un aviso civil atrapado. El de 21° Civil C-17546-2020 es un juez partidor nombrado en esa causa y se descarta según la regla. El pegado del 16 de Octubre aviso 96 junta Cobranza de Concepción con un partidor y los dos se descartan igual.
Descarte de tribunales no civiles. 20 en ip.db, todos de Familia, Cobranza, Trabajo o Policía Local. 0 en real_sim.
No se juntaron propiedades distintas en un bien. 0 de 550 bienes con dos inscripciones distintas en ip.db.
Unión de B y G. 0 avisos solo en G el 9, el 16 y el 23 de Octubre.
guardar_edicion rechaza una edición repetida y guarda todo en una sola transacción.
v_calendario no toma publicaciones descartadas.
Se conserva el visto al rehacer cambios y el nuevo llamado reinicia el vale vista solo la primera vez.
La carga del PC no puede llamar a Haiku. Sin cliente, leer_con_ia corta si no hay respuesta guardada (motor\vale_vista.py, línea 372).
El candado de la base real está en nube.py y en procesar_edicion.py.
Las 9 ediciones reales cargan con 0 avisos sin leer por la IA y 1 cambio (dirección, 29 de Octubre).

Ideas de mejora
1. Ligada a F2-01 y F2-09. Una revisión de consistencia al cargar cada edición que liste las causas con más de un bien y la misma inscripción, y avise "posible propiedad partida" en la ficha.
2. Ligada a F2-05 y F2-06. Una franja persistente "Ediciones con problemas" que lea ediciones.alarmas y las marcas fallidas o ausentes de los últimos 30 días, con un reintento automático de los días sin marca.

No alcancé a revisar. No corrí las 19 pruebas (no quise escribir __pycache__ en la carpeta). Tampoco revisé a fondo las reglas de navegación del lector ni la extracción de fechas fuera de la regla de los pegados, no probé retomar con Haiku pendiente y no miré el estado real de Supabase.

## Sección F3. Código en general y seguridad básica (auditor 3)

Leí completo ESTADO_PROYECTO.md y las bitácoras del 20, 21, 22 y 29 de Octubre. Trabajé solo con lectura y con una copia aparte en $HOME/aud3/copia, que incluye el código y una copia de interfaz_prueba.db. No abrí ni copié agendar_remates.db, no llamé a Haiku ni a Supabase y no escribí nada en la carpeta del proyecto. Corrí todo con PYTHONDONTWRITEBYTECODE=1 y comprobé con find -newer que no apareció ningún archivo nuevo.

F3-01. Gravedad alta. No hay respaldo automático de agendar_remates.db, y si la base se daña la agenda no abre y no avisa nada.
Evidencia. Busqué "respald", "backup", "copy2" y ".backup(" en interfaz, db, motor y servidor y no hay ningún resultado. El .gitignore en su línea 1 deja fuera todo *.db, así que la base tampoco está en GitHub. El único respaldo es agendar_remates_vacia_antes_carga_21oct.db, que es la base vacía. En la copia probé con un .db dañado. El servidor se cae en db/crear_base.py línea 16 con sqlite3.DatabaseError, que no es OSError (servidor.py línea 174 no lo atrapa), y el navegador nunca se abre.
VERIFICADO.
Consecuencia. Con pythonw Diego hace doble clic y no pasa nada visible. El error queda solo en logs/servidor.log. Las ediciones se pueden rearmar desde capturas e ia_respuestas. Lo que marcó Diego se pierde entero, es decir las causas agendadas, las causas a mano, el vale vista entregado, el remate asistido, los cambios vistos y los quitados. Eso puede costar un remate.
Sugerencia. Al abrir la agenda, una copia diaria con con.backup() a una carpeta respaldos/ que guarde las últimas 14. En main, atrapar sqlite3.DatabaseError y mostrar una página de error en vez de quedar mudo.

F3-02. Gravedad alta, con probabilidad baja. El aviso "FECHAS DE REMATES HAN SIDO CAMBIADAS" se puede perder para siempre.
Evidencia. En motor/procesar_edicion.py la línea 453 guarda la edición en su propia transacción (db/carga.py línea 193) y recién después la línea 458 corre registrar_cambios en otra. Además interfaz/nube.py, en sus líneas 86 a 92, solo vuelve a tocar una edición ya guardada cuando su alarma es de vale vista o de dirección. Nada repite registrar_cambios si algo falla entre una transacción y la otra.
VERIFICADO la estructura. Que ocurra lo pongo como SUPUESTO bajo 5% al año. Hace falta una excepción dentro de registrar_cambios, o que el PC se apague justo en ese momento.
Consecuencia. La edición queda cargada sin su fila en cambios. El calendario muestra la fecha nueva, pero el aviso grande nunca sale para esa causa.
Sugerencia. Juntar las dos cosas en una sola transacción, o dejar una alarma "Cambios pendientes" que nube.py trate como edición por retomar.

F3-03. Gravedad media. Los errores del servidor no quedan en logs/servidor.log, y algunos llegan con un mensaje equivocado.
Evidencia. interfaz/servidor.py silencia log_message en las líneas 54 y 55. Las líneas 100 y 101 y las 134 y 135 atrapan cualquier excepción y solo la devuelven a la página. En la copia, un pedido que rompe /api/estado devolvió 500 y la salida del servidor quedó vacía. En interfaz/nube.py, líneas 64 a 70, todo texto que contenga "Errno" se traduce como "No se pudo conectar con Supabase. Revisa que el PC tenga internet.", y eso incluye disco lleno, permiso negado o archivo bloqueado.
VERIFICADO lo del log y el código del mensaje. Que pase en el PC de Diego es SUPUESTO.
Consecuencia. Diego ve un aviso de 7 segundos y no queda ningún rastro para revisar después. Una falla de disco le pide revisar el internet.
Sugerencia. Poner traceback.print_exc() con la hora y la ruta en esos except. En nube.py, elegir el mensaje de internet según el tipo de error (URLError, timeout) y no según el texto.

F3-04. Gravedad media. Un solo dato malo deja toda la agenda sin abrir.
Evidencia. interfaz/datos.py línea 478 revisa solo la forma de la fecha, así que acepta 2026-13-45. Las líneas 480 y 481 no revisan vd ni vh. En la copia, POST /api/manual con vh "mañana" respondió ok. Desde ese momento /api/estado responde 500 "Invalid isoformat string" en cada carga.
VERIFICADO el bloqueo. Que ocurra desde la página es SUPUESTO 10%, porque esos campos son de tipo fecha en agenda.html (líneas 277 y 279).
Consecuencia. Con un solo registro raro, venga de F3-05 o de un cambio futuro del código, Diego pierde todo el calendario hasta que alguien arregle la base a mano.
Sugerencia. Validar fecha, vd y vh con dt.date.fromisoformat en agregar_manual. En agenda(), aislar cada causa para que una dañada no bote a las demás.

F3-05. Gravedad media, con probabilidad baja. El servidor acepta acciones de cualquier página web.
Evidencia. interfaz/servidor.py, desde la línea 103, no revisa Origin, Host ni Content-Type. En la copia, POST /api/marcar con text/plain y un Origin ajeno respondió {"ok": true}. Un GET a /api/estado con un Host ajeno respondió 200 con la agenda completa.
VERIFICADO que el servidor lo acepta. Que un sitio real lo logre en el Chrome de Diego es SUPUESTO 25%, porque Chrome reciente pide permiso de red local antes de dejar que un sitio público hable con 127.0.0.1.
Consecuencia. Un sitio malicioso podría marcar vale vista entregado (con eso la ventana deja de verse), quitar causas o provocar el bloqueo de F3-04. Requiere un ataque dirigido.
Sugerencia. Responder 403 cuando el Host no sea 127.0.0.1 o localhost con el puerto, o cuando el Origin sea ajeno. Exigir application/json en los POST.

F3-06. Gravedad media. Una prueba apunta a la base real.
Evidencia. pruebas/test_union_vale_vista.py línea 386 corre procesar_edicion --retomar contra RAIZ/agendar_remates.db para comprobar que se niega. Si el candado de motor/procesar_edicion.py línea 480 se rompe, el comando sigue hasta crear(ruta) en la línea 494 y escribe meta y feriados en la base real antes de fallar. Es el mismo error que la bitácora del 20 (punto 16) ya corrigió en test_nube, y aquí no se corrigió.
VERIFICADO el código. Hoy no escribió nada, la huella quedó igual.
Sugerencia. Usar una base de mentira llamada agendar_remates.db dentro de la carpeta temporal, como hace test_nube.

F3-07. Gravedad media. La agenda se apaga por falta de señal y la página no lo dice.
Evidencia. En agenda.html línea 344 el latido tiene un catch vacío. El servidor se apaga a los 180 segundos sin señal (servidor.py líneas 145 a 152). Si el PC se suspende o Chrome descarta la pestaña inactiva, la página sigue en pantalla con datos viejos. Recién al hacer clic sale "No se pudo leer la agenda. Failed to fetch".
VERIFICADO que la página no avisa. Que se apague después de suspender el PC en Windows es SUPUESTO 55%.
Consecuencia. Diego vuelve en la mañana, ve la agenda vieja, cree que está al día y lo que marque no se guarda.
Sugerencia. Si el latido falla dos veces seguidas, tapar la página con "La agenda se cerró. Ábrela de nuevo con el ícono".

F3-08. Gravedad media. La clave de Supabase del PC tiene más permisos de los que necesita.
Evidencia. SUPABASE_KEY en config.py tiene la forma de la clave secreta nueva de Supabase, con prefijo sb_secret y 41 caracteres. Esa clave salta RLS y puede leer, escribir y borrar todo el proyecto. El PC solo lee, porque nube.py usa listar, existe, leer_texto y bajar. config.py guarda además la clave de Anthropic (forma sk-ant) y la contraseña del Mercurio, y el uso diario ya no las necesita. Hay copia de esas claves en __pycache__/config.cpython-310.pyc y config.cpython-314.pyc, que quedan fuera de git. La nube también usa la secreta, y allá sí corresponde porque escribe.
VERIFICADO la forma y el uso. config.py nunca entró a git.
Consecuencia. Quien copie la carpeta (pendrive, nube, otra herramienta o una sesión de IA conectada a D) se lleva una llave que puede borrar el bucket y gastar el saldo de Haiku.
Sugerencia. Para el PC, usar la clave publicable con una política de solo lectura sobre el bucket agendar, o URLs firmadas. Sacar del config.py del PC lo que ya no se usa. Si se cambian las claves, borrar también esos .pyc.

F3-09. Gravedad baja. Cada doble clic escribe en la base que está en uso.
servidor.py llama a crear() en la línea 140, antes de intentar tomar el puerto en la línea 142. Un segundo doble clic escribe el esquema y los feriados en agendar_remates.db mientras la primera agenda está abierta. VERIFICADO el orden. El riesgo de "database is locked" es SUPUESTO 20%. Sugerencia. Tomar primero el puerto y crear la base después.

F3-10. Gravedad baja. Cualquier error al tomar el puerto se lee como "ya está abierta".
servidor.py línea 174 atrapa todo OSError. Si otro programa ocupa el 8765, el navegador se abre hacia ese programa. VERIFICADO. Sugerencia. Preguntar a /api/latido si quien responde es la agenda y, si no, dejarlo anotado en el log.

F3-11. Gravedad baja. La base se puede bloquear durante la actualización callada.
Desde el 29 de Octubre, la actualización sin pantalla corre mientras Diego usa la página. Las conexiones tienen la espera por defecto de 5 segundos (servidor.py línea 58). Un clic en una carga larga puede dar "database is locked". SUPUESTO 40%. Se ve como aviso, no se pierde en silencio. Sugerencia. Usar timeout=30 en sqlite3.connect.

F3-12. Gravedad baja. listar() no pagina.
servidor/estado.py línea 79 pide como máximo 1000 nombres y no fija el orden. Con una marca por día, hacia julio de 2029 las marcas más nuevas quedarían fuera. SUPUESTO 80%. Además nube.py línea 84 baja todas las marcas de los 30 días en cada apertura. Sugerencia. Pedir el orden descendente y leer solo las marcas que faltan.

F3-13. Gravedad baja. El encabezado de ESTADO_PROYECTO.md está desactualizado.
Dice "Última actualización 21 de Octubre", y el punto 1 de Próximo paso deja GitHub en 6b1c7ea. La referencia local origin/master está en dec0c8a, del 29 de Octubre. Un chat nuevo puede confundirse. VERIFICADO.

Revisado sin problemas
El .gitignore cubre config.py, *.db, logs, capturas, perfil_navegador, .env y __pycache__.
Revisé git log --all -p (123 commits) con los patrones sk-ant largo, JWT, sb_secret, sb_publishable, ghp, github_pat y AKIA. No hay ninguna clave. Las 3 apariciones de "sk-ant-" son textos de reportes que describen la búsqueda. config.py y los .db nunca se subieron.
En logs, reportes y bitácoras no hay claves.
diario.yml toma los secretos como variables de entorno, la fecha va por env (sin inyección), CARGA_REAL_APROBADA queda en False en la nube y curl no imprime la clave.
El servidor escucha solo en 127.0.0.1 (línea 142).
El código de una sola instancia está bien hecho (allow_reuse_address en False y SO_EXCLUSIVEADDRUSE). En el shell Linux el segundo arranque respondió "ya está abierta". En Windows lo dejo como SUPUESTO 85%.
Todas las consultas SQL usan ?. Los f-string solo llevan nombres de una lista fija (datos.py líneas 454 y 466).
El texto del aviso siempre pasa por la función E de agenda.html (línea 118). Revisé las 130 interpolaciones que no usan E y son números, íconos fijos o HTML que ya viene escapado. Los links llevan rel noopener y el prefijo https fijo.
Los candados de procesar_edicion (línea 480), nube.py (línea 52) y cargar_banco comparan con resolve(). Desde el 21 de Octubre CARGA_REAL_APROBADA es True, así que el de nube.py ya no frena nada, por decisión de Diego.
_extraer rechaza rutas con ".." o absolutas dentro del zip.
No hay funciones sin uso en interfaz, db, motor ni servidor.

Medición
Antes, a las 04:08 UTC del 30 de Octubre. agendar_remates.db md5 94faa67971394700481da38c92c2f7b5, 7.426.048 bytes, hora 22:51:17 UTC del 29 de Octubre. interfaz_prueba.db md5 61fa8e674cb3f5e50a405babefcbb333. ia_respuestas con 1.319 .json.
Después, a las 04:16 UTC. Huellas, horas y conteo idénticos, sin ningún cambio.
Las 19 pruebas terminaron en TODO OK con el python3 3.10 del shell y código de salida 0. Ninguna escribió respuestas nuevas de Haiku.
Una observación SUPUESTA al 60%. logs/servidor.log no existe, así que la agenda con pythonw todavía no ha corrido en Windows. Lo más probable es que la hora 22:51 de la base real venga de la medición en Linux del 29 de Octubre (bitácora del 29, punto 3), si se hizo sin --base. Si fue así, crear() escribió en la base real.
[Nota de Claude. Esa medición se hizo con --base sobre una copia en $HOME/vis, así que no tocó la base real. Ver la lectura de Claude arriba.]

Ideas de mejora
1. Ligada a F3-01. Un respaldo diario automático al abrir la agenda y un botón "Exportar mis causas" que guarde agenda, agenda_manual y agenda_quitados en un archivo legible.
2. Ligada a F3-03 y F3-05. Una función única para registrar errores en servidor.log, usada por los except del servidor y de nube.py, y la guardia de Host y Origin en el mismo cambio.

No alcancé a revisar a fondo la lógica de lectura de motor/vale_vista.py, direccion.py, extraccion.py, cortador.py y lector_mercurio.py. Tampoco probé el comportamiento real en Windows, ni el estado vivo de Supabase y GitHub, ni si el repositorio sigue privado.

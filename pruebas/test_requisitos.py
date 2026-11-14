"""Requisitos para participar además del vale vista (motor\\requisitos.py, pedido de Diego del 13 de Noviembre de 2026).
Prueba SIN internet y sin IA. Las frases son de avisos reales de los Juzgados Civiles de Santiago (ediciones del 21 de Octubre al
12 de Noviembre), copiadas tal como salieron en el diario, con sus espacios de más.
1. Cada requisito se lee con su plazo, su dirección de correo y la frase del aviso.
2. Lo que NO es requisito no se lee (correo para el pago del saldo, correo de consultas, firma del juez, deudores de alimentos,
   bases en la Oficina Judicial Virtual, texto de una demanda).
3. La advertencia de patrón roto sale solo con patrón fuerte y nunca asume el requisito.
4. La frase citada es siempre texto del aviso (se revisa en todos los avisos del banco del 14 de Octubre)."""
import json, re, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor import requisitos as R
from motor.cortador import construir_rollo, cortar
from motor.orden_columnas import leer_pagina

FALLAS = []


def revisar(nombre, condicion, detalle=""):
    print(("ok    " if condicion else "FALLA ") + nombre + ("" if condicion else "  ->  " + str(detalle)[:400]))
    if not condicion:
        FALLAS.append(nombre)


def claves(t):
    return [r["clave"] for r in R.leer(t)]


_NADA = {"clave": None, "detalle": "", "plazo": None, "cuando": "sin leer", "correo": None, "frase": "", "zoom": {"id": None, "url": None, "codigo": None}}


def uno(t, clave, n=0):
    """El requisito pedido, o uno vacío si no salió. Así una lectura que falta da FALLA y no una prueba caída."""
    r = [r for r in R.leer(t) if r["clave"] == clave]
    return r[n] if len(r) > n else dict(_NADA)


T3 = ("Mínimo subasta $ 60.830.951.- Los postores, a más tardar a las 15 hrs. del día hábil anterior a la realización de la subasta, deberán "
      "enviar un correo electrónico a xandrade @pjud.cl, indicando asunto ‘Remate’, con señalamiento del rol de causa y fecha de realización, "
      "a fin de coordinar su participación, así como para obtener información del protocolo de realización de subasta y recibir el link con "
      "la invitación a la misma. Asimismo, los postores, a más tardar a las 15 hrs del día hábil anterior al remate, deberán manifestar su "
      "intención de participar en ésta, ingresando escrito por OJ.V. que así lo señale, con una copia legible del vale vista entregado al "
      "Tribunal, además de señalar un correo electrónico para su conexión y número de teléfono, bajo apercibimiento de que, si así no lo "
      "hiciere, no se le considerará como postor en la subasta. Bases y antecedentes oficina judicial virtual ‘Banco con Pérez’ Rol C-1-2024.")
c3 = uno(T3, "correo")
revisar("3° Civil. correo con la dirección sin el espacio del diario", c3["correo"] == "xandrade@pjud.cl", c3)
revisar("3° Civil. correo con su plazo en palabras del aviso", c3["plazo"] == "a más tardar a las 15 hrs. del día hábil anterior a la realización de la subasta", c3["plazo"])
revisar("3° Civil. la abreviatura hrs. y el correo no cortan la oración", c3["frase"].startswith("Los postores, a más tardar") and c3["frase"].endswith("invitación a la misma"), c3["frase"])
o3 = uno(T3, "ojv")
revisar("3° Civil. escrito por la Oficina Judicial Virtual con su plazo", o3["detalle"].startswith("Ingresa un escrito") and o3["plazo"] == "a más tardar a las 15 hrs del día hábil anterior al remate", o3)
revisar("3° Civil. también lee datos de contacto y que el link llega por correo, y nada más", claves(T3) == ["correo", "ojv", "contacto", "link_por_correo"], claves(T3))
revisar("bases y antecedentes en la Oficina Judicial Virtual no es un trámite", claves("Bases y antecedentes oficina judicial virtual ‘Banco con Pérez’ Rol C-1-2024.") == [])

T29 = ("Los postores interesados deberán ingresar comprobante legible de rendición de la caución, a través del módulo especialmente establecido "
       "al efecto en la Oficina Judicial Virtual, y enviar un correo a la casilla electrónica jcsantiago29_remates @pjud.cl, hasta las 12:00 "
       "hrs. del día hábil anterior a la subasta, y si dicho día fuera sábado, hasta las 12:00 hrs. del viernes anterior a la subasta, "
       "indicando su nombre completo y adjuntando copia -por ambos lados- de su cédula de identidad, indicando el Rol de la causa en la cual "
       "participará, un correo electrónico y número telefónico para el caso que se requiera contactarlo durante la subasta por problemas de conexión.")
revisar("29° Civil. problemas de conexión después de la dirección sigue siendo un requisito, no un correo de consultas",
        claves(T29) == ["correo", "ojv", "cedula", "contacto"], claves(T29))
revisar("29° Civil. el plazo trae la regla del sábado", uno(T29, "correo")["plazo"] == "hasta las 12:00 hrs. del día hábil anterior a la subasta, y si dicho día fuera sábado, hasta las 12:00 hrs. del viernes anterior a la subasta", uno(T29, "correo")["plazo"])
revisar("29° Civil. una sola cita aunque la oración traiga cuatro requisitos", len(R.para_ficha("29° Juzgado Civil de Santiago", T29, "zoom", {})["frases"]) == 1)

# Oración larga de aviso telegráfico (armada repitiendo un tramo real, porque en el diario pasan de 900 letras). Dos requisitos lejos uno del otro.
_LARGA = "Interesados deberán enviar correo a jcsantiago4_remates@pjud.cl copia del vale vista " + "y demás derechos en proporción al valor de lo adquirido en unión de los otros adquirentes " * 12 + "y deberán contar con clave única"
_fl = R.para_ficha("4° Juzgado Civil de Santiago", _LARGA, "zoom", {})
revisar("oración de más de 900 letras. una sola cita, recortada con puntos suspensivos", [r["clave"] for r in _fl["requisitos"]] == ["correo", "clave"] and len(_fl["frases"]) == 1
        and _fl["frases"][0].endswith(" …") and len(_fl["frases"][0]) <= 904, (len(_fl["frases"]), [len(x) for x in _fl["frases"]]))

T2 = ("Los interesados deberán presentar el vale vista en dependencias del tribunal, el día hábil anterior a la fecha fijada para el remate, "
      "entre las 12:00 y 14:00 horas, debiendo entregar copia de su carnet de identidad, además de señalar el nombre completo del postor, su "
      "mail y teléfono, a fin de coordinar su participación vía correo electrónico y recibir el link con la invitación del remate a efectuarse "
      "por videoconferencia a través de la plataforma Zoom. El saldo del precio de la subasta deberá pagarse al contado, dentro de quinto día "
      "hábil de efectuado el remate, mediante cupón de pago en el Banco Estado o depósito judicial a la cuenta corriente del Tribunal, "
      "ingresando copia de dicho comprobante por la Oficina Judicial Virtual, en la causa respectiva en el plazo estipulado en las presentes "
      "bases de remate y enviar aviso al correo electrónico del Tribunal pasalazar@pjud.cl, indicando su nombre, Rut y Rol de la causa.")
revisar("2° Civil. el correo y la Oficina Judicial Virtual del pago del saldo NO son requisitos para participar",
        claves(T2) == ["cedula", "contacto", "link_por_correo"], claves(T2))
revisar("2° Civil. plataforma Zoom. El saldo corta la oración", "saldo" not in uno(T2, "cedula")["frase"], uno(T2, "cedula")["frase"][-80:])
revisar("2° Civil. la cédula va junto con el vale vista y toma su plazo con el horario (punto 1 de Diego, 13 de Noviembre)",
        uno(T2, "cedula")["detalle"] == "Copia de la cédula" and uno(T2, "cedula")["plazo"] == "el día hábil anterior a la fecha fijada para el remate, entre las 12:00 y 14:00 horas"
        and uno(T2, "contacto")["plazo"] == uno(T2, "cedula")["plazo"], uno(T2, "cedula"))

T8 = "No se admitirá la entrega de vale vista de garantía en una oportunidad distinta. Consultas relativas a la subasta, comunicarse al correo electrónico jcsantiago8_ remates@pjud.cl. Demás bases en la causa."
revisar("8° Civil. correo de consultas no es un requisito, queda como correo del tribunal", claves(T8) == ["ayuda"] and uno(T8, "ayuda")["correo"] == "jcsantiago8_remates@pjud.cl", R.leer(T8))

T16 = ("En momento presentar vale vista, postor deberá informar correo electrónico y número teléfono válido a través acta predeterminada será "
       "suscrita postor e incorporada carpeta electrónica ministro de fe conjuntamente copia vale vista. Se utilizará plataforma zoom para lo "
       "cual se requiere de computador o teléfono con cámara, micrófono y audio del mismo equipo y conexión a internet. Problemas de conexión "
       "informarlos al mail jcsantiago16_remates@pjud.cl. Las partes y postores deberán conectarse a la sesión con al menos 10 minutos de anticipación.")
revisar("16° Civil. acta predeterminada y contacto, y la carpeta electrónica que llena el tribunal no es un trámite del postor",
        claves(T16) == ["contacto", "formulario", "minutos", "equipo", "ayuda"], claves(T16))
revisar("16° Civil. entrar 10 minutos antes", uno(T16, "minutos")["detalle"] == "Entra 10 minutos antes")
revisar("16° Civil. sin fecha en la frase, el correo y teléfono se dejan al entregar el vale vista (punto 1 de Diego)",
        uno(T16, "contacto")["plazo"] is None and uno(T16, "contacto")["cuando"] == R.AL_ENTREGAR and uno(T16, "formulario")["cuando"] == R.AL_ENTREGAR, uno(T16, "contacto"))
revisar("con plazo propio no se agrega el cuándo, y un requisito que no va con el vale vista tampoco",
        uno(T2, "contacto")["cuando"] is None and uno(T3, "correo")["cuando"] is None and uno(T3, "contacto")["cuando"] is None, (uno(T2, "contacto"), uno(T3, "contacto")))

revisar("clave. tener activa la Clave Única o firma electrónica avanzada es requisito",
        uno("Para participar en la subasta realizada por videoconferencia, todo postor deberá tener activa su clave única del estado o firma electrónica avanzada, para la eventual suscripción de la pertinente acta de remate.", "clave")["detalle"] == "Clave Única o firma electrónica avanzada")
revisar("clave. Los postores deberán contar con clave única", claves("Los postores deberán contar con clave única.") == ["clave"])
revisar("clave. la firma del juez y la del adjudicatario después del remate no son requisitos para participar",
        claves("El juez y el ministro de fe del tribunal firmarán el acta de remate con su firma electrónica avanzada, dejando constancia en la misma, del hecho de haberse firmado por el adjudicatario a través de su clave única. El acta de remate deberá ser suscrita por el adjudicatario inmediatamente después de realizada la subasta, mediante firma electrónica avanzada o clave única.") == [])
revisar("clave. los exceptuados de firmar en persona no son un requisito",
        claves("El acta de remate deberá firmarse personalmente el mismo día de la subasta, solo quedan exceptuados de dicha exigencia aquellos participantes que cuenten con firma electrónica avanzada.") == [])
revisar("deudores de alimentos no se lee (irrelevante, decisión de Diego)",
        claves("De conformidad a lo establecido en el artículo 29 de Ley 21.389, no se admitirá la participación como postores de personas que cuenten con inscripción vigente en calidad de deudores en el Registro Nacional de Deudores de Alimentos.") == [])
revisar("lo de después de adjudicar no se lee (queda para el futuro)",
        claves("El acta de remate se enviará el mismo día en que se realizó la subasta al correo electrónico del adjudicatario, quien deberá firmarla inmediatamente con firma electrónica avanzada remitiéndola antes de las 15:00 horas al correo electrónico jcsantiago18@pjud.cl o presencialmente en secretaria del Tribunal a más tardar el día siguiente.") == [])
revisar("la devolución del vale vista no se lee",
        claves("La garantía para aquellos postores que no se adjudiquen el bien subastado será devuelta sólo al tomador, a partir del día siguiente a la subasta, exhibiendo cédula de identidad y mandato/personería vigentes.") == [])

T1 = ("Cada postor para participar en la subasta deberá constituir garantía suficiente a través de vale vista endosable a nombre del Primer "
      "Juzgado Civil de Santiago, Rut N° 60.306.001-6, el cual deberá ser entregado hasta las 14:00 horas del día hábil anterior a la subasta, "
      "junto a los datos necesarios para su individualización, como lo son: copia de la cédula de identidad por ambos lados de quien trae vale "
      "vista, Rut, número de celular y correo electrónico, nombre de quien hace posturas, representante de la empresa adjudicataria, si "
      "correspondiera, nombre del banco emisor vale vista y nombre de la persona que retirará eventualmente el vale vista en caso de no adjudicarse el inmueble.")
revisar("1° Civil. la hoja de datos se lee aunque diga adjudicataria y retirará", claves(T1) == ["cedula", "contacto", "formulario"], claves(T1))
T24 = "Deberá acompañarse vale vista a la orden del tribunal, con indicación del tomador para facilitar su devolución, oferentes deberán acompañar conjuntamente con el vale vista su cedula de identidad vigente, el mismo día de la subasta."
revisar("24° Civil. para facilitar su devolución no tapa la cédula vigente", claves(T24) == ["cedula"] and uno(T24, "cedula")["detalle"] == "Lleva tu cédula vigente", R.leer(T24))

z = uno("La subasta se llevará a efecto mediante la plataforma Zoom, utilizando para ello el siguiente enlace: https://zoom.us/j/ 6413248095?pwd=bThMeFc4VlY1WmlH cXZEbjZWMTc0Zz09 ID de reunión: 641 324 8095 Código de acceso: 757295.", "link")["zoom"]
revisar("zoom. ID y código aunque el diario parta el link", z == {"id": "6413248095", "otro_id": None, "codigo": "757295", "url": "https://zoom.us/j/6413248095"}, z)
z = uno("Los postores podrán participar de la subasta a través del siguiente link: https://pjud-cl.zoom.us/j/ 92898706317.", "link")["zoom"]
revisar("zoom. dirección del Poder Judicial", z["url"] == "https://pjud-cl.zoom.us/j/92898706317" and z["codigo"] is None, z)
revisar("zoom. el 22° Civil escribe el número después de link", uno("rematará por videoconferencia, mediante plataforma zoom en el link: 98584722830 propiedad raíz.", "link")["zoom"]["id"] == "98584722830")
z = uno("ingresar a través del siguiente enlace: https://zoom.us/j/41823801092 pwd=cnR4, o mediante ID de reunión 418 238 0109, contraseña 453304.", "link")
revisar("zoom. si el link y el ID traen números distintos no se arma el link y se avisa", z["zoom"]["url"] is None and "dos números distintos" in z["detalle"], z)

T15 = ("Para ello deberán comunicar su asistencia al tribunal al correo electrónico jcsantiago15@pjud.cl, señalando el nombre y Rut de la persona "
       "que asistirá a entregar el vale vista como también el rol de la causa. Los postores, a más tardar a las 14:00 horas del día hábil anterior "
       "a la realización de la subasta, deberán enviar un correo electrónico al mail del tribunal jcsantiago15@pjud.cl, indicando en el asunto "
       "’Remate’ junto con el rol de la causa y la fecha de realización, manifestando su intención de participar.")
revisar("15° Civil. dos correos distintos, uno para dejar el vale vista y otro para participar",
        [r["detalle"] for r in R.leer(T15)] == ["Avisa por correo quién irá a dejar el vale vista", "Escribe al tribunal antes del remate"] and uno(T15, "correo", 0)["plazo"] is None
        and uno(T15, "correo", 1)["plazo"] == "a más tardar a las 14:00 horas del día hábil anterior a la realización de la subasta", R.leer(T15))
T22 = "se rematará a través de la plataforma Zoom, ID de la reunión 950 8480 2601, debiendo el interesado solicitar el código de acceso al correo 22jcivil santiago_remates @pjud.cl."
revisar("22° Civil. pedir el código de acceso por correo, con la dirección partida por el diario",
        uno(T22, "correo")["detalle"].startswith("Pide por correo el código de acceso") and uno(T22, "correo")["correo"] == "22jcivilsantiago_remates@pjud.cl", R.leer(T22))
T6 = "Los cupones de pago deberán ser acompañados a la causa, para calificar su suficiencia, a más tardar el día hábil anterior a la subasta, hasta las 12:30 hrs, por medio de la respectiva presentación a través de la OJV."
revisar("6° Civil. la Oficina Judicial Virtual solo si la garantía es cupón de pago, con el plazo entero",
        uno(T6, "ojv")["detalle"].startswith("Solo si la garantía es con cupón de pago") and uno(T6, "ojv")["plazo"] == "a más tardar el día hábil anterior a la subasta, hasta las 12:30 hrs", uno(T6, "ojv"))
T20 = "Debe ser acompañado materialmente al tribunal en horario atención de público al menos 1 día hábil anterior a realización de subasta y cuya gestión debe ser solicitada con al menos 1 semana de anticipación al correo electrónico jcsantiago20@pjud.cl."
revisar("20° Civil. en un aviso sin comas el plazo del correo es el de la semana, no el del vale vista", uno(T20, "correo")["plazo"].startswith("con al menos 1 semana de anticipación"), uno(T20, "correo"))
revisar("el texto de una demanda pegada al aviso no se lee", claves("Primer Otrosí: Acompaña documentos Segundo Otrosi: Se tenga presente Tercer Otrosí: Personería Cuarto Otrosí: Bienes.") == [])
revisar("un correo que no es del Poder Judicial no se toma", R.correos("por Eduardo Zenay | edozenay@gmail.com basta, y enviar un correo") == [])
revisar("12° Civil. Mis Remates con Clave Única", [r["clave"] for r in R.leer("Una vez que el postor ha sido aceptado por el tribunal en el sistema computacional, circunstancia que podrá verificar con su clave única del Estado, en el módulo ’Mis Remates’, deberá entregar el vale vista materialmente en el Tribunal, entre las 9:00 y las 13:00 horas del día anterior a la realización de la subasta.")] == ["ojv", "clave"])
revisar("18° Civil. persona jurídica y compra para un tercero",
        claves("Cada postor que se adjudique para un tercero, deberá presentar ante el juez los documentos suficientes. En el caso de corresponder a una persona jurídica, deberá señalar los datos del representante legal de la misma (nombre completo y rut) y acompañar además copia de personería con firma electrónica verificable.") == ["persona_juridica", "tercero"])
revisar("sin texto no hay requisitos y no se cae", R.leer(None) == [] and R.leer("") == [])

# Advertencia de patrón roto. Solo con patrón fuerte (80% de las causas y al menos 10 causas), y nunca asume el requisito.
TR = "3° Juzgado Civil de Santiago"
TAB = {"tribunales": {TR: {"causas": 25, "requisitos": {"correo": 23, "ojv": 19, "clave": 20, "link": 25, "equipo": 25}},
                      "9° Juzgado Civil de Santiago": {"causas": 9, "requisitos": {"correo": 9}}}}
revisar("patrón. fuerte desde el 80% justo, y el 76% no", [k for k, _, _ in R.fuertes(TR, TAB)] == ["correo", "clave", "link"], R.fuertes(TR, TAB))
revisar("patrón. un tribunal con menos de 10 causas no tiene patrón", R.fuertes("9° Juzgado Civil de Santiago", TAB) == [] and R.fuertes("otro", TAB) == [] and R.fuertes(None, TAB) == [])
f = R.para_ficha(TR, "Postores deberán contar con clave única. Mínimo $ 10.", "zoom", TAB)
revisar("patrón roto. avisa lo que falta con su n, y lo que el aviso trae no se avisa",
        f["advertencias"][0] == "En el 3° Civil 23 de 25 causas medidas piden mandar un correo al tribunal antes del remate y el aviso de esta causa no lo trae."
        and "traen el link" in f["advertencias"][1] and f["advertencias"][-1] == R.ROTO and len(f["advertencias"]) == 3 and not any("Clave" in a for a in f["advertencias"][:-1]), f["advertencias"])
revisar("patrón roto. no agrega el requisito a la lista, no se asume", [r["clave"] for r in f["requisitos"]] == ["clave"])
f = R.para_ficha(TR, "Postores deberán contar con clave única.", "presencial", TAB)
revisar("patrón roto. en un remate presencial no se pide el link", not any("link" in a for a in f["advertencias"]) and len(f["advertencias"]) == 2, f["advertencias"])
f = R.para_ficha(TR, None, None, TAB)
revisar("causa a mano. sin aviso, la costumbre del tribunal va como advertencia y no como requisito",
        f["a_mano"] and f["requisitos"] == [] and f["advertencias"][0].endswith("piden mandar un correo al tribunal antes del remate.") and f["advertencias"][-1] == R.A_MANO, f)
f = R.para_ficha("8° Juzgado Civil de Santiago", "Postores deberán rendir caución.", "zoom", {})
revisar("videoconferencia sin link ni correo. se avisa que el aviso no dice cómo llega el link", f["nada"] and len(f["advertencias"]) == 1 and "no dice cómo llega el link" in f["advertencias"][0], f)
revisar("sin requisitos y presencial. caja vacía sin advertencias", R.para_ficha("8° Juzgado Civil de Santiago", "Postores deberán rendir caución.", "presencial", {})["advertencias"] == [])

# La tabla medida (db\requisitos_patron.json, pruebas\medir_requisitos.py) existe y dice cómo se midió.
P = R.patron()
revisar("tabla medida. está, cuenta por causa y trae los 30 civiles con su n", P.get("cuenta_por", "").startswith("causa") and len(P["tribunales"]) == 30
        and all(v["causas"] >= 1 and all(n <= v["causas"] for n in v["requisitos"].values()) for v in P["tribunales"].values()), str(P)[:200])
revisar("tabla medida. la fecha va con el mes en palabras", re.fullmatch(r"\d{1,2} de [A-Z][a-z]+ de \d{4}", P.get("medido_el", "")) is not None, P.get("medido_el"))
revisar("tabla medida. el 3° Civil tiene el correo como patrón fuerte y el 8° y el 14° no tienen ninguno",
        "correo" in [k for k, _, _ in R.fuertes(TR)] and R.fuertes("8° Juzgado Civil de Santiago") == [] and R.fuertes("14° Juzgado Civil de Santiago") == [])

# La frase citada es siempre texto del aviso. Todos los avisos del banco del 14 de Octubre.
B = RAIZ / "banco_pruebas" / "2026-10-14"
rollo, m = construir_rollo([(n, leer_pagina(B / f"mercurio_2026-10-14_{n}.txt")) for n in ("B11", "C8")])
malas, total = [], 0
for a in cortar(rollo, m):
    plano = re.sub(r"\s+", " ", a.texto)
    for r in R.leer(a.texto):
        total += 1
        if r["frase"].strip("… ") not in plano or (r["plazo"] and r["plazo"] not in plano) or r["titulo"] != R.TITULO[r["clave"]]:
            malas.append((a.orden, r["clave"], r["frase"][:80]))
revisar("cita. en el banco del 14 de Octubre toda frase y todo plazo están escritos así en el aviso", total > 100 and not malas, (total, malas[:3]))

# La ficha. Caja nueva, solo en la ficha, después de Cómo llenar el vale vista.
html = (RAIZ / "interfaz" / "agenda.html").read_text(encoding="utf-8")
datos = (RAIZ / "interfaz" / "datos.py").read_text(encoding="utf-8")
fh = html[html.index("function fichaHTML("):html.index("function irAFicha(")]
rq = html[html.index("function requisitosHTML("):html.index("/* vista=true")]
# 13 de Noviembre (Diego, C-9156-2025). La frase de la regla del vale vista va pegada a Cómo llenar el vale vista y la caja de requisitos
# después. Al revés la frase quedaba al final de la ficha, como si saliera de la nada.
revisar("ficha. la caja Requisitos para participar va después de Cómo llenar el vale vista y de la frase del vale vista",
        "${formaHTML(it,vista)}\n  ${it.vv_regla?`<blockquote>“${E(it.vv_regla)}”</blockquote>`:''}\n  ${requisitosHTML(it)}" in fh and "<h3>Requisitos para participar</h3>" in rq)
revisar("ficha. la caja no está en el buscador ni en el calendario", html.count("requisitosHTML(") == 2)
revisar("ficha. muestra el plazo, el cuándo, a quién escribir, la frase del aviso y las advertencias",
        "${E(r.plazo)}" in rq and "${r.cuando?`<div><span class=\"peq\" style=\"font-weight:700;letter-spacing:.06em\">CUÁNDO</span> ${E(r.cuando)}" in rq and "Escribir a <b" in rq and "${E(r.correo)}" in rq and "q.frases.map(f=>`<blockquote>“${E(f)}”</blockquote>`)" in rq and '(q.advertencias||[]).map(a=>`<div class="al ambar"' in rq)
revisar("ficha. todo texto del aviso pasa por E antes de mostrarse", "${r." not in rq.replace("${r.correo?", "").replace("${r.plazo?", "").replace("${r.cuando?", "").replace("${r.zoom&&r.zoom.url?", ""))
revisar("datos. la causa del diario lee su propio aviso y la causa a mano lee el texto guardado si lo hay",
        '"requisitos": RQ.para_ficha(f["tribunal"], f.get("aviso_texto"), f["modalidad"])' in datos and '"requisitos": requisitos_manual(m)' in datos and 'q = RQ.para_ficha(m["tribunal"], a["texto"] if a else None, m["modalidad"])' in datos)
# 13 de Noviembre (Diego). Causa a mano C-8034-2020 del 2° Civil con el texto del recorte del diario (db\avisos_a_mano.json).
from interfaz import datos as D
_am = D.aviso_a_mano("2° Juzgado Civil de Santiago", "8034", "2020")
_qm = D.requisitos_manual({"tribunal": "2° Juzgado Civil de Santiago", "rol": "8034", "anio": "2020", "modalidad": "zoom"})
revisar("a mano. C-8034-2020 lee su aviso copiado de la foto, cédula, contacto y link por correo con el plazo y su horario",
        _am and [r["clave"] for r in _qm["requisitos"]] == ["cedula", "contacto", "link_por_correo"] and not _qm["a_mano"] and _qm["advertencias"] == []
        and _qm["requisitos"][0]["plazo"] == "el día hábil anterior a la fecha fijada para el remate, entre las 12:00 y 14:00 horas" and _qm["fuente"].startswith("Copiado a mano"), _qm)
_qn = D.requisitos_manual({"tribunal": "2° Juzgado Civil de Santiago", "rol": "1", "anio": "2000", "modalidad": "zoom"})
revisar("a mano. una causa a mano sin texto guardado sigue mostrando la costumbre del tribunal como advertencia", _qn["a_mano"] and _qn["fuente"] is None and _qn["advertencias"][-1] == R.A_MANO, _qn)
revisar("ficha. la fuente del texto a mano se muestra en la caja", "${q.fuente?E(q.fuente)+'.':'Leído del aviso de esta causa.'}" in rq)
revisar("requisitos. el motor no importa nada de IA ni de internet", not re.search(r"anthropic|urllib|requests|haiku", (RAIZ / "motor" / "requisitos.py").read_text(encoding="utf-8").split('"""', 2)[2], re.I))

print("\nRESULTADO.", "TODO OK" if not FALLAS else f"{len(FALLAS)} fallas")
sys.exit(1 if FALLAS else 0)

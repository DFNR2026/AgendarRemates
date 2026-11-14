"""Requisitos extra para participar en un remate, además del vale vista (pedido de Diego, 13 de Noviembre de 2026).
Solo código, con patrones fijos, sin IA y sin costo. Se lee del texto del aviso de cada causa y se muestra con la frase que lo dice.
Nada se asume. Si un tribunal tiene un patrón fuerte y el aviso de una causa no lo trae, sale una advertencia de patrón roto, y el
paso siguiente es buscar la respuesta en las bases aprobadas o propuestas y, si no está ahí, preguntar en el tribunal.

Qué se lee (investigación del 13 de Noviembre sobre 574 causas de los 30 Juzgados Civiles de Santiago, REQUISITOS_PARTICIPAR.md).
  correo            mandar un correo al tribunal antes del remate, con su dirección y su plazo
  ojv               trámite previo por la Oficina Judicial Virtual (escrito, comprobante, vale vista digitalizado, módulo de remates)
  clave             Clave Única activa o firma electrónica avanzada
  cedula            copia de la cédula, o mostrarla
  contacto          dejar correo y teléfono
  formulario        formulario, acta predeterminada, documento anexo u hoja de datos que se llena al entregar el vale vista
  persona_juridica  personería, representante legal, RUT de la sociedad
  tercero           datos de la persona para quien se compra
  link, link_por_correo, link_en_causa, minutos, camara, equipo, ayuda     todo lo de la conexión por videoconferencia
Qué NO se lee, por decisión de Diego del 13 de Noviembre. Lo de después de adjudicar (firma del acta, pago del saldo, devolución),
que queda para el futuro, y el Registro de Deudores de Pensiones de Alimentos, que es irrelevante.
La palabra correo sola no es un requisito. En el 2° y el 26° Civil el correo es para avisar el pago del saldo y en el 8° es para
consultas (verificado en los avisos el 13 de Noviembre)."""
import functools, json, re
from pathlib import Path

_PATRON = Path(__file__).resolve().parent.parent / "db" / "requisitos_patron.json"
UMBRAL = 0.80          # patrón fuerte si lo dice el 80% de las causas del tribunal (propuesto por Claude el 13 de Noviembre)
MIN_CAUSAS = 10        # y el tribunal tiene al menos 10 causas medidas
# Solo estos requisitos generan advertencia de patrón roto. Los de equipo, minutos, cámara y ayuda son demasiado blandos.
AVISAN = ("correo", "ojv", "clave", "cedula", "contacto", "formulario", "link", "link_por_correo")
VIDEO = ("zoom", "en_linea", "mixta")
TITULO = {"correo": "CORREO AL TRIBUNAL", "ojv": "OFICINA JUDICIAL VIRTUAL", "clave": "CLAVE ÚNICA", "cedula": "CÉDULA",
          "contacto": "DATOS DE CONTACTO", "formulario": "FORMULARIO", "persona_juridica": "PERSONA JURÍDICA",
          "tercero": "COMPRA PARA OTRO", "link": "CONEXIÓN", "link_por_correo": "LINK", "link_en_causa": "LINK",
          "minutos": "ENTRAR ANTES", "camara": "CÁMARA", "equipo": "EQUIPO", "ayuda": "CORREO DEL TRIBUNAL"}
NOMBRE = {"correo": "piden mandar un correo al tribunal antes del remate", "ojv": "piden un trámite previo por la Oficina Judicial Virtual",
          "clave": "piden Clave Única o firma electrónica avanzada", "cedula": "piden copia de la cédula o mostrarla",
          "contacto": "piden dejar correo y teléfono", "formulario": "piden llenar un formulario o anexo al entregar el vale vista",
          "link": "traen el link o el ID de la videoconferencia", "link_por_correo": "dicen que el link de la videoconferencia llega por correo"}
ROTO = ("Se rompió el patrón del tribunal. Busca la respuesta en las bases aprobadas o propuestas y, si no está ahí, pregunta en el "
        "tribunal. No se asume el requisito.")
A_MANO = ("Esta causa se agregó a mano y no tiene aviso que leer. Lo de arriba es la costumbre del tribunal, no un dato de esta causa. "
          "Búscalo en las bases aprobadas o propuestas y, si no está ahí, pregunta en el tribunal.")
ORDEN = list(TITULO)
AL_ENTREGAR = "Al entregar el vale vista. La fecha está en la caja Entrega del vale vista."

_P = "\x00"            # punto protegido, para que una abreviatura o un correo no corten la oración
_ABREV = re.compile(r"\b(hrs|hs|Sra|Sr|Srta|Excma|Iltma|art|arts|Art|inc|N|No|Nro|fs|Fs|sig|sgte|sgtes|S\.A|S\.S|s\.s|Ltda|Cía|Av|Avda|"
                    r"Dpto|Depto|Of|aprox|pág|O\.J\.V|OJ\.V|O\.J|R\.U\.T|U\.F)\.", re.I)
# Puntos de adentro de una dirección de internet ("zoom. us", "www.pjud.cl"). "plataforma Zoom. El saldo" sí corta la oración.
_DOMINIO = re.compile(r"\b(?:zoom|pjud-?\s?cl|www|pjud|poderjudicial|docs|google|reca)\.\s?(?=(?:us|cl|com|pjud|zoom|google|poderjudicial)\b)", re.I)
_CORTE = re.compile(r"\.(?:-)?\s+(?=[A-ZÁÉÍÓÚÑ¿‘“\"'(]|\d\)\s)")
# El diario parte los correos con espacios ("xandrade @pjud.cl", "jcsantiago8_ remates@pjud.cl", "22jcivil santiago_remates@pjud.cl").
_MAIL = re.compile(r"(?<![\w.])((?:\d+jcivil\s?)?[A-Za-z][\w.]*(?:_\s?[A-Za-z]\w*)?_?)\s?@\s?pjud\.\s?cl\b", re.I)
# Solo cuentan las direcciones del Poder Judicial. El aviso C-5164-2025 del 29° trae pegado un correo de gmail que no es del tribunal.
# Texto de una demanda notificada por avisos, pegado al remate ("Tercer Otrosí: Personería"). No es un requisito.
_NO_AVISO = re.compile(r"otros[íi]\b|notif[íi]quese|vengo\s+en\b", re.I)
_TRIB_MAIL = re.compile(r"correo\s+electr[óo]nico\s+del\s+tribunal", re.I)
# Después de adjudicar o devolución. Fuera de esta tarea (Diego, 13 de Noviembre).
_DESPUES = re.compile(r"\bsaldo\b|pagarse|\bpagar\b|pagadero|adjudicatari|acta\s+(?:de\s+)?remate|ratific|devuelt|a\s+su\s+devoluci|"
                      r"retirar\s+(?:su\s+documentaci|el\s+documento)|podr[áa]\s+ser\s+retirado|transferencias\s+realizadas|escritura", re.I)
# Para cédula, contacto y formulario. El 1° Civil pide los datos del "representante de la empresa adjudicataria" ANTES del remate.
_DESPUES_SUAVE = re.compile(r"\bsaldo\b|pagarse|pagadero|acta\s+(?:de\s+)?remate|ratific|devuelt|a\s+su\s+devoluci|retirar\s+(?:su\s+documentaci|el\s+documento)|"
                            r"podr[áa]\s+ser\s+retirado|transferencias\s+realizadas|escritura", re.I)
_NO_POSTOR = re.compile(r"^\W*(?:en\s+el\s+caso\s+del\s+|el\s+)?ejecutante\b|^\W*(?:las\s+)?partes\s+del\s+juicio", re.I)
_ENVIAR = re.compile(r"envi\w+|remit\w+|coordin\w+|comunicar|confirmar|solicit\w+|manifest\w+|acompa[ñn]ar\s+comprobante", re.I)
_AYUDA = re.compile(r"problemas\s+de\s+conexi|consultas?\b|consultad|\bdudas\b|no\s+pudiere\s+acceder|correo\s+institucional", re.I)
_OJV = re.compile(r"oficina\s+judicial\s+virtual|(?<!\w)o\.?\s?j\.?\s?v\b\.?|carpeta\s+electr[óo]nica|expediente\s+digital|"
                  r"m[óo]dulo\s+\W?(?:audiencias?\s+de\s+remates?|remates|mis\s+remates)", re.I)
_OJV_PRE = re.compile(r"postor|interesad|garant|cauci|vale\s+vista|cup[óo]n|intenci[óo]n|digitaliz|postula", re.I)
_OJV_NO = re.compile(r"antecedentes\s+(?:en\s+)?(?:la\s+)?(?:oficina|carpeta|o\.?j)|incorporad[ao]\s+(?:a\s+la\s+|en\s+la\s+|a\s+)?carpeta|"
                     r"ejecutante\s+(?:y\s+acreedor\s+hipotecario,?\s+)?deber", re.I)
# Tener, contar con o mantener la clave. "El juez firmará con su firma electrónica avanzada" y "el adjudicatario firmará con clave
# única" no son requisitos para participar, son de después.
_CU = r"(?:clave\s+[úu]nica|firma\s+(?:electr[óo]nica|digital)\s+avanzad\w*)"
_CLAVE = re.compile(r"(?:\bten(?:er|ga|gan|dr[áa]n?)|\bcontar|\bcuenten?|\bmantener|\butilizar)\W+(?:\w+\W+){0,4}?" + _CU +
                    "|" + _CU + r"(?:\s+del\s+estado)?\s+activ|verificar\s+con\s+su\s+clave\s+[úu]nica", re.I)
_CLAVE_NO = re.compile(r"exceptuad", re.I)
_CEDULA = re.compile(r"(?:foto)?copia[^.]{0,80}?(?:c[ée]dula|carn[ée]t?\b)|(?:c[ée]dula|carn[ée]t?)\b[^.]{0,50}?copia\s+simple|"
                     r"exhibir\s+(?:en\s+c[áa]mara\s+)?(?:su\s+|sus\s+respectivas\s+)?c[ée]dula|exhibici[óo]n\s+de\s+la\s+(?:correspondiente\s+)?c[ée]dula|"
                     r"c[ée]dula\s+de\s+identidad\s+vigente|su\s+c[ée]dula\s+de\s+identidad\s+vigente", re.I)
_CONTACTO = re.compile(r"(?:correo|e-?mail)[^.]{0,140}?(?:tel[ée]f[oó]n|celular)|(?:tel[ée]f[oó]n|celular)[^.]{0,140}?(?:correo|e-?mail)|registrar\s+correo", re.I)
_FORM = re.compile(r"formulario|acta\s+predeterminada|documento\s+anexo|datos\s+necesarios\s+para\s+su\s+individualizaci[óo]n", re.I)
_PJ = re.compile(r"personer[íi]a|(?:copia|c[ée]dula|datos|rut)[^.]{0,80}representante\s+legal|representante\s+legal[^.]{0,60}(?:nombre|rut)|"
                 r"persona\s+jur[íi]dica[^.]{0,90}(?:exhibir|rut)|rut\s+de\s+la\s+sociedad", re.I)
_TERCERO = re.compile(r"(?:adjudique|adquir\w+)\s+para\s+(?:un\s+)?tercero|para\s+qui[ée]n\s+pretende\s+adquirir|por\s+quien\s+se\s+presentan|"
                      r"en\s+representaci[óo]n\s+de\s+un\s+tercero", re.I)
_ZOOM_URL = re.compile(r"(pjud-?\s?cl\.\s?)?zoom\.?\s?us/\s?j/\s?((?:\d\s?){9,11})", re.I)
_ZOOM_ID = re.compile(r"\bID\b\s*(?:zoom\s*)?(?:de\s+)?(?:la\s+)?(?:reuni[óo]n|audiencia|tribunal)?\s*(?:N°)?\s*:?\s*((?:\d\s?){9,11})(?!\d)", re.I)
_ZOOM_LINK_NUM = re.compile(r"\blink\s*:\s*((?:\d\s?){9,11})(?!\d)", re.I)       # el 22° Civil escribe "en el link: 98584722830"
_ZOOM_COD = re.compile(r"(?:c[óo]digo\s+(?:de\s+)?acceso|contraseña|\bclave)\s*:?\s*(\d{4,8})\b", re.I)
_LINK_CORREO = re.compile(r"(?:link|enlace|invitaci[óo]n(?:es)?)\b[^.]{0,60}?(?:(?:v[íi]a|por|mediante|al)\s+correo|se\s+remitir[áa]|ser[áa]\s+enviad)|"
                          r"(?:remitir[áa]?n?|enviar[áa])\s+(?:v[íi]a\s+|un\s+)*correo\s+electr[óo]nico[^.]{0,260}?(?:link|datos\s+necesarios|forma\s+de\s+conectarse|invitaci)|"
                          r"comunicar[áa]\s+mediante\s+correo|recibir(?:[áa]n)?\s+(?:el\s+)?(?:link|enlace)|se\s+enviar[áa]\s+la\s+invitaci[óo]n|remit\w+\s+las?\s+invitaci[óo]n", re.I)
_LINK_CAUSA = re.compile(r"publicar[áa]\s+en\s+(?:los\s+)?(?:presentes\s+)?autos|link[^.]{0,60}se\s+publicar[áa]\s+en\s+(?:los\s+)?autos|"
                         r"link\s+que\s+(?:se\s+)?estampar[áa]\s+en\s+la\s+resoluci[óo]n|agenda\s+de\s+remates\s+en\s+la\s+p[áa]gina", re.I)
_MINUTOS = re.compile(r"(\d{1,2})\s+minutos\s+(?:de\s+)?(?:antelaci[óo]n|anticipaci[óo]n)|(?:antelaci[óo]n|anticipaci[óo]n)\s+de\s+(\d{1,2})\s+minutos", re.I)
_CAMARA = re.compile(r"c[áa]mara\s+encendida|habilitad[ao]s?\s+y\s+activos|habilitadas?\s+la\s+c[áa]mara|exhib\w+\s+(?:en|a\s+la)\s+c[áa]mara", re.I)
_EQUIPO = re.compile(r"c[áa]mara|micr[óo]fono|elementos?\s+(?:de\s+conexi[óo]n\s+y\s+)?tecnol[óo]gicos|medios?\s+tecnol[óo]gicos?|conexi[óo]n\s+a\s+internet", re.I)
_VV = re.compile(r"vale\s+(?:a\s+la\s+)?vista|en\s+(?:dicho|el\s+mismo)\s+acto|dicho\s+documento|garant[íi]a|cauci[óo]n", re.I)
_PLAZO = re.compile(r"(?:a\s+m[áa]s\s+tardar,?\s|hasta\s+(?:las\s+)?\d|hasta\s+el\s+d[íi]a|antes\s+de\s+las\s+\d|con\s+(?:a\s+lo\s+menos|al\s+menos)\s|"
                    r"al\s+menos\s+(?:veinticuatro|un|una|\d+)\s+(?:horas?|d[íi]as?|semanas?)|"
                    r"(?:el\s+)?d[íi]a\s+(?:h[áa]bil\s+)?(?:inmediatamente\s+)?(?:anterior|precedente)|"
                    r"(?:el\s+)?(?:d[íi]a\s+)?(?:lunes|martes|mi[ée]rcoles|jueves|viernes)\s+(?:(?:inmediatamente\s+)?anterior|de\s+la\s+semana\s+anterior))"
                    r"[^,;.]{0,150}(?:,?\s+y\s+si\s+dicho\s+d[íi]a\s+fuer[ae]\s+s[áa]bado,?\s+[^,;.]{0,80})?"
                    # 13 de Noviembre (Diego, punto 1). El horario que viene pegado después de la coma, "el día hábil anterior a la fecha
                    # fijada para el remate, entre las 12:00 y 14:00 horas" (2° Civil), también es parte del plazo.
                    r"(?:,?\s+(?:entre|de|desde)\s+(?:las\s+)?\d{1,2}(?:[:.]\d{2})?\s+(?:y|a|hasta)\s+(?:las\s+)?\d{1,2}(?:[:.]\d{2})?(?:\s*(?:horas|hrs\.?|hs\.?))?)?", re.I)
# Los avisos telegráficos no ponen comas. El plazo se corta donde empieza la orden siguiente.
_PLAZO_FIN = re.compile(r"\s(?:deber\w*|postores|interesados|indicando|mediante|debiendo|ingresando|acompañando|oportunidad|y\s+cuya|a\s+fin\s+de|en\s+cuyo)\b", re.I)
_CON_PLAZO = ("correo", "ojv", "cedula", "contacto", "formulario")


def oraciones(texto: str | None) -> list:
    """Las oraciones del aviso, con los espacios en uno. Una abreviatura, un correo o un link no cortan la oración."""
    t = re.sub(r"\s+", " ", texto or "").strip()
    t = _ABREV.sub(lambda m: m.group(0).replace(".", _P), t)
    t = _DOMINIO.sub(lambda m: m.group(0).replace(".", _P), t)
    t = re.sub(r"(\d)\.(?=\d)", r"\1" + _P, t)
    t = re.sub(r"@\s?(\w+)\.\s?(cl|com)\b", lambda m: m.group(0).replace(".", _P), t)
    return [o.strip() for o in _CORTE.split(t) if o.strip()]


def _limpia(o: str) -> str:
    return o.replace(_P, ".")


def correos(o: str) -> list:
    """Direcciones de correo escritas en la oración, sin los espacios que mete el diario."""
    out = []
    for m in _MAIL.finditer(o.replace(_P, ".")):
        out.append((m.start(), re.sub(r"\s", "", m.group(1)).lower() + "@pjud.cl"))
    return sorted(out)


def _plazo(o: str, pos: int):
    """El plazo escrito en la oración, con las palabras del aviso. Primero el que viene después del requisito, si no el anterior más cercano."""
    todos, i = [], 0
    while True:
        m = _PLAZO.search(o, i)
        if not m:
            break
        txt = m.group(0)
        c = _PLAZO_FIN.search(txt, 12)
        if c:
            txt = txt[:c.start()]
        a, b = m.start(), m.start() + len(txt)
        if todos and a - todos[-1][1] <= 2:          # "a más tardar el día hábil anterior a la subasta, hasta las 12:30 hrs" es un solo plazo
            todos[-1] = (todos[-1][0], b)
        else:
            todos.append((a, b))
        i = max(b, m.start() + 1)
    if not todos:
        return None
    despues = [p for p in todos if p[0] >= pos]
    a, b = despues[0] if despues else todos[-1]
    return _limpia(o[a:b]).strip(" ,")


def _frase(o: str, pos: int, largo=900) -> str:
    """La oración tal como está en el aviso. Si es muy larga, el tramo desde un poco antes del primer requisito, con puntos suspensivos."""
    o2 = _limpia(o)
    if len(o2) <= largo:
        return o2
    a = max(0, pos - 300)
    b = min(len(o2), a + largo)
    a = max(0, b - largo)
    if a:
        a = o2.find(" ", a) + 1
    if b < len(o2):
        b = o2.rfind(" ", 0, b)
    return ("… " if a else "") + o2[a:b] + (" …" if b < len(o2) else "")


def _zoom(o: str):
    """ID, código y dirección de Zoom de la oración. El ID escrito manda sobre el del link, porque el diario parte y ensucia los links."""
    u, i, c = _ZOOM_URL.search(o.replace(_P, ".")), _ZOOM_ID.search(o) or _ZOOM_LINK_NUM.search(o), _ZOOM_COD.search(o)
    if not (u or i):
        return None
    del_link = re.sub(r"\s", "", u.group(2)) if u else None
    del_id = re.sub(r"\s", "", i.group(1)) if i else None
    ident = del_id or del_link
    casa = "pjud-cl.zoom.us" if (u and u.group(1)) else "zoom.us"
    distintos = bool(del_link and del_id and del_link != del_id)      # el aviso trae dos números. No se arma link, se muestra la frase
    return {"id": ident, "otro_id": del_link if distintos else None, "codigo": c.group(1) if c else None,
            "url": None if distintos else f"https://{casa}/j/{ident}"}


def leer(texto: str | None) -> list:
    """Copia de la lectura guardada. El buscador pide la misma causa muchas veces y leer un aviso cuesta unos milisegundos."""
    return [dict(r) for r in _leer(texto)]


@functools.lru_cache(maxsize=4096)
def _leer(texto: str | None) -> tuple:
    """Lista de requisitos del aviso. Cada uno con clave, título, detalle, plazo, correo, frase del aviso y, en la conexión, el Zoom.
    Una clave puede salir más de una vez si dos oraciones distintas la piden (el 15° Civil pide dos correos)."""
    out, vistos, frases = [], set(), {}

    def pon(clave, o, pos, detalle, **mas):
        frase = frases.setdefault(o, _frase(o, pos))          # una sola cita por oración, aunque traiga varios requisitos
        k = (clave, detalle, mas.get("correo"), mas.get("plazo"))
        if k in vistos:
            return
        vistos.add(k)
        cuando = mas.get("cuando") if not mas.get("plazo") else None
        out.append({"clave": clave, "titulo": TITULO[clave], "detalle": detalle, "plazo": mas.get("plazo"), "cuando": cuando,
                    "correo": mas.get("correo"), "zoom": mas.get("zoom"), "frase": frase})

    for o in oraciones(texto):
        if _NO_AVISO.search(o):
            continue
        despues, no_postor = bool(_DESPUES.search(o)), bool(_NO_POSTOR.search(o))
        ms = correos(o)
        oc = _limpia(o)          # mismo largo que o, así las posiciones valen para los dos
        trib_mail = _TRIB_MAIL.search(o)
        # correo al tribunal antes del remate, o correo de ayuda
        if (ms or trib_mail) and not no_postor:
            pos = ms[0][0] if ms else trib_mail.start()
            dire = " y ".join(dict.fromkeys(d for _, d in ms)) if ms else None
            ay = _AYUDA.search(o)
            if ay and ay.start() < pos:          # la consulta va antes de la dirección. En el 29° "problemas de conexión" va después y es un requisito
                pon("ayuda", o, pos, "Para consultas o problemas de conexión", correo=dire)
            elif _ENVIAR.search(o) and not despues:
                if re.search(r"c[óo]digo\s+de\s+acceso", o, re.I):
                    det = "Pide por correo el código de acceso de la videoconferencia"
                elif re.search(r"comunicar\w*\s+(?:previamente\s+)?(?:su\s+)?asistencia", o, re.I):
                    det = "Avisa por correo quién irá a dejar el vale vista"
                else:
                    det = "Escribe al tribunal antes del remate"
                pon("correo", o, pos, det, correo=dire, plazo=_plazo(o, pos))
        # trámite previo por la Oficina Judicial Virtual
        m = _OJV.search(oc)
        if m and _OJV_PRE.search(o) and not despues and not no_postor and not _OJV_NO.search(oc):
            solo_cupon = re.search(r"cup[óo]n", o, re.I) and not re.search(r"vale\s+vista", o, re.I)
            det = ("Solo si la garantía es con cupón de pago, se sube por la Oficina Judicial Virtual" if solo_cupon
                   else "Revisa en Mis Remates, con tu Clave Única, que el tribunal te aceptó antes de entregar el vale vista"
                   if re.search(r"mis\s+remates|aceptado\s+por\s+el\s+tribunal", o, re.I)
                   else "Sube el vale vista digitalizado por la Oficina Judicial Virtual" if re.search(r"digitaliz|imagen\s+digital", o, re.I)
                   else "Ingresa un escrito por la Oficina Judicial Virtual" if re.search(r"escrito", o, re.I)
                   else "Sube el comprobante de la garantía por la Oficina Judicial Virtual" if re.search(r"comprobante|copia\s+legible", o, re.I)
                   else "Trámite previo por la Oficina Judicial Virtual")
            pon("ojv", o, m.start(), det, plazo=_plazo(o, m.start()))
        if not _DESPUES_SUAVE.search(o) and not no_postor:
            junto = "Junto con el vale vista" if _VV.search(o) else None
            # 13 de Noviembre (Diego, punto 1). Si la frase va junto con la entrega del vale vista y no trae su propia fecha, el momento es
            # esa entrega, cuya fecha está en la caja Entrega del vale vista. No se calcula ni se asume otra fecha.
            al_vv = AL_ENTREGAR if junto else None
            m = _CEDULA.search(o)
            if m:
                det = ("Copia de la cédula" if re.search(r"copia", o, re.I) else "Muestra tu cédula" if re.match(r"exhib", m.group(0), re.I)
                       else "Lleva tu cédula vigente")
                pon("cedula", o, m.start(), det, plazo=_plazo(o, m.start()) if junto else None, cuando=al_vv)
            m = _CONTACTO.search(o)
            if m and not (ms and _AYUDA.search(o) and _AYUDA.search(o).start() < ms[0][0]):
                pon("contacto", o, m.start(), "Deja tu correo y tu teléfono", plazo=_plazo(o, m.start()) if junto else None, cuando=al_vv)
            m = _FORM.search(o)
            if m:
                pon("formulario", o, m.start(), "Se llena al entregar el vale vista" if junto else "Formulario", plazo=_plazo(o, m.start()) if junto else None, cuando=al_vv)
            m = _PJ.search(o)
            if m:
                pon("persona_juridica", o, m.start(), "Si participas como empresa")
            m = _TERCERO.search(o)
            if m:
                pon("tercero", o, m.start(), "Si compras para otra persona, lleva sus datos")
        m = _CLAVE.search(o)
        if m and not _CLAVE_NO.search(o):
            ambas = re.search(r"firma\s+(?:electr[óo]nica|digital)\s+avanzad", o, re.I) and re.search(r"clave\s+[úu]nica", o, re.I)
            solo_fea = not re.search(r"clave\s+[úu]nica", o, re.I)
            pon("clave", o, m.start(), "Clave Única o firma electrónica avanzada" if ambas else "Firma electrónica avanzada" if solo_fea else "Clave Única activa")
        # conexión por videoconferencia
        z = _zoom(o)
        if z:
            u = _ZOOM_URL.search(o.replace(_P, ".")) or _ZOOM_ID.search(o) or _ZOOM_LINK_NUM.search(o)
            det = "ID " + z["id"] + (" y código " + z["codigo"] if z["codigo"] else "")
            if z["otro_id"]:
                det = f"El aviso trae dos números distintos, {z['id']} en el ID y {z['otro_id']} en el link. Mira la frase"
            pon("link", o, u.start(), det, zoom=z)
        m = _LINK_CORREO.search(o)
        if m and not despues:
            pon("link_por_correo", o, m.start(), "El link llega por correo")
        m = _LINK_CAUSA.search(o)
        if m:
            pon("link_en_causa", o, m.start(), "El link se publica en la causa o en la agenda de remates del Poder Judicial")
        m = _MINUTOS.search(o)
        if m and not despues:
            pon("minutos", o, m.start(), f"Entra {m.group(1) or m.group(2)} minutos antes")
        m = _CAMARA.search(o)
        if m:
            pon("camara", o, m.start(), "Cámara y micrófono encendidos, y la cédula a la vista si la piden")
        elif _EQUIPO.search(o) and not despues:
            pon("equipo", o, _EQUIPO.search(o).start(), "Computador o teléfono con cámara, micrófono e internet")
    out.sort(key=lambda r: ORDEN.index(r["clave"]))
    return tuple(out)


@functools.lru_cache(maxsize=1)
def patron() -> dict:
    """Se lee una vez por cada vez que se abre la agenda. Tabla medida de cuántas causas de cada tribunal dicen cada requisito (db\\requisitos_patron.json, la escribe
    pruebas\\medir_requisitos.py). Sin archivo no hay advertencias."""
    try:
        return json.loads(_PATRON.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def fuertes(tribunal: str | None, tabla: dict | None = None) -> list:
    """Requisitos que son patrón fuerte en ese tribunal. [(clave, causas que lo dicen, causas medidas)]."""
    t = ((tabla if tabla is not None else patron()).get("tribunales") or {}).get((tribunal or "").strip())
    if not t or t["causas"] < MIN_CAUSAS:
        return []
    return [(k, t["requisitos"].get(k, 0), t["causas"]) for k in AVISAN if t["requisitos"].get(k, 0) / t["causas"] >= UMBRAL]


def _corto(tribunal):
    m = re.match(r"(\d+°)\s+Juzgado\s+Civil", tribunal or "")
    return (m.group(1) + " Civil") if m else (tribunal or "este tribunal")


def para_ficha(tribunal: str | None, texto: str | None, modalidad: str | None = None, tabla: dict | None = None) -> dict:
    """Lo que muestra la caja de requisitos de la ficha. Cada causa muestra lo que dice su propio aviso. Las advertencias salen cuando
    el tribunal tiene un patrón fuerte y este aviso no lo trae. Sin texto (causa a mano) solo van las costumbres del tribunal como
    advertencia, porque no hay aviso que leer."""
    reqs = leer(texto) if texto is not None else []
    tengo = {r["clave"] for r in reqs}
    adv, faltan = [], []
    video = modalidad in VIDEO
    for k, si, n in fuertes(tribunal, tabla):
        if k in tengo or (k in ("link", "link_por_correo") and modalidad == "presencial"):
            continue
        faltan.append(k)
        base = f"En el {_corto(tribunal)} {si} de {n} causas medidas {NOMBRE[k]}"
        adv.append(base + ("." if texto is None else " y el aviso de esta causa no lo trae."))
    if adv:
        adv.append(A_MANO if texto is None else ROTO)
    conexion = ("link", "link_por_correo", "link_en_causa", "correo")       # con un correo para coordinar ya se sabe a quién pedirlo
    if texto is not None and video and not (tengo & set(conexion)) and not (set(faltan) & {"link", "link_por_correo"}):
        adv.append("El remate es por videoconferencia y el aviso no dice cómo llega el link. Búscalo en las bases o pregunta en el tribunal.")
    frases = list(dict.fromkeys(r["frase"] for r in reqs))
    return {"requisitos": reqs, "frases": frases, "advertencias": adv, "a_mano": texto is None,
            "nada": texto is not None and not reqs}

"""Extracción por código de los datos de formato fijo de un aviso (parte 3.6).
Cada valor sale con la frase exacta del aviso de donde se sacó (cita). Si el código no está seguro, deja el valor
vacío y agrega una alerta. Nunca adivina.

Etapa 1. Fecha y hora del remate.
"""
import datetime as dt
import re

MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
         "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}
_MES = "|".join(MESES)
_DIA_SEM = r"(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)\s+"
# "6 de noviembre de 2026", "3 noviembre 2026", "05 de noviembre del año 2026", "29 de Octubre 2026"
FECHA_TEXTO = re.compile(rf"\b(\d{{1,2}})\s+(?:de\s+)?({_MES})\s*,?\s+(?:de\s+|del\s+)?(?:a[ñn]o\s+)?(\d{{4}})\b", re.I)
# "11/11/2026", "27/10/ 2026"
FECHA_NUM = re.compile(r"\b(\d{1,2})/(\d{1,2})/\s?(\d{4})\b")
# "a las 13:15 horas", "13:45 hrs.", "a las 11.30 horas", "a las 11:00,", "A Las 15:05 Horas", "10:30 HRS"
HORA = re.compile(r"(?:\ba(?:\s+las)?\s+)?\b(\d{1,2})[:.]\s?(\d{2})\b(?:\s*(?:horas|hrs?)\b\.?)?", re.I)
# Palabras que anuncian el remate
VERBO = re.compile(r"\b(?:se\s+)?(?:rematar[áa]n?|remata|subastar[áa]n?|se\s+subasta|remate|subasta|llamado\s+con\s+fecha)\b", re.I)


def _fechas(texto):
    """Todas las fechas del aviso, en orden. (inicio, fin, AAAA-MM-DD, cita)."""
    out = []
    for m in FECHA_TEXTO.finditer(texto):
        try:
            d = dt.date(int(m.group(3)), MESES[m.group(2).lower()], int(m.group(1)))
        except ValueError:
            continue
        out.append((m.start(), m.end(), d.isoformat(), m.group(0)))
    for m in FECHA_NUM.finditer(texto):
        try:
            d = dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            continue
        out.append((m.start(), m.end(), d.isoformat(), m.group(0)))
    return sorted(out)


def _hora_tras(texto, desde, hasta):
    """Primera hora válida en texto[desde:hasta] que venga con 'a las' delante o 'horas/hrs' detrás."""
    for m in HORA.finditer(texto, desde, hasta):
        h, mi = int(m.group(1)), int(m.group(2))
        tiene_marca = m.group(0).lower().startswith("a") or re.search(r"(?:horas|hrs?)\.?$", m.group(0), re.I)
        if 0 <= h <= 23 and 0 <= mi <= 59 and tiene_marca:
            return f"{h:02d}:{mi:02d}", m.group(0).strip()
    return None, None


def fecha_y_hora(texto: str, fecha_edicion: str | None = None) -> dict:
    """Devuelve {'fecha_remate': {valor, cita}, 'hora_remate': {valor, cita}, 'alertas': [(tipo, texto)]}."""
    alertas = []
    fechas = _fechas(texto)
    # Fecha del remate. La primera fecha que aparece dentro de los 250 caracteres que siguen a un verbo de remate.
    candidatas = []
    for v in VERBO.finditer(texto):
        for ini, fin, valor, cita in fechas:
            if v.start() <= ini <= v.end() + 250:
                candidatas.append((ini, fin, valor, cita))
                break
    # También vale una fecha seguida de cerca (40 caracteres) por el verbo ("12/11/2026, 12:00 horas, se rematará", aviso 61 del 14-10).
    for v in VERBO.finditer(texto):
        for ini, fin, valor, cita in fechas:
            if fin <= v.start() <= fin + 40:
                candidatas.append((ini, fin, valor, cita))
    elegida = min(candidatas) if candidatas else None
    # Red de seguridad. Si hay fechas DISTINTAS que siguen de cerca (100 caracteres) a un verbo de remate,
    # el trozo puede traer dos avisos pegados. No se entrega fecha.
    cercanas = set()
    for v in VERBO.finditer(texto):
        for ini, fin, valor, cita in fechas:
            if v.end() <= ini <= v.end() + 100:
                cercanas.add(valor)
                break
    resultado = {"fecha_remate": {"valor": None, "cita": None}, "hora_remate": {"valor": None, "cita": None}, "alertas": alertas}
    if len(cercanas) > 1:
        alertas.append(("revisar_lectura", f"El trozo trae más de una fecha de remate ({', '.join(sorted(cercanas))}). Puede tener dos avisos pegados."))
        return resultado
    if not elegida:
        alertas.append(("revisar_lectura", "No se encontró la fecha del remate."))
        return resultado
    ini, fin, valor, cita = elegida
    resultado["fecha_remate"] = {"valor": valor, "cita": cita}
    if fecha_edicion and valor < fecha_edicion:
        alertas.append(("error_escritura", f"La fecha del remate ({valor}) es anterior a la edición del diario ({fecha_edicion})."))
    h, hc = _hora_tras(texto, fin, fin + 80)
    if h is None:
        h, hc = _hora_tras(texto, max(0, ini - 80), ini)
    if h is None:
        alertas.append(("revisar_lectura", "No se encontró la hora del remate junto a la fecha."))
    resultado["hora_remate"] = {"valor": h, "cita": hc}
    return resultado


# --- Etapa 2. Mínimo y costas -----------------------------------------------------------------------------
MINIMO = re.compile(r"m[ií]nimo", re.I)
# Una mención de "mínimo" que pertenece a la garantía o a las alzas no es el mínimo del remate
_NO_ES_MINIMO = re.compile(r"(?:%[^%]{0,15}|sobre\s+el\s+|conforme\s+al\s+|equivalente\s+al\s+)$", re.I)
_PESOS = r"\$\s?(\d{1,3}(?:\.\s?\d{3})+|\d+)"
_NUM_UF = r"(\d{1,3}(?:\.\d{3})+(?:\s?,\d+)?|\d+(?:\s?,\d+)?)"
MONTO = re.compile(
    rf"(\$\s?)?{_NUM_UF}\s*\.?-?\s*(?:UF\b|U\.F\.|unidades\s+de\s+fomento)"     # 355,969402 unidades de fomento / 1.100 UF / "$1.771,0860.- Unidades de Fomento" (signo $ por error)
    rf"|\bUF\s*{_NUM_UF}"                                                         # UF 2.824.-
    rf"|{_PESOS}", re.I)                                                          # $ 17.364.913
_ETIQUETA = re.compile(r"\b(oficina|lote|departamento|depto|casa|local|bodega|estacionamiento|parcela|sitio)\s*(?:N[°º]?\s*)?(\d+[A-Za-z]?)\b", re.I)


def _a_numero(m):
    """(monto, moneda, signo_pesos_en_uf). Grupos. 1 signo $ antes de UF, 2 número UF, 3 número tras 'UF', 4 pesos."""
    if m.group(4):
        return float(re.sub(r"[.\s]", "", m.group(4))), "CLP", False
    txt = m.group(2) or m.group(3)
    return float(re.sub(r"\s", "", txt).replace(".", "").replace(",", ".")), "UF", bool(m.group(1))


def _costas(texto, desde):
    """Costas que siguen al mínimo. Montos en pesos entre el último 'más' y la palabra 'costas' (hasta 250 caracteres),
    más una segunda parte 'y $ X ... costas' pegada a la primera (costas procesales y personales)."""
    fin_busqueda = desde + 250
    c = re.search(r"costas", texto[desde:fin_busqueda], re.I)
    if not c:
        return None, None
    pos_costas = desde + c.start()
    mas = [x for x in re.finditer(r"\bm[aá]s\b", texto[desde:pos_costas], re.I)]
    if not mas:
        return None, None
    ini = desde + mas[-1].start()
    fin = pos_costas + len("costas")
    montos = [float(re.sub(r"[.\s]", "", x.group(1))) for x in re.finditer(_PESOS, texto[ini:pos_costas])]
    if not montos:
        # la palabra costas va antes del monto ("más las costas procesales y personales que corresponden a la suma de $ 1.315.000")
        alreves = re.match(rf"[^.$]{{0,90}}?suma\s+de\s+{_PESOS}", texto[fin:fin + 130], re.I)
        if alreves:
            montos = [float(re.sub(r"[.\s]", "", alreves.group(1)))]
            fin = fin + alreves.end()
            return sum(montos), texto[ini:fin]
    seg = re.match(rf"[^$]{{0,40}}?\by\s+{_PESOS}[^$]{{0,40}}?costas", texto[fin:fin + 120], re.I)
    if seg:
        montos.append(float(re.sub(r"[.\s]", "", seg.group(1))))
        fin = fin + seg.end()
    if not montos:
        return None, None
    return sum(montos), texto[ini:fin]


def _monto_legible(monto, moneda):
    """$ 77.387.528 o 1.771,086 UF, como se escribe en Chile."""
    if moneda == "CLP":
        return "$ " + f"{monto:,.0f}".replace(",", ".")
    entero, _, dec = f"{monto:.6f}".rstrip("0").rstrip(".").partition(".")
    return f"{int(entero):,}".replace(",", ".") + ("," + dec if dec else "") + " UF"


def minimo_y_costas(texto: str) -> dict:
    """Devuelve {'minimo': {monto, moneda, costas_clp, cita, cita_costas} o {'lista': [...]}, 'alertas': [...]}."""
    alertas, hallados = [], []
    for a in MINIMO.finditer(texto):
        if _NO_ES_MINIMO.search(texto[max(0, a.start() - 30):a.start()]):
            continue
        m = MONTO.search(texto, a.end(), a.end() + 200)
        if not m:
            continue
        # el monto no debe pertenecer a otra mención de "mínimo" o a la garantía que esté entre medio
        entre = texto[a.end():m.start()]
        if re.search(r"%|garant[ií]a|cauci[oó]n", entre, re.I):
            continue
        monto, moneda, signo_raro = _a_numero(m)
        if signo_raro:
            alertas.append(("error_escritura", f"El aviso pone el signo $ a un monto en Unidades de Fomento ({m.group(0).strip()})."))
        # El inmueble de este mínimo. Primero el nombrado entre "mínimo" y el monto ("Mínimo para el Lote 1 es $"),
        # si no, el último nombrado en los 300 caracteres anteriores ("Lote 4. ... Estacionamiento N° 6 ..., cuyo mínimo").
        etiqueta = _ETIQUETA.search(texto, a.start(), m.start())
        if not etiqueta:
            previas = list(_ETIQUETA.finditer(texto, max(0, a.start() - 300), a.start()))
            etiqueta = previas[-1] if previas else None
        hallados.append({"monto": monto, "moneda": moneda, "cita": texto[a.start():m.end()], "fin": m.end(),
                         "inmueble": f"{etiqueta.group(1).lower()} {etiqueta.group(2)}" if etiqueta else None})
    vacio = {"monto": None, "moneda": None, "costas_clp": None, "cita": None}
    if not hallados:
        alertas.append(("revisar_lectura", "No se encontró el mínimo del remate."))
        return {"minimo": vacio, "alertas": alertas}
    # Un solo monto repetido es un solo remate. Varios montos, o el mismo monto para inmuebles distintos, son varios.
    if len({(h["monto"], h["moneda"]) for h in hallados}) == 1:
        distintos = hallados[:1]
    else:
        distintos = []
        for h in hallados:
            if (h["monto"], h["moneda"], h["inmueble"]) not in [(d["monto"], d["moneda"], d["inmueble"]) for d in distintos]:
                distintos.append(h)
    if len(distintos) == 1:
        h = distintos[0]
        costas, cita_c = _costas(texto, h["fin"])
        r = {"monto": h["monto"], "moneda": h["moneda"], "costas_clp": costas, "cita": h["cita"]}
        if cita_c:
            r["cita_costas"] = cita_c
        return {"minimo": r, "alertas": alertas}
    # Varios mínimos distintos. Solo es una lista de remates si cada uno nombra su lote, oficina o depto.
    if all(d["inmueble"] for d in distintos) and len({d["inmueble"] for d in distintos}) == len(distintos):
        lista = []
        for d in distintos:
            costas, cita_c = _costas(texto, d["fin"])
            el = {"monto": d["monto"], "moneda": d["moneda"], "costas_clp": costas, "cita": d["cita"], "inmueble": d["inmueble"]}
            lista.append(el)
        return {"minimo": {"lista": lista}, "alertas": alertas}
    alertas.append(("revisar_lectura", "El aviso trae varios montos mínimos y el código no pudo asignar cada uno a su inmueble: "
                    + ", ".join(_monto_legible(d["monto"], d["moneda"]) for d in distintos)))
    return {"minimo": vacio, "alertas": alertas}


# --- Etapa 3. Garantía --------------------------------------------------------------------------------------
_GARANTIA = re.compile(r"garant[ií]a|cauci[oó]n|vale\s+(?:a\s+la\s+)?vista|consignar", re.I)
_PORC = re.compile(r"(?:un\s+)?(\d{1,2}(?:,\d+)?)\s?%", re.I)
_MONTO_FIJO = re.compile(rf"(?:garant[ií]a|cauci[oó]n)[^.$%]{{0,40}}?{_PESOS}|ascendente\s+a\s+{_PESOS}", re.I)


def garantia(texto: str) -> dict:
    """Devuelve {'garantia': {porcentaje, base, base_origen, monto, moneda, cita}, 'alertas': [...]}.
    base_origen. 'texto' si el aviso dice de qué es el porcentaje. 'asumido' si no lo dice (decisión de Diego,
    se asume el mínimo y el HUD lo muestra como ASUMIDO)."""
    alertas = []
    anclas = [a.start() for a in _GARANTIA.finditer(texto)]
    porcentajes = []
    for p in _PORC.finditer(texto):
        # el porcentaje debe estar cerca de una palabra de garantía (hasta 300 caracteres después o 80 antes).
        # 300 por el aviso de Iquique ("garantía suficiente de cualquiera de estas dos formas... 10% del mínimo")
        if any(a - 80 <= p.start() <= a + 300 for a in anclas):
            porcentajes.append(p)
    g = {"porcentaje": None, "base": "sin_dato", "base_origen": None, "monto": None, "moneda": None, "cita": None}
    if porcentajes:
        p = porcentajes[0]
        g["porcentaje"] = float(p.group(1).replace(",", "."))
        if g["porcentaje"].is_integer():
            g["porcentaje"] = int(g["porcentaje"])
        despues = texto[p.end():p.end() + 45]
        fin = p.end()
        b = re.match(r"\s*(?:del?\s+|al\s+)?(?:(?:precio|valor|monto)\s+)?(?:de\s+(?:la\s+)?)?(m[ií]nimo|tasaci[oó]n)", despues, re.I)
        if b:
            g["base"] = "tasacion" if b.group(1).lower().startswith("tasaci") else "minimo"
            g["base_origen"] = "texto"
            fin = p.end() + b.end()
        else:
            g["base"], g["base_origen"] = "minimo", "asumido"
            alertas.append(("condicion_especial", f"{g['porcentaje']}% DEL MÍNIMO ASUMIDO. EL AVISO NO LO DICE."))
        g["cita"] = texto[p.start():fin]
        otros = {float(x.group(1).replace(",", ".")) for x in porcentajes[1:]} - {float(g["porcentaje"])}
        if otros:
            alertas.append(("revisar_lectura", f"El aviso menciona otro porcentaje cerca de la garantía ({', '.join(f'{o:g}%' for o in sorted(otros))})."))
    mf = _MONTO_FIJO.search(texto)
    if mf and not re.search(r"m[ií]nimo", texto[mf.start():mf.end()], re.I):
        g["monto"] = float(re.sub(r"[.\s]", "", mf.group(1) or mf.group(2)))
        g["moneda"] = "CLP"
        if g["cita"] is None:
            g["cita"] = mf.group(0)
    if g["porcentaje"] is None and g["monto"] is None:
        g["base"] = "sin_dato"
        alertas.append(("dato_faltante", "El código no encontró el porcentaje ni el monto de la garantía. Revisa el aviso o las bases."))
    if g["porcentaje"] is not None and g["porcentaje"] != 10:
        alertas.append(("condicion_especial", f"Garantía del {g['porcentaje']}%, no del 10%."))
    if g["base"] == "tasacion":
        alertas.append(("condicion_especial", "Garantía sobre la TASACIÓN, no sobre el mínimo."))
    return {"garantia": g, "alertas": alertas}


# --- Etapa 4. Modalidad -------------------------------------------------------------------------------------
_ZOOM = re.compile(r"\bzoom\b|video[\s-]?conferencia|telem[áa]tic[ao]|en\s+forma\s+virtual", re.I)
_OTRA_PLATAFORMA = re.compile(r"\b(?:google\s+)?meet\b|vendaya", re.I)
# Frases de remate presencial que usan los avisos
_PRESENCIAL = re.compile(
    r"(?:de|en)\s+(?:manera|forma)\s+presencial|\bpresencialmente\b|remate\s+presencial|modalidad\s+presencial|presencia\s+f[ií]sica"
    r"|(?:remat\w*|subast\w*|realizar[áa]|efectuar[áa]|llevar[áa]\s+a\s+cabo)\W+(?:\w+\W+){0,16}?"
    r"(?:en\s+)?(?:las\s+)?(?:dependencias|recinto)(?:\s+f[ií]sicas)?\s+(?:del?\s+)?(?:\w+\s+){0,2}?(?:tribunal|juzgado)", re.I)
# Si cerca de la frase se habla de la entrega o devolución del vale vista, no se refiere al remate
_NO_ES_REMATE = re.compile(r"vale\s+(?:a\s+la\s+)?vista|entreg|secretar|turno|devoluci|devuelt|restitu|retir|acompa[ñn]|garant|\bacta\b|suscrib|firma", re.I)
# Mixta dicha en una sola frase. "vía plataforma Zoom o en forma presencial", "vía www.vendaya.cl y presencialmente"
_MIXTA = re.compile(r"(?:zoom|video[\s-]?conferencia|meet|vendaya)[^.]{0,30}?\b(?:o|y)\s+(?:en\s+forma\s+|de\s+manera\s+)?presencial(?:mente)?"
                    r"|presencial(?:mente)?[^.]{0,30}?\b(?:o|y)\s+(?:v[ií]a\s+)?(?:zoom|video[\s-]?conferencia)", re.I)


def _presencial(texto):
    for m in _PRESENCIAL.finditer(texto):
        alrededor = texto[max(0, m.start() - 120):m.start()] + texto[m.end():m.end() + 30]
        if not _NO_ES_REMATE.search(alrededor) and not _NO_ES_REMATE.search(m.group(0)):
            return m
    return None


def modalidad(texto: str) -> dict:
    """Devuelve {'modalidad': {valor, cita}, 'plataforma': str|None, 'alertas': [...]}.
    valor. zoom, presencial, mixta, en_linea o sin_dato."""
    alertas = []
    z, o, p = _ZOOM.search(texto), _OTRA_PLATAFORMA.search(texto), _presencial(texto)
    mx = _MIXTA.search(texto)
    plataforma = None
    if o:
        plataforma = "Google Meet" if "meet" in o.group(0).lower() else "vendaya.cl"
    elif z and "zoom" in texto.lower():
        plataforma = "Zoom"
    virtual = z or o
    if mx or (virtual and p):
        valor, cita = "mixta", (mx or p).group(0)
        alertas.append(("condicion_especial", "El aviso nombra remate presencial y también en línea. Revisa cuál aplica."))
    elif o:
        valor, cita = "en_linea", o.group(0)
        alertas.append(("condicion_especial", f"Remate en línea por {plataforma}, no por Zoom."))
    elif z:
        valor, cita = "zoom", z.group(0)
    elif p:
        valor, cita = "presencial", p.group(0)
    else:
        valor, cita = "sin_dato", None
        alertas.append(("revisar_lectura", "El aviso no dice si el remate es por Zoom o presencial."))
    return {"modalidad": {"valor": valor, "cita": cita}, "plataforma": plataforma, "alertas": alertas}


# --- Etapa 5. Tribunal en forma única -----------------------------------------------------------------------
_UNIDADES = {"primer": 1, "primero": 1, "segundo": 2, "tercer": 3, "tercero": 3, "cuarto": 4, "quinto": 5, "sexto": 6,
             "septimo": 7, "séptimo": 7, "octavo": 8, "noveno": 9}
_DECENAS = {"decimo": 10, "décimo": 10, "vigesimo": 20, "vigésimo": 20, "trigesimo": 30, "trigésimo": 30}
_ESPECIALES = {"undecimo": 11, "undécimo": 11, "duodecimo": 12, "duodécimo": 12, "decimotercer": 13, "decimotercero": 13}
_PAL_ORD = "|".join(sorted(list(_UNIDADES) + list(_DECENAS) + list(_ESPECIALES), key=len, reverse=True))
_ORDINAL = rf"(?:(\d{{1,2}})\s*(?:°|º|er|ER|o\b)?|((?:{_PAL_ORD})(?:\s+(?:{_PAL_ORD}))?)(?:\s*\(\s*\d{{1,2}}\s*°?\s*\))?)"
_TIPO = (r"(civil|(?:de\s+)?letras\s+(?:en\s+lo\s+)?civil|(?:de\s+letras\s+)?(?:de\s+)?cobranza\s+laboral(?:\s+y\s+previsional)?"
         r"|de\s+letras(?:\s+del\s+trabajo)?|letras|de\s+familia|familia|de\s+polic[ií]a\s+local|polic[ií]a\s+local)")
# Palabras que no son ciudad ("7° JUZGADO CIVIL, EN calle Huérfanos 1409")
_NO_CIUDAD = {"en", "ubicado", "ubicada", "con", "causa", "autos", "rol", "huerfanos", "huérfanos", "calle", "avenida", "juicio", "expediente", "domiciliado"}
_TRIBUNAL = re.compile(rf"(?:{_ORDINAL}\s*)?juz(?:gado)?\.?\s+{_TIPO}\s*,?\s*(?:de\s+|del\s+)?([A-ZÁÉÍÓÚÑa-záéíóúñ]+(?:\s+(?!(?i:huerfanos|huérfanos|ubicado))(?-i:[A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ]+))?)", re.I)
_MINUSC = {"de", "del", "y"}


def _ordinal_a_numero(dig, pal):
    if dig:
        return int(dig)
    partes = pal.lower().split()
    if len(partes) == 1 and partes[0] in _ESPECIALES:
        return _ESPECIALES[partes[0]]
    total = 0
    for p in partes:
        total += _DECENAS.get(p, 0) + _UNIDADES.get(p, 0) + _ESPECIALES.get(p, 0)
    return total or None


def _titulo(txt):
    return " ".join(w if w in _MINUSC else w[:1].upper() + w[1:] for w in txt.lower().split())


def tribunal(texto: str) -> dict:
    """Devuelve {'tribunal': {valor, cita}, 'alertas': [...]}. Forma única. '7° Juzgado Civil de Santiago',
    'Juzgado de Letras de Colina', 'Juzgado de Cobranza Laboral y Previsional de Santiago'."""
    alertas = []
    m = _TRIBUNAL.search(texto[:400])
    if not m:
        alertas.append(("revisar_lectura", "No se encontró el tribunal al comienzo del aviso."))
        return {"tribunal": {"valor": None, "cita": None}, "alertas": alertas}
    num = _ordinal_a_numero(m.group(1), m.group(2)) if (m.group(1) or m.group(2)) else None
    tipo = re.sub(r"\s+", " ", m.group(3).lower())
    tipo = re.sub(r"^de\s+", "", tipo)
    if "civil" in tipo:
        tipo = "civil"                                            # "de Letras en lo Civil" y "de Letras Civil" son juzgados civiles
    elif "cobranza" in tipo:
        tipo = re.sub(r"^letras\s+(?:de\s+)?", "", tipo)          # "de Letras de Cobranza Laboral" es de Cobranza Laboral
    ciudad = m.group(4)
    if ciudad.split()[0].lower() in _NO_CIUDAD:
        ciudad = "Santiago" if re.search(r"hu[ée]rfanos", texto[m.end():m.end() + 150], re.I) else None
    if not ciudad:
        alertas.append(("revisar_lectura", "No se encontró la ciudad del tribunal."))
        return {"tribunal": {"valor": None, "cita": m.group(0)}, "alertas": alertas}
    ciudad = _titulo(ciudad)
    if tipo in ("letras", "de letras") and num and ciudad == "Santiago":
        tipo = "civil"                                            # en Santiago los juzgados de letras numerados son los civiles
    tipo = {"civil": "Civil"}.get(tipo, "de " + _titulo(tipo))
    valor = (f"{num}° " if num else "") + f"Juzgado {tipo} de {ciudad}"
    return {"tribunal": {"valor": valor, "cita": m.group(0)}, "alertas": alertas}


# --- Todo junto ----------------------------------------------------------------------------------------------
def extraer(texto: str, fecha_edicion: str | None = None) -> dict:
    """Corre las cinco extracciones. Si el trozo trae dos avisos pegados (dos fechas de remate distintas),
    NO entrega ningún dato. Solo la alerta, para que Diego lea el aviso en su página."""
    fh, mc, ga, mo, tr = fecha_y_hora(texto, fecha_edicion), minimo_y_costas(texto), garantia(texto), modalidad(texto), tribunal(texto)
    alertas = fh["alertas"] + mc["alertas"] + ga["alertas"] + mo["alertas"] + tr["alertas"]
    pegado = any("dos avisos pegados" in t for _, t in fh["alertas"])
    if pegado:
        return {"pegado": True, "fecha_remate": {"valor": None, "cita": None}, "hora_remate": {"valor": None, "cita": None},
                "minimo": {"monto": None, "moneda": None, "costas_clp": None, "cita": None},
                "garantia": {"porcentaje": None, "base": "sin_dato", "base_origen": None, "monto": None, "moneda": None, "cita": None},
                "modalidad": {"valor": "sin_dato", "cita": None}, "plataforma": None, "tribunal": {"valor": None, "cita": None},
                "alertas": [a for a in fh["alertas"] if "dos avisos pegados" in a[1]]}
    return {"pegado": False, "fecha_remate": fh["fecha_remate"], "hora_remate": fh["hora_remate"], "minimo": mc["minimo"],
            "garantia": ga["garantia"], "modalidad": mo["modalidad"], "plataforma": mo["plataforma"], "tribunal": tr["tribunal"],
            "alertas": alertas}

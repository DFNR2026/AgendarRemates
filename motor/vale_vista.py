"""Parte 3.7a. Regla del vale vista con IA (Claude Haiku 5.5). La IA nunca tiene la última palabra.

1. La IA elige la regla de una lista cerrada (escrita SOLO con lo visto en el banco del 14 de Octubre), entrega sus datos
   y la frase exacta de donde salen.
2. El código revisa la respuesta (verificar). Lo que no se puede comprobar queda en rojo.
3. El código calcula el desde y el hasta (calcular) con los feriados y las decisiones de Diego.
4. Dos lecturas por aviso. Si no coinciden, rojo. Las respuestas se guardan en ia_respuestas\\vale_vista por huella
   (modelo, versión de las instrucciones y texto del aviso), así una republicación no se paga dos veces y las pruebas
   corren sin internet.

Colores. verde (todo verificado), ambar (verificado, pero depende de una pregunta al abogado), rojo, sin_dato.
"""
import csv, datetime as dt, hashlib, json, re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MODELO = "claude-haiku-5-5"
VERSION_INSTRUCCIONES = "vv-2"
CARPETA_RESPUESTAS = RAIZ / "ia_respuestas" / "vale_vista"
HORA_CIERRE_SUPUESTA = "14:00"          # pregunta 3 al abogado
NO_ENCONTRADA = "La IA no encontró la regla del vale vista. Revísala en el aviso."

REGLAS = ["dias_habiles_antes", "horas_antes", "dia_anterior", "dia_anterior_sabado_a_viernes", "dia_anterior_sabado_a_habil",
          "viernes_anterior", "martes_o_jueves_anterior", "en_el_remate", "fecha_fija", "sin_dato", "otra"]

INSTRUCCIONES = """Eres un lector de avisos de remates judiciales de Chile publicados en El Mercurio. Tu única tarea es encontrar CUÁNDO debe entregarse el vale vista (o la garantía o caución) para participar en el remate, y clasificar esa regla. No calculas fechas. Copias frases exactas del aviso.

Responde con el formato JSON pedido. Campos.
- regla. Una de estas, la que diga el aviso.
  dias_habiles_antes. "el día hábil anterior a la subasta", "quinto día hábil anterior". Usa el campo dias (1 si dice el día hábil anterior).
  horas_antes. "con 72 horas de antelación", "al menos 24 horas de anticipación". Usa el campo horas.
  dia_anterior. "el día anterior a la subasta" o "el día precedente", sin la palabra hábil.
  dia_anterior_sabado_a_viernes. Día anterior, y el aviso agrega que si cae en sábado se entrega el viernes anterior.
  dia_anterior_sabado_a_habil. Día anterior, y el aviso agrega que si cae en sábado se entrega el día hábil anterior.
  viernes_anterior. "el día viernes anterior a la fecha de la subasta".
  martes_o_jueves_anterior. "los días martes y jueves, anterior a la realización de la subasta".
  en_el_remate. El vale vista se presenta en el mismo remate, por ejemplo "al momento de efectuarse el llamado a remate".
  fecha_fija. El aviso da una fecha concreta para la entrega. Usa el campo fecha en formato AAAA-MM-DD.
  sin_dato. El aviso pide vale vista o garantía pero NO dice cuándo se entrega.
  otra. El aviso dice cuándo se entrega pero no calza con ninguna de las anteriores.
- dias, horas, fecha. Solo si la regla los usa. Si no, null.
- hora_desde y hora_hasta. El horario de entrega que dice el aviso para ese día, en formato HH:MM de 24 horas. "hasta las 14:00 horas" da hora_hasta 14:00 y hora_desde null. "entre las 12:00 y 14:00 horas" da 12:00 y 14:00. Si el aviso no da horario, null.
- frase_regla. La frase EXACTA del aviso, copiada letra por letra, que dice cuándo se entrega el vale vista. Debe contener el día y, si lo hay, el horario. null si la regla es sin_dato.
- frases_extra. Otras frases EXACTAS del aviso que completan la regla, por ejemplo la excepción del sábado ("el que si recayere en día sábado deberá ser presentado el día viernes anterior"). Lista vacía si no hay.
- contradiccion. Si el aviso da DOS plazos u horarios distintos para la MISMA entrega del vale vista, copia aquí la frase exacta del segundo. Si no, null.

Cuidado con estas trampas. NO son la entrega del vale vista.
- La devolución, restitución o retiro del vale vista a quienes no se adjudican.
- El correo electrónico o el escrito por la Oficina Judicial Virtual que se envía antes del remate, salvo que el aviso diga que la entrega del vale vista es ese mismo envío.
- El pago del saldo del precio, la firma del acta, la fecha del remate y la fecha para el caso de suspensión.
- El cupón de pago o el depósito, cuando el aviso da un plazo distinto para el vale vista.
Si hay entrega material del vale vista en el tribunal y además un correo con otro horario, la regla es la de la entrega material.

Ejemplos (de avisos reales).
1. "deberá ser entregado hasta las 14:00 horas del día hábil anterior a la subasta" da regla dias_habiles_antes, dias 1, hora_desde null, hora_hasta 14:00.
2. "deberán presentarlo en dependencias de tribunal día hábil anterior a remate, entre 12:00 y 14:00 horas" da dias_habiles_antes, dias 1, 12:00 y 14:00.
3. "con 72 horas de antelación al día y hora de realización del remate" da horas_antes, horas 72.
4. "entre las 9 y las 13 horas del día anterior a la realización de la subasta" da dia_anterior, 09:00 y 13:00.
5. "El vale vista deberá ser presentado en la secretaría del tribunal el día anterior al fijado para la subasta, entre las 12:00 y 14:00 horas" más "el que si recayere en día sábado deberá ser presentado el día viernes anterior" da dia_anterior_sabado_a_viernes, 12:00 y 14:00, y la segunda frase va en frases_extra.
6. "compareciendo al Tribunal el día viernes anterior a la fecha de la subasta, de 12:00 a 13:00 horas" da viernes_anterior, 12:00 y 13:00.
7. "al momento de efectuarse el llamado a remate" da en_el_remate.
8. "deberán acreditarse a más tardar el 6 de noviembre de 2026" da fecha_fija, fecha 2026-11-06.
9. Un aviso que solo dice "los vales vista se califican al hacerse el llamado al remate" sin decir cuándo se entregan da sin_dato.
10. "más tardar quinto día hábil anterior fecha subasta" da dias_habiles_antes, dias 5.
"""

ESQUEMA = {
    "type": "object",
    "properties": {
        "regla": {"type": "string", "enum": REGLAS},
        "dias": {"type": ["integer", "null"]},
        "horas": {"type": ["integer", "null"]},
        "fecha": {"type": ["string", "null"]},
        "hora_desde": {"type": ["string", "null"]},
        "hora_hasta": {"type": ["string", "null"]},
        "frase_regla": {"type": ["string", "null"]},
        "frases_extra": {"type": "array", "items": {"type": "string"}},
        "contradiccion": {"type": ["string", "null"]},
    },
    "required": ["regla", "dias", "horas", "fecha", "hora_desde", "hora_hasta", "frase_regla", "frases_extra", "contradiccion"],
    "additionalProperties": False,
}


# --- Feriados y días hábiles -----------------------------------------------------------------------------------
def cargar_feriados():
    fer, anios = set(), set()
    for p in sorted((RAIZ / "db").glob("feriados_*.csv")):
        for r in csv.DictReader(open(p, encoding="utf-8")):
            fer.add(r["fecha"]); anios.add(int(r["fecha"][:4]))
    return fer, anios

FERIADOS, ANIOS_FERIADOS = cargar_feriados()

def habil(d): return d.weekday() < 5 and d.isoformat() not in FERIADOS
def habil_antes(d):
    d -= dt.timedelta(days=1)
    while not habil(d): d -= dt.timedelta(days=1)
    return d


# --- Cálculo del desde y el hasta -----------------------------------------------------------------------------
# CORRECCIÓN de Diego (18 de Octubre). "calificados al momento de hacerse el llamado al remate" es entrega en el remate.
_CALIFICA_LLAMADO = re.compile(r"calificad[oa]s?\s+al\s+momento\s+de\s+(?:hacerse|efectuarse|realizarse)\s+el\s+llamado", re.I)


def calcular(r: dict, fecha_remate: str, hora_remate: str | None, fecha_edicion: str) -> dict:
    """r = respuesta ya verificada. Devuelve {vv_desde, vv_desde_origen, vv_hasta, preguntas, motivo_rojo}."""
    out = {"vv_desde": None, "vv_desde_origen": None, "vv_hasta": None, "preguntas": [], "motivo_rojo": None}
    regla, hd, hh = r["regla"], r.get("hora_desde"), r.get("hora_hasta")
    d0 = dt.date.fromisoformat(fecha_remate)
    desde_est = (dt.date.fromisoformat(fecha_edicion) + dt.timedelta(days=1)).isoformat()
    if regla == "en_el_remate":
        x = f"{fecha_remate} {hora_remate}" if hora_remate else fecha_remate
        out.update(vv_desde=x, vv_desde_origen="texto", vv_hasta=x); return out
    if regla == "horas_antes":
        if not hora_remate:
            out["motivo_rojo"] = "Falta la hora del remate para contar las horas."; return out
        t = dt.datetime.fromisoformat(f"{fecha_remate} {hora_remate}") - dt.timedelta(hours=r["horas"])
        if habil(t.date()):
            hasta = t.strftime("%Y-%m-%d %H:%M")
        else:
            hasta = f"{habil_antes(t.date() + dt.timedelta(days=1)).isoformat()} {HORA_CIERRE_SUPUESTA}"
            out["preguntas"].append(3)
        out.update(vv_desde=desde_est, vv_desde_origen="estimado_dia_siguiente_edicion", vv_hasta=hasta); return out
    if regla == "dias_habiles_antes":
        d = d0
        for _ in range(r["dias"]): d = habil_antes(d)
    elif regla in ("dia_anterior", "dia_anterior_sabado_a_viernes", "dia_anterior_sabado_a_habil"):
        d = d0 - dt.timedelta(days=1)
        if not habil(d):
            cubre = regla != "dia_anterior" and d.weekday() == 5
            d = habil_antes(d + dt.timedelta(days=1))
            if not cubre: out["preguntas"].append(2)
    elif regla in ("viernes_anterior", "martes_o_jueves_anterior"):
        dias = (4,) if regla == "viernes_anterior" else (1, 3)
        d = d0 - dt.timedelta(days=1)
        while d.weekday() not in dias: d -= dt.timedelta(days=1)
        if len(dias) > 1: out["preguntas"].append(5)
        if not habil(d): out["preguntas"].append(2)
    elif regla == "fecha_fija":
        d = dt.date.fromisoformat(r["fecha"])
    else:
        out["motivo_rojo"] = f"Regla {regla} sin cálculo."; return out
    out["vv_hasta"] = f"{d.isoformat()} {hh}" if hh else d.isoformat()
    if hd:
        out.update(vv_desde=f"{d.isoformat()} {hd}", vv_desde_origen="texto")
    else:
        out.update(vv_desde=desde_est, vv_desde_origen="estimado_dia_siguiente_edicion")
    return out


# --- Verificación de la respuesta -----------------------------------------------------------------------------
def buscar_frase(frase: str | None, texto: str) -> str | None:
    """Busca la frase en el aviso aceptando SOLO diferencias de espacios (decisión de Diego). Devuelve el tramo tal
    como está escrito en el aviso, o None."""
    if not frase:
        return None
    sin = re.sub(r"\s+", "", frase)
    if not sin:
        return None
    pos = [i for i, c in enumerate(texto) if not c.isspace()]
    compacto = "".join(texto[i] for i in pos)
    k = compacto.find(sin)
    if k < 0:
        return None
    return texto[pos[k]:pos[k + len(sin) - 1] + 1]


_NUM = {1: "un|uno|primer", 2: "dos|segundo", 3: "tres|tercer", 4: "cuatro|cuarto", 5: "cinco|quinto", 6: "seis|sexto",
        7: "siete|séptimo|septimo", 10: "diez|décimo|decimo", 12: "doce", 24: "veinticuatro|veinte y cuatro",
        36: "treinta y seis", 48: "cuarenta y ocho", 72: "setenta y dos", 96: "noventa y seis"}

def _numero_en(n: int, t: str) -> bool:
    pal = _NUM.get(n)
    return bool(re.search(rf"(?<!\d){n}(?!\d)", t) or (pal and re.search(rf"\b(?:{pal})\b", t, re.I)))

def _hora_en(hhmm: str, t: str) -> bool:
    h, m = int(hhmm[:2]), hhmm[3:]
    minutos = rf"\s?[:.]\s?{m}" if m != "00" else rf"(?:\s?[:.]\s?00)?"
    return bool(re.search(rf"(?<![\d:.]){h:d}{minutos}(?![\d])|(?<![\d:.])0{h:d}{minutos}(?![\d])", t))

_PALABRAS = {
    "dias_habiles_antes": [r"h[áa]bil"],
    "horas_antes": [r"horas", r"antelaci|anticipaci|antes"],
    "dia_anterior": [r"anterior|precedente|previo"],
    "dia_anterior_sabado_a_viernes": [r"anterior", r"s[áa]bado", r"viernes"],
    "dia_anterior_sabado_a_habil": [r"anterior", r"s[áa]bado", r"h[áa]bil"],
    "viernes_anterior": [r"viernes"],
    "martes_o_jueves_anterior": [r"martes", r"jueves"],
    "en_el_remate": [r"llamado|momento|acto|audiencia|d[íi]a del remate|al remate|en el remate|la subasta"],
    "fecha_fija": [],
}
_DEVOLUCION = re.compile(r"devoluci|devuelt|restitu|retir", re.I)
_DETECTOR = re.compile(r"antelaci|anticipaci|a\s+m[áa]s\s+tardar|hasta\s+las|d[íi]a\s+(?:h[áa]bil\s+)?anterior|d[íi]a\s+precedente|viernes|martes", re.I)
_DIA_SEMANA = {"lunes": 0, "martes": 1, "miércoles": 2, "miercoles": 2, "jueves": 3, "viernes": 4}
_NO_ES_ENTREGA = re.compile(r"correo|electr[óo]nic|cup[óo]n|oficina\s+judicial|\bO\.?J\.?V\b|escrito", re.I)
_ANCLA_VV = re.compile(r"vale\s+(?:a\s+la\s+)?vista|garant[íi]a|cauci[óo]n", re.I)


def detector_reglas(texto: str) -> list:
    """Frases de plazo cerca de vale vista, garantía o caución que no hablan de devolución. Sirve para no aceptar un
    sin_dato de la IA cuando el aviso sí parece dar un plazo."""
    hallados = []
    for a in _ANCLA_VV.finditer(texto):
        tramo = texto[a.start():a.start() + 250]
        m = _DETECTOR.search(tramo)
        if m:
            alrededor = tramo[max(0, m.start() - 80):m.end() + 40]
            if not _DEVOLUCION.search(alrededor):
                hallados.append(alrededor.strip())
    return hallados


def verificar(r: dict, texto: str) -> dict:
    """Revisa una respuesta de la IA contra el texto del aviso.
    Devuelve {ok, motivos [..], frase_regla, frases_extra, contradiccion} con las frases tal como están en el aviso."""
    motivos = []
    regla = r.get("regla")
    if regla not in REGLAS:
        return {"ok": False, "motivos": [f"Regla desconocida ({regla})."]}
    if regla == "otra":
        motivos.append("La IA dice que la regla no calza con ninguna conocida.")
    frase = buscar_frase(r.get("frase_regla"), texto)
    extras = []
    for e in r.get("frases_extra") or []:
        f = buscar_frase(e, texto)
        if f is None:
            motivos.append(f"Frase extra no encontrada en el aviso ({e[:60]}).")
        else:
            extras.append(f)
    contra = buscar_frase(r.get("contradiccion"), texto) if r.get("contradiccion") else None
    if r.get("contradiccion") and contra is None:
        motivos.append("La frase de contradicción no está en el aviso.")
    descartada = None
    if contra:
        k = texto.find(contra)
        alrededor = texto[max(0, k - 120):k] + contra
        if _NO_ES_ENTREGA.search(alrededor):
            # 14-10 avisos 4, 10, 11, 13, 14, 15, 16, 48 y 49. El "segundo plazo" era el correo, el escrito por la OJV o el
            # cupón de pago, que no son la entrega material del vale vista (decisión de Diego). No es contradicción.
            descartada, contra = contra, None
        else:
            motivos.append("El aviso da dos plazos u horarios distintos para la entrega.")
    if regla == "sin_dato":
        det = detector_reglas(texto)
        if det:
            motivos.append(f"La IA no encontró regla, pero el aviso parece dar un plazo ({det[0][:80]}).")
        return {"ok": not motivos, "motivos": motivos, "frase_regla": None, "frases_extra": extras, "contradiccion": contra, "descartada": descartada}
    if regla == "otra":
        return {"ok": False, "motivos": motivos, "frase_regla": frase, "frases_extra": extras, "contradiccion": contra}
    if frase is None:
        motivos.append("La frase de la regla no está en el aviso." if r.get("frase_regla") else "La IA no entregó la frase de la regla.")
        return {"ok": False, "motivos": motivos, "frase_regla": None, "frases_extra": extras, "contradiccion": contra}
    todo = " ".join([frase] + extras)
    if _DEVOLUCION.search(frase):
        motivos.append("La frase habla de devolución o retiro, no de entrega.")
    for patron in _PALABRAS[regla]:
        if not re.search(patron, todo, re.I):
            motivos.append(f"La frase no trae las palabras propias de la regla {regla}.")
            break
    if regla == "en_el_remate" and not _CALIFICA_LLAMADO.search(frase) and (
            not re.search(r"acompa[ñn]|entreg|present|exhib|consign", frase, re.I) or re.search(r"calific", frase, re.I)):
        # 14-10 avisos 27 y 28. "Los vales vista recepcionados serán calificados al momento de hacerse el llamado" no dice
        # cuándo se ENTREGAN, solo cuándo se califican.
        # CORRECCIÓN de Diego (18 de Octubre). Esa frase SÍ vale como entrega en el remate. Hay remates donde el vale vista se
        # entrega minutos antes de empezar, en el llamado. Por eso esa frase exacta pasa (_CALIFICA_LLAMADO). Las demás
        # frases con "calificar" o sin verbo de entrega siguen en rojo.
        motivos.append("La frase no dice que el vale vista se entregue en el remate (solo cuándo se califica).")
    if regla == "dia_anterior" and re.search(r"h[áa]bil", frase, re.I):
        motivos.append("La frase dice día hábil, no día anterior.")
    if regla == "dias_habiles_antes":
        n = r.get("dias")
        if not isinstance(n, int) or n < 1:
            motivos.append("Faltan los días hábiles.")
        elif n > 1 and not _numero_en(n, todo):
            motivos.append(f"El número de días ({n}) no está en la frase.")
    if regla == "horas_antes":
        n = r.get("horas")
        if not isinstance(n, int) or n < 1:
            motivos.append("Faltan las horas.")
        elif not _numero_en(n, todo):
            motivos.append(f"El número de horas ({n}) no está en la frase.")
    if regla == "fecha_fija":
        from motor.extraccion import _fechas
        if not r.get("fecha") or r["fecha"] not in {f[2] for f in _fechas(todo)}:
            motivos.append("La fecha fija no está escrita en la frase.")
    for campo in ("hora_desde", "hora_hasta"):
        v = r.get(campo)
        if v is None:
            continue
        if not re.fullmatch(r"[0-2]\d:[0-5]\d", v) or int(v[:2]) > 23:
            motivos.append(f"{campo} con formato inválido ({v})."); continue
        if not _hora_en(v, todo):
            motivos.append(f"La hora {v} no está en la frase.")
    if r.get("hora_desde") and r.get("hora_hasta") and r["hora_desde"] >= r["hora_hasta"]:
        motivos.append("La hora desde no es anterior a la hora hasta.")
    return {"ok": not motivos, "motivos": motivos, "frase_regla": frase, "frases_extra": extras, "contradiccion": contra, "descartada": descartada}


def _clave_lectura(r: dict) -> tuple:
    """Lo que debe coincidir entre las dos lecturas. La regla y sus datos. No el largo de la frase copiada, que varía
    entre lecturas sin cambiar nada (14-10, avisos 5, 10, 14, 15, 34 y 43). Las dos frases igual se verifican."""
    return (r.get("regla"), r.get("dias"), r.get("horas"), r.get("fecha"), r.get("hora_desde"), r.get("hora_hasta"))


def resolver(lecturas: list, texto: str, fecha_remate: str | None, hora_remate: str | None, fecha_edicion: str) -> dict:
    """Une las dos lecturas, verifica y calcula. Devuelve el bloque vale_vista en el formato del banco nivel 2
    más color, motivos y preguntas."""
    base = {"regla": None, "cita": None, "citas_extra": [], "vv_desde": None, "vv_desde_origen": None, "vv_hasta": None,
            "vv_estado": None, "color": "rojo", "motivos": [], "preguntas": [], "contradiccion": None}
    if len(lecturas) < 2:
        base["motivos"].append("Falta la segunda lectura de la IA."); base["vv_estado"] = "revisar"; return base
    if _clave_lectura(lecturas[0]) != _clave_lectura(lecturas[1]):
        base["motivos"].append("Las dos lecturas de la IA no coinciden."); base["vv_estado"] = "revisar"
        base["regla"] = lecturas[0].get("regla"); return base
    r = lecturas[0]
    v = verificar(r, texto)
    v2 = verificar(lecturas[1], texto)
    if v["ok"] and not v2["ok"]:
        v = {**v, "ok": False, "motivos": ["Segunda lectura. " + m for m in v2["motivos"]]}
    base.update(regla=r["regla"], cita=v.get("frase_regla"), citas_extra=v.get("frases_extra") or [], contradiccion=v.get("contradiccion"))
    base["motivos"] += v["motivos"]
    if r["regla"] == "sin_dato" and v["ok"]:
        base.update(color="sin_dato", vv_estado="sin_dato"); return base
    if not v["ok"]:
        base["vv_estado"] = "revisar"; return base
    if not fecha_remate:
        base["motivos"].append("Falta la fecha del remate."); base["vv_estado"] = "revisar"; return base
    if fecha_remate < fecha_edicion:
        base["motivos"].append("La fecha del remate es anterior a la edición."); base["vv_estado"] = "revisar"; return base
    if int(fecha_remate[:4]) not in ANIOS_FERIADOS:
        base["motivos"].append(f"No están cargados los feriados de {fecha_remate[:4]}."); base["vv_estado"] = "revisar"; return base
    c = calcular(r, fecha_remate, hora_remate, fecha_edicion)
    if c["motivo_rojo"]:
        base["motivos"].append(c["motivo_rojo"]); base["vv_estado"] = "revisar"; return base
    if r["regla"] == "fecha_fija" and c["vv_hasta"][:10] < fecha_edicion:
        base["motivos"].append("La fecha de entrega es anterior a la edición. Posible error de escritura del aviso.")
        base["vv_estado"] = "revisar"; return base
    if c["vv_hasta"][:10] > fecha_remate:
        base["motivos"].append("La entrega quedaría después del remate."); base["vv_estado"] = "revisar"; return base
    # La frase nombra un día de la semana y el cálculo cae en otro (6-10 aviso 80, "el día jueves inmediatamente anterior"
    # leído como día anterior dio viernes, un día TARDE). Solo lunes a viernes, porque sábado y domingo aparecen en las
    # excepciones ("si recayere en día sábado", 14-10 aviso 21) y la entrega nunca cae en fin de semana.
    nombrados = {_DIA_SEMANA[w.lower()] for w in re.findall(r"\b(lunes|martes|mi[ée]rcoles|jueves|viernes)\b", base["cita"] or "", re.I)}
    if nombrados and dt.date.fromisoformat(c["vv_hasta"][:10]).weekday() not in nombrados:
        base["motivos"].append("La frase nombra un día de la semana distinto al que da el cálculo.")
        base["vv_estado"] = "revisar"; return base
    preg = list(c["preguntas"])
    if r["regla"] == "dias_habiles_antes" and re.search(r"horario\s+de\s+atenci", base["cita"] or "", re.I):
        preg.append(4)
    base.update(vv_desde=c["vv_desde"], vv_desde_origen=c["vv_desde_origen"], vv_hasta=c["vv_hasta"], preguntas=sorted(set(preg)))
    base.update(color="ambar" if preg else "verde", vv_estado="revisar" if preg else "calculado")
    return base


# --- Llamada a la IA con respuestas guardadas -----------------------------------------------------------------
def huella(texto: str) -> str:
    return hashlib.sha256(f"{MODELO}|{VERSION_INSTRUCCIONES}|{texto}".encode("utf-8")).hexdigest()


def leer_guardada(texto: str):
    p = CARPETA_RESPUESTAS / f"{huella(texto)}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def leer_con_ia(texto: str, cliente=None, lecturas: int = 2) -> dict:
    """Devuelve {'lecturas': [..], 'uso': [..]} desde lo guardado, o llama a la IA y lo guarda."""
    g = leer_guardada(texto)
    if g and len(g["lecturas"]) >= lecturas:
        return g
    if cliente is None:
        raise RuntimeError("No hay respuesta guardada para este aviso y no se entregó cliente de IA.")
    out = {"modelo": MODELO, "version": VERSION_INSTRUCCIONES, "lecturas": [], "uso": [], "errores": []}
    for _ in range(lecturas):
        try:
            resp = cliente.messages.create(
                model=MODELO, max_tokens=800, thinking={"type": "disabled"},
                system=[{"type": "text", "text": INSTRUCCIONES, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": "AVISO\n" + texto}],
                output_config={"format": {"type": "json_schema", "schema": ESQUEMA}})
            out["uso"].append({"entrada": resp.usage.input_tokens, "salida": resp.usage.output_tokens,
                               "cache_lectura": getattr(resp.usage, "cache_read_input_tokens", 0) or 0,
                               "cache_escritura": getattr(resp.usage, "cache_creation_input_tokens", 0) or 0,
                               "stop": resp.stop_reason})
            bloque = next(b for b in resp.content if getattr(b, "type", None) == "text")
            out["lecturas"].append(json.loads(bloque.text))
        except Exception as e:                      # la lectura queda en rojo, nunca se inventa
            out["errores"].append(f"{type(e).__name__}: {str(e)[:300]}")
    if len(out["lecturas"]) == lecturas:
        CARPETA_RESPUESTAS.mkdir(parents=True, exist_ok=True)
        (CARPETA_RESPUESTAS / f"{huella(texto)}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def cliente_desde_config():
    import importlib.util, anthropic
    spec = importlib.util.spec_from_file_location("config", RAIZ / "config.py")
    c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
    return anthropic.Anthropic(api_key=c.ANTHROPIC_API_KEY)

"""Datos de la interfaz (18 de Octubre). Todo lo que la página muestra sale de aquí, y todas las acciones de Diego pasan
por aquí. El servidor (interfaz\\servidor.py) solo traduce pedidos web a estas funciones, así se prueban sin navegador.
Decisiones de Diego del 18 de Octubre en ESTADO_PROYECTO.md y en la bitácora del 18.
"""
import datetime as dt
import re
from db.carga import normalizar
from db.crear_base import aviso_feriados
from motor.republicaciones import CAMPOS
from motor.sincronizacion import estado_sincronizacion

try:
    import config
    BASE_URL = config.MERCURIO_BASE_URL
except Exception:                                   # en otro PC sin config.py la agenda igual funciona
    BASE_URL = "https://digital.elmercurio.com"

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
MESC = ["Ene.", "Feb.", "Mar.", "Abr.", "May.", "Jun.", "Jul.", "Ago.", "Sep.", "Oct.", "Nov.", "Dic."]
DIAC = ["Lun.", "Mar.", "Mié.", "Jue.", "Vie.", "Sáb.", "Dom."]
DIAL = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
ROJAS = {"error_escritura", "rol_mal_impreso", "contradiccion", "dato_faltante"}
AMBAR = {"condicion_especial", "aviso_previo"}


class ErrorDato(ValueError):
    """Un pedido que no se puede cumplir (falta un dato, no existe el remate). La página muestra el texto."""


# --- Formatos (meses siempre en palabras, pedido de Diego) -------------------------------------------------------
def _fecha(iso):
    return dt.date.fromisoformat(iso[:10])


def corta(iso):
    d = _fecha(iso)
    return f"{DIAC[d.weekday()]} {d.day} {MESC[d.month - 1]}"


def larga(iso):
    d = _fecha(iso)
    return f"{DIAL[d.weekday()]} {d.day} de {MESES[d.month - 1]} de {d.year}"


def dia_mes(iso):
    d = _fecha(iso)
    return f"{d.day} {MESC[d.month - 1]}"


def punto(t):
    """Cierra la oración sin dejar dos puntos seguidos ('9 Oct.' ya termina en punto)."""
    return t if t.endswith(".") else t + "."


def numero(n, dec=0):
    """Número a la chilena. 1234567.8 con dec=0 da '1.234.568', 983.8089 con dec=4 da '983,8089'."""
    s = f"{n:,.{dec}f}".replace(",", "_").replace(".", ",").replace("_", ".")
    if dec and "," in s:
        s = s.rstrip("0").rstrip(",")
    return s


def plata(monto, moneda):
    if monto is None:
        return None
    return f"{numero(monto, 4)} UF" if moneda == "UF" else f"${numero(monto)}"


def tribunal_corto(t):
    if not t:
        return "Sin tribunal"
    s = re.sub(r"\bJuzgado\s+(?:de\s+)?", "", t)
    return re.sub(r"\s+de\s+Santiago$", "", s).strip()


def rol_texto(tipo_id, rol, anio):
    if not rol:
        return "Sin rol"
    return f"{'RIT ' if tipo_id == 'RIT' else ''}C-{rol}-{anio}"


def _hora(v):
    return v[11:16] if v and len(v) > 10 else None


EN_EL_REMATE = "Se entrega en el mismo remate, antes del llamado. Puede ser minutos antes de empezar."


def texto_vv(desde, hasta, origen=None, regla=None):
    if not hasta:
        return "Sin fecha. Dato faltante"
    desde = desde or hasta
    d1, h1, d2, h2 = desde[:10], _hora(desde), hasta[:10], _hora(hasta)
    if regla == "en_el_remate":
        # Pedido de Diego (18 de Octubre). Que quede claro que hay remates donde el vale vista se entrega ahí mismo.
        return f"{corta(d2)}{' a las ' + h2 if h2 else ''}. {EN_EL_REMATE}"
    if d1 == d2:
        if h1 and h2 and h1 != h2:
            return f"{corta(d1)} de {h1} a {h2}"
        return f"{corta(d1)} a las {h2}" if h2 else corta(d1)
    txt = f"Desde {corta(d1)}{' ' + h1 if h1 else ''} hasta {corta(d2)}{' a las ' + h2 if h2 else ''}"
    return txt + (" (el desde es estimado)" if origen == "estimado_dia_siguiente_edicion" else "")


def tipo_vv(desde, hasta, regla=None):
    """Tipo de entrega del vale vista para la ficha (Diego, 22 de Octubre). remate, dia, rango o None si no hay fecha."""
    if not hasta:
        return None
    if regla == "en_el_remate":
        return "remate"
    return "dia" if (desde or hasta)[:10] == hasta[:10] else "rango"


def color_vv(estado, hasta):
    if estado == "calculado" and hasta:
        return "verde"
    if estado == "revisar" and hasta:
        return "ambar"
    return "rojo"


def modo(modalidad):
    """pres (martillo), virt (computador) o nose (signo de interrogación). El mixto es raro y va con signo (decisión de Diego)."""
    return {"presencial": "pres", "zoom": "virt", "en_linea": "virt"}.get(modalidad or "", "nose")


def modalidad_texto(modalidad, plataforma=None):
    return {"presencial": "Presencial", "zoom": "Virtual (Zoom)", "en_linea": f"Virtual ({plataforma or 'en línea'})",
            "mixta": "Presencial y en línea a la vez. No es lo normal, revisa el aviso"}.get(modalidad or "", "El aviso no dice la modalidad")


def dinero(f):
    """Mínimo, garantía y monto del vale vista de un remate (fila con las columnas de remates)."""
    p, base, mf = f.get("garantia_porcentaje"), f.get("garantia_base"), f.get("garantia_monto")
    minimo = plata(f.get("minimo_monto"), f.get("minimo_moneda"))
    if minimo and f.get("minimo_costas_clp"):
        minimo += f" más ${numero(f['minimo_costas_clp'])} de costas"
    uf = None
    if mf:
        gar, monto = "Monto fijo", plata(mf, f.get("garantia_moneda") or "CLP")
    elif p is not None and base == "tasacion":
        gar, monto = f"{p:g}% de la tasación", f"{p:g}% de la tasación (el aviso no da el monto)"
    elif p is not None and f.get("minimo_monto"):
        gar = f"{p:g}% del mínimo"
        v = f["minimo_monto"] * p / 100
        monto = plata(v, f.get("minimo_moneda"))
        uf = round(v, 4) if f.get("minimo_moneda") == "UF" else None
    else:
        gar, monto = "Sin dato", "Sin dato"
    return {"minimo": minimo or "Sin dato", "garantia": gar, "monto": monto, "uf": uf, "uf_txt": monto if uf else None,
            "otro_porcentaje": (f"{p:g}%" if p is not None and p != 10 else None)}


# --- Un remate con todo lo que muestra la ficha ------------------------------------------------------------------
_REMATE = ("SELECT r.id AS remate_id, r.bien_id, r.sub_orden, r.inmueble, r.direccion, r.comuna, r.fecha_remate, r.hora_remate, "
           "r.modalidad, r.plataforma, r.minimo_monto, r.minimo_moneda, r.minimo_costas_clp, r.garantia_porcentaje, r.garantia_base, "
           "r.garantia_monto, r.garantia_moneda, r.vv_regla, r.vv_regla_texto, r.vv_desde, r.vv_desde_origen, r.vv_hasta, r.vv_estado, "
           "a.id AS aviso_id, a.tipo_id, a.rol, a.anio, a.tribunal, e.fecha AS edicion, "
           "(SELECT c.valor FROM citas c WHERE c.aviso_id = a.id AND c.campo = 'caratulado' ORDER BY c.sub_orden, c.n_cita LIMIT 1) AS caratula "
           "FROM remates r JOIN avisos a ON a.id = r.aviso_id JOIN ediciones e ON e.id = a.edicion_id WHERE r.id = ?")


def _dict(cur, fila):
    return {d[0]: v for d, v in zip(cur.description, fila)} if fila else None


def publicaciones(con, bien_id):
    """Cada aviso publicado de la propiedad con su link. ant = es del llamado anterior (antes del último nuevo llamado)."""
    if bien_id is None:
        return []
    corte = con.execute("SELECT MAX(e.fecha) FROM cambios k JOIN remates r ON r.id = k.remate_nuevo JOIN avisos a ON a.id = r.aviso_id "
                        "JOIN ediciones e ON e.id = a.edicion_id WHERE k.bien_id = ? AND k.campo = 'nuevo_llamado'", (bien_id,)).fetchone()[0]
    filas = con.execute("SELECT DISTINCT edicion, ruta_inicio, ruta_fin FROM v_buscador WHERE bien_id = ? ORDER BY edicion", (bien_id,)).fetchall()
    out = []
    for ed, ri, rf in filas:
        out.append({"edicion": ed, "texto": dia_mes(ed), "href": BASE_URL + ri if ri else None,
                     "href_fin": BASE_URL + rf if rf else None, "ant": bool(corte and ed < corte)})
    return out


def alertas_de(con, aviso_id, sub_orden):
    out = []
    for tipo, texto in con.execute("SELECT tipo, texto FROM alertas WHERE aviso_id = ? AND sub_orden IN (0, ?) ORDER BY id", (aviso_id, sub_orden)):
        out.append({"tipo": tipo, "texto": texto, "clase": "rojo" if tipo in ROJAS else ("ambar" if tipo in AMBAR else "info")})
    return out


def armar(con, remate_id, extra=None):
    cur = con.execute(_REMATE, (remate_id,))
    f = _dict(cur, cur.fetchone())
    if not f:
        raise ErrorDato("No existe ese remate.")
    f.update(extra or {})
    al = alertas_de(con, f["aviso_id"], f["sub_orden"])
    pubs = publicaciones(con, f["bien_id"])
    vigentes = [p for p in pubs if not p["ant"]]
    din = dinero(f)
    return {
        "tipo": "diario", "remate_id": f["remate_id"], "bien_id": f["bien_id"], "aviso_id": f["aviso_id"],
        "rol": rol_texto(f["tipo_id"], f["rol"], f["anio"]), "rol_num": f["rol"], "anio": f["anio"],
        "tribunal": f["tribunal"] or "Sin tribunal", "tc": tribunal_corto(f["tribunal"]), "caratula": f["caratula"] or "Sin carátula",
        "inmueble": f["inmueble"], "fecha_remate": f["fecha_remate"], "hora": f["hora_remate"],
        "remate_txt": (larga(f["fecha_remate"]) + (f" a las {f['hora_remate']}" if f["hora_remate"] else "")) if f["fecha_remate"] else "Sin fecha del remate",
        "remate_corto": (corta(f["fecha_remate"]) + (f" a las {f['hora_remate']}" if f["hora_remate"] else "")) if f["fecha_remate"] else "Sin fecha",
        "mod": modo(f["modalidad"]), "mod_txt": modalidad_texto(f["modalidad"], f["plataforma"]),
        "direccion": ", ".join(x for x in (f["direccion"], f["comuna"]) if x) or "El programa todavía no lee la dirección de este aviso.",
        **din, "asumido": any("ASUMIDO" in a["texto"] for a in al),
        "vv_desde": f["vv_desde"], "vv_hasta": f["vv_hasta"], "vv_txt": texto_vv(f["vv_desde"], f["vv_hasta"], f["vv_desde_origen"], f["vv_regla"]), "vv_tipo": tipo_vv(f["vv_desde"], f["vv_hasta"], f["vv_regla"]),
        "vv_color": color_vv(f["vv_estado"], f["vv_hasta"]), "vv_regla": f["vv_regla_texto"],
        "vv_de_publicacion": f.get("vv_de_publicacion"), "alertas": al,
        "pubs": pubs, "pub_txt": "Publicado en El Mercurio los días " + ", ".join(p["texto"] for p in vigentes) if vigentes else "",
        "edicion": f["edicion"],
    }


# --- Agenda --------------------------------------------------------------------------------------------------------
def agenda(con, hoy):
    out = []
    cur = con.execute("SELECT * FROM v_calendario")
    for fila in cur.fetchall():
        c = _dict(cur, fila)
        extra_regla = {}
        if c["vv_de_publicacion"]:   # el vale vista viene de una publicación anterior (v_calendario), su regla también
            x = con.execute("SELECT r.vv_regla FROM remates r JOIN avisos a ON a.id = r.aviso_id JOIN ediciones e ON e.id = a.edicion_id "
                            "WHERE r.bien_id = ? AND e.fecha = ? AND r.vv_hasta = ? LIMIT 1", (c["bien_id"], c["vv_de_publicacion"], c["vv_hasta"])).fetchone()
            extra_regla = {"vv_regla": x[0] if x else None}
        it = armar(con, c["remate_id"], {**extra_regla, "vv_desde": c["vv_desde"], "vv_hasta": c["vv_hasta"], "vv_estado": c["vv_estado"],
                                         "vv_regla_texto": c["vv_regla_texto"], "vv_desde_origen": c["vv_desde_origen"],
                                         "vv_de_publicacion": c["vv_de_publicacion"], "direccion": c["direccion"], "comuna": c["comuna"]})
        sin_ver = {k[0] for k in con.execute("SELECT campo FROM cambios WHERE bien_id = ? AND visto = 0", (c["bien_id"],))}
        it.update(agenda_id=c["agenda_id"], vv_entregado=bool(c["vv_entregado"]), remate_asistido=bool(c["remate_asistido"]),
                  cambio_fecha=bool(sin_ver & {"fecha_remate", "hora_remate"}), cambios_sin_ver=bool(sin_ver - {"nuevo_llamado"}),
                  nuevo_llamado=con.execute("SELECT 1 FROM cambios WHERE bien_id = ? AND campo = 'nuevo_llamado'", (c["bien_id"],)).fetchone() is not None)
        if c["vv_de_publicacion"]:
            it["vv_txt"] += f" (del aviso del {dia_mes(c['vv_de_publicacion'])}, el más nuevo aún no se lee)"
        out.append(it)
    for m in manuales(con):
        out.append(m)
    return sorted(out, key=lambda x: (x["fecha_remate"] or "9999", x.get("hora") or ""))


def manuales(con):
    out = []
    cur = con.execute("SELECT * FROM agenda_manual ORDER BY id")
    for fila in cur.fetchall():
        m = _dict(cur, fila)
        vd, vh = m["vv_desde"] or m["vv_hasta"], m["vv_hasta"] or m["vv_desde"]
        al = [] if vh else [{"tipo": "dato_faltante", "texto": "Falta la fecha del vale vista. Anótala cuando la sepas.", "clase": "rojo"}]
        pub = []
        if not m["publicado_ignorado"] and m["rol"]:
            cur2 = con.execute("SELECT b.remate_id, b.tribunal, b.edicion, b.fecha_remate, b.inmueble FROM v_buscador b "
                               "WHERE b.rol = ? AND b.anio = ? ORDER BY b.edicion DESC", (m["rol"], m["anio"] or ""))
            vistos = set()
            for rid, trib, ed, fr, inm in cur2.fetchall():
                if m["tribunal"] and normalizar(m["tribunal"]) != normalizar(trib):
                    continue
                bien = con.execute("SELECT bien_id FROM remates WHERE id = ?", (rid,)).fetchone()[0]
                if bien in vistos:
                    continue
                vistos.add(bien)
                pub.append({"remate_id": rid, "texto": punto(f"Salió publicada en El Mercurio el {dia_mes(ed)}"
                            + (f" ({inm})" if inm else "") + (f", remate el {corta(fr)}" if fr else ""))})
        out.append({
            "tipo": "manual", "manual_id": m["id"], "bien_id": None, "rol": rol_texto("ROL", m["rol"], m["anio"]) if m["rol"] else "Sin rol",
            "tribunal": m["tribunal"] or "Tribunal sin nombre", "tc": tribunal_corto(m["tribunal"]), "caratula": m["caratula"] or "Sin carátula",
            "fecha_remate": m["fecha_remate"], "hora": m["hora_remate"],
            "remate_txt": larga(m["fecha_remate"]) + (f" a las {m['hora_remate']}" if m["hora_remate"] else ""),
            "remate_corto": corta(m["fecha_remate"]) + (f" a las {m['hora_remate']}" if m["hora_remate"] else ""),
            "mod": modo(m["modalidad"]), "mod_txt": modalidad_texto(m["modalidad"]), "direccion": "Agregada a mano, sin dirección.",
            "minimo": "Sin dato", "garantia": "Sin dato", "monto": m["monto_vv"] or "Sin dato", "uf": None, "uf_txt": None,
            "otro_porcentaje": None, "asumido": False, "vv_desde": vd, "vv_hasta": vh, "vv_txt": texto_vv(vd, vh), "vv_tipo": tipo_vv(vd, vh),
            "vv_color": "verde" if vh else "rojo", "vv_regla": None, "alertas": al, "pubs": [], "pub_txt": "Agregada a mano. No viene de El Mercurio.",
            "vv_entregado": bool(m["vv_entregado"]), "cambio_fecha": False, "cambios_sin_ver": False, "nuevo_llamado": False,
            "publicado": pub})
    return out


# --- Avisos grandes ------------------------------------------------------------------------------------------------
_ETIQUETA = {c: e[:1].upper() + e[1:] for c, e, _ in CAMPOS}
_ETIQUETA.update(fecha_remate="Fecha del remate", hora_remate="Hora", minimo="Mínimo", vv_hasta="Plazo del vale vista", vv_desde="Desde del vale vista")


def valor_cambio(campo, v):
    if v is None:
        return "vacío"
    if campo == "fecha_remate":
        return larga(v)
    if campo in ("vv_hasta", "vv_desde") and re.match(r"\d{4}-\d\d-\d\d", v):
        return corta(v) + (f" a las {_hora(v)}" if _hora(v) else "")
    if campo == "minimo":
        m = re.match(r"([\d.]+)\s*(CLP|UF)?", v)
        return plata(float(m.group(1)), m.group(2) or "CLP") if m else v
    if campo == "garantia_porcentaje":
        return f"{float(v):g}%"
    return v


def _titulo(con, bien_id):
    f = con.execute("SELECT a.tipo_id, a.rol, a.anio, a.tribunal FROM remates r JOIN avisos a ON a.id = r.aviso_id "
                    "JOIN ediciones e ON e.id = a.edicion_id WHERE r.bien_id = ? ORDER BY e.fecha DESC LIMIT 1", (bien_id,)).fetchone()
    car = con.execute("SELECT c.valor FROM citas c JOIN remates r ON r.aviso_id = c.aviso_id WHERE r.bien_id = ? AND c.campo = 'caratulado' "
                      "ORDER BY c.aviso_id DESC LIMIT 1", (bien_id,)).fetchone()
    inm = con.execute("SELECT inmueble FROM bienes WHERE id = ?", (bien_id,)).fetchone()
    return f"{f[3] or 'Sin tribunal'} · {rol_texto(f[0], f[1], f[2])}" + (f" · {inm[0]}" if inm and inm[0] else ""), (car[0] if car else "")


def _edicion_de(con, remate_id):
    return con.execute("SELECT e.fecha FROM remates r JOIN avisos a ON a.id = r.aviso_id JOIN ediciones e ON e.id = a.edicion_id WHERE r.id = ?",
                       (remate_id,)).fetchone()[0]


def pub_remate(con, remate_id):
    """El aviso de un remate con su link (y el de la página siguiente si va partido). Para las tablas de cambios (Diego,
    21 de Octubre, para llegar al aviso físico de cada lado)."""
    f = con.execute("SELECT edicion, ruta_inicio, ruta_fin FROM v_buscador WHERE remate_id = ? LIMIT 1", (remate_id,)).fetchone()
    if not f:
        return None
    ed, ri, rf = f
    return {"edicion": ed, "texto": dia_mes(ed), "href": BASE_URL + ri if ri else None,
            "href_fin": BASE_URL + rf if rf else None, "ant": False}


def avisos_grandes(con):
    """Cambios sin ver de las causas agendadas. Uno por par de publicaciones. El nuevo llamado va aparte (decisión de Diego)."""
    filas = con.execute("SELECT k.bien_id, k.remate_anterior, k.remate_nuevo, k.campo, k.valor_anterior, k.valor_nuevo FROM cambios k "
                        "JOIN agenda g ON g.bien_id = k.bien_id WHERE k.visto = 0 ORDER BY k.bien_id, k.remate_nuevo, k.id").fetchall()
    cambios, llamados = {}, []
    for bien, ra, rn, campo, va, vn in filas:
        titulo, car = _titulo(con, bien)
        ea, en = _edicion_de(con, ra), _edicion_de(con, rn)
        if campo == "nuevo_llamado":
            a, n = armar(con, ra), armar(con, rn)
            llamados.append({"bien_id": bien, "titulo": titulo, "caratula": car,
                             "antes": f"Llamado anterior (aviso del {dia_mes(ea)})", "despues": f"Nuevo llamado (aviso del {dia_mes(en)})",
                             "filas": [{"campo": "Fecha del remate", "a": larga(va) if va else "vacío", "b": larga(vn) if vn else "vacío"},
                                       {"campo": "Hora", "a": a["hora"] or "vacío", "b": n["hora"] or "vacío"},
                                       {"campo": "Mínimo", "a": a["minimo"], "b": n["minimo"]},
                                       {"campo": "Monto del vale vista", "a": a["monto"], "b": n["monto"]}],
                             "nota": "Son dos remates distintos, no un error del aviso. Vale vista entregado y remate asistido volvieron a cero.",
                             "pub_a": pub_remate(con, ra), "pub_b": pub_remate(con, rn)})
            continue
        g = cambios.setdefault((bien, ra, rn), {"bien_id": bien, "titulo": titulo, "caratula": car, "antes": f"Aviso del {dia_mes(ea)}",
                                                 "despues": f"Aviso del {dia_mes(en)}", "filas": [], "fecha": False,
                                                 "pub_a": pub_remate(con, ra), "pub_b": pub_remate(con, rn)})
        g["filas"].append({"campo": _ETIQUETA.get(campo, campo), "a": valor_cambio(campo, va), "b": valor_cambio(campo, vn)})
        g["fecha"] = g["fecha"] or campo in ("fecha_remate", "hora_remate")
    grupos = list(cambios.values())
    titulo = ("FECHAS DE REMATES HAN SIDO CAMBIADAS EN DIFERENTES AVISOS" if any(g["fecha"] for g in grupos)
              else "DATOS DE REMATES HAN CAMBIADO EN DIFERENTES AVISOS")
    return {"cambios": grupos, "titulo_cambios": titulo, "llamados": llamados}


def quitados_que_volvieron(con):
    """Causas quitadas con la X que volvieron con un NUEVO LLAMADO después de quitarlas (decisión de Diego del 18 de Octubre).
    Una republicación del mismo remate no cuenta, sería ruido todos los días."""
    out = []
    for bien, ult in con.execute("SELECT bien_id, ultima_edicion FROM agenda_quitados").fetchall():
        f = con.execute("SELECT e.fecha, k.remate_nuevo FROM cambios k JOIN remates r ON r.id = k.remate_nuevo JOIN avisos a ON a.id = r.aviso_id "
                        "JOIN ediciones e ON e.id = a.edicion_id WHERE k.bien_id = ? AND k.campo = 'nuevo_llamado' AND e.fecha > ? "
                        "ORDER BY e.fecha DESC LIMIT 1", (bien, ult)).fetchone()
        if f:
            titulo, car = _titulo(con, bien)
            ultimo = con.execute("SELECT remate_id, fecha_remate FROM v_buscador WHERE bien_id = ? ORDER BY edicion DESC, remate_id DESC LIMIT 1", (bien,)).fetchone()
            out.append({"bien_id": bien, "remate_id": ultimo[0], "titulo": titulo, "caratula": car,
                        "texto": punto(f"Volvió a publicarse con un nuevo llamado el {dia_mes(f[0])}") + (" " + punto(f"Remate el {corta(ultimo[1])}") if ultimo[1] else "")})
    return out


# --- Estado completo para la página --------------------------------------------------------------------------------
def estado(con, hoy):
    s = estado_sincronizacion(con, hoy)
    fer = aviso_feriados(con, dt.date.fromisoformat(hoy))
    return {"hoy": hoy, "hoy_txt": larga(hoy), "franja_negra": s["franja_negra"],
            "franja_ambar": s["franja_ambar"] + ([fer + "."] if fer else []),
            "agenda": agenda(con, hoy), **avisos_grandes(con), "quitados": quitados_que_volvieron(con),
            "feriados": {f: n for f, n in con.execute("SELECT fecha, nombre FROM feriados")},
            "ediciones": [r[0] for r in con.execute("SELECT fecha FROM ediciones ORDER BY fecha DESC")],
            "ediciones_txt": {r[0]: dia_mes(r[0]) for r in con.execute("SELECT fecha FROM ediciones")}}


def buscar(con, hoy, tribunal="", rol="", anio="", edicion="", pasados=False, limite=300):
    """Decisión de Diego. Por defecto los remates vigentes (que todavía no pasan) de todas las ediciones, la publicación
    más nueva de cada propiedad. Con edición, solo lo publicado ese día. Los tres campos filtran solos. Los remates sin fecha
    van al final, para que arriba queden los más próximos."""
    sql = ("SELECT remate_id FROM (SELECT b.*, ROW_NUMBER() OVER (PARTITION BY COALESCE(b.bien_id, -b.remate_id) "
           "ORDER BY b.edicion DESC, b.remate_id DESC) AS n FROM v_buscador b {w}) WHERE n = 1 {v} ORDER BY fecha_remate IS NULL, fecha_remate, tribunal")
    par = []
    w = ""
    if edicion:
        w, par = "WHERE b.edicion = ?", [edicion]
    v = "" if pasados else "AND (fecha_remate IS NULL OR fecha_remate >= ?)"
    if not pasados:
        par.append(hoy)
    ids = [r[0] for r in con.execute(sql.format(w=w, v=v), par)]
    t, r_, a_ = normalizar(tribunal), re.sub(r"\D", "", rol or ""), re.sub(r"\D", "", anio or "")
    out = []
    for rid in ids:
        f = con.execute("SELECT a.tribunal, a.rol, a.anio FROM remates r JOIN avisos a ON a.id = r.aviso_id WHERE r.id = ?", (rid,)).fetchone()
        if t and t not in normalizar(f[0]):
            continue
        if r_ and r_ not in (f[1] or ""):
            continue
        if a_ and a_ not in (f[2] or ""):
            continue
        out.append(rid)
    total = len(out)
    agendados = {r[0] for r in con.execute("SELECT bien_id FROM agenda")}
    res = []
    for rid in out[:limite]:
        it = armar(con, rid)
        it["en_calendario"] = it["bien_id"] in agendados
        res.append(it)
    return {"total": total, "mostrados": len(res), "resultados": res}


# --- Acciones de Diego -----------------------------------------------------------------------------------------------
def _ahora():
    return dt.datetime.now().isoformat(timespec="seconds")


def agendar(con, remate_id):
    f = con.execute("SELECT bien_id FROM remates WHERE id = ?", (remate_id,)).fetchone()
    if not f or f[0] is None:
        raise ErrorDato("Ese remate no tiene una propiedad identificada y no se puede agendar. Agrégalo a mano.")
    with con:
        con.execute("INSERT OR IGNORE INTO agenda(bien_id, remate_base_id, agregado_en) VALUES (?,?,?)", (f[0], remate_id, _ahora()))
        con.execute("DELETE FROM agenda_quitados WHERE bien_id = ?", (f[0],))
    return {"bien_id": f[0]}


def quitar(con, bien_id=None, manual_id=None):
    with con:
        if manual_id is not None:
            con.execute("DELETE FROM agenda_manual WHERE id = ?", (manual_id,))
            return {}
        ult = con.execute("SELECT MAX(edicion) FROM v_buscador WHERE bien_id = ?", (bien_id,)).fetchone()[0]
        con.execute("DELETE FROM agenda WHERE bien_id = ?", (bien_id,))
        if ult:
            con.execute("INSERT OR REPLACE INTO agenda_quitados(bien_id, quitado_en, ultima_edicion) VALUES (?,?,?)", (bien_id, _ahora(), ult))
    return {}


def ignorar_quitado(con, bien_id):
    ult = con.execute("SELECT MAX(edicion) FROM v_buscador WHERE bien_id = ?", (bien_id,)).fetchone()[0]
    with con:
        con.execute("UPDATE agenda_quitados SET ultima_edicion = ? WHERE bien_id = ?", (ult, bien_id))
    return {}


def marcar(con, campo, valor, bien_id=None, manual_id=None):
    if campo not in ("vv_entregado", "remate_asistido"):
        raise ErrorDato("Campo desconocido.")
    with con:
        if manual_id is not None:
            con.execute(f"UPDATE agenda_manual SET {campo} = ? WHERE id = ?", (1 if valor else 0, manual_id))
        else:
            con.execute(f"UPDATE agenda SET {campo} = ? WHERE bien_id = ?", (1 if valor else 0, bien_id))
    return {}


def visto(con, tipo, bienes=None):
    """tipo 'cambios' o 'llamado'. Marca como vistos los cambios de las causas agendadas que se mostraron."""
    cond = "campo = 'nuevo_llamado'" if tipo == "llamado" else "campo <> 'nuevo_llamado'"
    with con:
        con.execute(f"UPDATE cambios SET visto = 1 WHERE {cond} AND bien_id IN (SELECT bien_id FROM agenda)"
                    + (f" AND bien_id IN ({','.join('?' * len(bienes))})" if bienes else ""), list(bienes or []))
    return {}


_MOD = {"pres": "presencial", "virt": "zoom", "nose": "sin_dato"}


def agregar_manual(con, datos):
    fecha = (datos.get("fecha") or "").strip()
    if not re.fullmatch(r"\d{4}-\d\d-\d\d", fecha):
        raise ErrorDato("Falta la fecha del remate.")
    vd, vh = (datos.get("vd") or "").strip() or None, (datos.get("vh") or "").strip() or None
    if vd and vh and vd > vh:
        raise ErrorDato("El desde del vale vista no puede ir después del hasta.")
    rol = re.sub(r"\D", "", datos.get("rol") or "") or None
    anio = re.sub(r"\D", "", datos.get("anio") or "") or None
    with con:
        cur = con.execute("INSERT INTO agenda_manual(tribunal, rol, anio, caratula, fecha_remate, hora_remate, modalidad, vv_desde, vv_hasta, "
                          "monto_vv, agregado_en) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                          ((datos.get("trib") or "").strip() or None, rol, anio, (datos.get("car") or "").strip() or None, fecha,
                           (datos.get("hora") or "").strip() or None, _MOD.get(datos.get("mod"), "sin_dato"), vd, vh,
                           (datos.get("monto") or "").strip() or None, _ahora()))
    return {"manual_id": cur.lastrowid}


def reemplazar_manual(con, manual_id, remate_id):
    """Diego acepta cambiar la causa a mano por la publicada. Se agenda la del diario y se conserva lo que marcó."""
    m = con.execute("SELECT vv_entregado, remate_asistido FROM agenda_manual WHERE id = ?", (manual_id,)).fetchone()
    if not m:
        raise ErrorDato("Esa causa a mano ya no existe.")
    r = agendar(con, remate_id)
    with con:
        con.execute("UPDATE agenda SET vv_entregado = ?, remate_asistido = ? WHERE bien_id = ?", (m[0], m[1], r["bien_id"]))
        con.execute("DELETE FROM agenda_manual WHERE id = ?", (manual_id,))
    return r


def ignorar_publicado(con, manual_id):
    with con:
        con.execute("UPDATE agenda_manual SET publicado_ignorado = 1 WHERE id = ?", (manual_id,))
    return {}

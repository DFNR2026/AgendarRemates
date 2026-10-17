"""Une el motor con la base (paso 4 del ESTADO, 16 de Octubre). Lectura ya hecha -> corte -> extracción por código -> carga.

traducir() pasa lo que entrega motor.extraccion.extraer() al formato que espera db.carga.guardar_edicion()
(el del banco nivel 2). La carga guarda las citas con método 'codigo' y las alertas del código con su tipo.
Todavía no hay vale vista ni dirección (parte 3.7), así que cada remate queda con la alerta de vale vista no leído.

Uso. python -m motor.procesar_edicion AAAA-MM-DD RUTA_BASE [--sin-ia]   (desde D:\\Agendar_Remates)
Si Haiku no respondió en todos los avisos, la edición queda con alarma y se termina con
python -m motor.procesar_edicion --retomar AAAA-MM-DD RUTA_BASE (no vuelve a leer el Mercurio ni a cargar la edición).
Desde la parte 3.7a cada aviso pasa por Haiku para la regla del vale vista (agregar_vale_vista). Necesita internet y la
clave en config.py. Si no hay cómo llamar a Haiku, la carga sigue con las respuestas guardadas y el resto queda como
vale vista no leído. --sin-ia carga como antes, sin vale vista.
Lee capturas\\AAAA-MM-DD (páginas y navegacion.json que guarda el lector). No carga en agendar_remates.db
hasta que Diego lo apruebe. Una edición con dos rollos (B y G los viernes) se une sin duplicar por la huella del texto
de cada aviso (16 de Octubre, ver unir_rollos).
"""
import json, re, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.cortador import construir_rollo, cortar, roles_en
from motor.orden_columnas import leer_pagina
from motor.extraccion import extraer
from db.carga import guardar_edicion, es_partidor

CAPTURAS = RAIZ / "capturas"

# Vale vista leído por la IA (parte 3.7a, diseño aprobado por Diego, bitácora del 16, punto 42). Colores sin cambiar el
# esquema. calculado = verde, revisar con vv_hasta = ámbar, revisar sin vv_hasta = rojo, sin_dato = sin dato.
VV_CONTRADICCION = "El aviso da dos plazos u horarios distintos para la entrega del vale vista."
VV_ERROR_ESCRITURA = "El aviso pide el vale vista en una fecha anterior a la edición. Posible error de escritura del aviso."


# Textos del rojo en palabras simples (decisión de Diego del 17 de Octubre). Cada alerta roja empieza con el grupo,
# sigue el motivo simple y termina con la explicación del grupo. Si hay varios motivos va el grupo más grave.
GRUPOS = {   # en orden de gravedad
    "Error del aviso": "El problema está en cómo se redactó el aviso, no en la IA. No se puede saber cuál de las dos versiones vale. "
                       "Revisa el aviso, y si el remate te interesa, confirma en el tribunal o en las bases. Un error de redacción "
                       "podría servir para objetar el remate (pregunta para el abogado).",
    "Dudoso": "Puede ser un error de redacción del aviso o una mala lectura de la IA, y el programa no logra distinguirlo. "
              "Revisa el aviso para ver cuál de los dos es.",
    "Límite del programa": "El aviso puede estar bien y la IA no tiene la culpa. Falló otra parte del programa. Revisa la fecha o "
                           "la hora en el aviso. Si faltan los feriados, hay que cargar el archivo de feriados de ese año.",
    "Regla nueva": "El aviso está bien y la IA no se equivocó. El programa todavía no sabe calcular esa regla. Lee la regla en "
                   "el aviso y anota la fecha a mano. Más adelante se agrega la regla, validándola con otra edición anotada.",
    "Falla de la IA": "El aviso está bien escrito y fue Haiku el que se equivocó. El programa lo atrapó y por eso no te da una "
                      "fecha. Lee la regla en el aviso y anota la fecha a mano. Si este error se repite mucho con el mismo tipo "
                      "de frase, se mejoran las instrucciones de la IA.",
}
_IA_FRASE = "La IA citó una frase que no está escrita así en el aviso."
_IA_REGLA = "La IA leyó una regla que no calza con las palabras del aviso."
# (patrón del motivo técnico de motor\\vale_vista.py, grupo, motivo simple). El primero que calza manda.
_MOTIVOS = [
    (r"^La frase no dice que el vale vista se entregue en el remate", "Falla de la IA", "La IA dijo que el vale vista se entrega en el remate, pero el aviso no lo dice."),
    (r"^La frase no trae las palabras propias de la regla en_el_remate", "Falla de la IA", "La IA dijo que el vale vista se entrega en el remate, pero el aviso no lo dice."),
    (r"^Las dos lecturas de la IA no coinciden", "Falla de la IA", "Las dos lecturas de la IA dieron reglas distintas."),
    (r"^Falta la segunda lectura de la IA", "Falla de la IA", "La IA entregó una sola lectura de las dos que se piden."),
    (r"^Regla desconocida", "Falla de la IA", "La IA respondió una regla que no está en la lista."),
    (r"^La frase de la regla no está en el aviso|^La IA no entregó la frase de la regla|^Frase extra no encontrada|^La frase de contradicción no está", "Falla de la IA", _IA_FRASE),
    (r"^La frase habla de devolución", "Falla de la IA", "La IA tomó la frase de la devolución del vale vista, no la de su entrega."),
    (r"^La IA no encontró regla, pero el aviso parece dar un plazo", "Falla de la IA", "La IA no encontró la regla, pero el aviso parece dar un plazo."),
    (r"^La frase nombra un día de la semana distinto", "Falla de la IA", "El día que nombra el aviso no calza con el día que calculó el programa con la regla de la IA."),
    (r"^La frase no trae las palabras propias|^La frase dice día hábil|^Faltan los días hábiles|^El número de días|^Faltan las horas|"
     r"^El número de horas|^La fecha fija no está escrita|^hora_desde con formato|^hora_hasta con formato|^La hora \d|^La hora desde no es anterior", "Falla de la IA", _IA_REGLA),
    (r"^La IA dice que la regla no calza con ninguna conocida", "Regla nueva", "La regla del aviso es de un tipo que el programa todavía no conoce."),
    (r"^El aviso da dos plazos u horarios distintos", "Error del aviso", "El aviso da dos plazos u horarios distintos para la entrega."),
    (r"^La fecha de entrega es anterior a la edición", "Error del aviso", "El aviso pide el vale vista en una fecha que ya pasó al publicarse."),
    (r"^La fecha del remate es anterior a la edición", "Error del aviso", "La fecha del remate ya pasó al publicarse."),
    (r"^La entrega quedaría después del remate", "Dudoso", "El plazo de entrega quedaría después del remate."),
    (r"^Falta la fecha del remate", "Límite del programa", "El programa no encontró la fecha del remate."),
    (r"^Falta la hora del remate", "Límite del programa", "El programa no encontró la hora del remate."),
    (r"^No están cargados los feriados de (\d{4})", "Límite del programa", "Faltan los feriados de {0}."),
    (r"^Regla .* sin cálculo", "Límite del programa", "El programa no tiene cálculo para esta regla."),
]


def traducir_motivo(m: str) -> tuple:
    """Motivo técnico de resolver() -> (grupo, motivo simple). Un motivo que no se conoce queda como Dudoso con su texto."""
    m = re.sub(r"^(?:Segunda lectura\. )+", "", m.strip())
    for patron, grupo, simple in _MOTIVOS:
        k = re.search(patron, m)
        if k:
            return grupo, simple.format(*k.groups())
    return "Dudoso", m


def texto_rojo(motivos: list) -> str:
    """Alerta roja completa. Grupo más grave, motivos simples sin repetir y la explicación del grupo."""
    pares = [traducir_motivo(m) for m in motivos] or [("Dudoso", "El programa no dejó motivo.")]
    grupo = min((g for g, _ in pares), key=list(GRUPOS).index)
    simples = list(dict.fromkeys(s for _, s in pares))
    return f"{grupo}. {' '.join(simples)} {GRUPOS[grupo]}"


def _preguntas_texto(p: list) -> str:
    if len(p) == 1:
        return f"Fecha del vale vista provisoria. Depende de la pregunta {p[0]} al abogado."
    return f"Fecha del vale vista provisoria. Depende de las preguntas {', '.join(map(str, p[:-1]))} y {p[-1]} al abogado."


def bloque_vale_vista(res: dict) -> dict:
    """Resultado de motor.vale_vista.resolver() -> bloque 'vale_vista' para db.carga (formato del banco más 'metodo' y
    'alertas'). Las citas van con método ia (la frase ya viene tal como está en el aviso). En rojo nunca se guardan fechas."""
    from motor.vale_vista import NO_ENCONTRADA
    color, cita = res["color"], res.get("cita")
    b = {"metodo": "ia", "regla": res.get("regla"), "cita": cita, "citas_extra": list(res.get("citas_extra") or []),
         "vv_desde": res.get("vv_desde"), "vv_desde_origen": res.get("vv_desde_origen"), "vv_hasta": res.get("vv_hasta"),
         "vv_estado": res.get("vv_estado"), "color": color, "alertas": []}
    if color == "verde":
        b["vv_estado"] = "calculado"
    elif color == "ambar":
        b["vv_estado"] = "revisar"
        b["alertas"].append(("condicion_especial", _preguntas_texto(res.get("preguntas") or []), cita))
    elif color == "sin_dato":
        b.update(vv_estado="sin_dato", vv_desde=None, vv_desde_origen=None, vv_hasta=None)
        b["alertas"].append(("dato_faltante", NO_ENCONTRADA, None))
    else:                                            # rojo
        b.update(vv_estado="revisar", vv_desde=None, vv_desde_origen=None, vv_hasta=None)
        b["alertas"].append(("revisar_lectura", texto_rojo(list(res.get("motivos") or [])), cita))
    if res.get("contradiccion"):                     # contradicción real (ya se descartaron correo, escrito, OJV y cupón)
        b["alertas"].append(("contradiccion", VV_CONTRADICCION, res["contradiccion"]))
    if any("Posible error de escritura" in m for m in res.get("motivos") or []):
        b["alertas"].append(("error_escritura", VV_ERROR_ESCRITURA, cita))
    # La fecha del remate anterior a la edición NO se avisa aquí. Ya la avisa extraccion.fecha_y_hora con las dos fechas en
    # palabras (06-10 aviso 45, 15-10 C-5633-2024). Salían dos alertas iguales (aprobado por Diego el 17 de Octubre, noche).
    return b


def traducir(x: dict) -> dict:
    """Salida de extraer() -> formato del banco nivel 2 (sin vale_vista ni dirección, que son de la parte 3.7)."""
    return {"tribunal": (x.get("tribunal") or {}).get("valor"),
            "fecha_remate": x["fecha_remate"], "hora_remate": x["hora_remate"], "modalidad": x["modalidad"],
            "plataforma": x.get("plataforma"), "minimo": x["minimo"], "garantia": x["garantia"],
            "inscripcion": x.get("inscripcion"), "caratula": x.get("caratula"), "alertas": list(x.get("alertas") or []), "dudas": [], "pegado": bool(x.get("pegado"))}


def extraer_avisos(avisos: list, fecha: str) -> dict:
    """{orden: datos traducidos} para todos los avisos del cortador."""
    return {a.orden: traducir(extraer(a.texto, fecha)) for a in avisos}


def agregar_vale_vista(avisos: list, extraido: dict, fecha: str, cliente=None) -> dict:
    """Parte 3.7a. Agrega a cada aviso el bloque 'vale_vista' leído por Haiku (motor.vale_vista), después de extraer(),
    con la fecha y la hora del remate que dio el código. Se saltan los avisos de partición y los marcados como pegados.
    Usa primero las respuestas guardadas (ia_respuestas\\vale_vista). Si no hay respuesta guardada y Haiku no está
    disponible (sin cliente, sin internet, sin saldo o cualquier error), ese aviso queda SIN bloque y la carga pone la
    alerta de siempre (vale vista no leído). Nunca se cae la carga por la IA.
    Devuelve un resumen {leidos, sin_ia, saltados, colores, errores}."""
    from motor import vale_vista as V
    resumen = {"leidos": 0, "sin_ia": 0, "saltados": 0, "colores": {}, "errores": []}
    for a in avisos:
        ex = extraido[a.orden]
        if ex.get("pegado") or es_partidor(ex.get("tribunal"), a.texto):
            resumen["saltados"] += 1; continue
        try:
            g = V.leer_con_ia(a.texto, cliente)
        except Exception as e:
            resumen["sin_ia"] += 1; resumen["errores"].append(f"aviso {a.orden}. {type(e).__name__}. {str(e)[:120]}"); continue
        if len(g.get("lecturas") or []) < 2:
            resumen["sin_ia"] += 1; resumen["errores"].append(f"aviso {a.orden}. {' '.join(g.get('errores') or ['Faltan lecturas de la IA.'])[:200]}"); continue
        res = V.resolver(g["lecturas"], a.texto, (ex.get("fecha_remate") or {}).get("valor"), (ex.get("hora_remate") or {}).get("valor"), fecha)
        ex["vale_vista"] = bloque_vale_vista(res)
        resumen["leidos"] += 1
        resumen["colores"][res["color"]] = resumen["colores"].get(res["color"], 0) + 1
    return resumen


VV_ALARMA = "Vale vista. "      # comienzo de la línea de alarma de la edición (la busca retomar_vale_vista)


def cambiar_alarma(alarmas: str | None, prefijo: str, nueva: str | None, estado: str) -> tuple:
    """Reemplaza la línea de alarma que empieza con prefijo EN SU MISMO LUGAR (17 de Octubre. Antes se borraba y se agregaba
    al final, y al retomar el vale vista quedaba después de la línea de la dirección, distinto a una carga nueva).
    Sin línea nueva se borra. El estado vuelve a ok solo si no queda ninguna alarma."""
    lineas = (alarmas or "").splitlines()
    k = next((i for i, x in enumerate(lineas) if x.startswith(prefijo)), None)
    if k is not None:
        lineas[k:k + 1] = [nueva] if nueva else []
    elif nueva:
        lineas.append(nueva)
    if nueva:
        estado = "con_alarmas"
    elif not lineas:
        estado = "ok"
    return lineas, estado


def alarma_vale_vista(vv: dict) -> str | None:
    """Línea de alarma de la edición si quedaron avisos sin leer por la IA (decisión de Diego del 17 de Octubre)."""
    if not vv or not vv.get("sin_ia"):
        return None
    return (f"{VV_ALARMA}{vv['sin_ia']} de {vv['sin_ia'] + vv['leidos']} avisos quedaron sin leer por la IA. "
            "Se puede retomar sin volver a leer el Mercurio.")


def retomar_vale_vista(con, fecha: str, cliente=None) -> dict:
    """Decisión 8 (17 de Octubre). Termina de leer el vale vista de una edición YA cargada cuando Haiku no respondió en
    todos los avisos. No vuelve a leer el Mercurio ni a cargar la edición (la carga rechaza una edición repetida).
    Busca los avisos visibles que siguen con la alerta de vale vista no leído, pregunta a Haiku solo por esos (primero las
    respuestas guardadas, así lo ya pagado no se paga de nuevo) y deja cada uno igual que si se hubiera leído en la carga.
    Actualiza la línea de alarma de la edición. Todo en una transacción. Si Haiku vuelve a fallar, esos avisos siguen
    pendientes y no se cae nada."""
    from motor import vale_vista as V
    from db.carga import VV_NO_LEIDO
    fila = con.execute("SELECT id, estado, alarmas FROM ediciones WHERE fecha = ?", (fecha,)).fetchone()
    if not fila:
        raise ValueError(f"La edición {fecha} no está en la base. No hay nada que retomar.")
    ed_id, estado, alarmas = fila
    pend = con.execute("SELECT DISTINCT a.id, a.orden, a.texto FROM avisos a JOIN alertas al ON al.aviso_id = a.id "
                       "WHERE a.edicion_id = ? AND a.filtro_estado <> 'descartado' AND al.texto = ? ORDER BY a.orden",
                       (ed_id, VV_NO_LEIDO)).fetchall()
    resumen = {"pendientes_antes": 0, "leidos": 0, "sin_ia": 0, "saltados": 0, "colores": {}, "errores": []}
    with con:
        for aviso_id, orden, texto in pend:
            if extraer(texto, fecha).get("pegado"):          # en la carga tampoco se le pregunta a la IA
                resumen["saltados"] += 1; continue
            resumen["pendientes_antes"] += 1
            try:
                g = V.leer_con_ia(texto, cliente)
            except Exception as e:
                resumen["sin_ia"] += 1; resumen["errores"].append(f"aviso {orden}. {type(e).__name__}. {str(e)[:120]}"); continue
            if len(g.get("lecturas") or []) < 2:
                resumen["sin_ia"] += 1; resumen["errores"].append(f"aviso {orden}. {' '.join(g.get('errores') or ['Faltan lecturas de la IA.'])[:200]}"); continue
            f, h, n_rem = con.execute("SELECT fecha_remate, hora_remate, COUNT(*) FROM remates WHERE aviso_id = ?", (aviso_id,)).fetchone()
            res = V.resolver(g["lecturas"], texto, f, h, fecha)
            b = bloque_vale_vista(res)
            con.execute("UPDATE remates SET vv_regla = ?, vv_regla_texto = ?, vv_desde = ?, vv_desde_origen = ?, vv_hasta = ?, vv_estado = ? "
                        "WHERE aviso_id = ?", (b["regla"], b["cita"], b["vv_desde"], b["vv_desde_origen"], b["vv_hasta"], b["vv_estado"], aviso_id))
            subs = [r[0] for r in con.execute("SELECT sub_orden FROM alertas WHERE aviso_id = ? AND texto = ? ORDER BY id", (aviso_id, VV_NO_LEIDO))]
            con.execute("DELETE FROM alertas WHERE aviso_id = ? AND texto = ?", (aviso_id, VV_NO_LEIDO))
            for sub in subs:                                   # mismas posiciones que la alerta que reemplaza (igual que la carga)
                for tipo, txt, cita in b["alertas"]:
                    con.execute("INSERT INTO alertas(aviso_id, sub_orden, tipo, texto, cita, origen) VALUES (?,?,?,?,?,?)",
                                (aviso_id, sub, tipo, txt, cita, "codigo"))
            if b["cita"]:                                      # mismas citas que pone la carga (db.carga._citas_de)
                comun = 1 if n_rem == 1 else 0
                for i, c in enumerate([b["cita"]] + b["citas_extra"], start=1):
                    con.execute("INSERT INTO citas(aviso_id, sub_orden, campo, n_cita, valor, cita, metodo, verificada) VALUES (?,?,?,?,?,?,?,?)",
                                (aviso_id, comun, "vv_regla_texto", i, b["regla"], c, "ia", int(c in texto)))
            resumen["leidos"] += 1
            resumen["colores"][res["color"]] = resumen["colores"].get(res["color"], 0) + 1
        # Línea de alarma de la edición. Se cuenta sobre todos los avisos que la IA debe leer, no solo los de esta vuelta.
        total = con.execute("SELECT COUNT(*) FROM avisos WHERE edicion_id = ? AND filtro_estado <> 'descartado'", (ed_id,)).fetchone()[0] - resumen["saltados"]
        nueva = alarma_vale_vista({"sin_ia": resumen["sin_ia"], "leidos": total - resumen["sin_ia"]})
        lineas, estado = cambiar_alarma(alarmas, VV_ALARMA, nueva, estado)
        con.execute("UPDATE ediciones SET alarmas = ?, estado = ? WHERE id = ?", ("\n".join(lineas) or None, estado, ed_id))
    return resumen


# --- Dirección leída por la IA (parte 3.7b, decisiones de Diego del 17 de Octubre) -----------------------------------
DIR_ALARMA = "Dirección. "      # comienzo de la línea de alarma de la edición (la busca retomar_direccion)


def bloque_direccion(res: dict) -> dict:
    """Resultado de motor.direccion.resolver() -> bloque 'direccion' para db.carga ('lista' una por remate, método ia,
    alertas por color). En rojo y sin dato la lista va vacía. El rojo lleva las dos lecturas y la frase del aviso."""
    from motor import direccion as DR
    b = {"metodo": "ia", "color": res["color"], "lista": list(res.get("inmuebles") or []), "alertas": []}
    if res["color"] == "rojo":
        b["alertas"].append(("revisar_lectura", DR.texto_rojo(res), res.get("frase")))
    elif res["color"] == "sin_dato":
        b["alertas"].append(("dato_faltante", DR.NO_ENCONTRADA, None))
    return b


def _n_remates(ex: dict) -> int:
    mi = ex.get("minimo") or {}
    return len(mi["lista"]) if mi.get("lista") else 1


def agregar_direccion(avisos: list, extraido: dict, fecha: str, cliente=None) -> dict:
    """Parte 3.7b. Agrega a cada aviso el bloque 'direccion' leído por Haiku (motor.direccion), con la cantidad de remates
    que dio el código. Se saltan los avisos de partición y los pegados (igual que el vale vista). Primero las respuestas
    guardadas. Si Haiku no está, el aviso queda con la alerta de dirección no leída y se puede retomar. Nunca se cae."""
    from motor import direccion as DR
    from db.carga import DIR_NO_LEIDA
    resumen = {"leidos": 0, "sin_ia": 0, "saltados": 0, "colores": {}, "errores": []}
    for a in avisos:
        ex = extraido[a.orden]
        if ex.get("pegado") or es_partidor(ex.get("tribunal"), a.texto):
            resumen["saltados"] += 1; continue
        n = _n_remates(ex)
        try:
            g = DR.leer_con_ia(a.texto, n, cliente)
        except Exception as e:
            g = {"lecturas": [], "errores": [f"{type(e).__name__}. {str(e)[:120]}"]}
        if len(g.get("lecturas") or []) < 2:
            resumen["sin_ia"] += 1; resumen["errores"].append(f"aviso {a.orden}. {' '.join(g.get('errores') or ['Faltan lecturas de la IA.'])[:200]}")
            ex["direccion"] = {"metodo": "ia", "color": None, "lista": [], "alertas": [("dato_faltante", DIR_NO_LEIDA, None)]}
            continue
        res = DR.resolver(g["lecturas"], a.texto, n)
        ex["direccion"] = bloque_direccion(res)
        resumen["leidos"] += 1
        resumen["colores"][res["color"]] = resumen["colores"].get(res["color"], 0) + 1
    return resumen


def alarma_direccion(dr: dict) -> str | None:
    if not dr or not dr.get("sin_ia"):
        return None
    return (f"{DIR_ALARMA}{dr['sin_ia']} de {dr['sin_ia'] + dr['leidos']} avisos quedaron sin leer por la IA. "
            "Se puede retomar sin volver a leer el Mercurio.")


def retomar_direccion(con, fecha: str, cliente=None) -> dict:
    """Termina de leer la dirección de una edición YA cargada (igual que retomar_vale_vista). Busca los avisos visibles con la
    alerta de dirección no leída, pregunta a Haiku solo por esos (primero lo guardado) y los deja igual que si se hubieran
    leído en la carga. Actualiza la alarma de la edición. Una transacción."""
    from motor import direccion as DR
    from db.carga import DIR_NO_LEIDA
    fila = con.execute("SELECT id, estado, alarmas FROM ediciones WHERE fecha = ?", (fecha,)).fetchone()
    if not fila:
        raise ValueError(f"La edición {fecha} no está en la base. No hay nada que retomar.")
    ed_id, estado, alarmas = fila
    pend = con.execute("SELECT DISTINCT a.id, a.orden, a.texto FROM avisos a JOIN alertas al ON al.aviso_id = a.id "
                       "WHERE a.edicion_id = ? AND a.filtro_estado <> 'descartado' AND al.texto = ? ORDER BY a.orden",
                       (ed_id, DIR_NO_LEIDA)).fetchall()
    resumen = {"pendientes_antes": len(pend), "leidos": 0, "sin_ia": 0, "colores": {}, "errores": []}
    with con:
        for aviso_id, orden, texto in pend:
            subs = [r[0] for r in con.execute("SELECT sub_orden FROM remates WHERE aviso_id = ? ORDER BY sub_orden", (aviso_id,))]
            n = len(subs)
            try:
                g = DR.leer_con_ia(texto, n, cliente)
            except Exception as e:
                g = {"lecturas": [], "errores": [f"{type(e).__name__}. {str(e)[:120]}"]}
            if len(g.get("lecturas") or []) < 2:
                resumen["sin_ia"] += 1; resumen["errores"].append(f"aviso {orden}. {' '.join(g.get('errores') or [])[:200]}"); continue
            res = DR.resolver(g["lecturas"], texto, n)
            b = bloque_direccion(res)
            pos = [r[0] for r in con.execute("SELECT sub_orden FROM alertas WHERE aviso_id = ? AND texto = ? ORDER BY id", (aviso_id, DIR_NO_LEIDA))]
            con.execute("DELETE FROM alertas WHERE aviso_id = ? AND texto = ?", (aviso_id, DIR_NO_LEIDA))
            for sub in pos:
                for tipo, txt, cita in b["alertas"]:
                    con.execute("INSERT INTO alertas(aviso_id, sub_orden, tipo, texto, cita, origen) VALUES (?,?,?,?,?,?)",
                                (aviso_id, sub, tipo, txt, cita, "codigo"))
            for k, (sub, el) in enumerate(zip(subs, b["lista"]), start=1):
                con.execute("UPDATE remates SET direccion = ?, comuna = ? WHERE aviso_id = ? AND sub_orden = ?",
                            (el["direccion"], el["comuna"], aviso_id, sub))
                for i, c in enumerate([el["cita"]] + list(el.get("citas_extra") or []), start=1):
                    con.execute("INSERT INTO citas(aviso_id, sub_orden, campo, n_cita, valor, cita, metodo, verificada) VALUES (?,?,?,?,?,?,?,?)",
                                (aviso_id, sub if n > 1 else 1, "direccion", i, el["direccion"], c, "ia", int(c in texto)))
            resumen["leidos"] += 1
            resumen["colores"][res["color"]] = resumen["colores"].get(res["color"], 0) + 1
        total_pend = con.execute("SELECT COUNT(DISTINCT a.id) FROM avisos a JOIN alertas al ON al.aviso_id = a.id WHERE a.edicion_id = ? "
                                 "AND a.filtro_estado <> 'descartado' AND al.texto = ?", (ed_id, DIR_NO_LEIDA)).fetchone()[0]
        leidos_total = con.execute("SELECT COUNT(DISTINCT aviso_id) FROM citas c JOIN avisos a ON a.id = c.aviso_id WHERE a.edicion_id = ? "
                                   "AND c.campo = 'direccion' AND c.metodo = 'ia'", (ed_id,)).fetchone()[0]
        nueva = alarma_direccion({"sin_ia": total_pend, "leidos": leidos_total}) if total_pend else None
        lineas, estado = cambiar_alarma(alarmas, DIR_ALARMA, nueva, estado)
        con.execute("UPDATE ediciones SET alarmas = ?, estado = ? WHERE id = ?", ("\n".join(lineas) or None, estado, ed_id))
    return resumen


def huella(texto: str) -> str:
    """Solo letras y números en minúscula. Ignora espacios, guiones y signos, que cambian entre la lectura de B y la de G
    (2026-10-09. 7 de 127 avisos con diferencias de espacios, 127 de 127 iguales con esta huella)."""
    return re.sub(r"[\W_]+", "", texto.lower())


def unir_rollos(cortados: list) -> tuple:
    """cortados = [avisos del cortador por rollo], en el orden de la navegación. El primero es el principal.
    Un aviso de otro rollo con gemelo (misma huella) en el principal no se carga, solo se cuenta. Las repeticiones se
    cuentan, así dos avisos iguales de verdad no se funden en uno. Un aviso sin gemelo se carga después de los del
    principal, con alerta. Si los gemelos imprimen el rol distinto, el aviso del principal lleva una alerta.
    Devuelve (avisos, alertas_extra {orden: [(tipo, texto)]}, resumen)."""
    avisos = list(cortados[0])
    alertas, resumen = {}, []
    for k, otro in enumerate(cortados[1:], start=2):
        libres = {}
        for a in avisos[:len(cortados[0])]:
            libres.setdefault(huella(a.texto), []).append(a)
        unidos = espacios = 0
        solos = []
        for b in otro:
            gem = libres.get(huella(b.texto))
            if gem:
                a = gem.pop(0)
                unidos += 1
                espacios += a.texto != b.texto
                if (a.rol_impreso or "") != (b.rol_impreso or ""):
                    alertas.setdefault(a.orden, []).append(("revisar_lectura",
                        f"El cuerpo {b.paginas[0][0]} imprime este rol distinto ({b.rol_impreso}, aquí {a.rol_impreso}). Revisa el aviso en la página."))
            else:
                solos.append(b)
        for b in solos:
            b.orden = len(avisos) + 1
            avisos.append(b)
            alertas.setdefault(b.orden, []).append(("revisar_lectura",
                f"Aviso que solo aparece en el cuerpo {b.paginas[0][0]}. No tiene gemelo en el cuerpo {cortados[0][0].paginas[0][0]}."))
        c1, c2 = cortados[0][0].paginas[0][0], otro[0].paginas[0][0] if otro else "?"
        resumen.append(f"Cuerpo {c2} repite al {c1}. {unidos} de {len(otro)} avisos unidos por huella del texto. "
                       f"{espacios} con diferencias de espacios. {len(solos)} solo en {c2}.")
    return avisos, alertas, resumen


def desde_captura(fecha: str, carpeta: Path | None = None):
    """Arma edición, páginas, avisos y alertas de la unión desde capturas\\FECHA (navegacion.json del lector).
    Con varios rollos (B y G los viernes) se cortan por separado y se unen sin duplicar (unir_rollos)."""
    d = carpeta or (CAPTURAS / fecha)
    nav = json.loads((d / "navegacion.json").read_text(encoding="utf-8"))
    if not nav["rollos"]:
        raise ValueError(f"La edición {fecha} no tiene rollos de remates. No se cargó nada.")
    por_nombre = {p["pagina"]: p for p in nav["paginas_con_remates"]}
    paginas, cortados, roles = [], [], set()
    for rollo_nombres in nav["rollos"]:
        for n in rollo_nombres:
            paginas.append({"nombre": n, "cuerpo": n[0], "numero": int(n[1:]), "id_pagina": por_nombre[n]["id"],
                            "orden_rollo": len(paginas) + 1, "texto": (d / por_nombre[n]["archivo"]).read_text(encoding="utf-8")})
        rollo, marcas = construir_rollo([(n, leer_pagina(d / por_nombre[n]["archivo"])) for n in rollo_nombres])
        cortados.append(cortar(rollo, marcas))
        roles |= {(r[1], r[2]) for r in roles_en(rollo)}
    avisos, alertas, resumen = unir_rollos(cortados)
    alarmas = list(nav.get("alarmas") or []) + resumen
    solo_otro = len(avisos) > len(cortados[0])
    cuerpos = " ".join(f"{c}{v.split('n=')[-1]}" for c, v in sorted(nav["cuerpos"].items()))
    edicion = {"fecha": fecha, "leida_en": nav["leida_en"], "estado": "con_alarmas" if nav.get("alarmas") or solo_otro else "ok",
               "cuerpos_revisados": cuerpos, "roles_en_texto": len(roles), "alarmas": "\n".join(alarmas) or None,
               "_roles": roles}                # para el cuadre (parte 4). La carga no guarda esta clave
    return edicion, paginas, avisos, alertas


def cargar_edicion(con, fecha: str, ahora: str, carpeta: Path | None = None, cliente=None, usar_ia: bool = True) -> dict:
    """usar_ia=False deja el vale vista sin leer (como antes de la parte 3.7a). Con usar_ia=True y cliente=None solo se usan
    las respuestas guardadas (así corren las pruebas sin internet)."""
    from motor import republicaciones as RP
    edicion, paginas, avisos, alertas = desde_captura(fecha, carpeta)
    extraido = extraer_avisos(avisos, fecha)
    for orden, extra in alertas.items():
        extraido[orden]["alertas"] += extra
    # Parte 4. Cuadre de cuentas. Aviso con dos roles distintos y roles del texto que no quedaron en ningún aviso.
    for orden, extra in RP.alertas_cuadre(avisos, extraido).items():
        extraido[orden]["alertas"] += extra
    linea_cuadre = RP.alarma_cuadre(edicion.get("_roles") or set(), avisos)
    if linea_cuadre:
        edicion = dict(edicion, estado="con_alarmas", alarmas="\n".join(x for x in (edicion.get("alarmas"), linea_cuadre) if x))
    vv = agregar_vale_vista(avisos, extraido, fecha, cliente) if usar_ia else None
    dr = agregar_direccion(avisos, extraido, fecha, cliente) if usar_ia else None      # parte 3.7b
    for linea in (alarma_vale_vista(vv), alarma_direccion(dr)):
        if linea:
            edicion = dict(edicion, estado="con_alarmas", alarmas="\n".join(x for x in (edicion.get("alarmas"), linea) if x))
    res = guardar_edicion(con, edicion, paginas, avisos, extraido, ahora, metodo="codigo")
    if vv is not None:
        res["vale_vista"] = vv
    if dr is not None:
        res["direccion"] = dr
    res["cambios"] = RP.registrar_cambios(con, fecha, ahora)        # parte 4, cambios entre publicaciones
    return res


def cliente_o_nada():
    """Cliente de Haiku desde config.py, o (None, motivo) si no se puede crear (sin paquete anthropic, sin clave, error)."""
    from motor import vale_vista as V
    try:
        return V.cliente_desde_config(), None
    except Exception as e:
        return None, f"No se pudo crear el cliente de Haiku ({type(e).__name__}). Se usan solo las respuestas guardadas."


if __name__ == "__main__":
    import datetime as dt
    from db.crear_base import crear, BASE
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(args) < 2:
        raise SystemExit("Uso. python -m motor.procesar_edicion AAAA-MM-DD RUTA_BASE [--sin-ia] [--solo-guardadas]\n"
                         "     python -m motor.procesar_edicion --retomar AAAA-MM-DD RUTA_BASE [--solo-guardadas]")
    fecha, ruta = args[0], Path(args[1])
    if ruta.resolve() == BASE.resolve():
        raise SystemExit("Por ahora solo en bases de prueba. La base real espera la aprobación de Diego.")
    # --solo-guardadas no crea el cliente de Haiku (nunca llama a la API). Lo usan las pruebas (17 de Octubre, la prueba del
    # paso 5 llamó a Haiku en el PC de Diego porque el comando creaba el cliente con la clave de config.py).
    solo_guardadas = "--solo-guardadas" in sys.argv
    if solo_guardadas:
        print("Solo respuestas guardadas. No se llama a Haiku.")
    if "--retomar" in sys.argv:
        # Decisión 8. Termina el vale vista de una edición ya cargada, sin volver a leer el Mercurio.
        if not ruta.exists():
            raise SystemExit(f"No existe la base {ruta}. No hay nada que retomar.")
        cliente, motivo = (None, None) if solo_guardadas else cliente_o_nada()
        if motivo:
            print("AVISO.", motivo)
        con = crear(ruta)
        print("Vale vista.", retomar_vale_vista(con, fecha, cliente))
        print("Dirección.", retomar_direccion(con, fecha, cliente))      # parte 3.7b
        from motor.republicaciones import registrar_cambios
        print("Cambios.", registrar_cambios(con, fecha, dt.datetime.now().isoformat(timespec="seconds")))   # parte 4
        raise SystemExit(0)
    usar_ia = "--sin-ia" not in sys.argv
    cliente, motivo = cliente_o_nada() if usar_ia and not solo_guardadas else (None, None)
    if motivo:
        print("AVISO.", motivo)
    print(cargar_edicion(crear(ruta), fecha, dt.datetime.now().isoformat(timespec="seconds"), cliente=cliente, usar_ia=usar_ia))

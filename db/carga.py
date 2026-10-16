"""Guarda en la base una edición ya leída y cortada, con lo extraído de cada aviso.
Parte 3.5, etapa 2. Lo extraído usa el formato del banco nivel 2 (banco_pruebas/2026-10-14/banco_nivel2_2026-10-14.json),
que es el mismo formato que deberá entregar la extracción de la parte 3.6.

Reglas que aplica.
- Ningún aviso se bota. Los de JUEZ PARTIDOR se guardan como 'descartado' (solo para el cuadre de cuentas).
- Un aviso con lista de mínimos genera un remate por cada elemento (aviso 30 del 14 de Octubre, 4 lotes).
- Cada remate visible queda unido a un bien. Si la causa trae un solo remate se une por causa. Si trae varios,
  por el número de depto, lote u oficina. La unión con publicaciones de otras ediciones se mide en la parte 4.
- El rol mal impreso lo detecta el código (prefijo con letras de más, o número y año pegados sin guion).
- Si un remate no trae fecha de vale vista, el código crea una alerta dato_faltante (pedido de Diego del 15 de Octubre).
"""
import hashlib, re, unicodedata

CORNISA = re.compile(r"1616\s+Remates\s+de\s+propiedades")


def normalizar(t: str | None) -> str:
    t = unicodedata.normalize("NFKD", t or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    t = re.sub(r"[°º.,;:()]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def clave_causa(rol: str, anio: str, tribunal: str) -> str:
    return f"{rol}-{anio}|{normalizar(tribunal)}"


_INMUEBLE = re.compile(r"\b(oficina|lote|departamento|depto|casa|local|bodega|estacionamiento|parcela|sitio)\s*(?:n\s*)?([0-9]+[a-z]?)\b")


def clave_inmueble(texto: str | None) -> str:
    """'oficina 602' da 'oficina 602'. 'Lote 1, casa 1 y estacionamiento 1' da 'lote 1'. Si no hay número, el texto normalizado."""
    t = normalizar(texto)
    m = _INMUEBLE.search(t)
    if not m:
        return t
    tipo = "depto" if m.group(1) == "departamento" else m.group(1)
    return f"{tipo} {m.group(2)}"


def rol_mal_impreso(impreso: str | None) -> str | None:
    """Devuelve el motivo si el rol impreso no tiene la forma letra-número-año, o None si está bien."""
    if not impreso:
        return None
    s = re.sub(r"^(?:rol|rit|expediente|n\s*[°º]|[:\s])+", "", impreso.strip(), flags=re.I)
    if re.match(r"[A-Za-z]{2,}\s*-", s):
        return f"Rol impreso con letras de más en el prefijo ({impreso})"
    if re.fullmatch(r"[A-Za-z]-?\s?\d{5,}", s.replace(".", "")) and re.search(r"(?:19|20)\d\d$", s):
        return f"Rol impreso con el número y el año pegados, sin guion ({impreso})"
    return None


def rol_sin_guion(impreso: str | None) -> str | None:
    """Detalle menor (decisión de Diego). La letra va pegada al número o separada por un espacio (C2461-2022, C 19087-2024)."""
    if not impreso or rol_mal_impreso(impreso):
        return None
    s = re.sub(r"^(?:rol|rit|expediente|n\s*[°º]|[:\s])+", "", impreso.strip(), flags=re.I)
    if re.match(r"[A-Za-z]\s?\d", s):
        return f"Sin guion en el rol ({impreso})"
    return None


def plataforma(cita: str | None) -> str | None:
    c = (cita or "").lower()
    if "meet" in c: return "Google Meet"
    if "vendaya" in c: return "vendaya.cl"
    if "zoom" in c: return "Zoom"
    return None


# Remates de partición (juez o jueza partidor, partidora o árbitro). Decisión de Diego. Se descartan del todo.
# Se busca al comienzo del aviso, sin importar mayúsculas (el diario escribe "Juez partidor", "JUEZ PARTIdor", "ANTE ARBITRO").
PARTICION = re.compile(r"\bJUEZA?\s+(?:[ÁA]RBITRO|PARTIDORA?)\b|\bANTE\s+(?:EL\s+|LA\s+)?[ÁA]RBITRO\b|\bPARTICI[OÓ]N\b|\bPARTICIONAL\b", re.I)


def es_partidor(tribunal: str | None, texto: str) -> bool:
    t = normalizar(tribunal)
    return t.startswith(("juez partidor", "jueza partidora", "juez arbitro", "jueza arbitro")) or bool(PARTICION.search(texto[:300]))


def _citas_de(ex: dict, sub_lista: dict):
    """Rinde (sub_orden, campo, n_cita, valor, cita). sub_lista dice a qué remate va el mínimo de cada elemento de la lista."""
    unico = not sub_lista            # aviso con un solo remate. Todo va al remate 1
    comun = 1 if unico else 0         # aviso con varios remates. Lo común va al aviso completo (0)
    for campo, clave in (("fecha_remate", "fecha_remate"), ("hora_remate", "hora_remate"), ("modalidad", "modalidad"), ("direccion", "direccion")):
        d = ex.get(clave) or {}
        if d.get("cita"):
            yield comun, campo, 1, d.get("valor"), d["cita"]
    m = ex.get("minimo") or {}
    for k, el in (sub_lista.items() if sub_lista else [(1, m)]):
        if el.get("cita"):
            yield k, "minimo_monto", 1, el.get("monto"), el["cita"]
        if el.get("cita_costas"):
            yield k, "minimo_costas_clp", 1, el.get("costas_clp"), el["cita_costas"]
    g = ex.get("garantia") or {}
    if g.get("cita"):
        campo = "garantia_porcentaje" if g.get("porcentaje") is not None else "garantia_monto" if g.get("monto") is not None else "garantia_base"
        valor = g.get("porcentaje") if g.get("porcentaje") is not None else g.get("monto")
        yield comun, campo, 1, valor, g["cita"]
    v = ex.get("vale_vista") or {}
    if v.get("cita"):
        yield comun, "vv_regla_texto", 1, v.get("regla"), v["cita"]
        for i, extra in enumerate(v.get("citas_extra") or [], start=2):
            yield comun, "vv_regla_texto", i, v.get("regla"), extra


VV_NO_LEIDO = "El programa todavía no lee la regla del vale vista de este aviso. Revísala en el aviso."
VV_NO_DICE = "El aviso no dice cuándo se entrega el vale vista. Debes averiguarlo en las bases o en el tribunal."


def guardar_edicion(con, edicion: dict, paginas: list[dict], avisos: list, extraido: dict, ahora: str,
                    clasificar_duda=None, metodo: str = "ia") -> dict:
    """Guarda una edición completa en una sola transacción. Si algo falla no queda nada a medias.
    edicion = {fecha, leida_en, estado, cuerpos_revisados, roles_en_texto}
    paginas = [{nombre 'B11', cuerpo, numero, id_pagina, texto, orden_rollo}]
    avisos  = avisos del cortador (motor.cortador.Aviso)
    extraido = {orden: datos del aviso en formato del banco nivel 2}
    clasificar_duda = función opcional que convierte cada texto de 'dudas' en un tipo de alerta (o None si no es alerta).
    metodo = 'ia' (banco anotado) o 'codigo' (motor\\procesar_edicion.py). Va a cada cita.
    Lo que entrega el motor trae además 'plataforma' y 'alertas' [(tipo, texto)] ya clasificadas por el código, y no trae
    'vale_vista' (lo leerá la parte 3.7). Sin esa clave la alerta dice que el programa no lo leyó, no que el aviso no lo dice."""
    fecha = edicion["fecha"]
    if con.execute("SELECT 1 FROM ediciones WHERE fecha = ?", (fecha,)).fetchone():
        raise ValueError(f"La edición {fecha} ya está en la base. No se cargó nada.")
    faltan = [a.orden for a in avisos if a.orden not in extraido]
    if faltan:
        raise ValueError(f"Faltan los datos extraídos de los avisos {faltan}. No se cargó nada.")
    with con:
        cur = con.execute("INSERT INTO ediciones(fecha, leida_en, estado, cuerpos_revisados, roles_en_texto, alarmas) VALUES (?,?,?,?,?,?)",
                          (fecha, edicion["leida_en"], edicion["estado"], edicion.get("cuerpos_revisados"), edicion.get("roles_en_texto"),
                           edicion.get("alarmas")))
        ed_id = cur.lastrowid
        id_pag = {}
        for p in paginas:
            ruta = f"/{fecha.replace('-', '/')}/{p['cuerpo']}/{p['id_pagina']}"
            cur = con.execute("INSERT INTO paginas(edicion_id, cuerpo, numero, id_pagina, ruta, orden_rollo, cornisas_1616, texto, sha256) "
                              "VALUES (?,?,?,?,?,?,?,?,?)",
                              (ed_id, p["cuerpo"], p["numero"], p["id_pagina"], ruta, p["orden_rollo"],
                               len(CORNISA.findall(p["texto"])), p["texto"], hashlib.sha256(p["texto"].encode("utf-8")).hexdigest()))
            id_pag[p["nombre"]] = cur.lastrowid

        remates_por_causa, pendientes_bien, n_remates = {}, [], 0
        for a in avisos:
            ex = extraido[a.orden]
            tribunal = ex.get("tribunal")
            causa_id = None
            # Una causa necesita rol Y tribunal (la base exige ambos). Si el código no encontró el tribunal (ej. trozo marcado
            # como dos avisos pegados, 2026-10-09 aviso 120) el aviso se guarda sin causa y con alerta, en vez de romper la carga.
            sin_tribunal = a.tipo_id != "SIN_ROL" and not tribunal
            if a.tipo_id != "SIN_ROL" and tribunal:
                clave = clave_causa(a.rol, a.anio, tribunal)
                con.execute("INSERT OR IGNORE INTO causas(clave, tipo_id, rol, anio, tribunal) VALUES (?,?,?,?,?)",
                            (clave, a.tipo_id, a.rol, a.anio, tribunal))
                causa_id = con.execute("SELECT id FROM causas WHERE clave = ?", (clave,)).fetchone()[0]
            descartado = es_partidor(tribunal, a.texto)
            cur = con.execute(
                "INSERT INTO avisos(edicion_id, causa_id, orden, pagina_inicio_id, pagina_fin_id, texto, rol_impreso, tipo_id, rol, anio, "
                "tribunal, filtro_estado, filtro_motivos) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (ed_id, causa_id, a.orden, id_pag[a.paginas[0]], id_pag[a.paginas[-1]], a.texto, a.rol_impreso, a.tipo_id, a.rol, a.anio,
                 tribunal, "descartado" if descartado else "pasa", "juez partidor" if descartado else None))
            aviso_id = cur.lastrowid
            if sin_tribunal:
                con.execute("INSERT INTO alertas(aviso_id, tipo, texto, origen) VALUES (?,?,?,?)",
                            (aviso_id, "revisar_lectura", f"El aviso tiene rol ({a.rol}-{a.anio}) pero no se encontró el tribunal. "
                             "No se pudo unir a su causa. Revisa el aviso en la página.", "codigo"))

            # Remates. Uno por elemento de la lista de mínimos, o uno solo.
            m = ex.get("minimo") or {}
            lista = m.get("lista") or [m]
            sub_lista = {k: el for k, el in enumerate(lista, start=1)} if m.get("lista") else {}
            g, v, mod = ex.get("garantia") or {}, ex.get("vale_vista") or {}, ex.get("modalidad") or {}
            for k, el in enumerate(lista, start=1):
                cur = con.execute(
                    "INSERT INTO remates(aviso_id, sub_orden, inmueble, direccion, fecha_remate, hora_remate, modalidad, plataforma, "
                    "minimo_monto, minimo_moneda, minimo_costas_clp, garantia_porcentaje, garantia_base, garantia_monto, garantia_moneda, "
                    "vv_regla, vv_regla_texto, vv_desde, vv_desde_origen, vv_hasta, vv_estado) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (aviso_id, k, el.get("inmueble"), (ex.get("direccion") or {}).get("valor"),
                     (ex.get("fecha_remate") or {}).get("valor"), (ex.get("hora_remate") or {}).get("valor"),
                     mod.get("valor"), ex["plataforma"] if "plataforma" in ex else plataforma(mod.get("cita")),
                     el.get("monto"), el.get("moneda"), el.get("costas_clp"),
                     g.get("porcentaje"), g.get("base") or "sin_dato", g.get("monto"), g.get("moneda"),
                     v.get("regla"), v.get("cita"), v.get("vv_desde"), v.get("vv_desde_origen"), v.get("vv_hasta"), v.get("vv_estado")))
                n_remates += 1
                if not v.get("vv_hasta"):
                    con.execute("INSERT INTO alertas(aviso_id, sub_orden, tipo, texto, origen) VALUES (?,?,?,?,?)",
                                (aviso_id, k if sub_lista else 0, "dato_faltante",
                                 VV_NO_DICE if "vale_vista" in ex else VV_NO_LEIDO, "codigo"))
                if not descartado:
                    pendientes_bien.append((cur.lastrowid, causa_id, aviso_id, k, el.get("inmueble"), tribunal, ex))
                    if causa_id:
                        remates_por_causa[causa_id] = remates_por_causa.get(causa_id, 0) + 1

            # Citas. El código comprueba que cada frase esté letra por letra en el texto del aviso.
            for sub, campo, n_cita, valor, cita in _citas_de(ex, sub_lista):
                con.execute("INSERT INTO citas(aviso_id, sub_orden, campo, n_cita, valor, cita, metodo, verificada) VALUES (?,?,?,?,?,?,?,?)",
                            (aviso_id, sub, campo, n_cita, None if valor is None else str(valor), cita, metodo, int(cita in a.texto)))

            # Alertas. Rol mal impreso por código. Las dudas, si hay con qué clasificarlas.
            motivo_rol = rol_mal_impreso(a.rol_impreso)
            if motivo_rol:
                con.execute("INSERT INTO alertas(aviso_id, tipo, texto, cita, origen) VALUES (?,?,?,?,?)",
                            (aviso_id, "rol_mal_impreso", motivo_rol, a.rol_impreso, "codigo"))
            elif rol_sin_guion(a.rol_impreso):
                con.execute("INSERT INTO alertas(aviso_id, tipo, texto, cita, origen) VALUES (?,?,?,?,?)",
                            (aviso_id, "detalle_menor", rol_sin_guion(a.rol_impreso), a.rol_impreso, "codigo"))
            for tipo, texto in ex.get("alertas") or []:          # alertas del código (motor). Ya traen su tipo
                con.execute("INSERT INTO alertas(aviso_id, tipo, texto, origen) VALUES (?,?,?,?)", (aviso_id, tipo, texto, "codigo"))
            for duda in (ex.get("dudas") or []) if clasificar_duda else []:
                tipo = clasificar_duda(duda)
                if tipo is None or (tipo == "rol_mal_impreso" and motivo_rol):
                    continue
                con.execute("INSERT INTO alertas(aviso_id, tipo, texto, origen) VALUES (?,?,?,?)", (aviso_id, tipo, duda, "ia"))

        # Bienes. Se arman al final porque la regla depende de cuántos remates trae cada causa en la edición.
        usadas = set()
        for remate_id, causa_id, aviso_id, k, inmueble, tribunal, ex in pendientes_bien:
            if causa_id:
                base = con.execute("SELECT clave FROM causas WHERE id = ?", (causa_id,)).fetchone()[0]
                varios = remates_por_causa[causa_id] > 1
                clave = f"{base}|{clave_inmueble(inmueble or (ex.get('direccion') or {}).get('valor'))}" if varios else base
            else:
                clave = f"sin_rol|{normalizar(tribunal)}|{normalizar((ex.get('direccion') or {}).get('valor'))}"
            if clave in usadas:   # dos remates de la misma edición que la regla no logra distinguir. No se adivina.
                con.execute("INSERT INTO alertas(aviso_id, sub_orden, tipo, texto, origen) VALUES (?,?,?,?,?)",
                            (aviso_id, k, "revisar_lectura", f"No se pudo distinguir este remate de otro de la misma causa ({clave})", "codigo"))
                clave = f"{clave}|{(ex.get('fecha_remate') or {}).get('valor')} {(ex.get('hora_remate') or {}).get('valor')}"
            usadas.add(clave)
            con.execute("INSERT OR IGNORE INTO bienes(causa_id, clave, inmueble, creado_en) VALUES (?,?,?,?)",
                        (causa_id, clave, inmueble, ahora))
            bien_id = con.execute("SELECT id FROM bienes WHERE clave = ?", (clave,)).fetchone()[0]
            con.execute("UPDATE remates SET bien_id = ? WHERE id = ?", (bien_id, remate_id))

        con.execute("UPDATE ediciones SET avisos_extraidos = ?, remates_extraidos = ? WHERE id = ?", (len(avisos), n_remates, ed_id))
    return {"edicion_id": ed_id, "avisos": len(avisos), "remates": n_remates}

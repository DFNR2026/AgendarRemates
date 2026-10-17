"""Parte 4 (17 de Octubre). Cuadre de cuentas de cada edición y cambios entre publicaciones de una misma propiedad.
Todo con código, sin IA. Decisiones de Diego del 17 de Octubre.

Cuadre.
- Cada rol que el código encuentra en el texto de la sección debe quedar dentro de algún aviso. Si no, la edición lleva
  una alarma "Cuadre. ...".
- Un aviso que imprime dos roles distintos (09-10 aviso 10, "Rol C-3673-2025" al comienzo y "Rol C-14254-2025" al final,
  con un solo remate) lleva una alerta de error de escritura del aviso. Es un error humano del secretario, no lo normal.

Cambios entre publicaciones.
- Cada remate se compara con la publicación anterior de la misma propiedad (mismo bien, edición anterior).
- Solo cuenta un cambio de un valor a OTRO valor. De vacío a valor es un dato que se completa y no se anota. De valor a
  vacío tampoco (casi siempre es un dato que la IA todavía no leyó ese día).
- La fecha estimada del "desde" del vale vista (día siguiente a la edición) cambia sola cada día y no se compara.
- Si el mismo texto de un aviso de otro día quedó en otra propiedad, el aviso nuevo lleva la alerta posible_republicacion.
"""
import re
from motor.cortador import roles_en
from motor.numeros_texto import palabras_a_cifras
from motor.direccion import norm
from motor.extraccion import clave_caratula

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
CUADRE_ALARMA = "Cuadre. "


def fecha_legible(f: str) -> str:
    """'2026-10-09' da '9 de Octubre de 2026'. Los meses nunca en número (pedido de Diego del 15 de Octubre)."""
    a, m, d = f[:10].split("-")
    return f"{int(d)} de {MESES[int(m) - 1]} de {a}"


def huella(texto: str) -> str:
    return re.sub(r"[\W_]+", "", (texto or "").lower())


# --- Cuadre ----------------------------------------------------------------------------------------------------
def roles_del_aviso(texto: str) -> list:
    """Roles distintos que imprime el aviso, en orden, como (numero, anio, impreso)."""
    vistos, out = set(), []
    for r in roles_en(texto):
        if (r[1], r[2]) not in vistos:
            vistos.add((r[1], r[2])); out.append((r[1], r[2], r[4].strip()))
    return out


def alertas_cuadre(avisos: list, extraido: dict) -> dict:
    """{orden: [(tipo, texto)]} para los avisos que imprimen dos roles distintos. Los marcados como pegados ya llevan su
    propia alerta (dos avisos en un trozo) y no se repiten."""
    out = {}
    for a in avisos:
        rs = roles_del_aviso(a.texto)
        if len(rs) > 1 and not (extraido.get(a.orden) or {}).get("pegado"):
            out.setdefault(a.orden, []).append(("error_escritura",
                f"El aviso imprime {len(rs)} roles distintos ({' y '.join(r[2] for r in rs)}). Es un error de escritura del aviso. "
                "Confirma en el tribunal cuál es el correcto antes de ir."))
    return out


def alarma_cuadre(roles_texto: set, avisos: list) -> str | None:
    """Roles del texto de la sección que no quedaron dentro de ningún aviso (texto que se perdió al cortar)."""
    dentro = set()
    for a in avisos:
        dentro |= {(r[0], r[1]) for r in roles_del_aviso(a.texto)}
    faltan = sorted(roles_texto - dentro)
    if not faltan:
        return None
    return (f"{CUADRE_ALARMA}{len(faltan)} rol{'es' if len(faltan) > 1 else ''} del texto no quedaron dentro de ningún aviso "
            f"({', '.join(f'{n}-{a}' for n, a in faltan[:5])}). Revisa la página.")


# --- Cambios entre publicaciones ------------------------------------------------------------------------------
# (campo, etiqueta legible, función de comparación). Se compara solo si los dos valores existen.
_N = lambda v: None if v in (None, "", "sin_dato") else v
CAMPOS = [
    ("fecha_remate", "la fecha del remate", lambda v: v),
    ("hora_remate", "la hora del remate", lambda v: v),
    ("modalidad", "la modalidad", lambda v: v),
    ("minimo", "el mínimo", lambda v: v),
    ("garantia_porcentaje", "el porcentaje de la garantía", lambda v: v),
    ("garantia_base", "la base de la garantía", lambda v: v),
    ("garantia_monto", "el monto de la garantía", lambda v: v),
    ("vv_desde", "el desde del vale vista", lambda v: v),
    ("vv_hasta", "el plazo del vale vista", lambda v: v),
    ("direccion", "la dirección", lambda v: norm(palabras_a_cifras(v))),
    ("comuna", "la comuna", lambda v: norm(v)),
    ("caratula", "la carátula", lambda v: clave_caratula(v)),
]
_Q = ("SELECT r.id, r.bien_id, e.fecha, r.fecha_remate, r.hora_remate, r.modalidad, "
      "CASE WHEN r.minimo_monto IS NULL THEN NULL ELSE r.minimo_monto || ' ' || COALESCE(r.minimo_moneda, '') END, "
      "r.garantia_porcentaje, r.garantia_base, r.garantia_monto, "
      "CASE WHEN r.vv_desde_origen = 'texto' THEN r.vv_desde END, r.vv_hasta, r.direccion, r.comuna, "
      "(SELECT c.valor FROM citas c WHERE c.aviso_id = a.id AND c.campo = 'caratulado' LIMIT 1), a.id, a.texto "
      "FROM remates r JOIN avisos a ON a.id = r.aviso_id JOIN ediciones e ON e.id = a.edicion_id "
      "WHERE a.filtro_estado <> 'descartado' AND r.bien_id IS NOT NULL ")


def _legible(campo, v):
    if v is None:
        return "vacío"
    if campo in ("fecha_remate",) or (campo in ("vv_desde", "vv_hasta") and re.match(r"\d{4}-\d\d-\d\d", str(v))):
        s = str(v)
        return fecha_legible(s) + (f" a las {s[11:16]}" if len(s) > 10 else "")
    return str(v)


def registrar_cambios(con, fecha: str, ahora: str) -> dict:
    """Compara cada remate visible de la edición con la publicación anterior de su mismo bien y guarda en cambios lo que
    pasó de un valor a otro valor. También revisa la edición siguiente, si ya estaba cargada (una edición vieja cargada
    después). Rehace lo de esas ediciones, así se puede correr de nuevo (por ejemplo después de retomar)."""
    sig = con.execute("SELECT MIN(fecha) FROM ediciones WHERE fecha > ?", (fecha,)).fetchone()[0]
    res = {"comparados": 0, "cambios": 0, "por_campo": {}, "posibles_republicaciones": 0}
    with con:
        for f in [x for x in (fecha, sig) if x]:
            nuevos = con.execute(_Q + "AND e.fecha = ?", (f,)).fetchall()
            ids = [x[0] for x in nuevos]
            if ids:
                con.execute(f"DELETE FROM cambios WHERE remate_nuevo IN ({','.join('?' * len(ids))})", ids)
            for n in nuevos:
                ant = con.execute(_Q + "AND r.bien_id = ? AND e.fecha < ? ORDER BY e.fecha DESC, r.id DESC LIMIT 1", (n[1], f)).fetchone()
                if not ant:
                    continue
                res["comparados"] += 1
                for i, (campo, _, clave) in enumerate(CAMPOS, start=3):
                    va, vn = _N(ant[i]), _N(n[i])
                    if va is None or vn is None or clave(va) == clave(vn):
                        continue
                    con.execute("INSERT INTO cambios(bien_id, remate_anterior, remate_nuevo, campo, valor_anterior, valor_nuevo, detectado_en) "
                                "VALUES (?,?,?,?,?,?,?)", (n[1], ant[0], n[0], campo, str(va), str(vn), ahora))
                    res["cambios"] += 1; res["por_campo"][campo] = res["por_campo"].get(campo, 0) + 1
            # Posible republicación. El mismo texto (solo letras y números) de otro día quedó en otra propiedad.
            avisos_f = con.execute("SELECT a.id, a.texto, GROUP_CONCAT(r.bien_id) FROM avisos a JOIN ediciones e ON e.id = a.edicion_id "
                                   "JOIN remates r ON r.aviso_id = a.id WHERE e.fecha = ? AND a.filtro_estado <> 'descartado' GROUP BY a.id", (f,)).fetchall()
            con.execute("DELETE FROM alertas WHERE tipo = 'posible_republicacion' AND origen = 'codigo' AND aviso_id IN "
                        "(SELECT a.id FROM avisos a JOIN ediciones e ON e.id = a.edicion_id WHERE e.fecha = ?)", (f,))
            previas = {}                      # huella -> (fecha, bienes) de la publicación anterior más reciente con ese texto
            for f2, bienes2, texto2 in con.execute(
                    "SELECT e.fecha, GROUP_CONCAT(r.bien_id), a.texto FROM avisos a JOIN ediciones e ON e.id = a.edicion_id "
                    "JOIN remates r ON r.aviso_id = a.id WHERE e.fecha < ? AND a.filtro_estado <> 'descartado' GROUP BY a.id "
                    "ORDER BY e.fecha", (f,)):
                previas[huella(texto2)] = (f2, bienes2)
            for aviso_id, texto, bienes in avisos_f:
                p = previas.get(huella(texto))
                if p and sorted(bienes.split(",")) != sorted(p[1].split(",")):
                    con.execute("INSERT INTO alertas(aviso_id, sub_orden, tipo, texto, origen) VALUES (?,?,?,?,?)",
                                (aviso_id, 0, "posible_republicacion",
                                 f"El mismo aviso salió el {fecha_legible(p[0])} y quedó como otra propiedad. Revisa si es la misma.", "codigo"))
                    res["posibles_republicaciones"] += 1
    return res


def texto_cambio(campo: str, anterior, nuevo, fecha_anterior: str) -> str:
    """Cómo se le muestra un cambio a Diego. Ejemplo. 'Cambió la fecha del remate respecto de la publicación del 6 de
    Octubre de 2026. Antes 20 de Octubre de 2025, ahora 20 de Octubre de 2026.'"""
    etiqueta = dict((c, e) for c, e, _ in CAMPOS).get(campo, campo)
    return (f"Cambió {etiqueta} respecto de la publicación del {fecha_legible(fecha_anterior)}. "
            f"Antes {_legible(campo, anterior)}, ahora {_legible(campo, nuevo)}.")

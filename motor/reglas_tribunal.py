"""Reglas propias de un tribunal, dichas por quien redacta sus avisos (decisiones de Diego).

24° Juzgado Civil de Santiago (Diego, 6 de Noviembre de 2026). La secretaria del tribunal, que es quien redacta los avisos
del Mercurio, le dijo a Diego que el vale vista se entrega en el mismo momento del remate y que los remates son siempre
presenciales. Siempre se contrasta con el aviso.
  Si el aviso no dice nada, vale la regla de la secretaria.
  Si el aviso dice otra cosa, se deja lo del aviso y se alerta.
  Si la lectura del aviso falló (rojo), se pone la fecha de la secretaria en ámbar, avisando que hay que revisar el aviso.
11° Juzgado Civil de Santiago (Diego, 6 de Noviembre de 2026). El secretario confirmó que el vale vista es nominativo a la orden
del tribunal, que se entrega el mismo día del remate y que se lleva fotocopia de la cédula por ambos lados. Diego decidió que, si
el aviso no dice cuándo, va en el mismo remate como en el 24°. Sus avisos dicen "al momento de efectuarse el llamado a remate".
Nada de esto cambia la lectura de los demás tribunales."""
from motor.vale_vista import NO_ENCONTRADA

TRIB_24 = "24° Juzgado Civil de Santiago"
TRIB_11 = "11° Juzgado Civil de Santiago"
VV_SECRETARIA = ("Regla de la secretaria del 24° Civil. El vale vista se entrega en el mismo remate, porque el aviso no dice "
                 "cuándo se entrega.")
VV_SECRETARIA_ROJO = ("No se pudo leer la regla del vale vista del aviso. Se usa la regla de la secretaria del 24° Civil, que dice "
                      "que se entrega en el mismo remate. Revisa que el aviso no diga otra cosa.")
VV_SECRETARIA_CONTRA = ("El aviso da otra fecha para el vale vista, pero la secretaria del 24° Civil dijo que se entrega en el "
                        "mismo remate. Confirma en el tribunal.")
MOD_SECRETARIA = ("El aviso no dice si el remate es por Zoom o presencial. La secretaria del 24° Civil dijo que sus remates "
                  "son siempre presenciales.")
MOD_SECRETARIA_CONTRA = ("El aviso dice que el remate es {}, pero la secretaria del 24° Civil dijo que sus remates son siempre "
                         "presenciales. Confirma en el tribunal.")
MOD_SIN_DATO = "El aviso no dice si el remate es por Zoom o presencial."
_MOD_TXT = {"zoom": "por Zoom", "en_linea": "en línea", "mixta": "presencial y también en línea"}


def es_24(tribunal) -> bool:
    return (tribunal or "").strip() == TRIB_24


# Textos por tribunal para la regla del vale vista. El 24° es la secretaria y el 11° el secretario.
_QUIEN = {TRIB_24: ("la secretaria", "de la secretaria"), TRIB_11: ("el secretario", "del secretario")}
_NUM = {TRIB_24: "24°", TRIB_11: "11°"}


def textos_vv(tribunal):
    (q, de), n = _QUIEN[tribunal], _NUM[tribunal]
    return (f"Regla {de} del {n} Civil. El vale vista se entrega en el mismo remate, porque el aviso no dice cuándo se entrega.",
            f"No se pudo leer la regla del vale vista del aviso. Se usa la regla {de} del {n} Civil, que dice que se entrega en el "
            "mismo remate. Revisa que el aviso no diga otra cosa.",
            f"El aviso da otra fecha para el vale vista, pero {q} del {n} Civil dijo que se entrega en el mismo remate. Confirma en el tribunal.")


def tiene_regla_vv(tribunal) -> bool:
    return (tribunal or "").strip() in _QUIEN


def vale_vista_secretaria(b: dict, fecha_remate, hora_remate, tribunal) -> dict:
    """Igual que vale_vista_24 para cualquier tribunal con regla confirmada (24° y 11°)."""
    t = (tribunal or "").strip()
    if t not in _QUIEN:
        return b
    return _vale_vista(b, fecha_remate, hora_remate, *textos_vv(t))


def vale_vista_24(b: dict, fecha_remate, hora_remate) -> dict:
    return _vale_vista(b, fecha_remate, hora_remate, VV_SECRETARIA, VV_SECRETARIA_ROJO, VV_SECRETARIA_CONTRA)


def _vale_vista(b: dict, fecha_remate, hora_remate, VV_SECRETARIA, VV_SECRETARIA_ROJO, VV_SECRETARIA_CONTRA) -> dict:
    """Bloque vale_vista de motor.procesar_edicion.bloque_vale_vista -> bloque con la regla de la secretaria aplicada.
    Sin fecha del remate no se puede poner la entrega, y el bloque queda igual."""
    if not fecha_remate:
        return b
    x = f"{fecha_remate} {hora_remate}" if hora_remate else fecha_remate
    color = b.get("color")
    if color == "sin_dato":
        al = [a for a in b["alertas"] if a[1] != NO_ENCONTRADA] + [("condicion_especial", VV_SECRETARIA, None)]
        return {**b, "regla": "en_el_remate", "cita": None, "citas_extra": [], "vv_desde": x, "vv_desde_origen": None,
                "vv_hasta": x, "vv_estado": "calculado", "color": "verde", "alertas": al}
    if color == "rojo":
        al = [a for a in b["alertas"] if a[0] != "revisar_lectura"] + [("condicion_especial", VV_SECRETARIA_ROJO, b.get("cita"))]
        return {**b, "regla": "en_el_remate", "vv_desde": x, "vv_desde_origen": None, "vv_hasta": x, "vv_estado": "revisar",
                "color": "ambar", "alertas": al}
    if b.get("regla") != "en_el_remate":                       # verde o ámbar con otra regla. Manda el aviso, se alerta
        return {**b, "alertas": b["alertas"] + [("contradiccion", VV_SECRETARIA_CONTRA, b.get("cita"))]}
    return b                                                   # el aviso dice lo mismo que la secretaria


def modalidad_24(ex: dict) -> dict:
    """Datos traducidos de un aviso (motor.procesar_edicion.traducir) -> con la modalidad de la secretaria aplicada."""
    v = (ex.get("modalidad") or {}).get("valor")
    if v == "sin_dato":
        al = [a for a in ex["alertas"] if a[1] != MOD_SIN_DATO] + [("condicion_especial", MOD_SECRETARIA)]
        return {**ex, "modalidad": {"valor": "presencial", "cita": None}, "alertas": al}
    if v in _MOD_TXT:
        return {**ex, "alertas": ex["alertas"] + [("contradiccion", MOD_SECRETARIA_CONTRA.format(_MOD_TXT[v]))]}
    return ex

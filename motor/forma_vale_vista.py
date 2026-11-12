"""Forma del vale vista y cómo llenarlo (pedido de Diego, 6 de Noviembre de 2026). Solo código, sin IA.
Formas que piden los tribunales (Diego).
  a) nominativo, a la orden del tribunal (el 11° Civil lo confirmó con su secretario)
  b) endosable, a la orden del tribunal
  c) endosable, a la orden del postor (poco común. En 467 causas medidas el 6 de Noviembre solo el 14° Civil, "vale vista tomado a
     propia orden, susceptible de ser endosado al momento de la subasta")
  Además el 30° Civil escribe "nominativo o endosable", o sea sirve cualquiera de los dos (decisión de Diego).
El vale vista se llena con el tribunal escrito en palabras, el RUT del tribunal (db\\tribunales_santiago.csv), el monto y si es
nominativo o endosable. La forma se lee del texto del aviso y se muestra con la frase que la dice. Si el aviso no lo dice, queda
sin dato, salvo en el 11° Civil, donde vale lo que dijo el secretario."""
import csv, re
from pathlib import Path

_CSV = Path(__file__).resolve().parent.parent / "db" / "tribunales_santiago.csv"
TRIB_11 = "11° Juzgado Civil de Santiago"
TRIB_2 = "2° Juzgado Civil de Santiago"
# 12 de Noviembre (Diego). Devolución del vale vista. No suele venir en el aviso, se sabe preguntando en el tribunal o leyendo las
# bases. En un remate por videoconferencia el vale vista no se devuelve al terminar, hay que ir a retirarlo.
# desde "habil_siguiente" es el día hábil siguiente al remate (puesto por Claude, Diego dijo "día posterior al remate en adelante").
DEVOLUCION = {TRIB_2: {"desde": "habil_siguiente", "horario": ("12:00", "14:00"), "fuente": "regla del 2° Civil que trajo Diego"}}
SECRETARIO_11_LLEVAR = "Fotocopia de la cédula de identidad por ambos lados (secretario del 11° Civil)."
TIPO_TXT = {"nominativo": "Nominativo", "endosable": "Endosable", "nominativo_o_endosable": "Nominativo o endosable, sirve cualquiera"}
ORDEN_TXT = {"tribunal": "A la orden del tribunal", "postor": "A la orden del postor"}

_FIN_ORACION = re.compile(r"\.\s+")          # un punto seguido de espacio. Así no corta "$66.762.980" ni "60.306.001-6"
_AMBOS = re.compile(r"nominativ\w*\s+(?:o|y/o)\s+endosable|endosable\s+(?:o|y/o)\s+nominativ\w*", re.I)
_NOMI = re.compile(r"nominativ\w*|no\s+endosable", re.I)
_ENDO = re.compile(r"(?<!no )endosable|susceptible\s+de\s+ser\s+endosad[oa]", re.I)     # el 14° Civil escribe "susceptible de ser endosado"
_POSTOR = re.compile(r"(?:a\s+la\s+)?orden\s+(?:del?\s+)?(?:propio\s+)?(?:postor|tomador|oferente|interesado)|a\s+(?:su\s+)?propia\s+orden", re.I)   # 14° Civil, "a propia orden"
# Los avisos escriben "a la orden del tribunal", "orden Tribunal", "a nombre del Primer Juzgado", "a nombre Décimo Tercer Juzgado",
# "nominativo al 11° Juzgado" o "nominativo a nombre de ‘11° Juzgado’". Entre medio caben hasta tres palabras (el número del
# juzgado), nunca "llegada" (orden de llegada).
_ENTRE = r"(?:del?\s+|de\s+este\s+)?(?:(?!llegada)\S+\s+){0,3}?"
_TRIB = re.compile(r"(?:a\s+la\s+)?orden\s+" + _ENTRE + r"(?:tribunal|juzgado)|a\s+nombre\s+" + _ENTRE + r"(?:tribunal|juzgado)"
                   r"|nominativ\w*\s+(?:a\s+nombre\s+de\s+\W?|al\s+)" + _ENTRE + r"(?:tribunal|juzgado)", re.I)


def _tabla():
    try:
        with open(_CSV, encoding="utf-8", newline="") as f:
            return {r["tribunal"]: r for r in csv.DictReader(f)}
    except OSError:
        return {}


TABLA = _tabla()


def leer(texto: str | None) -> dict:
    """{'tipo': nominativo | endosable | nominativo_o_endosable | None, 'orden': tribunal | postor | None, 'cita': frase o None}.
    La cita es la oración del aviso que lo dice, tal como está."""
    out = {"tipo": None, "orden": None, "cita": None}
    for o in _FIN_ORACION.split(texto or ""):
        o = o.strip()
        if not re.search(r"vale\s*vista", o, re.I):
            continue
        tipo = "nominativo_o_endosable" if _AMBOS.search(o) else "nominativo" if _NOMI.search(o) else "endosable" if _ENDO.search(o) else None
        orden = "postor" if _POSTOR.search(o) else "tribunal" if _TRIB.search(o) else None
        if tipo and not out["tipo"]:
            out["tipo"], out["cita"] = tipo, o
        if orden and not out["orden"]:
            out["orden"] = orden
            out["cita"] = out["cita"] or o
        if out["tipo"] and out["orden"]:
            break
    return out


def como_llenar(tribunal: str | None, texto: str | None) -> dict:
    """Lo que la ficha muestra para llenar el vale vista. Sin texto (causa a mano) solo usa la tabla y la regla del 11°."""
    t = (tribunal or "").strip()
    f = leer(texto)
    fila = TABLA.get(t) or {}
    alertas = []
    tipo, orden, de_regla = f["tipo"], f["orden"], False
    if t == TRIB_11:
        if tipo in ("endosable",):
            alertas.append("El aviso dice endosable, pero el secretario del 11° Civil dijo nominativo. Confirma en el tribunal.")
        elif not tipo:
            tipo, de_regla = "nominativo", True
        orden = orden or "tribunal"
    elif t == TRIB_2:          # 12 de Noviembre (Diego). En el 2° Civil el vale vista es siempre endosable. Ninguno de sus 49 avisos lo dice.
        if tipo == "nominativo":
            alertas.append("El aviso dice nominativo, pero en el 2° Civil el vale vista es siempre endosable. Confirma en el tribunal.")
        elif not tipo:
            tipo, de_regla = "endosable", True
    nada = "El aviso no lo dice" if texto is not None else "Sin dato, la causa se agregó a mano"
    tipo_txt = TIPO_TXT.get(tipo, nada)
    if de_regla:
        tipo_txt += " (lo dijo el secretario del 11° Civil)" if t == TRIB_11 else " (siempre endosable en el 2° Civil, el aviso no lo dice)"
    return {"a_nombre_de": fila.get("en_palabras") or (t or "Sin tribunal"),
            "rut": fila.get("rut") or "Sin RUT en la tabla de tribunales",
            "tipo": tipo, "tipo_txt": tipo_txt,
            "orden_txt": ORDEN_TXT.get(orden, nada),
            "cita": f["cita"], "llevar": SECRETARIO_11_LLEVAR if t == TRIB_11 else None, "alertas": alertas,
            "devolucion": DEVOLUCION.get(t)}

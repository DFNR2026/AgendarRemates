"""Mide la extracción por código contra un banco (parte 3.6). No es una prueba de TODO OK, es una medición.
Uso. python -m pruebas.medir_extraccion 14        (banco nivel 2 del 14 de Octubre, para AJUSTAR)
     python -m pruebas.medir_extraccion 06        (banco de validación del 6 de Octubre, solo al FINAL)
Cuenta por dato. acierto, vacío (el código no dio valor) y EQUIVOCADO (dio un valor distinto). Meta, 0 equivocados.
"""
import json, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.cortador import construir_rollo, cortar
from motor.orden_columnas import leer_pagina
from motor.extraccion import extraer
from db.carga import es_partidor, normalizar

BANCOS = {"14": ("2026-10-14", ("B11", "C8"), "banco_nivel2_2026-10-14.json"),
          "06": ("2026-10-06", ("B7", "B8", "B9", "B10"), "banco_validacion_2026-10-06.json")}
cual = sys.argv[1] if len(sys.argv) > 1 else "14"
fecha, pags, archivo = BANCOS[cual]
D = RAIZ / "banco_pruebas" / fecha
r, m = construir_rollo([(n, leer_pagina(D / f"mercurio_{fecha}_{n}.txt")) for n in pags])
av = {a.orden: a for a in cortar(r, m)}
banco = json.loads((D / archivo).read_text(encoding="utf-8"))["avisos"]

def _resumen_minimo(m):
    """Forma comparable del mínimo. Lista de (monto, moneda, costas) o None si no hay monto."""
    if not m: return None
    els = m.get("lista") or [m]
    if all(e.get("monto") is None for e in els): return None
    return [(round(e["monto"], 6), e.get("moneda"), e.get("costas_clp")) for e in els]

cuenta = {c: {"acierto": 0, "vacio": 0, "equivocado": 0} for c in ("fecha_remate", "hora_remate", "minimo", "garantia", "modalidad", "tribunal")}
detalle = []
no_anotados = 0
for e in banco:
    todo = extraer(av[e["n"]].texto, fecha)
    x = {"fecha_remate": todo["fecha_remate"], "hora_remate": todo["hora_remate"], "alertas": todo["alertas"]}
    mc = {"minimo": todo["minimo"], "alertas": []}
    x["minimo"] = {"valor": _resumen_minimo(mc["minimo"]), "cita": mc["minimo"].get("cita")}
    x["alertas"] = x["alertas"] + mc["alertas"]
    e = dict(e, minimo={"valor": _resumen_minimo(e["minimo"])})
    gc = {"garantia": todo["garantia"], "alertas": []}
    gx = gc["garantia"]
    x["garantia"] = {"valor": (gx["porcentaje"], gx["base"], gx["monto"]), "cita": gx["cita"]}
    x["alertas"] = x["alertas"] + gc["alertas"]
    ge = e["garantia"]
    ve = (ge.get("porcentaje"), ge.get("base") or "sin_dato", ge.get("monto"))
    if "base_origen" in ge: ve = ve + (ge["base_origen"],); x["garantia"]["valor"] = x["garantia"]["valor"] + (gx["base_origen"],)
    if ve == (None, "sin_dato", None) or ve == (None, "sin_dato", None, None): ve = None
    if x["garantia"]["valor"][:3] == (None, "sin_dato", None): x["garantia"]["valor"] = None
    e = dict(e, garantia={"valor": ve})
    mo = {"modalidad": todo["modalidad"], "alertas": []}
    x["modalidad"] = {"valor": None if mo["modalidad"]["valor"] == "sin_dato" else mo["modalidad"]["valor"], "cita": mo["modalidad"]["cita"]}
    x["alertas"] = x["alertas"] + mo["alertas"]
    me = e["modalidad"]["valor"]
    e = dict(e, modalidad={"valor": None if me in (None, "sin_dato") else me})
    tr = todo["tribunal"]
    # el tribunal se compara sin mayúsculas ni tildes. Los partidores (descartados) no se miden
    x["tribunal"] = {"valor": normalizar(tr["valor"]) if tr["valor"] else None, "cita": tr["cita"]}
    e = dict(e, tribunal={"valor": normalizar(e["tribunal"]) if e.get("tribunal") else None})
    if es_partidor(None, av[e["n"]].texto):
        x["tribunal"]["valor"] = e["tribunal"]["valor"]
    for c in cuenta:
        if c == "garantia" and ge.get("no_anotado"):
            no_anotados += 1           # partes de un aviso pegado sin garantía anotada antes del código (parte 3.6b). No se cuentan
            continue
        esperado, obtenido = e[c]["valor"], x[c]["valor"]
        if obtenido is None:
            k = "acierto" if esperado is None else "vacio"
        else:
            k = "acierto" if obtenido == esperado else "equivocado"
        cuenta[c][k] += 1
        if k != "acierto":
            detalle.append(f"{k.upper():10} {c:12} aviso {e['n']:3} esperado {esperado} obtenido {obtenido} | {x[c]['cita']} | {[a[1] for a in x['alertas']]}")
print(f"Banco {fecha}, {len(banco)} avisos")
for c, v in cuenta.items():
    print(f"{c:12} aciertos {v['acierto']:3} | vacíos {v['vacio']:3} | EQUIVOCADOS {v['equivocado']:3}")
if no_anotados: print(f"garantía no anotada (no se cuenta) en {no_anotados} avisos")
print("\n".join(detalle))

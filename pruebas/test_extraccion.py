"""Prueba de la extracción por código (parte 3.6) contra el banco del 14 de Octubre, que es el banco de AJUSTE.
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_extraccion
Falla si algún dato sale EQUIVOCADO o si los aciertos bajan del mínimo logrado. El banco de validación (6 de Octubre)
no se usa aquí. Se mide aparte con pruebas.medir_extraccion 06, solo al final.
"""
import json, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.cortador import construir_rollo, cortar
from motor.orden_columnas import leer_pagina
from motor.extraccion import extraer
from db.carga import es_partidor, normalizar

MINIMOS = {"fecha_remate": 60, "hora_remate": 60, "minimo": 61, "garantia": 61, "modalidad": 59, "tribunal": 61}   # logrados el 2026-10-15 (etapas 1 a 5). Tribunal sin contar partidores, que se descartan. Solo pueden subir.


def _resumen_minimo(m):
    els = m.get("lista") or [m]
    if all(e.get("monto") is None for e in els): return None
    return [(round(e["monto"], 6), e.get("moneda"), e.get("costas_clp")) for e in els]

D = RAIZ / "banco_pruebas" / "2026-10-14"
r, m = construir_rollo([(n, leer_pagina(D / f"mercurio_2026-10-14_{n}.txt")) for n in ("B11", "C8")])
av = {a.orden: a for a in cortar(r, m)}
banco = json.loads((D / "banco_nivel2_2026-10-14.json").read_text(encoding="utf-8"))["avisos"]

fallas, aciertos = [], {c: 0 for c in MINIMOS}
for e in banco:
    todo = extraer(av[e["n"]].texto, "2026-10-14")
    x = {"fecha_remate": todo["fecha_remate"], "hora_remate": todo["hora_remate"], "alertas": todo["alertas"]}
    mc = {"minimo": todo["minimo"], "alertas": []}
    x["minimo"] = {"valor": _resumen_minimo(mc["minimo"]), "cita": (mc["minimo"].get("lista") or [mc["minimo"]])[0].get("cita")}
    e = dict(e, minimo={"valor": _resumen_minimo(e["minimo"])})
    gx = todo["garantia"]
    x["garantia"] = {"valor": (gx["porcentaje"], gx["base"], gx["monto"]), "cita": gx["cita"]}
    ge = e["garantia"]
    e = dict(e, garantia={"valor": (ge.get("porcentaje"), ge.get("base") or "sin_dato", ge.get("monto"))})
    mo = todo["modalidad"]
    x["modalidad"] = {"valor": None if mo["valor"] == "sin_dato" else mo["valor"], "cita": mo["cita"]}
    e = dict(e, modalidad={"valor": None if e["modalidad"]["valor"] in (None, "sin_dato") else e["modalidad"]["valor"]})
    tr = todo["tribunal"]
    x["tribunal"] = {"valor": normalizar(tr["valor"]) if tr["valor"] else None, "cita": tr["cita"]}
    e = dict(e, tribunal={"valor": normalizar(e["tribunal"])})
    if es_partidor(None, av[e["n"]].texto):
        x["tribunal"]["valor"] = e["tribunal"]["valor"]
    for c in MINIMOS:
        esperado, obtenido = e[c]["valor"], x[c]["valor"]
        if obtenido is not None and obtenido != esperado:
            fallas.append(f"EQUIVOCADO {c} aviso {e['n']} esperado {esperado} obtenido {obtenido}")
        if obtenido == esperado:
            aciertos[c] += 1
        if obtenido is not None and x[c]["cita"] is not None and x[c]["cita"] not in av[e["n"]].texto:
            fallas.append(f"cita que no está en el aviso {c} aviso {e['n']}")
# Casos fijos de tribunal, tomados de textos reales de otras ediciones (cada uno motivó una regla)
CASOS_TRIBUNAL = {
    "EN AUTOS ROL C-2237-2025, del 2° Juzgado de Letras Civil de Chillán, caratulados": "2° Juzgado Civil de Chillán",
    "7° JUZGADO CIVIL, EN calle Huérfanos 1409, piso 2, Santiago, se rematará": "7° Juzgado Civil de Santiago",
    "EXTRACTO 17° JUZGADO DE LEtras de Santiago. Causa hipotecaria": "17° Juzgado Civil de Santiago",
    "EXTRACTO JUZGADO DE LETRAS de Cobranza Laboral de Temuco. Rit C-357- 2024.": "Juzgado de Cobranza Laboral de Temuco",
    "REMATE ANTE EL JUZgado de Letras del Trabajo de San Bernardo, Urmeneta 467": "Juzgado de Letras del Trabajo de San Bernardo",
    "REMATE ANTE DÉCIMO QUINTO (15°) JUZGADO CIVIL DE SANTIAGO, Huérfanos": "15° Juzgado Civil de Santiago",
    "VIGÉSIMO CUARTO JUZgado Civil de Santiago, Huérfanos 1409": "24° Juzgado Civil de Santiago",
    "REMATE 1° JUZGADO CIVIL DE SAN Miguel, Ureta Cox 855": "1° Juzgado Civil de San Miguel",
}
for texto, esperado in CASOS_TRIBUNAL.items():
    obtenido = extraer(texto)["tribunal"]["valor"]
    if obtenido != esperado:
        fallas.append(f"tribunal fijo. '{texto[:40]}' dio {obtenido} y debía dar {esperado}")
print(f"casos fijos de tribunal {len(CASOS_TRIBUNAL)}")
for c, n in aciertos.items():
    print(f"{c:12} aciertos {n} de {len(banco)} (mínimo {MINIMOS[c]})")
    if n < MINIMOS[c]: fallas.append(f"{c} bajó a {n} aciertos")
for f in fallas: print("FALLA", f)
print("\nRESULTADO.", "TODO OK" if not fallas else f"{len(fallas)} fallas")
sys.exit(1 if fallas else 0)

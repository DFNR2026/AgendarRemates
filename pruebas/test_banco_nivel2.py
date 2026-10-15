"""Revisa el banco nivel 2 (banco_pruebas/2026-10-14/banco_nivel2_2026-10-14.json). Solo código, sin IA.
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_banco_nivel2  (agrega -v para ver el detalle)

Qué comprueba.
1. Que cada frase citada exista letra por letra en el texto de su aviso (el texto lo arma el cortador
   desde las páginas del banco, con orden por posición). El número n de cada remate es su número de aviso en el cortador.
2. Que cada remate tenga fecha y hora válidas, y modalidad dentro de los valores permitidos.
3. Que la fecha del vale vista calce con su regla, recalculada desde la fecha del remate y db/feriados_2026.csv.
   Los remates en estado revisar o sin_dato no se recalculan (son estimaciones a la espera del abogado).
"""
import csv, json, sys, datetime as dt
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.cortador import construir_rollo, cortar
from motor.orden_columnas import leer_pagina

B = RAIZ / "banco_pruebas" / "2026-10-14"
VERBOSO = "-v" in sys.argv
MODALIDADES = {"zoom", "presencial", "mixta", "sin_dato", "en_linea"}
FER = {r["fecha"] for r in csv.DictReader(open(RAIZ / "db" / "feriados_2026.csv", encoding="utf-8"))}

def habil(d): return d.weekday() < 5 and d.isoformat() not in FER
def habiles_antes(d, n):
    k = 0
    while k < n:
        d -= dt.timedelta(days=1)
        if habil(d): k += 1
    return d

def esperado(regla, v, f, h):
    """Fecha (AAAA-MM-DD) que debería tener vv_hasta según la regla, o None si no se recalcula."""
    d0 = dt.date.fromisoformat(f)
    if regla == "dias_habiles_antes": return habiles_antes(d0, v["dias"]).isoformat()
    if regla == "dia_anterior": return (d0 - dt.timedelta(days=1)).isoformat()
    if regla == "dia_anterior_sabado_a_viernes":
        d = d0 - dt.timedelta(days=1)
        return (d - dt.timedelta(days=1) if d.weekday() == 5 else d).isoformat()
    if regla == "dia_anterior_sabado_a_habil":
        d = d0 - dt.timedelta(days=1)
        return (habiles_antes(d0, 1) if d.weekday() == 5 else d).isoformat()
    if regla == "viernes_anterior":
        d = d0 - dt.timedelta(days=1)
        while d.weekday() != 4: d -= dt.timedelta(days=1)
        return d.isoformat()
    if regla == "martes_o_jueves_anterior":
        d = d0 - dt.timedelta(days=1)
        while d.weekday() not in (1, 3): d -= dt.timedelta(days=1)
        return d.isoformat()
    if regla == "en_el_remate": return f
    if regla == "horas_antes":
        t = dt.datetime.fromisoformat(f"{f} {h}") - dt.timedelta(hours=v["horas"])
        d = t.date()
        while not habil(d): d -= dt.timedelta(days=1)
        return d.isoformat()
    return None   # fecha_fija, fecha_dicha_en_aviso, sin_dato

def citas(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("cita", "cita_costas") and v: yield k, v
            elif k == "citas_extra": yield from ((k, x) for x in v)
            else: yield from citas(v)
    elif isinstance(o, list):
        for v in o: yield from citas(v)

paginas = [(p, leer_pagina(B / f"mercurio_2026-10-14_{p}.txt")) for p in ("B11", "C8")]
rollo, marcas = construir_rollo(paginas)
texto = {a.orden: a.texto for a in cortar(rollo, marcas)}
banco = json.loads((B / "banco_nivel2_2026-10-14.json").read_text(encoding="utf-8"))["avisos"]

fallas = []
for a in banco:
    n = a["n"]; t = texto.get(n, "")
    for campo, c in citas(a):
        if c not in t: fallas.append(f"{n} cita no está en el aviso. {c[:70]}")
    f, h = a["fecha_remate"]["valor"], a["hora_remate"]["valor"]
    try: dt.datetime.fromisoformat(f"{f} {h}")
    except (TypeError, ValueError): fallas.append(f"{n} fecha u hora inválida {f} {h}")
    if a["modalidad"]["valor"] not in MODALIDADES: fallas.append(f"{n} modalidad inválida {a['modalidad']['valor']}")
    v = a["vale_vista"]
    if v["vv_estado"] == "calculado":
        e = esperado(v["regla"], v, f, h)
        if e and e != v["vv_hasta"][:10]: fallas.append(f"{n} vale vista {v['vv_hasta']} pero la regla {v['regla']} da {e}")
        if VERBOSO: print(n, v["regla"], v["vv_hasta"], "regla da", e)

total_citas = sum(1 for a in banco for _ in citas(a))
print(f"Remates en el banco {len(banco)} (esperados 61) | citas revisadas {total_citas}")
if len(banco) != 61: fallas.append(f"se esperaban 61 remates y hay {len(banco)}")
for x in fallas: print("FALLA", x)
print("\nRESULTADO.", "TODO OK" if not fallas else f"{len(fallas)} fallas")
sys.exit(1 if fallas else 0)

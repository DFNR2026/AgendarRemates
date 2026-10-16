"""Revisa el banco de VALIDACIÓN de la parte 3.6 (banco_pruebas/2026-10-06/banco_validacion_2026-10-06.json). Solo código, sin IA.
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_banco_validacion

Este banco lo anotó Claude ANTES de escribir el código de extracción. No se usa para ajustar reglas, solo para medir.
Comprueba que cada cita exista letra por letra en el texto de su aviso, que cada monto, costas y porcentaje aparezca
en su cita, que el rol calce con el del cortador, y que estén exactamente los 60 avisos de la muestra.
"""
import json, re, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.cortador import construir_rollo, cortar
from motor.orden_columnas import leer_pagina

D = RAIZ / "banco_pruebas" / "2026-10-06"
pags = [(n, leer_pagina(D / f"mercurio_2026-10-06_{n}.txt")) for n in ("B7", "B8", "B9", "B10")]
rollo, marcas = construir_rollo(pags)
av = {a.orden: a for a in cortar(rollo, marcas)}
banco = json.loads((D / "banco_validacion_2026-10-06.json").read_text(encoding="utf-8"))["avisos"]
muestra = json.loads((D / "muestra_validacion.json").read_text(encoding="utf-8"))["muestra"]


def num_en(cita, x):
    if x is None:
        return True
    s = re.sub(r"[\s.]", "", cita).replace(",", ".")
    candidatos = {str(x), f"{x:.10f}".rstrip("0").rstrip(".")}
    if float(x).is_integer():
        candidatos.add(str(int(x)))
    return any(c in s for c in candidatos)


fallas, n_citas = [], 0
for e in banco:
    t = av[e["n"]].texto
    bloques = [e] + list(e.get("avisos_pegados") or [])
    for b in bloques:
        for campo in ("fecha_remate", "hora_remate", "modalidad"):
            c = (b.get(campo) or {}).get("cita")
            if c:
                n_citas += 1
                if c not in t: fallas.append(f"{e['n']} {campo} cita no está. {c}")
        m = b.get("minimo") or {}
        for el in (m.get("lista") or [m]):
            for k in ("cita", "cita_costas"):
                if el.get(k):
                    n_citas += 1
                    if el[k] not in t: fallas.append(f"{e['n']} mínimo {k} no está. {el[k]}")
            if el.get("cita") and not num_en(el["cita"], el.get("monto")): fallas.append(f"{e['n']} monto {el.get('monto')} no aparece en su cita")
            if el.get("costas_partes"):
                if sum(el["costas_partes"]) != el.get("costas_clp"): fallas.append(f"{e['n']} las partes de costas no suman")
                for x in el["costas_partes"]:
                    if not num_en(el["cita_costas"], x): fallas.append(f"{e['n']} costas {x} no aparece en su cita")
            elif el.get("cita_costas") and not num_en(el["cita_costas"], el.get("costas_clp")): fallas.append(f"{e['n']} costas no aparecen en su cita")
    g = e["garantia"]
    if g.get("cita"):
        n_citas += 1
        if g["cita"] not in t: fallas.append(f"{e['n']} garantía cita no está. {g['cita']}")
        if g.get("porcentaje") is not None and f"{int(g['porcentaje'])}%" not in g["cita"]: fallas.append(f"{e['n']} porcentaje no aparece en su cita")
    if e["rol"] and f"{av[e['n']].rol}-{av[e['n']].anio}" != e["rol"]: fallas.append(f"{e['n']} rol distinto al del cortador")
if sorted(e["n"] for e in banco) != sorted(muestra): fallas.append("los avisos anotados no son los 60 de la muestra")

print(f"Avisos anotados {len(banco)} (muestra {len(muestra)}) | pegados {sum(1 for e in banco if e.get('pegado'))} | citas revisadas {n_citas}")
for f in fallas: print("FALLA", f)
print("\nRESULTADO.", "TODO OK" if not fallas else f"{len(fallas)} fallas")
sys.exit(1 if fallas else 0)

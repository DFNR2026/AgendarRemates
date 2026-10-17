"""Feriados calculados por ley (db\\feriados_calculo\\calcular_feriados.py, 17 de Octubre). Sin internet.
1. Las reglas reproducen la lista OFICIAL de 2026 (feriados.cl) fecha por fecha.
2. El traslado al lunes calza con casos reales de años anteriores.
3. db\\feriados_2027.csv es exactamente lo que da el cálculo y está marcado como PROVISORIO.
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_feriados
"""
import csv, datetime as dt, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "db" / "feriados_calculo"))
from calcular_feriados import feriados, a_lunes, pascua, CASOS_LUNES

FALLAS = []
def revisar(nombre, cond, detalle=""):
    print(("OK    " if cond else "FALLA ") + nombre, detalle)
    if not cond: FALLAS.append(nombre)

leer = lambda a: [(r["fecha"], r["nombre"], r["fuente"]) for r in csv.DictReader(open(RAIZ / "db" / f"feriados_{a}.csv", encoding="utf-8"))]
of26 = [(f, n) for f, n, _ in leer(2026)]
calc26 = [(d.isoformat(), n) for d, n in feriados(2026)]
revisar("las reglas reproducen los 16 feriados oficiales de 2026", of26 == calc26, str(set(of26) ^ set(calc26)))
revisar("traslado al lunes igual a los casos reales", all(a_lunes(dt.date.fromisoformat(k)).isoformat() == v for k, v in CASOS_LUNES.items()))
revisar("Pascua 2024 a 2027", [pascua(a).isoformat() for a in (2024, 2025, 2026, 2027)] == ["2024-03-31", "2025-04-20", "2026-04-05", "2027-03-28"])
f27 = leer(2027)
revisar("feriados_2027.csv es exactamente el cálculo", [(f, n) for f, n, _ in f27] == [(d.isoformat(), n) for d, n in feriados(2027)])
revisar("feriados_2027.csv está marcado como PROVISORIO en cada fila", all(x[2].startswith("PROVISORIO") for x in f27) and len(f27) == 16)
# La alarma de la base avisa los feriados provisorios (y sigue avisando los que faltan)
import tempfile
sys.path.insert(0, str(RAIZ))
from db.crear_base import crear, aviso_feriados
with tempfile.TemporaryDirectory() as tmp:
    con = crear(Path(tmp) / "f.db")
    al = aviso_feriados(con, dt.date(2026, 10, 17))
    revisar("la alarma avisa que 2027 es provisorio", al == "Los feriados de 2027 son provisorios (calculados por ley). Reemplázalos por la lista oficial cuando se publique", al)
    al = aviso_feriados(con, dt.date(2027, 12, 5))
    revisar("en diciembre de 2027 avisa que falta 2028 y que 2027 es provisorio", al.startswith("Faltan los feriados de 2028. Los feriados de 2027 son provisorios"), al)
    con.close()
print("\nRESULTADO.", "TODO OK" if not FALLAS else f"{len(FALLAS)} fallas")
sys.exit(1 if FALLAS else 0)

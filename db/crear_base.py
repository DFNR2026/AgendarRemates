"""Crea (o actualiza sin borrar nada) la base agendar_remates.db y carga los feriados.
Uso. python db\\crear_base.py   (desde D:\\Agendar_Remates)"""
import csv, sqlite3, sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
BASE = RAIZ.parent / "agendar_remates.db"

VERSION_ESQUEMA = "2"

def crear(ruta_base=BASE):
    con = sqlite3.connect(ruta_base)
    con.execute("PRAGMA foreign_keys = ON")
    # Una base de otra versión no se toca. El esquema usa CREATE TABLE IF NOT EXISTS y dejaría tablas viejas a medias.
    hay_meta = con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='meta'").fetchone()
    if hay_meta:
        fila = con.execute("SELECT valor FROM meta WHERE clave='version_esquema'").fetchone()
        if fila and fila[0] != VERSION_ESQUEMA:
            con.close()
            raise SystemExit(f"La base {ruta_base} es de la versión {fila[0]} del esquema y este programa usa la {VERSION_ESQUEMA}. No se tocó nada.")
    con.executescript((RAIZ / "esquema.sql").read_text(encoding="utf-8"))
    con.execute("INSERT OR REPLACE INTO meta(clave, valor) VALUES ('version_esquema', ?)", (VERSION_ESQUEMA,))
    for csv_feriados in sorted(RAIZ.glob("feriados_*.csv")):
        with open(csv_feriados, encoding="utf-8", newline="") as f:
            for fila in csv.DictReader(f):
                con.execute("INSERT OR REPLACE INTO feriados(fecha, nombre, ambito, fuente) VALUES (?,?,?,?)",
                            (fila["fecha"], fila["nombre"], fila["ambito"], fila["fuente"]))
    con.commit()
    return con

def aviso_feriados(con, hoy=None):
    """Devuelve un texto de alarma si falta cargar los feriados del año siguiente (a partir de diciembre) o del actual."""
    hoy = hoy or date.today()
    anios = {r[0] for r in con.execute("SELECT DISTINCT substr(fecha,1,4) FROM feriados")}
    faltan = [str(hoy.year)] if str(hoy.year) not in anios else []
    if hoy.month == 12 and str(hoy.year + 1) not in anios:
        faltan.append(str(hoy.year + 1))
    return f"Faltan los feriados de {', '.join(faltan)}" if faltan else ""

if __name__ == "__main__":
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE
    con = crear(ruta)
    tablas = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view') ORDER BY name")]
    print("Base lista en", ruta)
    print("Tablas y vistas.", ", ".join(tablas))
    print("Feriados cargados.", con.execute("SELECT COUNT(*) FROM feriados").fetchone()[0])
    alarma = aviso_feriados(con)
    if alarma:
        print("ALARMA.", alarma)

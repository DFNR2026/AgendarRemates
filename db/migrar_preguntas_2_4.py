"""Preguntas 2 y 4 al abogado dadas por resueltas el 4 de Noviembre de 2026 (decisión de Diego). Pone en verde lo ya cargado
sin recargar ediciones, para no cambiar los números internos de los remates que Diego tiene agendados.
Borra las alertas "Fecha del vale vista provisoria. Depende de la pregunta 2 (o 4) al abogado." y pasa esos remates de
revisar a calculado, solo si no les queda otra alerta de pregunta pendiente. No cambia ninguna fecha.
Sin --aplicar solo muestra. Con --aplicar exige un respaldo del mismo día en respaldos.
Uso. python -m db.migrar_preguntas_2_4 RUTA_BASE [--aplicar]
"""
import sys, sqlite3, datetime as dt
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
TEXTOS = tuple(f"Fecha del vale vista provisoria. Depende de la pregunta {n} al abogado." for n in (2, 4))


def main():
    ruta, aplicar = Path(sys.argv[1]), "--aplicar" in sys.argv
    con = sqlite3.connect(ruta)
    con.execute("PRAGMA foreign_keys = ON")
    alertas = con.execute(f"SELECT id, aviso_id, sub_orden FROM alertas WHERE texto IN ({','.join('?' * len(TEXTOS))})", TEXTOS).fetchall()
    remates = set()
    for _, aviso, sub in alertas:
        q = "SELECT id FROM remates WHERE aviso_id = ?" + ("" if sub == 0 else " AND sub_orden = ?")
        remates |= {r[0] for r in con.execute(q, (aviso,) if sub == 0 else (aviso, sub))}
    ids_alertas = [a[0] for a in alertas]
    quedan = {r for r in remates if con.execute(
        "SELECT 1 FROM alertas x JOIN remates r ON r.aviso_id = x.aviso_id AND x.sub_orden IN (0, r.sub_orden) "
        f"WHERE r.id = ? AND x.texto LIKE 'Fecha del vale vista provisoria%' AND x.id NOT IN ({','.join('?' * len(ids_alertas))})",
        (r, *ids_alertas)).fetchone()} if ids_alertas else set()
    a_verde = sorted(remates - quedan)
    print(f"alertas a borrar {len(alertas)}, remates que pasan a verde {len(a_verde)}, remates que siguen en ámbar por otra pregunta {len(quedan)}")
    if not aplicar:
        print("Solo lectura. Para aplicar agrega --aplicar."); return
    hoy = dt.date.today().isoformat()
    if not any((RAIZ / "respaldos").glob(f"*{hoy}*.db")):
        print(f"No hay respaldo de hoy ({hoy}) en respaldos. Se detiene."); sys.exit(1)
    with con:
        con.executemany("DELETE FROM alertas WHERE id = ?", [(i,) for i in ids_alertas])
        con.executemany("UPDATE remates SET vv_estado = 'calculado' WHERE id = ? AND vv_estado = 'revisar'", [(r,) for r in a_verde])
    print("Aplicado.")


if __name__ == "__main__":
    main()

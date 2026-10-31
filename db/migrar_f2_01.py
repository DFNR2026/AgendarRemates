"""F2-01 (31 de Octubre de 2026, regla B aprobada por Diego). Une en un solo bien la propiedad que quedó partida porque
El Mercurio publicó su aviso dos veces el mismo día (C-17115-2025 del 21° Civil, 23 y 24 de Octubre).
Rehace la regla nueva de db\\carga.py sobre lo ya cargado. Dentro de una edición, si una causa trae remates de avisos
distintos y todos con la misma identidad leída (inscripción o lote), esos remates van al bien de la causa sola.
Sin --aplicar solo muestra lo que haría. Con --aplicar exige que exista un respaldo del mismo día en respaldos.
Uso. python -m db.migrar_f2_01 RUTA_BASE [--aplicar]
"""
import sys, sqlite3, datetime as dt
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from db.carga import identidad_inmueble, clave_inmueble
from motor.extraccion import inscripcion
from motor import republicaciones as RP


def plan(con):
    filas = con.execute(
        "SELECT r.id, r.bien_id, r.inmueble, a.id, a.causa_id, c.clave, a.texto, e.fecha FROM remates r "
        "JOIN avisos a ON a.id = r.aviso_id JOIN ediciones e ON e.id = a.edicion_id JOIN causas c ON c.id = a.causa_id "
        "WHERE a.filtro_estado <> 'descartado' AND r.bien_id IS NOT NULL").fetchall()
    grupos = {}
    for rid, bid, inm, aid, cid, base, texto, fecha in filas:
        ident = clave_inmueble(inm) if inm else (inscripcion(texto, fecha)["clave"] or "")
        grupos.setdefault((cid, fecha), []).append((rid, bid, aid, ident, base))
    mover = []
    for (cid, fecha), g in grupos.items():
        if len(g) < 2 or g[0][3] == "" or len({x[3] for x in g}) != 1 or len({x[2] for x in g}) != len(g):
            continue
        base = g[0][4]
        destino = con.execute("SELECT id FROM bienes WHERE clave = ?", (base,)).fetchone()
        for rid, bid, aid, ident, _ in g:
            mover.append((rid, bid, aid, base, destino[0] if destino else None, fecha))
    return mover


def main():
    ruta, aplicar = Path(sys.argv[1]), "--aplicar" in sys.argv
    con = sqlite3.connect(ruta)
    con.execute("PRAGMA foreign_keys = ON")
    mv = plan(con)
    for x in mv:
        print(f"remate {x[0]} del {x[5]} pasa del bien {x[1]} al bien {x[4]} ({x[3]})")
    if not mv:
        print("Nada que unir."); return
    if any(x[4] is None for x in mv):
        print("Hay una causa sin bien de causa sola. No se adivina, se detiene."); sys.exit(1)
    viejos = sorted({x[1] for x in mv if x[1] != x[4]})
    refs = {t: con.execute(f"SELECT COUNT(*) FROM {t} WHERE bien_id IN ({','.join('?' * len(viejos))})", viejos).fetchone()[0]
            for t in ("agenda", "agenda_quitados", "cambios")} if viejos else {}
    print("bienes que quedan vacíos", viejos, "referencias", refs)
    if any(refs.values()):
        print("Algún bien a borrar está agendado, quitado o con cambios. Se detiene para revisarlo con Diego."); sys.exit(1)
    if not aplicar:
        print("Solo lectura. Para aplicar agrega --aplicar."); return
    hoy = dt.date.today().isoformat()
    if not any((RAIZ / "respaldos").glob(f"*{hoy}*.db")):
        print(f"No hay respaldo de hoy ({hoy}) en respaldos. Se detiene."); sys.exit(1)
    fechas = sorted({x[5] for x in mv})
    with con:
        for rid, bid, aid, base, destino, fecha in mv:
            con.execute("UPDATE remates SET bien_id = ? WHERE id = ?", (destino, rid))
            con.execute("DELETE FROM alertas WHERE aviso_id = ? AND texto LIKE 'No se pudo distinguir este remate de otro de la misma causa%'", (aid,))
        con.execute(f"DELETE FROM bienes WHERE id IN ({','.join('?' * len(viejos))}) "
                    "AND NOT EXISTS (SELECT 1 FROM remates r WHERE r.bien_id = bienes.id)", viejos)
    for f in fechas:            # rehace cambios y posibles republicaciones de esa edición y de la siguiente
        RP.registrar_cambios(con, f, dt.datetime.now().isoformat(timespec="seconds"))
    print("Aplicado. Ediciones rehechas", fechas)


if __name__ == "__main__":
    main()

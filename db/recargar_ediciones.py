"""Recarga ediciones ya cargadas desde sus capturas con el código actual (1 de Noviembre de 2026, F2-02 y F2-03).
Solo usa las respuestas de Haiku guardadas. Nunca llama a Haiku. Sirve cuando un arreglo del cortador o de la extracción
cambia lo que se lee de ediciones viejas (C-5618-2025 del 25 al 28 de Octubre, C-18510-2019 escondido el 27 de Octubre).
Se detiene sin tocar nada si una edición está agendada (agenda o agenda_manual apuntan a sus remates), si hay cambios o
alertas marcados como vistos en ellas, o si falta su captura completa. Con --aplicar exige un respaldo del mismo día.
Uso. python -m db.recargar_ediciones RUTA_BASE FECHA [FECHA ...] [--aplicar]
"""
import sys, sqlite3, datetime as dt
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.procesar_edicion import cargar_edicion
from motor import republicaciones as RP
from interfaz.nube import captura_completa


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ruta, fechas, aplicar = Path(args[0]), sorted(args[1:]), "--aplicar" in sys.argv
    con = sqlite3.connect(ruta)
    con.execute("PRAGMA foreign_keys = ON")
    marcas = ",".join("?" * len(fechas))
    ids = [r[0] for r in con.execute(f"SELECT id FROM ediciones WHERE fecha IN ({marcas})", fechas)]
    if len(ids) != len(fechas):
        print("Alguna fecha no está cargada en la base. Se detiene."); sys.exit(1)
    for f in fechas:
        if not captura_completa(RAIZ / "capturas" / f, f):
            print(f"Falta la captura completa del {f}. Se detiene."); sys.exit(1)
    rem = f"SELECT r.id FROM remates r JOIN avisos a ON a.id = r.aviso_id JOIN ediciones e ON e.id = a.edicion_id WHERE e.fecha IN ({marcas})"
    frenos = {
        "agendadas": con.execute(f"SELECT COUNT(*) FROM agenda WHERE remate_base_id IN ({rem})", fechas).fetchone()[0],
        "cambios vistos": con.execute(f"SELECT COUNT(*) FROM cambios WHERE visto = 1 AND (remate_nuevo IN ({rem}) OR remate_anterior IN ({rem}))", fechas * 2).fetchone()[0],
        "alertas vistas": con.execute(f"SELECT COUNT(*) FROM alertas x JOIN avisos a ON a.id = x.aviso_id JOIN ediciones e ON e.id = a.edicion_id "
                                      f"WHERE x.visto = 1 AND e.fecha IN ({marcas})", fechas).fetchone()[0],
    }
    bienes_antes = {r[0] for r in con.execute(f"SELECT DISTINCT r.bien_id FROM remates r WHERE r.id IN ({rem}) AND r.bien_id IS NOT NULL", fechas)}
    print("ediciones", fechas, "frenos", frenos)
    if any(frenos.values()):
        print("Hay algo agendado o visto en esas ediciones. Se detiene para revisarlo con Diego."); sys.exit(1)
    if not aplicar:
        print("Solo lectura. Para aplicar agrega --aplicar."); return
    hoy = dt.date.today().isoformat()
    if not any((RAIZ / "respaldos").glob(f"*{hoy}*.db")):
        print(f"No hay respaldo de hoy ({hoy}) en respaldos. Se detiene."); sys.exit(1)
    with con:
        con.execute(f"DELETE FROM cambios WHERE remate_nuevo IN ({rem}) OR remate_anterior IN ({rem})", fechas * 2)
        con.execute(f"DELETE FROM ediciones WHERE fecha IN ({marcas})", fechas)
    ahora = dt.datetime.now().isoformat(timespec="seconds")
    for f in fechas:
        r = cargar_edicion(con, f, ahora, RAIZ / "capturas" / f, cliente=None, usar_ia=True)
        print(f, r.get("avisos"), "avisos", r.get("remates"), "remates")
    # Cambios. Se rehacen en TODAS las ediciones desde la primera recargada (4 de Noviembre). Antes solo la siguiente de cada
    # una, y se perdía un cambio cuando la propiedad volvía a publicarse varios días después (C-14215-2025, del 31 de Octubre
    # al 4 de Noviembre). registrar_cambios conserva lo que Diego ya marcó como visto.
    for f in [x[0] for x in con.execute("SELECT fecha FROM ediciones WHERE fecha >= ? ORDER BY fecha", (fechas[0],))]:
        RP.registrar_cambios(con, f, ahora)
    with con:
        sueltos = [b for b in bienes_antes if not con.execute(
            "SELECT 1 FROM remates WHERE bien_id = ? UNION SELECT 1 FROM agenda WHERE bien_id = ? UNION "
            "SELECT 1 FROM agenda_quitados WHERE bien_id = ? UNION SELECT 1 FROM cambios WHERE bien_id = ?", (b,) * 4).fetchone()]
        if sueltos:
            con.execute(f"DELETE FROM bienes WHERE id IN ({','.join('?' * len(sueltos))})", sueltos)
    print("Aplicado. Bienes que quedaron sin remates y se borraron", sorted(sueltos))


if __name__ == "__main__":
    main()

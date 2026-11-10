"""Deja lo ya cargado igual que una carga hecha con el código actual, SIN recargar ediciones (10 de Noviembre de 2026).
Sirve cuando un arreglo de la lectura (fecha del remate, vale vista) cambia lo que se lee de avisos viejos y db\\recargar_ediciones
no puede usarse porque alguna edición tiene remates agendados o porque no conviene cambiar los números internos de los remates.
Cómo trabaja. Carga las ediciones desde sus capturas en una base temporal en memoria, con el código actual y solo con las respuestas
de Haiku guardadas (nunca llama a Haiku). Compara aviso por aviso con la base. En cada aviso distinto reemplaza los datos de sus
remates, sus alertas y sus citas por los de la carga nueva. No cambia ningún número interno, ni avisos, bienes, cambios, agenda,
agenda_manual, páginas ni ediciones.
Se salta un aviso, y lo dice, si su texto o su cantidad de remates no calza, si alguno de sus remates cambiaría de propiedad, si está
agendado o quitado, si tiene alertas marcadas como vistas o si algún cambio entre publicaciones apunta a sus remates. Avisa también
si la carga nueva daría otros bienes u otros cambios entre publicaciones, porque eso este programa no lo arregla.
Sin --aplicar solo muestra. Con --aplicar exige un respaldo del mismo día en respaldos.
Uso. python -m db.igualar_a_recarga RUTA_BASE [--aplicar]
"""
import sys, sqlite3, datetime as dt
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from db.crear_base import crear
from motor.procesar_edicion import cargar_edicion
from interfaz.nube import captura_completa

NO_SE_COPIAN = ("id", "aviso_id", "bien_id")
Q_CAMBIOS = ("SELECT b.clave, ea.fecha, en.fecha, x.campo, x.valor_anterior, x.valor_nuevo FROM cambios x JOIN bienes b ON b.id = x.bien_id "
             "JOIN remates ra ON ra.id = x.remate_anterior JOIN avisos aa ON aa.id = ra.aviso_id JOIN ediciones ea ON ea.id = aa.edicion_id "
             "JOIN remates rn ON rn.id = x.remate_nuevo JOIN avisos an ON an.id = rn.aviso_id JOIN ediciones en ON en.id = an.edicion_id")


def _aviso(con, cols, fecha, orden):
    """(id, texto, remates [{columna: valor, 'bien': clave, 'id': id}], alertas, citas, alertas vistas) de un aviso, o None."""
    f = con.execute("SELECT a.id, a.texto FROM avisos a JOIN ediciones e ON e.id = a.edicion_id WHERE e.fecha = ? AND a.orden = ?", (fecha, orden)).fetchone()
    if not f:
        return None
    rem = [dict(zip(cols + ["bien"], r)) for r in con.execute(
        f"SELECT {', '.join('r.' + c for c in cols)}, b.clave FROM remates r LEFT JOIN bienes b ON b.id = r.bien_id WHERE r.aviso_id = ? ORDER BY r.sub_orden", (f[0],))]
    ale = sorted(con.execute("SELECT sub_orden, tipo, texto, cita, origen FROM alertas WHERE aviso_id = ?", (f[0],)).fetchall(), key=str)
    cit = sorted(con.execute("SELECT sub_orden, campo, n_cita, valor, cita, metodo, verificada FROM citas WHERE aviso_id = ?", (f[0],)).fetchall(), key=str)
    vistas = con.execute("SELECT COUNT(*) FROM alertas WHERE aviso_id = ? AND visto = 1", (f[0],)).fetchone()[0]
    return f[0], f[1], rem, ale, cit, vistas


def main():
    ruta, aplicar = Path(sys.argv[1]), "--aplicar" in sys.argv
    if aplicar:
        hoy = dt.date.today().isoformat()
        from db.respaldo import carpeta_de
        if not any(carpeta_de(ruta).glob(f"{ruta.stem}_{hoy}*.db")):
            print(f"Falta un respaldo de hoy ({hoy}) en respaldos. No se tocó nada."); sys.exit(1)
    con = sqlite3.connect(ruta)
    con.execute("PRAGMA foreign_keys = ON")
    fechas = [r[0] for r in con.execute("SELECT fecha FROM ediciones ORDER BY fecha")]
    sin_captura = [f for f in fechas if not captura_completa(RAIZ / "capturas" / f, f)]
    if sin_captura:
        print("Ediciones sin captura completa, que no se revisan.", sin_captura)
    fechas = [f for f in fechas if f not in sin_captura]
    nueva = crear(":memory:")
    for f in fechas:                                   # en orden, igual que la carga diaria. cliente=None, solo respuestas guardadas
        cargar_edicion(nueva, f, "igualar", RAIZ / "capturas" / f, cliente=None, usar_ia=True)
    cols = [r[1] for r in con.execute("PRAGMA table_info(remates)")]
    copiar = [c for c in cols if c not in NO_SE_COPIAN]
    marcas = ",".join("?" * len(fechas))
    claves = set(con.execute(f"SELECT e.fecha, a.orden FROM avisos a JOIN ediciones e ON e.id = a.edicion_id WHERE e.fecha IN ({marcas})", fechas)) | \
             set(nueva.execute("SELECT e.fecha, a.orden FROM avisos a JOIN ediciones e ON e.id = a.edicion_id"))
    cambiar, saltados = [], []
    for fecha, orden in sorted(claves):
        v, n = _aviso(con, cols, fecha, orden), _aviso(nueva, cols, fecha, orden)
        if v is None or n is None:
            saltados.append((fecha, orden, "el aviso existe en un solo lado")); continue
        quita = lambda rem: [{k: r[k] for k in copiar} for r in rem]
        if (quita(v[2]), v[3], v[4]) == (quita(n[2]), n[3], n[4]) and [r["bien"] for r in v[2]] == [r["bien"] for r in n[2]]:
            continue
        ids = [r["id"] for r in v[2]]
        m = ",".join("?" * len(ids)) or "NULL"
        motivo = None
        if v[1] != n[1]: motivo = "el texto del aviso no calza"
        elif len(v[2]) != len(n[2]): motivo = "cambia la cantidad de remates"
        elif [r["bien"] for r in v[2]] != [r["bien"] for r in n[2]]: motivo = "algún remate cambiaría de propiedad"
        elif con.execute(f"SELECT 1 FROM agenda WHERE remate_base_id IN ({m}) OR bien_id IN (SELECT bien_id FROM remates WHERE id IN ({m}))", ids * 2).fetchone(): motivo = "está agendado"
        elif con.execute(f"SELECT 1 FROM agenda_quitados WHERE bien_id IN (SELECT bien_id FROM remates WHERE id IN ({m}))", ids).fetchone(): motivo = "está entre los quitados"
        elif v[5]: motivo = "tiene alertas marcadas como vistas"
        elif con.execute(f"SELECT 1 FROM cambios WHERE remate_anterior IN ({m}) OR remate_nuevo IN ({m})", ids * 2).fetchone(): motivo = "un cambio entre publicaciones apunta a sus remates"
        if motivo:
            saltados.append((fecha, orden, motivo)); continue
        cambiar.append((fecha, orden, v, n))
    print(f"Ediciones revisadas {len(fechas)}. Avisos revisados {len(claves)}. Avisos por cambiar {len(cambiar)}. Saltados {len(saltados)}.")
    for fecha, orden, v, n in cambiar:
        dif = sorted({k for a, b in zip(v[2], n[2]) for k in copiar if a[k] != b[k]})
        print(f"  {fecha} aviso {orden}. remate {dif or 'igual'}. alertas {len(v[3])} a {len(n[3])}. citas {len(v[4])} a {len(n[4])}.")
    for s in saltados:
        print("  SALTADO", *s)
    ca, cb = sorted(con.execute(Q_CAMBIOS + f" WHERE ea.fecha IN ({marcas}) AND en.fecha IN ({marcas})", fechas * 2).fetchall(), key=str), sorted(nueva.execute(Q_CAMBIOS).fetchall(), key=str)
    ba = sorted(r[0] for r in con.execute(f"SELECT DISTINCT b.clave FROM bienes b JOIN remates r ON r.bien_id = b.id JOIN avisos a ON a.id = r.aviso_id JOIN ediciones e ON e.id = a.edicion_id WHERE e.fecha IN ({marcas})", fechas))
    bb = sorted(r[0] for r in nueva.execute("SELECT DISTINCT b.clave FROM bienes b JOIN remates r ON r.bien_id = b.id"))
    print("Cambios entre publicaciones", "iguales" if ca == cb else f"DISTINTOS ({len(ca)} en la base, {len(cb)} en la carga nueva). Este programa no los arregla.")
    print("Bienes", "iguales" if ba == bb else f"DISTINTOS ({len(ba)} en la base, {len(bb)} en la carga nueva). Este programa no los arregla.")
    if not aplicar:
        print("Solo se mostró. Para aplicar agrega --aplicar."); return
    with con:
        for fecha, orden, v, n in cambiar:
            for a, b in zip(v[2], n[2]):
                con.execute(f"UPDATE remates SET {', '.join(c + ' = ?' for c in copiar)} WHERE id = ?", [b[c] for c in copiar] + [a["id"]])
            con.execute("DELETE FROM alertas WHERE aviso_id = ?", (v[0],))
            con.executemany("INSERT INTO alertas(aviso_id, sub_orden, tipo, texto, cita, origen) VALUES (?,?,?,?,?,?)", [(v[0], *x) for x in n[3]])
            con.execute("DELETE FROM citas WHERE aviso_id = ?", (v[0],))
            con.executemany("INSERT INTO citas(aviso_id, sub_orden, campo, n_cita, valor, cita, metodo, verificada) VALUES (?,?,?,?,?,?,?,?)", [(v[0], *x) for x in n[4]])
    print("Aplicado. Integridad", con.execute("PRAGMA integrity_check").fetchone()[0], "y claves", con.execute("PRAGMA foreign_key_check").fetchall() or "ok")
    con.close()


if __name__ == "__main__":
    main()

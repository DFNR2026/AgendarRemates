"""Parte 4. Cuadre de cuentas y cambios entre publicaciones, sin internet. No llama a Haiku. No toca agendar_remates.db.
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_republicaciones
Carga en orden las 7 ediciones del banco (copiadas de capturas el 17 de Octubre) con las respuestas guardadas.
Lo esperado se anotó a mano ANTES del código leyendo los 14 bienes cuyo texto cambia entre publicaciones (bitácora del 17).
"""
import sys, tempfile
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from db.crear_base import crear
from db.carga import VV_NO_LEIDO, DIR_NO_LEIDA
from motor.procesar_edicion import cargar_edicion
from motor import republicaciones as RP

FALLAS = []
def revisar(nombre, condicion, detalle=""):
    print(("OK    " if condicion else "FALLA ") + nombre, detalle)
    if not condicion: FALLAS.append(nombre)

antes = sorted(p.name for p in (RAIZ / "ia_respuestas").rglob("*.json"))
F = ["2026-09-01", "2026-10-06", "2026-10-09", "2026-10-10", "2026-10-11", "2026-10-13", "2026-10-14"]
B = RAIZ / "banco_pruebas"
tmp = tempfile.TemporaryDirectory()
con = crear(Path(tmp.name) / "siete.db")
for f in F:
    cargar_edicion(con, f, "2026-10-17T00:00:00", B / f)
uno = lambda sql, *p: con.execute(sql, p).fetchone()[0]

QC = ("SELECT b.clave, e1.fecha, e2.fecha, k.campo, k.valor_anterior, k.valor_nuevo FROM cambios k JOIN bienes b ON b.id = k.bien_id "
      "JOIN remates r1 ON r1.id = k.remate_anterior JOIN avisos a1 ON a1.id = r1.aviso_id JOIN ediciones e1 ON e1.id = a1.edicion_id "
      "JOIN remates r2 ON r2.id = k.remate_nuevo JOIN avisos a2 ON a2.id = r2.aviso_id JOIN ediciones e2 ON e2.id = a2.edicion_id ORDER BY 1, 4")
ESPERADOS = sorted([
    ("9854-2025|3 juzgado de familia de santiago", "2026-09-01", "2026-10-09", "fecha_remate", "2026-09-16", "2026-10-23"),
    ("9854-2025|3 juzgado de familia de santiago", "2026-09-01", "2026-10-09", "minimo", "84185608.0 CLP", "86542822.0 CLP"),
] + [(f"20712-2024|12 juzgado civil de santiago|lote {k}", "2026-10-06", "2026-10-11", "fecha_remate", "2025-10-20", "2026-10-20") for k in (1, 2, 3, 4)],
    key=lambda x: (x[0], x[3]))
cambios = con.execute(QC).fetchall()
revisar("los 6 cambios reales y ningún otro (3° Familia fecha y mínimo, 4 lotes del 12° Civil de 2025 a 2026)", cambios == ESPERADOS, str(cambios)[:300])
revisar("ningún cambio de vacío a valor ni de valor a vacío", uno("SELECT COUNT(*) FROM cambios WHERE valor_anterior IS NULL OR valor_nuevo IS NULL") == 0)
revisar("texto del cambio con el mes en palabras", RP.texto_cambio("fecha_remate", "2025-10-20", "2026-10-20", "2026-10-06")
        == "Cambió la fecha del remate respecto de la publicación del 6 de Octubre de 2026. Antes 20 de Octubre de 2025, ahora 20 de Octubre de 2026.")

dos = con.execute("SELECT e.fecha, a.orden, al.tipo FROM alertas al JOIN avisos a ON a.id = al.aviso_id JOIN ediciones e ON e.id = a.edicion_id "
                  "WHERE al.texto LIKE 'El aviso imprime % roles distintos%'").fetchall()
revisar("cuadre. alerta de dos roles solo en el 09-10 aviso 10, como error de escritura", dos == [("2026-10-09", 10, "error_escritura")], str(dos))
revisar("cuadre. ninguna edición con roles fuera de los avisos", uno("SELECT COUNT(*) FROM ediciones WHERE alarmas LIKE '%Cuadre. %'") == 0)
revisar("cuadre. la alarma avisa un rol que no quedó en ningún aviso", (RP.alarma_cuadre({("1", "2020"), ("2", "2021")}, []) or "").startswith("Cuadre. 2 roles del texto no quedaron"))

revisar("ya no existe la clave vacía sin_rol|| que juntaba propiedades distintas", uno("SELECT COUNT(*) FROM bienes WHERE clave = 'sin_rol||'") == 0)
QB = ("SELECT r.bien_id FROM remates r JOIN avisos a ON a.id = r.aviso_id JOIN ediciones e ON e.id = a.edicion_id WHERE e.fecha = ? AND a.orden = ?")
b01, b06, b09, b10, b11 = (uno(QB, f, o) for f, o in (("2026-09-01", 9), ("2026-10-06", 84), ("2026-10-09", 120), ("2026-10-10", 119), ("2026-10-11", 127)))
revisar("los avisos sin identificación de días distintos quedan separados, y la republicación idéntica unida",
        len({b01, b06, b09}) == 3 and b09 == b10 == b11, str((b01, b06, b09, b10, b11)))
revisar("ninguna posible republicación en las 7 ediciones", uno("SELECT COUNT(*) FROM alertas WHERE tipo = 'posible_republicacion'") == 0)

# Calendario. El 10-10 deja pendiente el vale vista del C-19295-2023 (5° Civil). Se muestra el del 9 de Octubre.
b, r = con.execute("SELECT r.bien_id, r.id FROM remates r JOIN avisos a ON a.id = r.aviso_id JOIN ediciones e ON e.id = a.edicion_id "
                   "WHERE a.rol = '19295' AND e.fecha = '2026-10-10'").fetchone()
con.execute("INSERT INTO agenda(bien_id, remate_base_id, agregado_en) VALUES (?,?,?)", (b, r, "x")); con.commit()
cal = con.execute("SELECT edicion_vigente, vv_hasta, vv_de_publicacion, mostrar_ventana_vv FROM v_calendario WHERE bien_id = ?", (b,)).fetchone()
revisar("calendario. vale vista pendiente en la publicación nueva, se muestra el de la anterior con su fecha",
        # La causa vuelve a salir el 11-10, también pendiente, así que la vigente es la del 11 (Claude esperaba la del 10)
        cal == ("2026-10-11", "2026-10-26 14:00", "2026-10-09", 1), str(cal))
revisar("calendario. la visita al tribunal también lo toma", con.execute("SELECT dia, roles FROM v_entregas_vv").fetchall() == [("2026-10-26", "19295-2023")])
esq = (RAIZ / "db" / "esquema.sql").read_text(encoding="utf-8")
revisar("los textos de pendiente de la vista son los de db\\carga.py", VV_NO_LEIDO in esq and DIR_NO_LEIDA in esq)

# Correr de nuevo no duplica. Una posible republicación se avisa (caso armado moviendo un remate a otro bien).
RP.registrar_cambios(con, "2026-10-11", "x")
revisar("registrar los cambios dos veces no duplica", con.execute(QC).fetchall() == ESPERADOS)
rid = uno("SELECT r.id FROM remates r JOIN avisos a ON a.id = r.aviso_id JOIN ediciones e ON e.id = a.edicion_id WHERE e.fecha = '2026-10-14' AND a.orden = 1")
con.execute("INSERT INTO bienes(clave, creado_en) VALUES ('prueba', 'x')"); con.execute("UPDATE remates SET bien_id = last_insert_rowid() WHERE id = ?", (rid,)); con.commit()
rp = RP.registrar_cambios(con, "2026-10-14", "x")
revisar("posible republicación cuando el mismo texto de otro día quedó en otra propiedad", rp["posibles_republicaciones"] == 1
        and uno("SELECT COUNT(*) FROM alertas WHERE tipo = 'posible_republicacion' AND texto LIKE 'El mismo aviso salió el 13 de Octubre de 2026%'") == 1, str(rp))
con.close()

# Una edición vieja cargada después. Los cambios de la edición siguiente se calculan igual.
D = crear(Path(tmp.name) / "desorden.db")
cargar_edicion(D, "2026-10-11", "x", B / "2026-10-11"); cargar_edicion(D, "2026-10-06", "x", B / "2026-10-06")
revisar("edición vieja cargada después. los 4 lotes cambian igual de fecha", D.execute("SELECT COUNT(*) FROM cambios WHERE campo = 'fecha_remate'").fetchone()[0] == 4)
D.close(); tmp.cleanup()
despues = sorted(p.name for p in (RAIZ / "ia_respuestas").rglob("*.json"))
revisar("candado. la prueba no escribió ninguna respuesta nueva en ia_respuestas (no llamó a Haiku)", antes == despues)
print("\nRESULTADO.", "TODO OK" if not FALLAS else f"{len(FALLAS)} fallas")
sys.exit(1 if FALLAS else 0)

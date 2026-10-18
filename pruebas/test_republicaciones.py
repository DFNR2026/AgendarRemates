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
# 18 de Octubre (decisión de Diego). El 3° Familia C-9854-2025 es un NUEVO LLAMADO (el remate del 16 de Septiembre no se hizo
# y vuelve a publicarse para el 23 de Octubre). Ya no se compara dato por dato (antes eran 2 cambios, fecha y mínimo).
ESPERADOS = sorted([
    ("9854-2025|3 juzgado de familia de santiago", "2026-09-01", "2026-10-09", "nuevo_llamado", "2026-09-16", "2026-10-23"),
] + [(f"20712-2024|12 juzgado civil de santiago|lote {k}", "2026-10-06", "2026-10-11", "fecha_remate", "2025-10-20", "2026-10-20") for k in (1, 2, 3, 4)],
    key=lambda x: (x[0], x[3]))
cambios = con.execute(QC).fetchall()
revisar("los 5 cambios reales y ningún otro (nuevo llamado del 3° Familia, 4 lotes del 12° Civil de 2025 a 2026)", cambios == ESPERADOS, str(cambios)[:300])
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
# Nuevo llamado (18 de Octubre, decisión de Diego). Texto, vuelta a cero de la agenda una sola vez, y el calendario no toma
# datos del llamado anterior.
revisar("nuevo llamado. texto para Diego", RP.texto_cambio("nuevo_llamado", "2026-09-16", "2026-10-23", "2026-09-01")
        == "Nuevo llamado. El remate anterior de esta propiedad era el 16 de Septiembre de 2026 (aviso del 1 de Septiembre de 2026) y no se hizo. Este aviso es un remate nuevo, con sus propias bases.")
b9854 = uno("SELECT b.id FROM bienes b JOIN causas c ON c.id = b.causa_id WHERE c.rol = '9854' AND c.anio = '2025'")
r01, r09, r10 = [uno("SELECT r.id FROM remates r JOIN avisos a ON a.id = r.aviso_id JOIN ediciones e ON e.id = a.edicion_id WHERE r.bien_id = ? AND e.fecha = ?", b9854, f)
                 for f in ("2026-09-01", "2026-10-09", "2026-10-10")]
with con:
    con.execute("INSERT INTO agenda(bien_id, remate_base_id, agregado_en, vv_entregado, remate_asistido) VALUES (?, ?, 'x', 1, 1)", (b9854, r01))
RP.registrar_cambios(con, "2026-10-09", "x")
revisar("nuevo llamado. retomar no borra lo que Diego marcó después", con.execute("SELECT vv_entregado, remate_asistido FROM agenda WHERE bien_id = ?", (b9854,)).fetchone() == (1, 1))
with con:
    con.execute("DELETE FROM cambios WHERE campo = 'nuevo_llamado' AND bien_id = ?", (b9854,))
RP.registrar_cambios(con, "2026-10-09", "x")
revisar("nuevo llamado. al detectarlo por primera vez, vale vista entregado y remate asistido vuelven a cero",
        con.execute("SELECT vv_entregado, remate_asistido FROM agenda WHERE bien_id = ?", (b9854,)).fetchone() == (0, 0))
revisar("nuevo llamado. sigue siendo uno solo", con.execute(QC).fetchall() == ESPERADOS)
a10 = uno("SELECT aviso_id FROM remates WHERE id = ?", r10)
with con:
    con.execute("UPDATE remates SET vv_hasta = '2026-09-15 14:00', vv_estado = 'calculado' WHERE id = ?", (r01,))
    con.execute("UPDATE remates SET vv_hasta = NULL WHERE id IN (?, ?)", (r09, r10))
    con.execute("INSERT INTO alertas(aviso_id, sub_orden, tipo, texto, origen) VALUES (?, 0, 'dato_faltante', ?, 'codigo')", (a10, VV_NO_LEIDO))
cal = con.execute("SELECT vv_hasta, vv_de_publicacion FROM v_calendario WHERE bien_id = ?", (b9854,)).fetchone()
revisar("nuevo llamado. con el vale vista pendiente, el calendario NO toma el del llamado anterior", cal == (None, None), str(cal))
with con:
    con.execute("UPDATE remates SET vv_hasta = '2026-10-22 14:00' WHERE id = ?", (r09,))
cal = con.execute("SELECT vv_hasta, vv_de_publicacion FROM v_calendario WHERE bien_id = ?", (b9854,)).fetchone()
revisar("nuevo llamado. sí toma una publicación anterior del mismo llamado", cal == ("2026-10-22 14:00", "2026-10-09"), str(cal))
with con:
    con.execute("DELETE FROM agenda WHERE bien_id = ?", (b9854,))
# Costumbre del tribunal en la garantía (18 de Octubre, aprobado por Diego). En las 7 ediciones del banco el 21° Civil pide 20%
# en todas sus propiedades que lo dicen. El 06-10 aviso 73 (rol 8679-2024, dos departamentos) imprime "al 20 del mínimo"
# sin el signo %. Desde el arreglo del porcentaje sin signo se lee 20% y ya no hay ninguna alerta de costumbre en las 7.
# Para probar la alerta se le borra el porcentaje a ese aviso en la base de prueba, como estaba antes del arreglo.
QK = ("SELECT e.fecha, a.orden, x.sub_orden, x.texto FROM alertas x JOIN avisos a ON a.id = x.aviso_id JOIN ediciones e ON e.id = a.edicion_id "
      "WHERE x.texto LIKE 'Costumbre del tribunal.%' ORDER BY 1, 2, 3")
revisar("costumbre. ninguna alerta en las 7 ediciones con la lectura actual", con.execute(QK).fetchall() == [], str(con.execute(QK).fetchall())[:300])
with con:
    con.execute("UPDATE remates SET garantia_porcentaje = NULL, garantia_base = 'sin_dato' WHERE aviso_id IN "
                "(SELECT a.id FROM avisos a JOIN ediciones e ON e.id = a.edicion_id WHERE e.fecha = '2026-10-06' AND a.orden = 73)")
RP.alertas_costumbre(con)
ck = con.execute(QK).fetchall()
revisar("costumbre. alerta solo en los dos remates del 06-10 aviso 73 (21° Civil, 20 sin el signo %)",
        [(f, o, s) for f, o, s, _ in ck] == [("2026-10-06", 73, 1), ("2026-10-06", 73, 2)], str(ck)[:400])
revisar("costumbre. el texto dice el porcentaje y la cuenta del tribunal",
        bool(ck) and ck[0][3].startswith("Costumbre del tribunal. El 21° Juzgado Civil de Santiago pidió garantía del 20% en ") and "Este aviso no dice el porcentaje." in ck[0][3], ck[0][3] if ck else "")
RP.alertas_costumbre(con)
revisar("costumbre. rehacerla no duplica", con.execute(QK).fetchall() == ck)
rid = uno("SELECT r.id FROM remates r JOIN avisos a ON a.id = r.aviso_id JOIN ediciones e ON e.id = a.edicion_id WHERE e.fecha = '2026-10-14' AND a.orden = 1")
con.execute("INSERT INTO bienes(clave, creado_en) VALUES ('prueba', 'x')"); con.execute("UPDATE remates SET bien_id = last_insert_rowid() WHERE id = ?", (rid,)); con.commit()
rp = RP.registrar_cambios(con, "2026-10-14", "x")
revisar("posible republicación cuando el mismo texto de otro día quedó en otra propiedad", rp["posibles_republicaciones"] == 1
        and uno("SELECT COUNT(*) FROM alertas WHERE tipo = 'posible_republicacion' AND texto LIKE 'El mismo aviso salió el 13 de Octubre de 2026%'") == 1, str(rp))
con.close()

# Marcha blanca del 17 de Octubre. La dirección de un terreno sin calle copiada con una palabra de más o con otros espacios
# no es un cambio (11981-2022 del 4° Civil y 2220-2020 del 6° Civil, 16 al 17 de Octubre).
M = crear(Path(tmp.name) / "dir.db")
M.execute("INSERT INTO ediciones(fecha, leida_en, estado) VALUES ('2026-10-16','x','ok'), ('2026-10-17','x','ok')")
M.execute("INSERT INTO paginas(edicion_id, cuerpo, numero, id_pagina, ruta, texto, sha256) VALUES (1,'B',1,'p1','/r1','t','h'), (2,'D',1,'p2','/r2','t','h')")
M.execute("INSERT INTO bienes(clave, creado_en) VALUES ('b1','x'), ('b2','x'), ('b3','x')")
for ed, txt in ((1, "aviso uno"), (2, "aviso uno bis")):
    M.execute("INSERT INTO avisos(edicion_id, orden, pagina_inicio_id, pagina_fin_id, texto) VALUES (?,1,?,?,?)", (ed, ed, ed, txt + " a"))
    M.execute("INSERT INTO avisos(edicion_id, orden, pagina_inicio_id, pagina_fin_id, texto) VALUES (?,2,?,?,?)", (ed, ed, ed, txt + " b"))
    M.execute("INSERT INTO avisos(edicion_id, orden, pagina_inicio_id, pagina_fin_id, texto) VALUES (?,3,?,?,?)", (ed, ed, ed, txt + " c"))
DIRS = {1: ("El Lote ASeis-Dos ‘a’, de la subdivisión del Lote A-6", "la parcela N° 9-8 del plano de las parcelasN°9y10A", "calle Uno 100"),
        2: ("Lote ASeis-Dos ‘a’, de la subdivisión del Lote A-6", "la parcela N° 9-8 del plano de las parcelas N °9y10A", "calle Dos 200")}
for ed in (1, 2):
    for k in range(3):
        aid = M.execute("SELECT id FROM avisos WHERE edicion_id = ? AND orden = ?", (ed, k + 1)).fetchone()[0]
        M.execute("INSERT INTO remates(aviso_id, sub_orden, bien_id, direccion) VALUES (?,1,?,?)", (aid, k + 1, DIRS[ed][k]))
M.commit()
RP.registrar_cambios(M, "2026-10-17", "x")
dc = M.execute("SELECT bien_id, campo FROM cambios").fetchall()
revisar("dirección con una palabra de más o con otros espacios no es cambio, una calle distinta sí", dc == [(3, "direccion")], str(dc))
M.close()

# Una edición vieja cargada después. Los cambios de la edición siguiente se calculan igual.
D = crear(Path(tmp.name) / "desorden.db")
cargar_edicion(D, "2026-10-11", "x", B / "2026-10-11"); cargar_edicion(D, "2026-10-06", "x", B / "2026-10-06")
revisar("edición vieja cargada después. los 4 lotes cambian igual de fecha", D.execute("SELECT COUNT(*) FROM cambios WHERE campo = 'fecha_remate'").fetchone()[0] == 4)
D.close(); tmp.cleanup()
despues = sorted(p.name for p in (RAIZ / "ia_respuestas").rglob("*.json"))
revisar("candado. la prueba no escribió ninguna respuesta nueva en ia_respuestas (no llamó a Haiku)", antes == despues)
print("\nRESULTADO.", "TODO OK" if not FALLAS else f"{len(FALLAS)} fallas")
sys.exit(1 if FALLAS else 0)

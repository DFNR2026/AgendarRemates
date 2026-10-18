"""Prueba de las vistas de la base (parte 3.5, etapa 3). Solo código, sin internet. No toca agendar_remates.db.
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_vistas

Carga el banco del 14 de Octubre en una base temporal, agenda remates reales y comprueba.
1. Buscador sin partidores, búsqueda por rol y por tribunal, link de aviso partido.
2. Calendario por remate (la oficina 602 sin la 603, dos de los cuatro lotes del aviso 30).
3. Entregas de vale vista juntas por tribunal y día (7° Civil 6 de Noviembre con 3 roles, 1° Civil 2 de Noviembre con 2).
4. Una republicación con otra fecha cambia el calendario y avisa el cambio sin ver.
5. Un partidor metido a la fuerza en la agenda no aparece en ninguna vista.
6. Quitar un remate (botón X) lo saca del calendario y de la entrega.
"""
import sqlite3, sys, tempfile
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from db.crear_base import crear
from db.cargar_banco import cargar

FALLAS = []
def revisar(nombre, condicion, detalle=""):
    print(("OK    " if condicion else "FALLA ") + nombre, detalle)
    if not condicion: FALLAS.append(nombre)

PARTIDORES = {55, 57, 58, 60}
VISTAS_CON_ORDEN = ("v_buscador", "v_alertas", "v_calendario")

with tempfile.TemporaryDirectory() as tmp:
    con = crear(Path(tmp) / "vistas.db")
    cargar(con)
    q = lambda sql, *a: con.execute(sql, a).fetchall()
    uno = lambda sql, *a: con.execute(sql, a).fetchone()[0]

    def agendar(orden, sub=1):
        rid, bid = con.execute("SELECT r.id, r.bien_id FROM remates r JOIN avisos a ON a.id = r.aviso_id WHERE a.orden = ? AND r.sub_orden = ?", (orden, sub)).fetchone()
        con.execute("INSERT INTO agenda(bien_id, remate_base_id, agregado_en) VALUES (?,?,?)", (bid, rid, "2026-10-15"))

    # 1. Buscador
    revisar("buscador con 61 remates (65 menos 4 de partidores)", uno("SELECT COUNT(*) FROM v_buscador") == 61)
    revisar("buscador sin partidores", not {r[0] for r in q("SELECT orden FROM v_buscador")} & PARTIDORES)
    revisar("buscar el rol 20712 da los 4 lotes", uno("SELECT COUNT(*) FROM v_buscador WHERE rol = '20712'") == 4)
    revisar("buscar el 7° Civil da sus 6 avisos (18 al 23)", uno("SELECT COUNT(*) FROM v_buscador WHERE tribunal LIKE '7° Juzgado Civil%'") == 6,
            str(uno("SELECT COUNT(*) FROM v_buscador WHERE tribunal LIKE '7° Juzgado Civil%'")))
    revisar("solo el aviso 20 trae dos links (B11 y C8)", q("SELECT orden, ruta_inicio, ruta_fin FROM v_buscador WHERE ruta_fin IS NOT NULL") ==
            [(20, "/2026/10/14/B/B-20261014-011", "/2026/10/14/C/L64MFDBT")])
    revisar("alertas sin partidores y errores del aviso marcados", not {r[0] for r in q("SELECT orden FROM v_alertas")} & PARTIDORES
            and {r[0] for r in q("SELECT orden FROM v_alertas WHERE error_del_aviso")} == {9, 17, 21})   # 6, 45 y 48 eran roles falsos (bitácora del 16)

    # 2. Calendario por remate
    for orden, sub in ((3, 1), (30, 1), (30, 3), (19, 1), (22, 1), (23, 1), (5, 1), (6, 1), (59, 1)):
        agendar(orden, sub)
    revisar("calendario con los 9 remates agendados", uno("SELECT COUNT(*) FROM v_calendario") == 9)
    revisar("la oficina 602 está y la 603 no", q("SELECT inmueble FROM v_calendario WHERE orden = 3") == [("oficina 602",)])
    revisar("el buscador marca agendada la 602 y no la 603", q("SELECT sub_orden, agendado FROM v_buscador WHERE orden = 3 ORDER BY sub_orden") == [(1, 1), (2, 0)])
    revisar("el aviso 59 (vale vista sin fecha) está en el calendario con su alerta", q("SELECT vv_estado, mostrar_ventana_vv, n_alertas FROM v_calendario WHERE orden = 59") == [("sin_dato", 0, 1)])
    revisar("la ficha del 59 dice que el aviso no trae fecha de vale vista", q("SELECT tipo FROM v_alertas WHERE orden = 59") == [("dato_faltante",)])
    # 18 de Octubre. 27 y 28 dejaron de ser "sin dato" en el banco (CORRECCIÓN de Diego, "calificados al momento de hacerse el llamado" es entrega en el remate).
    revisar("vales vista sin fecha visibles. 33, 50, 59 y 61 (los partidores no)", {r[0] for r in q("SELECT orden FROM v_alertas WHERE tipo = 'dato_faltante'")} == {33, 50, 59, 61})
    revisar("el aviso 48 muestra la ventana completa del 15 al 28 de Octubre", q("SELECT vv_desde, vv_hasta FROM v_buscador WHERE orden = 48") == [("2026-10-15", "2026-10-28 12:00")])

    # 3. Entregas por tribunal y día
    ent = {(t, d): (n, roles, h) for t, d, n, roles, h in q("SELECT tribunal, dia, vales_vista, roles, hora_limite FROM v_entregas_vv")}
    e7 = ent.get(("7° Juzgado Civil de Santiago", "2026-11-06"))
    revisar("7° Civil 6 de Noviembre. 3 vales vista en una tarea", e7 and e7[0] == 3 and len(e7[1].split(",")) == 3, str(e7))
    e1 = ent.get(("1° Juzgado Civil de Santiago", "2026-11-02"))
    revisar("1° Civil 2 de Noviembre. 2 vales vista (avisos 5 y 6)", e1 and e1[0] == 2, str(e1))
    e12 = ent.get(("12° Juzgado Civil de Santiago", "2026-10-19"))
    revisar("12° Civil 19 de Octubre. 2 lotes, 1 solo rol", e12 and e12[0] == 2 and e12[1] == "20712-2024", str(e12))
    revisar("el aviso 59 sin fecha no entra a las entregas", "Juzgado de Letras de Colina" not in {t for t, _ in ent})
    revisar("8 vales vista con fecha en 4 tareas", (sum(v[0] for v in ent.values()), len(ent)) == (8, 4), str((sum(v[0] for v in ent.values()), len(ent))))

    # 4. Republicación del aviso 19 con otra fecha en una edición posterior
    bien19, rem19 = con.execute("SELECT r.bien_id, r.id FROM remates r JOIN avisos a ON a.id = r.aviso_id WHERE a.orden = 19").fetchone()
    con.execute("INSERT INTO ediciones(id, fecha, leida_en, estado) VALUES (99, '2026-10-21', 'x', 'ok')")
    con.execute("INSERT INTO avisos(id, edicion_id, orden, texto, tribunal, rol, anio) VALUES (999, 99, 1, 'republicación', '7° Juzgado Civil de Santiago', '7013', '2025')")
    con.execute("INSERT INTO remates(id, aviso_id, sub_orden, bien_id, fecha_remate, hora_remate, vv_hasta, vv_estado) "
                "VALUES (999, 999, 1, ?, '2026-11-16', '12:00', '2026-11-13 14:00', 'calculado')", (bien19,))
    con.execute("INSERT INTO cambios(bien_id, remate_anterior, remate_nuevo, campo, valor_anterior, valor_nuevo, detectado_en) "
                "VALUES (?, ?, 999, 'fecha_remate', '2026-11-09', '2026-11-16', 'x')", (bien19, rem19))
    revisar("el calendario toma la publicación más nueva", q("SELECT fecha_remate, edicion_vigente, cambios_sin_ver FROM v_calendario WHERE bien_id = ?", bien19) ==
            [("2026-11-16", "2026-10-21", 1)])
    e7b = {d: n for t, d, n in q("SELECT tribunal, dia, vales_vista FROM v_entregas_vv WHERE tribunal LIKE '7°%'")}
    revisar("la entrega del 7° Civil se separa en dos días", e7b == {"2026-11-06": 2, "2026-11-13": 1}, str(e7b))

    # 5. Partidor metido a la fuerza en la agenda
    rid58 = uno("SELECT r.id FROM remates r JOIN avisos a ON a.id = r.aviso_id WHERE a.orden = 58")
    con.execute("INSERT INTO bienes(id, clave, creado_en) VALUES (777, 'forzado', 'x')")
    con.execute("UPDATE remates SET bien_id = 777 WHERE id = ?", (rid58,))
    con.execute("INSERT INTO agenda(bien_id, remate_base_id, agregado_en) VALUES (777, ?, 'x')", (rid58,))
    aparece = [v for v in VISTAS_CON_ORDEN if uno(f"SELECT COUNT(*) FROM {v} WHERE orden IN (55, 57, 58, 60)")]
    if uno("SELECT COUNT(*) FROM v_entregas_vv WHERE tribunal LIKE 'Juez partidor%'"): aparece.append("v_entregas_vv")
    if uno("SELECT COUNT(*) FROM v_historial_tribunal WHERE tribunal LIKE 'Juez partidor%'"): aparece.append("v_historial_tribunal")
    revisar("un partidor agendado a la fuerza no aparece en ninguna vista", not aparece, str(aparece))

    # Vale vista entregado. Sale de las visitas y deja de mostrar la ventana
    con.execute("UPDATE agenda SET vv_entregado = 1 WHERE bien_id = (SELECT r.bien_id FROM remates r JOIN avisos a ON a.id = r.aviso_id WHERE a.orden = 5)")
    revisar("al marcar entregado el aviso 5, la visita al 1° Civil del 2 de Noviembre baja a 1",
            q("SELECT vales_vista, roles FROM v_entregas_vv WHERE tribunal LIKE '1° Juzgado Civil de Santiago' AND dia = '2026-11-02'") == [(1, "2462-2022")])
    revisar("el aviso 5 sigue en el calendario pero sin ventana de vale vista", q("SELECT vv_entregado, mostrar_ventana_vv FROM v_calendario WHERE orden = 5") == [(1, 0)])

    # 6. Botón X
    con.execute("DELETE FROM agenda WHERE bien_id = (SELECT r.bien_id FROM remates r JOIN avisos a ON a.id = r.aviso_id WHERE a.orden = 23)")
    revisar("quitar el aviso 23 lo saca del calendario y de su entrega",
            uno("SELECT COUNT(*) FROM v_calendario WHERE orden = 23") == 0 and
            uno("SELECT vales_vista FROM v_entregas_vv WHERE tribunal LIKE '7°%' AND dia = '2026-11-06'") == 1)

    # Historial. Cuenta avisos y no lotes
    revisar("historial del 12° Civil cuenta 3 avisos (30, 31 y 32) y no 6 remates", q("SELECT vv_regla, veces FROM v_historial_tribunal WHERE tribunal LIKE '12°%'") == [("dia_anterior", 3)])
    con.close()

print()
print("RESULTADO. TODO OK" if not FALLAS else f"RESULTADO. {len(FALLAS)} FALLAS {FALLAS}")
sys.exit(1 if FALLAS else 0)

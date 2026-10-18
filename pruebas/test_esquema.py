"""Prueba del esquema 2 de la base (parte 3.5, etapa 1). Solo código, sin internet. No toca agendar_remates.db.
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_esquema

Qué comprueba.
1. Que la base se cree dos veces seguidas sobre el mismo archivo sin errores y sin duplicar nada.
2. Que estén las 14 tablas y las 5 vistas esperadas.
3. Que acepte lo nuevo (en_linea, descartado, garantía sobre tasación, varios remates por aviso, citas extra).
4. Que rechace valores inválidos y duplicados.
5. Que borrar un aviso borre sus remates, citas y alertas.
6. Que se niegue a tocar una base de la versión 1.
"""
import sqlite3, sys, tempfile
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from db.crear_base import crear, VERSION_ESQUEMA

FALLAS = []
def revisar(nombre, condicion, detalle=""):
    print(("OK    " if condicion else "FALLA ") + nombre, detalle)
    if not condicion: FALLAS.append(nombre)

def rechaza(con, sql, args=()):
    try:
        con.execute(sql, args)
    except sqlite3.IntegrityError:
        return True
    return False

ESPERADAS = {"meta", "ediciones", "paginas", "causas", "bienes", "avisos", "remates", "agenda_manual", "agenda_quitados",
             "citas", "alertas", "cambios", "agenda", "feriados"}

with tempfile.TemporaryDirectory() as tmp:
    ruta = Path(tmp) / "prueba.db"

    # 1 y 2. Crear dos veces
    con = crear(ruta)
    esquema1 = sorted(r[0] for r in con.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL"))
    fer1 = con.execute("SELECT COUNT(*) FROM feriados").fetchone()[0]
    con.close()
    con = crear(ruta)
    esquema2 = sorted(r[0] for r in con.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL"))
    fer2 = con.execute("SELECT COUNT(*) FROM feriados").fetchone()[0]
    revisar("crear dos veces deja el mismo esquema", esquema1 == esquema2)
    revisar("crear dos veces no duplica feriados", fer1 == fer2 and fer1 > 0, f"({fer1} y {fer2})")
    tablas = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    vistas = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='view'")}
    revisar("las 14 tablas esperadas (12 más agenda_manual y agenda_quitados, 18 de Octubre)", tablas == ESPERADAS, f"sobran {tablas - ESPERADAS} faltan {ESPERADAS - tablas}")
    VISTAS = {"v_buscador", "v_alertas", "v_calendario", "v_entregas_vv", "v_historial_tribunal"}
    revisar("las 5 vistas esperadas", vistas == VISTAS, f"sobran {vistas - VISTAS} faltan {VISTAS - vistas}")
    revisar("versión del esquema", con.execute("SELECT valor FROM meta WHERE clave='version_esquema'").fetchone()[0] == VERSION_ESQUEMA)
    revisar("llaves foráneas activas", con.execute("PRAGMA foreign_keys").fetchone()[0] == 1)

    # 3. Lo nuevo se acepta (un aviso de prueba con dos remates, como el aviso 3 del 14 de Octubre)
    con.execute("INSERT INTO ediciones(id, fecha, leida_en, estado) VALUES (1, '2026-10-14', '2026-10-15 00:14', 'ok')")
    con.execute("INSERT INTO paginas(id, edicion_id, cuerpo, numero, id_pagina, ruta, texto, sha256) "
                "VALUES (1, 1, 'C', 8, 'L64MFDBT', '/2026/10/14/C/L64MFDBT', 'x', 'h')")
    con.execute("INSERT INTO causas(id, clave, tipo_id, rol, anio, tribunal) VALUES (1, '8715-2025|1 civil santiago', 'ROL', '8715', '2025', '1° Juzgado Civil de Santiago')")
    con.execute("INSERT INTO bienes(id, causa_id, clave, inmueble, creado_en) VALUES (1, 1, 'b1', 'oficina 602', 'x'), (2, 1, 'b2', 'oficina 603', 'x')")
    con.execute("INSERT INTO avisos(id, edicion_id, causa_id, orden, pagina_inicio_id, texto) VALUES (1, 1, 1, 3, 1, 'texto')")
    con.execute("INSERT INTO remates(id, aviso_id, sub_orden, bien_id, modalidad, plataforma, garantia_base, vv_desde_origen) "
                "VALUES (1, 1, 1, 1, 'en_linea', 'Google Meet', 'tasacion', 'estimado_dia_siguiente_edicion')")
    con.execute("INSERT INTO remates(id, aviso_id, sub_orden, bien_id, modalidad) VALUES (2, 1, 2, 2, 'presencial')")
    con.execute("INSERT INTO citas(aviso_id, sub_orden, campo, n_cita, metodo, verificada) VALUES (1, 1, 'vv_hasta', 1, 'ia', 1), (1, 1, 'vv_hasta', 2, 'ia', 1)")
    con.execute("INSERT INTO alertas(aviso_id, sub_orden, tipo, texto, origen) VALUES (1, 0, 'rol_mal_impreso', 'CC-936-2026', 'codigo')")
    con.execute("INSERT INTO avisos(id, edicion_id, orden, texto, tipo_id, filtro_estado, filtro_motivos) VALUES (2, 1, 57, 'partidor', 'SIN_ROL', 'descartado', 'juez partidor')")
    con.execute("INSERT INTO agenda(bien_id, remate_base_id, agregado_en) VALUES (1, 1, 'x')")
    revisar("acepta en_linea, tasación, descartado, dos remates en un aviso y una cita extra", True)
    revisar("se puede agendar solo la oficina 602", con.execute("SELECT COUNT(*) FROM agenda").fetchone()[0] == 1)

    # 4. Lo inválido se rechaza
    revisar("rechaza modalidad meet", rechaza(con, "INSERT INTO remates(aviso_id, sub_orden, modalidad) VALUES (1, 3, 'meet')"))
    revisar("rechaza filtro oculto", rechaza(con, "INSERT INTO avisos(edicion_id, orden, texto, filtro_estado) VALUES (1, 99, 't', 'oculto')"))
    revisar("rechaza garantía sobre otra base", rechaza(con, "INSERT INTO remates(aviso_id, sub_orden, garantia_base) VALUES (1, 3, 'avaluo')"))
    revisar("rechaza origen de vale vista desconocido", rechaza(con, "INSERT INTO remates(aviso_id, sub_orden, vv_desde_origen) VALUES (1, 3, 'adivinado')"))
    revisar("rechaza remate con sub_orden repetido", rechaza(con, "INSERT INTO remates(aviso_id, sub_orden) VALUES (1, 2)"))
    revisar("rechaza remate con sub_orden 0", rechaza(con, "INSERT INTO remates(aviso_id, sub_orden) VALUES (1, 0)"))
    revisar("rechaza la misma cita dos veces", rechaza(con, "INSERT INTO citas(aviso_id, sub_orden, campo, n_cita, metodo, verificada) VALUES (1, 1, 'vv_hasta', 2, 'ia', 1)"))
    revisar("rechaza tipo de alerta desconocido", rechaza(con, "INSERT INTO alertas(aviso_id, tipo, texto, origen) VALUES (1, 'otra', 't', 'ia')"))
    revisar("rechaza agendar dos veces el mismo bien", rechaza(con, "INSERT INTO agenda(bien_id, remate_base_id, agregado_en) VALUES (1, 1, 'x')"))
    revisar("rechaza ruta de página repetida", rechaza(con, "INSERT INTO paginas(edicion_id, cuerpo, numero, id_pagina, ruta, texto, sha256) VALUES (1, 'B', 11, 'z', '/2026/10/14/C/L64MFDBT', 'x', 'h')"))
    revisar("rechaza remate de un aviso que no existe", rechaza(con, "INSERT INTO remates(aviso_id, sub_orden) VALUES (999, 1)"))

    # 5. Borrar un aviso arrastra lo suyo
    con.execute("DELETE FROM agenda")
    con.execute("DELETE FROM avisos WHERE id = 1")
    quedan = [con.execute(f"SELECT COUNT(*) FROM {t} WHERE aviso_id = 1").fetchone()[0] for t in ("remates", "citas", "alertas")]
    revisar("borrar el aviso borra sus remates, citas y alertas", quedan == [0, 0, 0], str(quedan))
    con.close()

    # 6. Una base de la versión 1 no se toca
    vieja = Path(tmp) / "vieja.db"
    c = sqlite3.connect(vieja)
    c.execute("CREATE TABLE meta (clave TEXT PRIMARY KEY, valor TEXT NOT NULL)")
    c.execute("INSERT INTO meta VALUES ('version_esquema', '1')"); c.commit(); c.close()
    try:
        crear(vieja); se_nego = False
    except SystemExit as e:
        se_nego = "versión 1" in str(e)
    c = sqlite3.connect(vieja)
    tablas_vieja = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    c.close()
    revisar("se niega a tocar una base de la versión 1", se_nego and tablas_vieja == {"meta"})

print()
print("RESULTADO. TODO OK" if not FALLAS else f"RESULTADO. {len(FALLAS)} FALLAS {FALLAS}")
sys.exit(1 if FALLAS else 0)

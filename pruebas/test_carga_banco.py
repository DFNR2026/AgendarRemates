"""Prueba de la carga del banco nivel 2 en la base (parte 3.5, etapa 2). Solo código, sin internet. No toca agendar_remates.db.
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_carga_banco

Los resultados esperados vienen de fuentes independientes de la carga. El banco nivel 2 (fechas, mínimos),
la bitácora del 15 de Octubre (rol mal impreso en 17. Los de 6, 45 y 48 eran falsos, bitácora del 16, contradicciones en 9 y 17) y el inventario (4 partidores).
"""
import json, sqlite3, sys, tempfile
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from db.crear_base import crear
from db.carga import guardar_edicion, rol_mal_impreso
from db.cargar_banco import cargar, datos_banco, clasificar_duda

FALLAS = []
def revisar(nombre, condicion, detalle=""):
    print(("OK    " if condicion else "FALLA ") + nombre, detalle)
    if not condicion: FALLAS.append(nombre)

banco = {a["n"]: a for a in json.loads((RAIZ / "banco_pruebas/2026-10-14/banco_nivel2_2026-10-14.json").read_text(encoding="utf-8"))["avisos"]}
PARTIDORES = {55, 57, 58, 60}

with tempfile.TemporaryDirectory() as tmp:
    con = crear(Path(tmp) / "banco.db")
    res = cargar(con)
    q = lambda sql, *a: con.execute(sql, a).fetchall()
    uno = lambda sql, *a: con.execute(sql, a).fetchone()[0]

    # Cantidades
    revisar("61 avisos y 65 remates", (uno("SELECT COUNT(*) FROM avisos"), uno("SELECT COUNT(*) FROM remates")) == (61, 65))
    revisar("la edición registra 61 avisos y 65 remates", q("SELECT avisos_extraidos, remates_extraidos FROM ediciones") == [(61, 65)])
    # 18 de Octubre. 27 y 28 dejaron de ser "sin dato" en el banco (CORRECCIÓN de Diego, "calificados al momento de hacerse el llamado" es entrega en el remate). Suman 2 citas.
    revisar("433 citas, todas encontradas en su aviso", (uno("SELECT COUNT(*) FROM citas"), uno("SELECT SUM(verificada) FROM citas")) == (433, 433))
    revisar("2 páginas con su ruta", q("SELECT ruta FROM paginas ORDER BY orden_rollo") == [("/2026/10/14/B/B-20261014-011",), ("/2026/10/14/C/L64MFDBT",)])

    # Partidores. Guardados para el cuadre, descartados y sin bien (no se pueden agendar)
    desc = {r[0] for r in q("SELECT orden FROM avisos WHERE filtro_estado = 'descartado'")}
    revisar("los 4 partidores quedan descartados", desc == PARTIDORES, str(sorted(desc)))
    revisar("cuadre. 57 visibles + 4 descartados = 61", uno("SELECT COUNT(*) FROM avisos WHERE filtro_estado = 'pasa'") == 57)
    revisar("los remates de partidores no tienen bien", uno("SELECT COUNT(*) FROM remates r JOIN avisos a ON a.id = r.aviso_id WHERE a.filtro_estado = 'descartado' AND r.bien_id IS NOT NULL") == 0)
    revisar("todo remate visible tiene su bien", uno("SELECT COUNT(*) FROM remates r JOIN avisos a ON a.id = r.aviso_id WHERE a.filtro_estado = 'pasa' AND r.bien_id IS NULL") == 0)
    revisar("61 bienes y 57 causas", (uno("SELECT COUNT(*) FROM bienes"), uno("SELECT COUNT(*) FROM causas")) == (61, 57))

    # Varios remates en un aviso
    a3 = q("SELECT r.inmueble, r.minimo_monto, b.clave FROM remates r JOIN avisos a ON a.id = r.aviso_id JOIN bienes b ON b.id = r.bien_id WHERE a.orden = 3 ORDER BY r.sub_orden")
    revisar("aviso 3 da 2 remates con su mínimo y bienes distintos", [(x[0], x[1]) for x in a3] == [("oficina 602", 42402396), ("oficina 603", 66522157)] and a3[0][2] != a3[1][2])
    a30 = q("SELECT r.minimo_monto, b.clave FROM remates r JOIN avisos a ON a.id = r.aviso_id JOIN bienes b ON b.id = r.bien_id WHERE a.orden = 30 ORDER BY r.sub_orden")
    revisar("aviso 30 da 4 lotes con su mínimo y 4 bienes", [x[0] for x in a30] == [el["monto"] for el in banco[30]["minimo"]["lista"]] and len({x[1] for x in a30}) == 4,
            str([x[1].split("|")[-1] for x in a30]))

    # Cada remate trae los datos del banco
    malos = []
    for orden, f, h, mod, vh, gb in q("SELECT a.orden, r.fecha_remate, r.hora_remate, r.modalidad, r.vv_hasta, r.garantia_base FROM remates r JOIN avisos a ON a.id = r.aviso_id"):
        b = banco[orden]
        if (f, h, mod, vh, gb) != (b["fecha_remate"]["valor"], b["hora_remate"]["valor"], b["modalidad"]["valor"], b["vale_vista"]["vv_hasta"], b["garantia"]["base"] or "sin_dato"):
            malos.append(orden)
    revisar("fecha, hora, modalidad, vale vista y base de garantía iguales al banco en los 65 remates", not malos, str(malos))
    distintos = [o for o, r, an in q("SELECT orden, rol, anio FROM avisos WHERE tipo_id != 'SIN_ROL'") if f"{r}-{an}" != banco[o]["rol"]]
    revisar("el rol que saca el código calza con el banco en los 57 avisos con rol", not distintos, str(distintos))
    revisar("garantía sobre tasación en 48 y 49", {r[0] for r in q("SELECT a.orden FROM remates r JOIN avisos a ON a.id = r.aviso_id WHERE r.garantia_base = 'tasacion'")} == {48, 49})
    revisar("plataformas de 57, 58 y 60", q("SELECT a.orden, r.plataforma FROM remates r JOIN avisos a ON a.id = r.aviso_id WHERE a.orden IN (57,58,60) ORDER BY a.orden") ==
            [(57, "Google Meet"), (58, "Google Meet"), (60, "vendaya.cl")])
    revisar("costas del aviso 17 aparte del mínimo", q("SELECT r.minimo_monto, r.minimo_moneda, r.minimo_costas_clp FROM remates r JOIN avisos a ON a.id = r.aviso_id WHERE a.orden = 17") == [(398.322141, "UF", 1189800)])

    # Link directo. El aviso 20 empieza en B11 y sigue en C8
    revisar("aviso 20 partido entre B11 y C8", q("SELECT pi.ruta, pf.ruta FROM avisos a JOIN paginas pi ON pi.id = a.pagina_inicio_id JOIN paginas pf ON pf.id = a.pagina_fin_id WHERE a.orden = 20") ==
            [("/2026/10/14/B/B-20261014-011", "/2026/10/14/C/L64MFDBT")])

    # Alertas
    roles = {r[0] for r in q("SELECT a.orden FROM alertas x JOIN avisos a ON a.id = x.aviso_id WHERE x.tipo = 'rol_mal_impreso' AND x.origen = 'codigo'")}
    # Hasta el 2026-10-15 se esperaban 6, 17, 45 y 48. Los avisos 6, 45 y 48 eran FALSOS. El cortador borraba el guion del rol partido
    # entre dos renglones ("Rol: C-2462-" y "2022"). Corregido el 2026-10-16 (bitácora del 16). Solo el 17 (CC-936-2026) es real.
    revisar("rol mal impreso detectado por código solo en el 17", roles == {17}, str(sorted(roles)))
    revisar("sin alerta de rol repetida en el 17", uno("SELECT COUNT(*) FROM alertas x JOIN avisos a ON a.id = x.aviso_id WHERE a.orden = 17 AND x.tipo = 'rol_mal_impreso'") == 1)
    contra = {r[0] for r in q("SELECT a.orden FROM alertas x JOIN avisos a ON a.id = x.aviso_id WHERE x.tipo = 'contradiccion'")}
    revisar("contradicciones en 9 y 17", contra == {9, 17}, str(sorted(contra)))
    revisar("roles bien impresos sin alerta (con N°, sin prefijo, espacio antes del año)",
            [rol_mal_impreso(x) for x in ("Rol N° C-2238-2020", "Rol N° 14328-2025", "Rol N° C-17079- 2024", "Rit C-3908-2025", "Rol: C-618-2025", "C-770-2014")] == [None] * 6)

    # Vale vista sin fecha. Lista de PREGUNTAS_ABOGADO.md (pregunta 7), con la numeración nueva del banco (57a=57, 58a=59, 58b=60, 59=61)
    sin_fecha = {r[0] for r in q("SELECT a.orden FROM alertas x JOIN avisos a ON a.id = x.aviso_id WHERE x.tipo = 'dato_faltante' AND x.origen = 'codigo'")}
    # 18 de Octubre. 27 y 28 dejaron de ser "sin dato" en el banco (CORRECCIÓN de Diego, "calificados al momento de hacerse el llamado" es entrega en el remate).
    revisar("alerta de vale vista sin fecha en 33, 50, 55, 57, 59, 60 y 61", sin_fecha == {33, 50, 55, 57, 59, 60, 61}, str(sorted(sin_fecha)))
    revisar("sin alerta repetida por la duda del banco", uno("SELECT COUNT(*) FROM alertas x JOIN avisos a ON a.id = x.aviso_id WHERE a.orden = 59") == 1)

    # Partidores reconocidos solo desde el texto, sin ayuda del tribunal anotado
    from db.carga import es_partidor, rol_sin_guion
    _, _, avisos_14, _ = datos_banco()
    revisar("los 4 partidores del 14 de Octubre se reconocen solo con el texto", {a.orden for a in avisos_14 if es_partidor(None, a.texto)} == PARTIDORES)
    revisar("un juzgado civil no se toma por partidor", not es_partidor("1° Juzgado Civil de Santiago", "REMATE 1° JUZGADO CIVIL DE SANtiago, Huérfanos 1409, se rematará"))
    revisar("formas de partición vistas en otras ediciones", all(es_partidor(None, x) for x in (
        "REMATE ANTE JUEZA ÁRBITRO doña Gabriela", "REMATE: ANTE ARBITRO SONIA DE las Mercedes", "REMATE. EN JUICIO DE PARTICIÓN Huenchunao",
        "EXTRACTO REMATE. JUEZ PARTIdor Álvaro", "REMATE JUICIO PARTICIONAL juez arbitro Sergio")))
    revisar("rol sin guion. detalle menor sí, rol mal impreso no",
            [bool(rol_sin_guion(x)) for x in ("Rol C8834-2022", "Rol N° C13771-2025", "Rol C 19087-2024", "Rol C-2238-2020", "Rol N° 14328-2025")] == [True, True, True, False, False]
            and rol_mal_impreso("rol C82062024") is not None and rol_sin_guion("rol C82062024") is None)
    revisar("el 14 de Octubre no trae roles sin guion", uno("SELECT COUNT(*) FROM alertas WHERE tipo = 'detalle_menor'") == 0)

    # No se carga dos veces
    try:
        cargar(con); repetida = False
    except ValueError:
        repetida = True
    revisar("una segunda carga de la misma edición se rechaza sin duplicar", repetida and uno("SELECT COUNT(*) FROM avisos") == 61)
    con.close()

    # Si falta un aviso, no queda nada a medias
    con = crear(Path(tmp) / "incompleta.db")
    edicion, paginas, avisos, extraido = datos_banco()
    extraido.pop(30)
    try:
        guardar_edicion(con, edicion, paginas, avisos, extraido, "x", clasificar_duda); rechazo = False
    except ValueError:
        rechazo = True
    revisar("si falta un aviso no se carga nada", rechazo and con.execute("SELECT COUNT(*) FROM ediciones").fetchone()[0] == 0)
    con.close()

print()
print("RESULTADO. TODO OK" if not FALLAS else f"RESULTADO. {len(FALLAS)} FALLAS {FALLAS}")
sys.exit(1 if FALLAS else 0)

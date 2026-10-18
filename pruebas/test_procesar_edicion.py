"""Prueba de la unión motor -> base (paso 4 del ESTADO, 16 de Octubre). Solo código, sin internet. No toca agendar_remates.db.
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_procesar_edicion

Carga el 14 de Octubre dos veces en bases de prueba, una desde el banco nivel 2 (anotado a mano) y otra desde el motor
(cortador + extraer() + traducir()), y compara remate por remate. Las únicas diferencias permitidas son las explicadas
en la bitácora del 16 (plataforma Zoom que el banco no tenía, partidores sin tribunal, vacíos ya conocidos de los avisos
55 y 61, y el inmueble escrito corto). Todo lo demás debe ser igual.
También carga el viernes 09-10 (cuerpos B y G) y comprueba la unión sin duplicar por huella del texto.
"""
import json, sys, tempfile
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from db.crear_base import crear
from db.cargar_banco import cargar, datos_banco
from db.carga import guardar_edicion, normalizar, VV_NO_LEIDO, VV_NO_DICE
from motor.procesar_edicion import extraer_avisos, desde_captura, cargar_edicion, unir_rollos
from motor.cortador import construir_rollo, cortar, Aviso
from motor.orden_columnas import leer_pagina

FALLAS = []
def revisar(nombre, condicion, detalle=""):
    print(("OK    " if condicion else "FALLA ") + nombre, detalle)
    if not condicion: FALLAS.append(nombre)

Q = ("SELECT a.orden, r.sub_orden, a.filtro_estado, a.tribunal, r.fecha_remate, r.hora_remate, r.modalidad, r.plataforma, "
     "r.minimo_monto, r.minimo_moneda, r.minimo_costas_clp, r.garantia_porcentaje, r.garantia_base, r.garantia_monto "
     "FROM remates r JOIN avisos a ON a.id = r.aviso_id ORDER BY 1, 2")
COLS = "orden sub filtro tribunal fecha hora modalidad plataforma minimo moneda costas g_porc g_base g_monto".split()
# Diferencias explicadas (bitácora del 16). (orden, columna) -> (banco, motor)
PERMITIDAS = {
    (15, "plataforma"): (None, "Zoom"), (30, "plataforma"): (None, "Zoom"),     # el banco la sacaba de la cita "videoconferencia"
    (55, "fecha"): ("2026-11-18", None), (55, "hora"): ("12:00", None), (55, "modalidad"): ("presencial", "sin_dato"),   # partidor, vacío conocido
    (61, "modalidad"): ("presencial", "sin_dato"),                              # "Se realizará dependencias Tribunal", vacío conocido
}
PARTIDORES = {55, 57, 58, 60}

with tempfile.TemporaryDirectory() as tmp:
    A = crear(Path(tmp) / "banco.db"); cargar(A)
    edicion, paginas, avisos, _ = datos_banco()
    B = crear(Path(tmp) / "motor.db")
    res = guardar_edicion(B, edicion, paginas, avisos, extraer_avisos(avisos, "2026-10-14"), "2026-10-16T00:00:00", metodo="codigo")
    uno = lambda con, sql: con.execute(sql).fetchone()[0]

    revisar("motor. 61 avisos y 65 remates", (res["avisos"], res["remates"]) == (61, 65), str(res))
    ra = {(x[0], x[1]): x for x in A.execute(Q)}
    rb = {(x[0], x[1]): x for x in B.execute(Q)}
    revisar("mismos remates (aviso y sub_orden) en las dos bases", ra.keys() == rb.keys())
    raras = []
    for k in sorted(ra):
        for i, c in enumerate(COLS[2:], start=2):
            va, vb = ra[k][i], rb[k][i]
            if c == "tribunal":
                if k[0] in PARTIDORES and vb is None:      # el código no da nombre a los partidores (se descartan por el texto)
                    continue
                va, vb = normalizar(va), normalizar(vb)
            if va != vb and PERMITIDAS.get((k[0], c)) != (ra[k][i], rb[k][i]):
                raras.append(f"{k} {c} banco={ra[k][i]!r} motor={rb[k][i]!r}")
    revisar("sin diferencias fuera de las explicadas", not raras, " | ".join(raras[:8]))
    revisar("los 4 partidores descartados por el texto", {r[0] for r in B.execute("SELECT orden FROM avisos WHERE filtro_estado = 'descartado'")} == PARTIDORES)
    revisar("61 bienes, igual que el banco", uno(B, "SELECT COUNT(*) FROM bienes") == uno(A, "SELECT COUNT(*) FROM bienes") == 61)
    # Desde la parte 3.7c (17 de Octubre) se suman las 57 carátulas (antes 382).
    revisar("citas del motor con método codigo y todas encontradas en su aviso (315 de la 3.6, 67 inscripciones de la 3.7b y 57 carátulas de la 3.7c)",
            B.execute("SELECT metodo, COUNT(*), SUM(verificada) FROM citas GROUP BY metodo").fetchall() == [("codigo", 439, 439)])
    revisar("3.7c. carátula de los 57 avisos visibles en el buscador", B.execute("SELECT COUNT(DISTINCT aviso_id), SUM(caratula IS NULL) FROM v_buscador").fetchone() == (57, 0))
    revisar("citas del banco siguen con método ia", A.execute("SELECT DISTINCT metodo FROM citas").fetchall() == [("ia",)])
    revisar("65 alertas de vale vista NO LEÍDO en el motor y ninguna que diga que el aviso no lo dice",
            (uno(B, f"SELECT COUNT(*) FROM alertas WHERE texto = '{VV_NO_LEIDO}'"), uno(B, f"SELECT COUNT(*) FROM alertas WHERE texto = '{VV_NO_DICE}'")) == (65, 0))
    revisar("el banco sigue diciendo que el aviso no lo dice (9 remates)", uno(A, f"SELECT COUNT(*) FROM alertas WHERE texto = '{VV_NO_DICE}'") == 9)
    revisar("alertas del código guardadas con su tipo y origen codigo",
            uno(B, "SELECT COUNT(*) FROM alertas WHERE tipo = 'condicion_especial' AND origen = 'codigo'") == 12
            and uno(B, "SELECT COUNT(*) FROM alertas WHERE origen = 'ia'") == 0)
    # Parte 3.7b (17 de Octubre). Con la etiqueta arreglada, el bien de cada remate del motor es el mismo que el del banco
    # (antes el lote 4 del aviso 30 quedaba como "estacionamiento 6").
    QB = "SELECT a.orden, r.sub_orden, b.clave FROM remates r JOIN avisos a ON a.id = r.aviso_id JOIN bienes b ON b.id = r.bien_id ORDER BY 1, 2"
    revisar("3.7b. claves de bien del motor iguales a las del banco (incluye el lote 4 del aviso 30)", A.execute(QB).fetchall() == B.execute(QB).fetchall(),
            str([x for x in B.execute(QB) if x[0] == 30]))
    revisar("3.7b. inscripciones del motor con método codigo y todas encontradas en su aviso",
            B.execute("SELECT COUNT(*), SUM(verificada), MIN(metodo), MAX(metodo) FROM citas WHERE campo = 'inscripcion'").fetchone() == (67, 67, "codigo", "codigo"))
    revisar("garantía 20% del aviso 43 avisada", uno(B, "SELECT COUNT(*) FROM alertas al JOIN avisos a ON a.id = al.aviso_id WHERE a.orden = 43 AND al.texto LIKE 'Garantía del 20%%'") == 1)

    # Viernes 2026-10-09. Cuerpos B (3 páginas) y G (8 páginas) con los mismos 127 avisos. Se unen sin duplicar por huella.
    # Copiados de capturas al banco el 2026-10-16 (HUELLAS_ESPERADAS.txt). Ver bitácora del 16.
    D09 = RAIZ / "banco_pruebas" / "2026-10-09"
    U = crear(Path(tmp) / "union.db")
    res = cargar_edicion(U, "2026-10-09", "2026-10-16T00:00:00", D09)
    # Eran 128 remates hasta el 17 de Octubre. Con la etiqueta arreglada (parte 3.7b) el aviso 87 se separa en sus 3
    # departamentos (antes 1 remate con la alerta de mínimos sin asignar), así que son 130. Sigue sin duplicar B y G.
    revisar("09-10. 127 avisos y 130 remates (no 254)", (res["avisos"], res["remates"]) == (127, 130), str(res)[:200])
    revisar("09-10. 11 páginas guardadas, las de B y las de G", uno(U, "SELECT COUNT(*) FROM paginas") == 11)
    alarma = uno(U, "SELECT alarmas FROM ediciones") or ""
    revisar("09-10. alarma de resumen de la unión", "127 de 127 avisos unidos" in alarma and "7 con diferencias de espacios" in alarma, alarma)
    # Remates idénticos a cargar solo el rollo B
    nav = json.loads((D09 / "navegacion.json").read_text(encoding="utf-8"))
    pn = {p["pagina"]: p for p in nav["paginas_con_remates"]}
    rb = nav["rollos"][0]
    r, m = construir_rollo([(n, leer_pagina(D09 / pn[n]["archivo"])) for n in rb])
    avb = cortar(r, m)
    ed, pg, _, _ = desde_captura("2026-10-09", D09)
    SB = crear(Path(tmp) / "solo_b.db")
    guardar_edicion(SB, dict(ed, alarmas=None), [p for p in pg if p["cuerpo"] == "B"], avb, extraer_avisos(avb, "2026-10-09"), "x", metodo="codigo")
    Q2 = ("SELECT a.orden, r.sub_orden, a.texto, a.filtro_estado, a.tribunal, r.fecha_remate, r.hora_remate, r.modalidad, r.minimo_monto, "
          "r.minimo_costas_clp, r.garantia_porcentaje, r.garantia_base, r.inmueble FROM remates r JOIN avisos a ON a.id = r.aviso_id ORDER BY 1, 2")
    revisar("09-10. remates de la unión idénticos a los del rollo B solo", U.execute(Q2).fetchall() == SB.execute(Q2).fetchall())
    revisar("09-10. alerta de rol distinto entre cuerpos en el aviso 40 (C-38622025 en B, C-3862- 2025 en G)",
            [r[0] for r in U.execute("SELECT a.orden FROM alertas al JOIN avisos a ON a.id = al.aviso_id WHERE al.texto LIKE 'El cuerpo G imprime este rol distinto%'")] == [40])
    # CAMBIO del 18 de Octubre (decisión de Diego, opción C). El aviso 120 era una falsa alarma de dos avisos pegados ("según resolución
    # del 4 de septiembre de 2026"). Ahora se lee entero y queda con su causa. Lo de "rol sin tribunal se guarda sin causa" se revisa
    # más abajo con el 01-09 aviso 29 ("DÉCIMO SÉPTIMO CIVIL de Santiago", sin la palabra juzgado).
    revisar("09-10. aviso 120 (rol C-22836-2024) ya no es falso pegado. Queda con su causa del 30° Civil y sin alerta de tribunal",
            U.execute("SELECT a.causa_id IS NOT NULL, a.tribunal, (SELECT COUNT(*) FROM alertas al WHERE al.aviso_id = a.id AND al.texto LIKE 'El aviso tiene rol%') "
                      "FROM avisos a WHERE a.orden = 120").fetchone() == (1, "30° Juzgado Civil de Santiago", 0))

    # Parte 3.7b (17 de Octubre). 01-09, 26 remates del rol C-5656-2013 (28° Civil). Antes quedaban unidos por fecha y hora
    # con la alerta "No se pudo distinguir". La inscripción en el Conservador los separa (decisión de Diego, solo para saber
    # qué propiedad es cuál). Copiado de capturas al banco el 17 de Octubre (HUELLAS_ESPERADAS.txt).
    D01 = RAIZ / "banco_pruebas" / "2026-09-01"
    S = crear(Path(tmp) / "s01.db")
    cargar_edicion(S, "2026-09-01", "2026-10-17T00:00:00", D01, usar_ia=False)
    c5656 = S.execute("SELECT COUNT(*), COUNT(DISTINCT r.bien_id), SUM(b.clave LIKE '%|fojas %') FROM remates r JOIN avisos a ON a.id = r.aviso_id "
                      "JOIN bienes b ON b.id = r.bien_id WHERE a.rol = '5656' AND a.anio = '2013'").fetchone()
    revisar("3.7b. 01-09. los 26 remates del C-5656-2013 quedan en 26 bienes distintos, cada uno por su inscripción", c5656 == (26, 26, 26), str(c5656))
    revisar("3.7b. 01-09. ninguna alerta de remate que no se pudo distinguir (antes 26)",
            uno(S, "SELECT COUNT(*) FROM alertas WHERE texto LIKE 'No se pudo distinguir%'") == 0)
    revisar("01-09. aviso 29 con rol y sin tribunal se guarda sin causa y con alerta (antes rompía la carga, caso movido desde el 09-10 el 18 de Octubre)",
            S.execute("SELECT a.causa_id IS NULL, COUNT(al.id) FROM avisos a JOIN alertas al ON al.aviso_id = a.id "
                      "WHERE a.orden = 29 AND al.texto LIKE 'El aviso tiene rol (1455-2023) pero no se encontró el tribunal%'").fetchone() == (1, 1))
    revisar("3.7b. 01-09. lote 44 del aviso 44 con su inscripción de La Serena",
            uno(S, "SELECT b.clave FROM remates r JOIN avisos a ON a.id = r.aviso_id JOIN bienes b ON b.id = r.bien_id WHERE a.orden = 44").endswith("|fojas 7694 n 6390 2009"))
    # 09-10. C-15288-2025 del 20° Civil, dos avisos (11:00 y 13:00) que la inscripción separa
    revisar("3.7b. 09-10. los dos remates del C-15288-2025 por su inscripción",
            sorted(x[0].split("|")[-1] for x in U.execute("SELECT b.clave FROM remates r JOIN avisos a ON a.id = r.aviso_id JOIN bienes b ON b.id = r.bien_id WHERE a.rol = '15288'"))
            == ["fojas 28638 n 41285 2017", "fojas 44321 n 64342 2023 + fojas 44321 n 64343 2023"])
    revisar("3.7b. 09-10. aviso 87 separado en sus 3 departamentos (antes quedaba con alerta de mínimos sin asignar)",
            [x[0] for x in U.execute("SELECT r.inmueble FROM remates r JOIN avisos a ON a.id = r.aviso_id WHERE a.orden = 87 ORDER BY r.sub_orden")]
            == ["departamento 3044", "departamento 204", "departamento 202"])
    S.close()

    # unir_rollos con casos hechos a mano. Repeticiones contadas y aviso que solo está en G.
    def av(orden, texto, pag, rol_imp="Rol C-1-2020"):
        return Aviso(orden=orden, texto=texto, inicio=0, paginas=[pag], rol_impreso=rol_imp)
    # B trae "dos" una vez y G dos veces. La segunda copia de G no tiene gemelo y debe agregarse (repeticiones contadas).
    b_ = [av(1, "REMATE uno, Rol C-1-2020.", "B1"), av(2, "REMATE dos igual.", "B1")]
    g_ = [av(1, "REMATE  uno,  Rol C-1-2020.", "G1"), av(2, "REMATE dos igual.", "G1"), av(3, "REMATE dos igual.", "G1"), av(4, "REMATE solo en G.", "G2")]
    todos, alertas, resumen = unir_rollos([b_, g_])
    revisar("unir_rollos. la copia de más y el aviso solo en G se agregan al final, en orden",
            [a.texto for a in todos] == ["REMATE uno, Rol C-1-2020.", "REMATE dos igual.", "REMATE dos igual.", "REMATE solo en G."] and [a.orden for a in todos] == [1, 2, 3, 4])
    revisar("unir_rollos. los dos agregados llevan alerta", all(any("solo aparece en el cuerpo G" in t for _, t in alertas.get(k, [])) for k in (3, 4)))
    revisar("unir_rollos. resumen", resumen == ["Cuerpo G repite al B. 2 de 4 avisos unidos por huella del texto. 1 con diferencias de espacios. 2 solo en G."], str(resumen))
    A.close(); B.close(); U.close(); SB.close()

    # Sincronización (18 de Octubre, aprobado por Diego). Franja negra si falta la edición de hoy o un día reciente,
    # franja ámbar si una edición reciente quedó incompleta. Y una edición sin remates queda anotada, no se pierde.
    from motor.sincronizacion import estado_sincronizacion
    from motor.procesar_edicion import SIN_REMATES, VV_ALARMA
    Z = crear(Path(tmp) / "sinc.db")
    revisar("sincronización. base vacía", estado_sincronizacion(Z, "2026-10-14")["franja_negra"] == ["SIN SINCRONIZAR. La base no tiene ninguna edición cargada."])
    for f in ("2026-10-13", "2026-10-14"):
        cargar_edicion(Z, f, "x", RAIZ / "banco_pruebas" / f, usar_ia=False)
    e = estado_sincronizacion(Z, "2026-10-14")
    revisar("sincronización. al día con el 13 y el 14 (los días antes de la primera edición no cuentan)", e["al_dia"] and e["faltan"] == [], str(e))
    e = estado_sincronizacion(Z, "2026-10-16")
    revisar("sincronización. faltan el 15 y hoy 16, con el día escrito", e["faltan"] == ["2026-10-15", "2026-10-16"] and e["franja_negra"] == [
        "SIN SINCRONIZAR. La última edición cargada es la del miércoles 14 de Octubre de 2026.",
        "Falta la edición del jueves 15 de Octubre de 2026.", "Falta la edición de hoy, viernes 16 de Octubre de 2026."], str(e["franja_negra"]))
    # Edición sin la sección de remates. Captura hecha a mano copiando el navegacion.json del 14 sin rollos.
    d15 = Path(tmp) / "2026-10-15"; d15.mkdir()
    nav = json.loads((RAIZ / "banco_pruebas" / "2026-10-14" / "navegacion.json").read_text(encoding="utf-8"))
    nav.update(fecha="2026-10-15", rollos=[], paginas_con_remates=[], alarmas=[])
    (d15 / "navegacion.json").write_text(json.dumps(nav, ensure_ascii=False), encoding="utf-8")
    cargar_edicion(Z, "2026-10-15", "x", d15, usar_ia=False)
    revisar("sin remates. la edición queda anotada con alarma y sin avisos",
            Z.execute("SELECT estado, alarmas, avisos_extraidos FROM ediciones WHERE fecha = '2026-10-15'").fetchone() == ("con_alarmas", SIN_REMATES, 0))
    e = estado_sincronizacion(Z, "2026-10-15")
    revisar("sin remates. no cuenta como día sin sincronizar, pero sale en la franja ámbar",
            e["faltan"] == [] and e["franja_negra"] == [] and e["franja_ambar"] == [f"La edición del jueves 15 de Octubre de 2026 está cargada pero incompleta. {SIN_REMATES}"], str(e))
    with Z:
        Z.execute("UPDATE ediciones SET estado = 'con_alarmas', alarmas = ? WHERE fecha = '2026-10-14'",
                  ("Cuerpo G repite al B. 1 de 1 avisos unidos.\n" + VV_ALARMA + "2 de 61 avisos quedaron sin leer por la IA. Se puede retomar sin volver a leer el Mercurio.",))
    e = estado_sincronizacion(Z, "2026-10-15")
    revisar("incompleta. el vale vista sin leer sale en ámbar y la alarma de la unión de rollos no",
            e["franja_ambar"][0] == "La edición del miércoles 14 de Octubre de 2026 está cargada pero incompleta. Vale vista. 2 de 61 avisos quedaron sin leer por la IA. Se puede retomar sin volver a leer el Mercurio."
            and len(e["franja_ambar"]) == 2, str(e["franja_ambar"]))
    Z.close()

print("\nRESULTADO.", "TODO OK" if not FALLAS else f"{len(FALLAS)} fallas")
sys.exit(1 if FALLAS else 0)

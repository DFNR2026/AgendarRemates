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
    revisar("citas del motor con método codigo y todas encontradas en su aviso",
            B.execute("SELECT metodo, COUNT(*), SUM(verificada) FROM citas GROUP BY metodo").fetchall() == [("codigo", 315, 315)])
    revisar("citas del banco siguen con método ia", A.execute("SELECT DISTINCT metodo FROM citas").fetchall() == [("ia",)])
    revisar("65 alertas de vale vista NO LEÍDO en el motor y ninguna que diga que el aviso no lo dice",
            (uno(B, f"SELECT COUNT(*) FROM alertas WHERE texto = '{VV_NO_LEIDO}'"), uno(B, f"SELECT COUNT(*) FROM alertas WHERE texto = '{VV_NO_DICE}'")) == (65, 0))
    revisar("el banco sigue diciendo que el aviso no lo dice (9 remates)", uno(A, f"SELECT COUNT(*) FROM alertas WHERE texto = '{VV_NO_DICE}'") == 9)
    revisar("alertas del código guardadas con su tipo y origen codigo",
            uno(B, "SELECT COUNT(*) FROM alertas WHERE tipo = 'condicion_especial' AND origen = 'codigo'") == 12
            and uno(B, "SELECT COUNT(*) FROM alertas WHERE origen = 'ia'") == 0)
    revisar("garantía 20% del aviso 43 avisada", uno(B, "SELECT COUNT(*) FROM alertas al JOIN avisos a ON a.id = al.aviso_id WHERE a.orden = 43 AND al.texto LIKE 'Garantía del 20%%'") == 1)

    # Viernes 2026-10-09. Cuerpos B (3 páginas) y G (8 páginas) con los mismos 127 avisos. Se unen sin duplicar por huella.
    # Copiados de capturas al banco el 2026-10-16 (HUELLAS_ESPERADAS.txt). Ver bitácora del 16.
    D09 = RAIZ / "banco_pruebas" / "2026-10-09"
    U = crear(Path(tmp) / "union.db")
    res = cargar_edicion(U, "2026-10-09", "2026-10-16T00:00:00", D09)
    revisar("09-10. 127 avisos y 128 remates (no 254)", (res["avisos"], res["remates"]) == (127, 128), str(res))
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
    revisar("09-10. aviso 120 con rol y sin tribunal se guarda sin causa y con alerta (antes rompía la carga)",
            U.execute("SELECT a.causa_id IS NULL, COUNT(al.id) FROM avisos a JOIN alertas al ON al.aviso_id = a.id "
                      "WHERE a.orden = 120 AND al.texto LIKE 'El aviso tiene rol (22836-2024) pero no se encontró el tribunal%'").fetchone() == (1, 1))

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

print("\nRESULTADO.", "TODO OK" if not FALLAS else f"{len(FALLAS)} fallas")
sys.exit(1 if FALLAS else 0)

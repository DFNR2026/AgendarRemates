"""Prueba de la unión motor -> base (paso 4 del ESTADO, 16 de Octubre). Solo código, sin internet. No toca agendar_remates.db.
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_procesar_edicion

Carga el 14 de Octubre dos veces en bases de prueba, una desde el banco nivel 2 (anotado a mano) y otra desde el motor
(cortador + extraer() + traducir()), y compara remate por remate. Las únicas diferencias permitidas son las explicadas
en la bitácora del 16 (plataforma Zoom que el banco no tenía, partidores sin tribunal, vacíos ya conocidos de los avisos
55 y 61, y el inmueble escrito corto). Todo lo demás debe ser igual.
"""
import json, sys, tempfile
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from db.crear_base import crear
from db.cargar_banco import cargar, datos_banco
from db.carga import guardar_edicion, normalizar, VV_NO_LEIDO, VV_NO_DICE
from motor.procesar_edicion import extraer_avisos, desde_captura

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

    # Edición con dos rollos (B y G los viernes). Se rechaza sin cargar nada.
    d = Path(tmp) / "dos_rollos"; d.mkdir()
    (d / "navegacion.json").write_text(json.dumps({"rollos": [["B11"], ["G5"]], "paginas_con_remates": []}), encoding="utf-8")
    try:
        desde_captura("2026-10-09", d); rechazada = False
    except ValueError as e:
        rechazada = "2 rollos" in str(e)
    revisar("una edición con dos rollos se rechaza", rechazada)
    A.close(); B.close()

print("\nRESULTADO.", "TODO OK" if not FALLAS else f"{len(FALLAS)} fallas")
sys.exit(1 if FALLAS else 0)

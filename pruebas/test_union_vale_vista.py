"""Parte 3.7a. Prueba SIN internet de la unión del vale vista a la carga (diseño aprobado, bitácora del 16, punto 42).
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_union_vale_vista
Usa los avisos del banco del 14 de Octubre (en git, idénticos letra por letra a los de capturas\\2026-10-14, verificado el
16 de Octubre) y las respuestas guardadas de Haiku en ia_respuestas\\vale_vista. No toca agendar_remates.db.
"""
import sys, tempfile
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from db.crear_base import crear
from db.cargar_banco import datos_banco
from db.carga import guardar_edicion
from motor.procesar_edicion import extraer_avisos

FALLAS = []
def revisar(nombre, condicion, detalle=""):
    print(("OK    " if condicion else "FALLA ") + nombre, detalle)
    if not condicion: FALLAS.append(nombre)

# Candado (17 de Octubre). Esta prueba NUNCA debe llamar a Haiku ni escribir respuestas en ia_respuestas.
CARPETA_IA = RAIZ / "ia_respuestas" / "vale_vista"
respuestas_al_inicio = sorted(x.name for x in CARPETA_IA.glob("*.json"))

edicion, paginas, avisos, _ = datos_banco()
texto = {a.orden: a.texto for a in avisos}
tmp = tempfile.TemporaryDirectory()
uno = lambda con, sql, p=(): con.execute(sql, p).fetchone()[0]

# --- Paso 1. Método por dato. Un bloque con 'metodo' manda sobre el método de la edición ------------------------------
ex = extraer_avisos(avisos, "2026-10-14")
frase = "deberá ser entregado hasta las 14:00 horas del día hábil anterior a la subasta"
revisar("paso 1. la frase de prueba está en el aviso 1", frase in texto[1])
ex[1]["vale_vista"] = {"metodo": "ia", "regla": "dias_habiles_antes", "cita": frase, "citas_extra": [frase]}
C1 = crear(Path(tmp.name) / "paso1.db")
guardar_edicion(C1, edicion, paginas, avisos, ex, "2026-10-16T00:00:00", metodo="codigo")
revisar("paso 1. las 2 citas del vale vista del aviso 1 van con método ia y verificadas",
        C1.execute("SELECT c.metodo, COUNT(*), SUM(c.verificada) FROM citas c JOIN avisos a ON a.id = c.aviso_id "
                   "WHERE a.orden = 1 AND c.campo = 'vv_regla_texto' GROUP BY c.metodo").fetchall() == [("ia", 2, 2)])
# Desde la parte 3.7b (17 de Octubre) el código agrega también las citas de la inscripción (campo inscripcion, 67 en el
# 14-10). Se cuentan aparte para que las 315 de la 3.6 sigan comparándose igual.
revisar("paso 1. las 315 citas del código siguen con método codigo (más las 67 de la inscripción)",
        uno(C1, "SELECT COUNT(*) FROM citas WHERE metodo = 'codigo' AND campo NOT IN ('vv_regla_texto', 'inscripcion', 'caratulado')") == 315
        and uno(C1, "SELECT COUNT(*) FROM citas WHERE metodo = 'codigo' AND campo = 'inscripcion'") == 67
        and uno(C1, "SELECT COUNT(*) FROM citas WHERE metodo = 'ia'") == 2)
C1.close()

# --- Paso 2. Las alertas del bloque del vale vista reemplazan a la alerta por defecto ----------------------------------
from db.carga import VV_NO_LEIDO, VV_NO_DICE
ex = extraer_avisos(avisos, "2026-10-14")
ex[1]["vale_vista"] = {"metodo": "ia", "alertas": []}                                  # verde, sin alertas
ex[30]["vale_vista"] = {"metodo": "ia", "alertas": [("revisar_lectura", "Prueba rojo", "cita x")]}   # 4 lotes
C2 = crear(Path(tmp.name) / "paso2.db")
guardar_edicion(C2, edicion, paginas, avisos, ex, "2026-10-16T00:00:00", metodo="codigo")
por_aviso = lambda n: C2.execute("SELECT al.sub_orden, al.tipo, al.texto, al.cita FROM alertas al JOIN avisos a ON a.id = al.aviso_id "
                                 "WHERE a.orden = ? AND (al.texto LIKE '%vale vista%' OR al.texto = 'Prueba rojo') ORDER BY 1", (n,)).fetchall()
revisar("paso 2. aviso 1 con lista vacía no lleva alerta de vale vista", por_aviso(1) == [])
revisar("paso 2. aviso 30 lleva la alerta del bloque en cada uno de sus 4 lotes y ninguna por defecto",
        por_aviso(30) == [(k, "revisar_lectura", "Prueba rojo", "cita x") for k in (1, 2, 3, 4)], str(por_aviso(30)))
revisar("paso 2. los otros 60 remates siguen con la alerta de vale vista no leído y ninguno con 'el aviso no lo dice'",
        (uno(C2, "SELECT COUNT(*) FROM alertas WHERE texto = ?", (VV_NO_LEIDO,)), uno(C2, "SELECT COUNT(*) FROM alertas WHERE texto = ?", (VV_NO_DICE,))) == (60, 0))
C2.close()

# --- Paso 3. Del resultado de resolver() al bloque con color y alertas (casos hechos a mano) -------------------------
from motor.procesar_edicion import bloque_vale_vista, VV_CONTRADICCION, VV_ERROR_ESCRITURA, texto_rojo as _texto_rojo
from motor.vale_vista import NO_ENCONTRADA
def res_(color, **k):
    r = {"regla": "dias_habiles_antes", "cita": "frase", "citas_extra": [], "vv_desde": "2026-10-15", "vv_desde_origen": "estimado_dia_siguiente_edicion",
         "vv_hasta": "2026-10-20 14:00", "vv_estado": "calculado", "color": color, "motivos": [], "preguntas": [], "contradiccion": None}
    r.update(k); return r
b = bloque_vale_vista(res_("verde"))
revisar("paso 3. verde = calculado, con fechas, método ia y sin alertas",
        (b["vv_estado"], b["vv_hasta"], b["metodo"], b["alertas"]) == ("calculado", "2026-10-20 14:00", "ia", []))
b = bloque_vale_vista(res_("ambar", vv_estado="revisar", preguntas=[2]))
revisar("paso 3. ámbar = revisar CON fechas y alerta condicion_especial de la pregunta 2",
        (b["vv_estado"], b["vv_hasta"]) == ("revisar", "2026-10-20 14:00")
        and b["alertas"] == [("condicion_especial", "Fecha del vale vista provisoria. Depende de la pregunta 2 al abogado.", "frase")], str(b["alertas"]))
b = bloque_vale_vista(res_("ambar", vv_estado="revisar", preguntas=[2, 3, 5]))
revisar("paso 3. ámbar con varias preguntas", b["alertas"][0][1] == "Fecha del vale vista provisoria. Depende de las preguntas 2, 3 y 5 al abogado.", b["alertas"][0][1])
b = bloque_vale_vista(res_("rojo", vv_estado="revisar", vv_desde=None, vv_hasta=None, motivos=["Las dos lecturas de la IA no coinciden."]))
revisar("paso 3. rojo = revisar SIN fechas y alerta revisar_lectura con el motivo",
        (b["vv_estado"], b["vv_desde"], b["vv_hasta"]) == ("revisar", None, None)
        and b["alertas"] == [("revisar_lectura", _texto_rojo(["Las dos lecturas de la IA no coinciden."]), "frase")]
        and b["alertas"][0][1].startswith("Falla de la IA. Las dos lecturas de la IA dieron reglas distintas."), str(b["alertas"]))
b = bloque_vale_vista(res_("rojo", vv_estado="revisar", vv_hasta="2026-10-20"))
revisar("paso 3. rojo nunca guarda fechas aunque vengan", (b["vv_desde"], b["vv_hasta"]) == (None, None))
b = bloque_vale_vista(res_("sin_dato", vv_estado="sin_dato", cita=None, vv_desde=None, vv_hasta=None))
revisar("paso 3. sin dato = sin_dato y alerta dato_faltante con el texto aprobado",
        b["vv_estado"] == "sin_dato" and b["alertas"] == [("dato_faltante", NO_ENCONTRADA, None)])
b = bloque_vale_vista(res_("rojo", vv_estado="revisar", vv_hasta=None, contradiccion="hasta las 12 hrs.",
                           motivos=["El aviso da dos plazos u horarios distintos para la entrega."]))
revisar("paso 3. contradicción real = alerta contradiccion con la segunda frase, además del rojo",
        [x[0] for x in b["alertas"]] == ["revisar_lectura", "contradiccion"] and b["alertas"][1] == ("contradiccion", VV_CONTRADICCION, "hasta las 12 hrs."))
b = bloque_vale_vista(res_("rojo", vv_estado="revisar", vv_hasta=None,
                           motivos=["La fecha de entrega es anterior a la edición. Posible error de escritura del aviso."]))
revisar("paso 3. vale vista pedido antes de la edición = alerta error_escritura", ("error_escritura", VV_ERROR_ESCRITURA, "frase") in b["alertas"])

# --- Paso 4. La unión completa con el 14 de Octubre y respuestas guardadas. Debe dar lo mismo que la medición ---------
from motor.procesar_edicion import agregar_vale_vista, cargar_edicion
from motor import vale_vista as V
from pruebas.medir_vale_vista import cargar as cargar_medicion, clasificar
_, _, _, esperado = cargar_medicion("14")
COLOR_BD = ("CASE WHEN r.vv_estado = 'calculado' THEN 'verde' WHEN r.vv_estado = 'revisar' AND r.vv_hasta IS NOT NULL THEN 'ambar' "
            "WHEN r.vv_estado = 'revisar' THEN 'rojo' WHEN r.vv_estado = 'sin_dato' THEN 'sin_dato' END")

def medir_base(con):
    """Clasifica cada aviso visible leyendo SOLO la base (color por las columnas, sin la columna color)."""
    cuenta, colores = {}, {}
    for orden, color, desde, hasta, regla in con.execute(
            f"SELECT a.orden, {COLOR_BD}, r.vv_desde, r.vv_hasta, r.vv_regla FROM remates r JOIN avisos a ON a.id = r.aviso_id "
            "WHERE a.filtro_estado <> 'descartado' AND r.sub_orden = 1 ORDER BY 1"):
        c = clasificar({"color": color, "vv_desde": desde, "vv_hasta": hasta, "regla": regla}, esperado[orden]) if color else "sin_bloque"
        cuenta[c] = cuenta.get(c, 0) + 1
        colores[color] = colores.get(color, 0) + 1
    return cuenta, colores

ex = extraer_avisos(avisos, "2026-10-14")
rv = agregar_vale_vista(avisos, ex, "2026-10-14")                 # cliente None. Solo respuestas guardadas
C4 = crear(Path(tmp.name) / "paso4.db")
r4 = guardar_edicion(C4, edicion, paginas, avisos, ex, "2026-10-16T00:00:00", metodo="codigo")
revisar("paso 4. 57 avisos leídos, 4 partidores saltados, 0 sin IA", (rv["leidos"], rv["saltados"], rv["sin_ia"]) == (57, 4, 0), str(rv))
cuenta, colores = medir_base(C4)
revisar("paso 4. desde la base. 53 aciertos, 4 no leídos (rojo), 0 equivocados, igual que la medición",
        cuenta == {"acierto": 53, "no_leido": 4}, str(cuenta))
revisar("paso 4. colores en la base iguales a los de resolver() (por aviso)", colores == rv["colores"], f"{colores} {rv['colores']}")
revisar("paso 4. 61 avisos visibles con bloque, ninguno se perdió", sum(colores.values()) == 57 and None not in colores)
revisar("paso 4. citas del vale vista con método ia y todas verificadas, las del código siguen con codigo",
        C4.execute("SELECT metodo, SUM(campo = 'vv_regla_texto') > 0, SUM(campo NOT IN ('vv_regla_texto', 'inscripcion', 'caratulado')), COUNT(*) = SUM(verificada) "
                   "FROM citas GROUP BY metodo ORDER BY metodo").fetchall() == [("codigo", 0, 315, 1), ("ia", 1, 0, 1)])
n_rem = lambda col: uno(C4, f"SELECT COUNT(*) FROM remates r JOIN avisos a ON a.id = r.aviso_id WHERE a.filtro_estado <> 'descartado' AND {COLOR_BD} = '{col}'")
GRUPO_SQL = " OR ".join(f"texto LIKE '{g}. %'" for g in ("Error del aviso", "Dudoso", "Límite del programa", "Regla nueva", "Falla de la IA"))
revisar("paso 4. una alerta revisar_lectura con grupo por cada remate en rojo",
        uno(C4, f"SELECT COUNT(*) FROM alertas WHERE tipo = 'revisar_lectura' AND ({GRUPO_SQL})") == n_rem("rojo") > 0)
rojos = dict(C4.execute(f"SELECT a.orden, al.texto FROM alertas al JOIN avisos a ON a.id = al.aviso_id WHERE al.tipo = 'revisar_lectura' AND ({GRUPO_SQL.replace('texto', 'al.texto')})").fetchall())
revisar("decisión 5, paso 2a. grupos de los 8 rojos del 14 de Octubre (9 error del aviso, los demás falla de la IA)",
        {k: v.split(". ")[0] for k, v in rojos.items()} == {2: "Falla de la IA", 9: "Error del aviso", 13: "Falla de la IA", 27: "Falla de la IA",
                                                           28: "Falla de la IA", 34: "Falla de la IA", 37: "Falla de la IA", 61: "Falla de la IA"},
        str({k: v.split(". ")[0] for k, v in rojos.items()}))
revisar("decisión 5, paso 2a. ninguna alerta roja muestra nombres internos (dia_anterior, en_el_remate, _)", not [v for v in rojos.values() if "_" in v])
revisar("paso 4. una alerta condicion_especial de pregunta al abogado por cada remate en ámbar",
        uno(C4, "SELECT COUNT(*) FROM alertas WHERE tipo = 'condicion_especial' AND texto LIKE 'Fecha del vale vista provisoria%'") == n_rem("ambar") > 0)
revisar("paso 4. una alerta dato_faltante de la IA por cada remate sin dato",
        uno(C4, "SELECT COUNT(*) FROM alertas WHERE tipo = 'dato_faltante' AND texto = ?", (NO_ENCONTRADA,)) == n_rem("sin_dato") > 0)
revisar("paso 4. contradicción real solo en el aviso 9 (de 11 a 14 y hasta las 12)",
        [x[0] for x in C4.execute("SELECT a.orden FROM alertas al JOIN avisos a ON a.id = al.aviso_id WHERE al.tipo = 'contradiccion'")] == [9])
revisar("paso 4. la alerta de vale vista no leído queda solo en los 4 remates de partidores (no se ven)",
        uno(C4, "SELECT COUNT(*) FROM alertas al JOIN avisos a ON a.id = al.aviso_id WHERE al.texto = ? AND a.filtro_estado = 'descartado'", (VV_NO_LEIDO,))
        == uno(C4, "SELECT COUNT(*) FROM alertas WHERE texto = ?", (VV_NO_LEIDO,)) == 4)
revisar("paso 4. ninguna alerta dice que el aviso no lo dice", uno(C4, "SELECT COUNT(*) FROM alertas WHERE texto = ?", (VV_NO_DICE,)) == 0)
revisar("paso 4. ningún rojo ni sin dato con fechas guardadas",
        uno(C4, "SELECT COUNT(*) FROM remates WHERE (vv_estado = 'sin_dato' OR (vv_estado = 'revisar' AND vv_hasta IS NULL)) AND vv_desde IS NOT NULL") == 0)
revisar("paso 4. los 4 lotes del aviso 30 con el mismo vale vista",
        uno(C4, "SELECT COUNT(DISTINCT coalesce(r.vv_hasta,'') || r.vv_estado) FROM remates r JOIN avisos a ON a.id = r.aviso_id WHERE a.orden = 30") == 1)
C4.close()

# Haiku no disponible. Sin respuestas guardadas y (a) sin cliente, (b) con un cliente que falla. No se cae nada.
class ClienteCaido:
    class messages:
        @staticmethod
        def create(**k): raise ConnectionError("sin internet (prueba)")
carpeta_real = V.CARPETA_RESPUESTAS
for nombre, cli in (("sin cliente", None), ("cliente que falla", ClienteCaido())):
    V.CARPETA_RESPUESTAS = Path(tmp.name) / f"vacia_{len(nombre)}"
    try:
        ex = extraer_avisos(avisos, "2026-10-14")
        rv = agregar_vale_vista(avisos, ex, "2026-10-14", cli)
        C5 = crear(Path(tmp.name) / f"caido_{len(nombre)}.db")
        r5 = guardar_edicion(C5, edicion, paginas, avisos, ex, "2026-10-16T00:00:00", metodo="codigo")
        revisar(f"Haiku no disponible ({nombre}). la carga no se cae y quedan las 65 alertas de vale vista no leído",
                (rv["sin_ia"], r5["remates"], uno(C5, "SELECT COUNT(*) FROM alertas WHERE texto = ?", (VV_NO_LEIDO,)),
                 uno(C5, "SELECT COUNT(*) FROM citas WHERE metodo = 'ia'")) == (57, 65, 65, 0), str(rv["errores"][:1]))
        revisar(f"Haiku no disponible ({nombre}). no se guardó ninguna respuesta", not V.CARPETA_RESPUESTAS.exists())
        C5.close()
    finally:
        V.CARPETA_RESPUESTAS = carpeta_real

# La misma unión desde capturas\2026-10-14 (lo que corre el programa). capturas está fuera de git, por eso es opcional.
if (RAIZ / "capturas" / "2026-10-14" / "navegacion.json").exists():
    C6 = crear(Path(tmp.name) / "captura.db")
    r6 = cargar_edicion(C6, "2026-10-14", "2026-10-16T00:00:00")
    revisar("captura 14-10. cargar_edicion da 53 aciertos, 4 no leídos, 0 equivocados", medir_base(C6)[0] == {"acierto": 53, "no_leido": 4}, str(r6.get("vale_vista")))
    C6.close()
else:
    print("AVISO capturas\\2026-10-14 no está en este equipo. Se omite la revisión desde la captura.")

# --- Paso 5. Si no se puede crear el cliente de Haiku, la línea de comandos sigue sin él ------------------------------
from motor.procesar_edicion import cliente_o_nada
original = V.cliente_desde_config
def sin_clave(): raise AttributeError("config.py sin ANTHROPIC_API_KEY (prueba)")
V.cliente_desde_config = sin_clave
try:
    cli, motivo = cliente_o_nada()
    revisar("paso 5. sin clave, cliente None y un aviso que lo dice", cli is None and motivo and "respuestas guardadas" in motivo, str(motivo))
finally:
    V.cliente_desde_config = original

# --- Decisión 5, paso 1. Cada motivo técnico del rojo en palabras simples (aprobado por Diego el 17 de Octubre) ---------
import re
from motor.procesar_edicion import traducir_motivo, texto_rojo, GRUPOS
IA, NUEVA, AVISO, DUDOSO, LIMITE = "Falla de la IA", "Regla nueva", "Error del aviso", "Dudoso", "Límite del programa"
CASOS = [  # (motivo técnico tal como lo escribe motor\vale_vista.py, grupo esperado, motivo simple esperado o None)
    ("Falta la hora del remate para contar las horas.", LIMITE, "El programa no encontró la hora del remate."),
    ("Regla otra sin cálculo.", LIMITE, None),
    ("La IA dice que la regla no calza con ninguna conocida.", NUEVA, None),
    ("Frase extra no encontrada en el aviso (si recayere en sábado).", IA, "La IA citó una frase que no está escrita así en el aviso."),
    ("La frase de contradicción no está en el aviso.", IA, "La IA citó una frase que no está escrita así en el aviso."),
    ("El aviso da dos plazos u horarios distintos para la entrega.", AVISO, None),
    ("La IA no encontró regla, pero el aviso parece dar un plazo (hasta las 14 horas).", IA, None),
    ("La frase de la regla no está en el aviso.", IA, "La IA citó una frase que no está escrita así en el aviso."),
    ("La IA no entregó la frase de la regla.", IA, "La IA citó una frase que no está escrita así en el aviso."),
    ("La frase habla de devolución o retiro, no de entrega.", IA, None),
    ("La frase no trae las palabras propias de la regla dias_habiles_antes.", IA, "La IA leyó una regla que no calza con las palabras del aviso."),
    ("La frase no trae las palabras propias de la regla en_el_remate.", IA, "La IA dijo que el vale vista se entrega en el remate, pero el aviso no lo dice."),
    ("La frase no dice que el vale vista se entregue en el remate (solo cuándo se califica).", IA, "La IA dijo que el vale vista se entrega en el remate, pero el aviso no lo dice."),
    ("La frase dice día hábil, no día anterior.", IA, "La IA leyó una regla que no calza con las palabras del aviso."),
    ("Faltan los días hábiles.", IA, "La IA leyó una regla que no calza con las palabras del aviso."),
    ("El número de días (3) no está en la frase.", IA, "La IA leyó una regla que no calza con las palabras del aviso."),
    ("Faltan las horas.", IA, "La IA leyó una regla que no calza con las palabras del aviso."),
    ("El número de horas (72) no está en la frase.", IA, "La IA leyó una regla que no calza con las palabras del aviso."),
    ("La fecha fija no está escrita en la frase.", IA, "La IA leyó una regla que no calza con las palabras del aviso."),
    ("hora_desde con formato inválido (25:00).", IA, "La IA leyó una regla que no calza con las palabras del aviso."),
    ("La hora 13:00 no está en la frase.", IA, "La IA leyó una regla que no calza con las palabras del aviso."),
    ("La hora desde no es anterior a la hora hasta.", IA, "La IA leyó una regla que no calza con las palabras del aviso."),
    ("Regla desconocida (lunes).", IA, None),
    ("Falta la segunda lectura de la IA.", IA, None),
    ("Las dos lecturas de la IA no coinciden.", IA, "Las dos lecturas de la IA dieron reglas distintas."),
    ("Falta la fecha del remate.", LIMITE, "El programa no encontró la fecha del remate."),
    ("La fecha del remate es anterior a la edición.", AVISO, "La fecha del remate ya pasó al publicarse."),
    ("No están cargados los feriados de 2027.", LIMITE, "Faltan los feriados de 2027."),
    ("La fecha de entrega es anterior a la edición. Posible error de escritura del aviso.", AVISO, "El aviso pide el vale vista en una fecha que ya pasó al publicarse."),
    ("La entrega quedaría después del remate.", DUDOSO, "El plazo de entrega quedaría después del remate."),
    ("La frase nombra un día de la semana distinto al que da el cálculo.", IA, None),
]
mal = []
for m, g, simple in CASOS:
    for pref in ("", "Segunda lectura. "):
        gg, ss = traducir_motivo(pref + m)
        if gg != g or (simple and ss != simple):
            mal.append(f"{pref}{m} -> {gg} | {ss}")
revisar("decisión 5. los 31 motivos técnicos (y con 'Segunda lectura') se traducen al grupo y texto aprobados", not mal, " || ".join(mal[:3]))
# Si alguien agrega un motivo nuevo en vale_vista.py, esta cuenta cambia y obliga a traducirlo y sumarlo a CASOS.
fuente = (RAIZ / "motor" / "vale_vista.py").read_text(encoding="utf-8")
n_fuente = len(re.findall(r'motivos"\]\.append\(|motivos\.append\(|motivo_rojo"\] = ', fuente))
revisar("decisión 5. vale_vista.py no tiene motivos nuevos sin traducir (29 lugares que escriben un motivo)", n_fuente == 29, str(n_fuente))
revisar("decisión 5. un motivo desconocido queda Dudoso con su texto, sin perderse", traducir_motivo("Algo nuevo.") == (DUDOSO, "Algo nuevo."))
t = texto_rojo(["La frase no trae las palabras propias de la regla en_el_remate.",
                "La frase no dice que el vale vista se entregue en el remate (solo cuándo se califica)."])
revisar("decisión 5. aviso 61. dos motivos con el mismo texto simple salen una sola vez",
        t == f"{IA}. La IA dijo que el vale vista se entrega en el remate, pero el aviso no lo dice. {GRUPOS[IA]}", t)
t = texto_rojo(["Las dos lecturas de la IA no coinciden.", "La entrega quedaría después del remate.", "El aviso da dos plazos u horarios distintos para la entrega."])
revisar("decisión 5. con varios grupos manda el más grave (Error del aviso)", t.startswith(f"{AVISO}. ") and t.endswith(GRUPOS[AVISO]), t[:80])
revisar("decisión 5. orden de gravedad aprobado", list(GRUPOS) == [AVISO, DUDOSO, LIMITE, NUEVA, IA])
textos = list(GRUPOS.values()) + [traducir_motivo(m)[1] for m, _, _ in CASOS]
revisar("decisión 5. ningún texto para Diego usa dos puntos ni punto y coma", not [x for x in textos if re.search(r"[:;]", x)])

# --- Decisión 5, paso 2b. Remate con fecha anterior a la edición = error_escritura (06-10 aviso 45, remate en 2025) -----
from motor.cortador import construir_rollo, cortar
from motor.orden_columnas import leer_pagina
D06 = RAIZ / "banco_pruebas" / "2026-10-06"
r06, m06 = construir_rollo([(n, leer_pagina(D06 / f"mercurio_2026-10-06_{n}.txt")) for n in ("B7", "B8", "B9", "B10")])
av06 = cortar(r06, m06)
ex06 = extraer_avisos(av06, "2026-10-06")
agregar_vale_vista(av06, ex06, "2026-10-06")
v45 = ex06[45].get("vale_vista") or {}
revisar("decisión 5, paso 2b. 06-10 aviso 45. rojo con grupo Error del aviso",
        v45.get("color") == "rojo" and v45["alertas"][0][1].startswith("Error del aviso. La fecha del remate ya pasó al publicarse."), str(v45.get("alertas"))[:200])
# Una sola alerta de error de escritura por la fecha pasada, la de la extracción (aprobado por Diego el 17 de Octubre, noche).
err45 = [t for k, t, *_ in ex06[45]["alertas"] + v45.get("alertas", []) if k == "error_escritura"]
revisar("06-10 aviso 45. una sola alerta de error de escritura por la fecha pasada, con las fechas en palabras",
        len(err45) == 1 and err45[0].startswith("La fecha del remate (") and "es anterior a la edición del diario (6 de Octubre de 2026)" in err45[0], str(err45))
revisar("ningún aviso del 06-10 lleva error de escritura de la fecha del remate desde el vale vista",
        not [o for o, x in ex06.items() if any(k == "error_escritura" and "fecha del remate" in t for k, t, *_ in (x.get("vale_vista") or {}).get("alertas", []))])

# --- Decisión 8, paso 3. Alarma de la edición cuando quedan avisos sin leer por la IA ------------------------------------
# 09-10 (B y G, en el banco con su navegacion.json). Solo parte de sus avisos tiene respuesta guardada, el resto queda sin IA.
from motor.procesar_edicion import alarma_vale_vista, VV_ALARMA
D09 = RAIZ / "banco_pruebas" / "2026-10-09"
C7 = crear(Path(tmp.name) / "alarma09.db")
r7 = cargar_edicion(C7, "2026-10-09", "2026-10-16T00:00:00", D09)
est, alarmas = C7.execute("SELECT estado, alarmas FROM ediciones").fetchone()
linea = alarma_vale_vista(r7["vale_vista"])
revisar("decisión 8, paso 3. 09-10 con avisos sin IA. edición con_alarmas y línea de vale vista al final, sin borrar la de la unión",
        # Desde la parte 3.7b (17 de Octubre) después de la línea del vale vista va la de la dirección. Antes se pedía que la
        # del vale vista fuera la última.
        est == "con_alarmas" and linea in alarmas.splitlines() and alarmas.splitlines()[-1].startswith("Dirección. ") and "127 de 127 avisos unidos" in alarmas
        and linea == f"{VV_ALARMA}{r7['vale_vista']['sin_ia']} de {r7['vale_vista']['sin_ia'] + r7['vale_vista']['leidos']} avisos quedaron sin leer por la IA. Se puede retomar sin volver a leer el Mercurio."
        and r7["vale_vista"]["sin_ia"] > 0, f"{est} | {linea}")
C7.close()
revisar("decisión 8, paso 3. sin avisos pendientes no hay alarma", alarma_vale_vista({"sin_ia": 0, "leidos": 57}) is None and alarma_vale_vista(None) is None)

# --- Decisión 8, paso 4. Retomar una edición ya cargada. Debe quedar IGUAL que si Haiku hubiera respondido en la carga ---
from motor.procesar_edicion import retomar_vale_vista
def foto(con):
    """Todo lo que toca el vale vista, sin ids internos."""
    q = lambda sql: sorted(con.execute(sql).fetchall(), key=repr)
    return {"remates": q("SELECT a.orden, r.sub_orden, r.vv_regla, r.vv_regla_texto, r.vv_desde, r.vv_desde_origen, r.vv_hasta, r.vv_estado "
                         "FROM remates r JOIN avisos a ON a.id = r.aviso_id"),
            "alertas": q("SELECT a.orden, al.sub_orden, al.tipo, al.texto, al.cita, al.origen FROM alertas al JOIN avisos a ON a.id = al.aviso_id"),
            "citas": q("SELECT a.orden, c.sub_orden, c.campo, c.n_cita, c.valor, c.cita, c.metodo, c.verificada FROM citas c JOIN avisos a ON a.id = c.aviso_id"),
            "edicion": q("SELECT estado, alarmas FROM ediciones")}

def cargar_sin_ia(ruta, fecha, carpeta=None, banco=False):
    """Simula que Haiku no respondió en ningún aviso (carpeta de respuestas vacía y sin cliente)."""
    V.CARPETA_RESPUESTAS = Path(tmp.name) / f"vacia_{ruta}"
    try:
        con = crear(Path(tmp.name) / ruta)
        if banco:
            ex = extraer_avisos(avisos, "2026-10-14"); agregar_vale_vista(avisos, ex, "2026-10-14")
            guardar_edicion(con, edicion, paginas, avisos, ex, "2026-10-16T00:00:00", metodo="codigo")
        else:
            cargar_edicion(con, fecha, "2026-10-16T00:00:00", carpeta)
        return con
    finally:
        V.CARPETA_RESPUESTAS = carpeta_real

# 14-10 (un aviso con 4 lotes, el 30). Carga sin IA y después retomar con las respuestas guardadas.
R14 = cargar_sin_ia("ret14.db", "2026-10-14", banco=True)
rr = retomar_vale_vista(R14, "2026-10-14")
F14 = crear(Path(tmp.name) / "fresca14.db")
ex = extraer_avisos(avisos, "2026-10-14"); agregar_vale_vista(avisos, ex, "2026-10-14")
guardar_edicion(F14, edicion, paginas, avisos, ex, "2026-10-16T00:00:00", metodo="codigo")
revisar("decisión 8, paso 4. 14-10 retomado queda igual que cargado con la IA (remates, alertas, citas y edición)", foto(R14) == foto(F14),
        str([k for k in foto(R14) if foto(R14)[k] != foto(F14)[k]]))
revisar("decisión 8, paso 4. 14-10 retomado da 53 aciertos, 4 no leídos, 0 equivocados", medir_base(R14)[0] == {"acierto": 53, "no_leido": 4}, str(rr))
antes = foto(R14); rr2 = retomar_vale_vista(R14, "2026-10-14")
revisar("decisión 8, paso 4. retomar dos veces no duplica nada", foto(R14) == antes and rr2["pendientes_antes"] == 0, str(rr2))

# 09-10 (B y G, alarma de la unión, aviso 120 pegado). Sin IA queda 121 de 121 pendientes, retomar deja lo mismo que la carga fresca.
R09 = cargar_sin_ia("ret09.db", "2026-10-09", D09)
revisar("decisión 8, paso 4. 09-10 cargado sin IA deja la alarma 121 de 121",
        "Vale vista. 121 de 121 avisos quedaron sin leer por la IA." in (R09.execute("SELECT alarmas FROM ediciones").fetchone()[0] or ""))
rr = retomar_vale_vista(R09, "2026-10-09")
F09 = crear(Path(tmp.name) / "fresca09.db"); cargar_edicion(F09, "2026-10-09", "2026-10-16T00:00:00", D09)
revisar("decisión 8, paso 4. 09-10 retomado queda igual que cargado con la IA (incluida la alarma de pendientes)", foto(R09) == foto(F09),
        str([k for k in foto(R09) if foto(R09)[k] != foto(F09)[k]]) + " " + str({k: rr[k] for k in ("pendientes_antes", "leidos", "sin_ia", "saltados")}))

# Haiku sigue caído al retomar. No cambia nada y no se cae.
R2 = cargar_sin_ia("ret_caido.db", "2026-10-14", banco=True)
antes = foto(R2)
V.CARPETA_RESPUESTAS = Path(tmp.name) / "vacia_otra_vez"
try:
    rr = retomar_vale_vista(R2, "2026-10-14", ClienteCaido())
finally:
    V.CARPETA_RESPUESTAS = carpeta_real
despues = foto(R2)
revisar("decisión 8, paso 4. con Haiku caído al retomar no cambian remates, alertas ni citas, y la edición queda con la alarma 57 de 57",
        all(despues[k] == antes[k] for k in ("remates", "alertas", "citas")) and rr["sin_ia"] == 57
        and despues["edicion"] == [("con_alarmas", "Vale vista. 57 de 57 avisos quedaron sin leer por la IA. Se puede retomar sin volver a leer el Mercurio.")],
        str(despues["edicion"]))
try:
    retomar_vale_vista(R2, "2030-01-01"); revisar("decisión 8, paso 4. edición que no está en la base da error claro", False)
except ValueError as e:
    revisar("decisión 8, paso 4. edición que no está en la base da error claro", "no está en la base" in str(e))
for c in (R14, F14, R09, F09, R2): c.close()

# --- Decisión 8, paso 5. Comando para retomar (en una base de prueba, sin cliente de Haiku en el shell) -----------------
import subprocess
ruta09 = Path(tmp.name) / "cli09.db"
V.CARPETA_RESPUESTAS = Path(tmp.name) / "vacia_cli"
try:
    C9 = crear(ruta09); cargar_edicion(C9, "2026-10-09", "2026-10-16T00:00:00", D09); C9.close()   # cerrada, Windows no borra un archivo abierto
finally:
    V.CARPETA_RESPUESTAS = carpeta_real
# UTF-8 de los dos lados (17 de Octubre). En Windows el comando escribía UTF-8 y la prueba leía con otra codificación,
# así "aprobación" llegaba como "aprobaciÃ³n" y la revisión de la base real fallaba sin que el comando hiciera nada malo.
import os
ENV_UTF8 = dict(os.environ, PYTHONIOENCODING="utf-8")
correr = lambda *a: subprocess.run([sys.executable, "-B", "-m", "motor.procesar_edicion", *a], cwd=RAIZ, capture_output=True,
                                   encoding="utf-8", errors="replace", env=ENV_UTF8, timeout=170)
sal = correr("--retomar", "2026-10-09", str(ruta09), "--solo-guardadas")
C8 = crear(ruta09)
esperado09 = r7["vale_vista"]          # carga del paso 3 con las mismas respuestas guardadas, sin cliente
revisar("decisión 8, paso 5. con --solo-guardadas el comando no crea el cliente de Haiku",
        "Solo respuestas guardadas. No se llama a Haiku." in sal.stdout and "cliente de Haiku" not in sal.stdout, sal.stdout[:200])
revisar("decisión 8, paso 5. el comando retoma el 09-10 y deja lo mismo que la carga con lo guardado",
        sal.returncode == 0 and f"'leidos': {esperado09['leidos']}" in sal.stdout
        and alarma_vale_vista(esperado09) in (C8.execute("SELECT alarmas FROM ediciones").fetchone()[0] or "").splitlines(),   # ya no es la última (3.7b)
        (sal.stdout + sal.stderr)[-200:])
C8.close()
sal = correr("--retomar", "2026-10-09", str(RAIZ / "agendar_remates.db"), "--solo-guardadas")
revisar("decisión 8, paso 5. el comando se niega a tocar la base real", "La base real espera la aprobación de Diego" in sal.stdout + sal.stderr)
sal = correr("--retomar", "2026-10-09", str(Path(tmp.name) / "no_existe.db"), "--solo-guardadas")
revisar("decisión 8, paso 5. base que no existe da error claro y no crea el archivo",
        "No existe la base" in sal.stdout + sal.stderr and not (Path(tmp.name) / "no_existe.db").exists())

# --- Paso 6. Banco de rojos (idea de Diego, aprobada el 17 de Octubre) -------------------------------------------------
import json
from motor.banco_rojos import registros_de_edicion, registrar
B14 = crear(Path(tmp.name) / "banco14.db")
ex = extraer_avisos(avisos, "2026-10-14"); agregar_vale_vista(avisos, ex, "2026-10-14")
guardar_edicion(B14, edicion, paginas, avisos, ex, "2026-10-16T00:00:00", metodo="codigo")
regs = registros_de_edicion(B14, "2026-10-14")
revisar("paso 6. 14-10 da 11 registros, los 8 rojos y los 3 sin dato",
        [(r["orden"], r["color"]) for r in regs] == [(2, "rojo"), (9, "rojo"), (13, "rojo"), (27, "rojo"), (28, "rojo"), (33, "sin_dato"),
                                                    (34, "rojo"), (37, "rojo"), (50, "sin_dato"), (59, "sin_dato"), (61, "rojo")], str([r["orden"] for r in regs]))
revisar("paso 6. el grupo del banco es el mismo de la alerta de la base",
        all(r["grupo"] == rojos[r["orden"]].split(". ")[0] for r in regs if r["color"] == "rojo"))
revisar("paso 6. cada registro trae texto, dos lecturas, motivos técnicos, huella, ruta y revisión vacía",
        all(r["texto"] and len(r["lecturas"]) == 2 and r["huella"] and r["ruta_pagina"] and r["revision"] == {} for r in regs)
        and all(r["motivos_tecnicos"] for r in regs if r["color"] == "rojo"))
CB = Path(tmp.name) / "banco_rojos"
x1 = registrar(regs, CB, "t1")
x2 = registrar(regs, CB, "t2")
lineas = (CB / "rojos_2026-10.jsonl").read_text(encoding="utf-8").splitlines()
revisar("paso 6. registrar dos veces no duplica", (x1["nuevos"], x2["nuevos"], x2["repetidos"], len(lineas)) == (11, 0, 11, 11), f"{x1} {x2} {len(lineas)}")
# El mismo texto en otra edición queda marcado como republicación de la primera
otra = [dict(r, edicion="2026-10-15") for r in regs[:2]]
x3 = registrar(otra, CB, "t3")
ult = [json.loads(l) for l in (CB / "rojos_2026-10.jsonl").read_text(encoding="utf-8").splitlines()][-2:]
revisar("paso 6. el mismo texto en otra edición queda como republicación de la primera",
        x3["republicaciones"] == 2 and all(u["republicacion_de"] == "2026-10-14" for u in ult)
        and all(json.loads(l)["republicacion_de"] is None for l in lineas), str(x3))
revisar("paso 6. el banco se escribe sin dos puntos ni punto y coma en los textos para Diego",
        not [s for r in regs for s in r["motivos_simples"] if ":" in s or ";" in s])
B14.close()

# Paso 6, comando. Desde la captura del 09-10 (en el banco) a un banco temporal, sin Haiku y sin tocar el banco real.
banco_real = RAIZ / "banco_rojos"
banco_real_antes = {p.name: p.stat().st_size for p in banco_real.glob("*.jsonl")}
CB2 = Path(tmp.name) / "banco_cli"
sal = subprocess.run([sys.executable, "-B", "-m", "motor.banco_rojos", "2026-10-09", "--desde-captura", str(D09), "--banco", str(CB2)],
                     cwd=RAIZ, capture_output=True, encoding="utf-8", errors="replace", env=ENV_UTF8, timeout=170)
reg09 = [json.loads(l) for p in CB2.glob("rojos_*.jsonl") for l in p.read_text(encoding="utf-8").splitlines()]
esperado_cli = sum(esperado09["colores"].get(c, 0) for c in ("rojo", "sin_dato"))
revisar("paso 6. el comando llena un banco desde la captura con los rojos y sin dato de la carga con lo guardado",
        sal.returncode == 0 and len(reg09) == esperado_cli > 0, f"{len(reg09)} {esperado_cli} {(sal.stdout + sal.stderr)[-150:]}")
revisar("paso 6. las pruebas no tocan el banco real", {p.name: p.stat().st_size for p in banco_real.glob("*.jsonl")} == banco_real_antes)

nuevas = sorted(set(x.name for x in CARPETA_IA.glob("*.json")) - set(respuestas_al_inicio))
revisar("candado. la prueba no escribió ninguna respuesta nueva en ia_respuestas (no llamó a Haiku)", not nuevas, str(nuevas[:3]))

print("\nRESULTADO.", "TODO OK" if not FALLAS else f"{len(FALLAS)} fallas")
tmp.cleanup()
sys.exit(1 if FALLAS else 0)

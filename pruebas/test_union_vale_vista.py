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
revisar("paso 1. las 315 citas del código siguen con método codigo",
        uno(C1, "SELECT COUNT(*) FROM citas WHERE metodo = 'codigo' AND campo <> 'vv_regla_texto'") == 315
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
from motor.procesar_edicion import bloque_vale_vista, VV_ROJO, VV_CONTRADICCION, VV_ERROR_ESCRITURA
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
        and b["alertas"] == [("revisar_lectura", VV_ROJO + " Las dos lecturas de la IA no coinciden.", "frase")], str(b["alertas"]))
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
        C4.execute("SELECT metodo, SUM(campo = 'vv_regla_texto') > 0, SUM(campo <> 'vv_regla_texto'), COUNT(*) = SUM(verificada) "
                   "FROM citas GROUP BY metodo ORDER BY metodo").fetchall() == [("codigo", 0, 315, 1), ("ia", 1, 0, 1)])
n_rem = lambda col: uno(C4, f"SELECT COUNT(*) FROM remates r JOIN avisos a ON a.id = r.aviso_id WHERE a.filtro_estado <> 'descartado' AND {COLOR_BD} = '{col}'")
revisar("paso 4. una alerta revisar_lectura de la IA por cada remate en rojo",
        uno(C4, "SELECT COUNT(*) FROM alertas WHERE tipo = 'revisar_lectura' AND texto LIKE ?", (VV_ROJO + "%",)) == n_rem("rojo") > 0)
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

print("\nRESULTADO.", "TODO OK" if not FALLAS else f"{len(FALLAS)} fallas")
tmp.cleanup()
sys.exit(1 if FALLAS else 0)

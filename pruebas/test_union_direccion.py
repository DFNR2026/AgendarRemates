"""Parte 3.7b. Unión de la dirección leída por la IA con la carga, sin internet. No llama a Haiku. No toca agendar_remates.db.
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_union_direccion

14 de Octubre desde el banco con las respuestas guardadas (dir-2). Dirección y comuna por remate, citas con método ia,
alerta roja con las dos lecturas y la frase del aviso, la IA fuera de la clave del bien, alarma y retomar.
"""
import sys, tempfile
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from db.crear_base import crear
from db.cargar_banco import datos_banco
from db.carga import guardar_edicion, DIR_NO_LEIDA, identidad_inmueble
from motor.procesar_edicion import extraer_avisos, agregar_vale_vista, agregar_direccion, retomar_direccion, alarma_direccion, DIR_ALARMA
from motor import direccion as DR

FALLAS = []
def revisar(nombre, condicion, detalle=""):
    print(("OK    " if condicion else "FALLA ") + nombre, detalle)
    if not condicion: FALLAS.append(nombre)

antes = sorted(p.name for p in (RAIZ / "ia_respuestas").rglob("*.json"))
tmp = tempfile.TemporaryDirectory()
edicion, paginas, avisos, _ = datos_banco()
uno = lambda con, sql: con.execute(sql).fetchone()[0]


def cargar(nombre, con_direccion=True, carpeta=None):
    con = crear(Path(tmp.name) / nombre)
    ex = extraer_avisos(avisos, "2026-10-14"); agregar_vale_vista(avisos, ex, "2026-10-14")
    real = DR.CARPETA_RESPUESTAS
    if carpeta: DR.CARPETA_RESPUESTAS = carpeta
    try:
        dr = agregar_direccion(avisos, ex, "2026-10-14") if con_direccion else None
    finally:
        DR.CARPETA_RESPUESTAS = real
    ed = dict(edicion)
    if dr and alarma_direccion(dr):
        ed = dict(ed, estado="con_alarmas", alarmas="\n".join(x for x in (ed.get("alarmas"), alarma_direccion(dr)) if x))
    guardar_edicion(con, ed, paginas, avisos, ex, "2026-10-17T00:00:00", metodo="codigo")
    return con, dr


C, dr = cargar("dir14.db")
# 21 de Octubre. Decisión de Diego, tribunales no civiles descartados. Salen el 56 y el 61 del 14-10 (Cobranza Laboral), los dos
# con dirección verde en el código anterior. Antes 57 leídos, 4 saltados, 56 verdes, 60 remates con dirección y 61 alertas sin Haiku.
revisar("14-10. 55 avisos leídos con lo guardado, 6 saltados (4 partidores y 2 de Cobranza Laboral), ninguno sin IA", (dr["leidos"], dr["saltados"], dr["sin_ia"]) == (55, 6, 0), str(dr["colores"]))
revisar("14-10. colores por aviso 54 verde y 1 rojo (el 26)", dr["colores"] == {"verde": 54, "rojo": 1}, str(dr["colores"]))
n_dir = uno(C, "SELECT COUNT(*) FROM remates r JOIN avisos a ON a.id = r.aviso_id WHERE a.filtro_estado <> 'descartado' AND r.direccion IS NOT NULL")
revisar("14-10. 58 remates visibles con dirección (59 menos el rojo)", n_dir == 58, str(n_dir))
revisar("14-10. aviso 1 con dirección y comuna", C.execute("SELECT r.direccion, r.comuna FROM remates r JOIN avisos a ON a.id = r.aviso_id WHERE a.orden = 1").fetchone()
        == ("calle Santiago Bueras 3951", "Peñaflor"))
lotes = [x for x in C.execute("SELECT r.direccion FROM remates r JOIN avisos a ON a.id = r.aviso_id WHERE a.orden = 30 ORDER BY r.sub_orden")]
revisar("14-10. aviso 30, cada lote con su casa", [x[0] for x in lotes] == ["calle Maipú 636, casa 1", "calle Maipú 636, casa 3", "calle Maipú 636, casa 5", "calle Maipú 636, estacionamiento 6"], str(lotes))
revisar("14-10. aviso 21 sin calle guarda la frase del aviso como descripción",
        uno(C, "SELECT r.direccion FROM remates r JOIN avisos a ON a.id = r.aviso_id WHERE a.orden = 21").startswith("Propiedad correspondiente al Lote número Dos"))
r26 = C.execute("SELECT r.direccion, al.texto, al.cita FROM remates r JOIN avisos a ON a.id = r.aviso_id JOIN alertas al ON al.aviso_id = a.id "
                "WHERE a.orden = 26 AND al.tipo = 'revisar_lectura' AND al.texto LIKE 'Falla de la IA. Las dos lecturas de la IA dieron direcciones%'").fetchone()
revisar("14-10. aviso 26 en rojo. dirección vacía y alerta con las dos lecturas y la frase del aviso",
        r26 is not None and r26[0] is None and " y la otra " in r26[1] and "En el aviso aparece así 'Calle Pedrales N° 01867'" in r26[1], str(r26)[:300])
citas = C.execute("SELECT metodo, COUNT(*), SUM(verificada) FROM citas WHERE campo = 'direccion' GROUP BY metodo").fetchall()
revisar("14-10. citas de la dirección con método ia y todas encontradas en su aviso", len(citas) == 1 and citas[0][0] == "ia" and citas[0][1] == citas[0][2] > 60, str(citas))
revisar("14-10. ninguna alerta de dirección no leída", uno(C, f"SELECT COUNT(*) FROM alertas WHERE texto = '{DIR_NO_LEIDA}'") == 0)

# La IA nunca entra en la clave del bien (decisión del diseño de la 3.7b)
S, _ = cargar("sin_dir14.db", con_direccion=False)
QB = "SELECT a.orden, r.sub_orden, b.clave FROM remates r JOIN avisos a ON a.id = r.aviso_id JOIN bienes b ON b.id = r.bien_id ORDER BY 1, 2"
revisar("las claves de bien son las mismas con y sin la dirección de la IA", C.execute(QB).fetchall() == S.execute(QB).fetchall())
revisar("identidad_inmueble no usa una dirección leída por la IA", identidad_inmueble(None, {"direccion": {"metodo": "ia", "valor": "calle X 1"}}) == ""
        and identidad_inmueble(None, {"direccion": {"valor": "calle X 1"}}, sin_rol=True) == "calle x 1")

# Sin Haiku (carpeta vacía y sin cliente). Alerta por remate, alarma de la edición y retomar con lo guardado.
V, drv = cargar("vacia14.db", carpeta=Path(tmp.name) / "vacia")
revisar("sin Haiku. 55 avisos quedan sin leer, la carga no se cae", drv["sin_ia"] == 55 and drv["leidos"] == 0, str(drv["sin_ia"]))
revisar("sin Haiku. una alerta de dirección no leída por remate visible (59)", uno(V, f"SELECT COUNT(*) FROM alertas WHERE texto = '{DIR_NO_LEIDA}'") == 59)
al = uno(V, "SELECT alarmas FROM ediciones") or ""
revisar("sin Haiku. alarma de la edición", f"{DIR_ALARMA}55 de 55 avisos quedaron sin leer por la IA. Se puede retomar sin volver a leer el Mercurio." in al, al)
rr = retomar_direccion(V, "2026-10-14")
def foto(con):
    q = lambda sql: sorted(con.execute(sql).fetchall(), key=repr)
    return {"remates": q("SELECT a.orden, r.sub_orden, r.direccion, r.comuna FROM remates r JOIN avisos a ON a.id = r.aviso_id"),
            "alertas": q("SELECT a.orden, al.sub_orden, al.tipo, al.texto, al.cita FROM alertas al JOIN avisos a ON a.id = al.aviso_id"),
            "citas": q("SELECT a.orden, c.sub_orden, c.campo, c.n_cita, c.valor, c.cita, c.metodo, c.verificada FROM citas c JOIN avisos a ON a.id = c.aviso_id"),
            "edicion": q("SELECT estado, alarmas FROM ediciones")}
fv, fc = foto(V), foto(C)
revisar("retomar. queda igual que la carga con la IA (remates, alertas, citas y edición)", fv == fc, str([k for k in fv if fv[k] != fc[k]]) + " " + str(rr)[:120])
fa = foto(V); rr2 = retomar_direccion(V, "2026-10-14")
revisar("retomar dos veces no duplica nada", foto(V) == fa and rr2["pendientes_antes"] == 0, str(rr2)[:120])
# Banco de rojos de la dirección (archivo aparte dir_rojos_AAAA-MM.jsonl, nunca el banco real en la prueba)
from motor.banco_rojos import registros_direccion, registrar
regs = registros_direccion(C, "2026-10-14")
revisar("banco de rojos. 14-10 da 1 registro de dirección (aviso 26, Falla de la IA)", [(r["orden"], r["grupo"]) for r in regs] == [(26, "Falla de la IA")], str([(r["orden"], r["grupo"]) for r in regs]))
bt = Path(tmp.name) / "banco_temporal"
r1, r2 = registrar(regs, bt, prefijo="dir_rojos"), registrar(regs, bt, prefijo="dir_rojos")
revisar("banco de rojos. va en dir_rojos_2026-10.jsonl y no se duplica", r1["nuevos"] == 1 and r2["repetidos"] == 1 and [p.name for p in bt.glob("*.jsonl")] == ["dir_rojos_2026-10.jsonl"])
for con in (C, S, V): con.close()
tmp.cleanup()

despues = sorted(p.name for p in (RAIZ / "ia_respuestas").rglob("*.json"))
revisar("candado. la prueba no escribió ninguna respuesta nueva en ia_respuestas (no llamó a Haiku)", antes == despues, str(sorted(set(despues) - set(antes)))[:200])
print("\nRESULTADO.", "TODO OK" if not FALLAS else f"{len(FALLAS)} fallas")
sys.exit(1 if FALLAS else 0)

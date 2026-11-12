"""Prueba 17. Interfaz (18 de Octubre). Datos de la página, acciones de Diego y el servidor local, sin internet ni Haiku.
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_interfaz
Carga en una base temporal las 7 ediciones del banco con las respuestas guardadas. Hoy se fija en el 14 de Octubre de 2026.
"""
import json, math, re, sys, tempfile, threading, urllib.request
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from db.crear_base import crear
from motor.procesar_edicion import cargar_edicion
from motor import republicaciones as RP
from interfaz import datos as D
from interfaz.servidor import servidor

# 21 de Octubre. Decisión de Diego, los tribunales no civiles se descartan. El único nuevo llamado real de las ediciones es el
# C-9854-2025 del 3° Juzgado de Familia, así que esta prueba APAGA el descarte de tribunales no civiles para seguir probando la
# lógica con ese caso (como si fuera un juzgado civil). Al final se vuelve a encender y se revisa que ese aviso quede descartado.
import re as _re
import db.carga as _CARGA
_NO_CIVIL_REAL = _CARGA.NO_CIVIL
_CARGA.NO_CIVIL = _re.compile(r"(?!)")          # no calza con nada

FALLAS = []
def revisar(nombre, condicion, detalle=""):
    print(("OK    " if condicion else "FALLA ") + nombre, detalle)
    if not condicion: FALLAS.append(nombre)

antes = sorted(p.name for p in (RAIZ / "ia_respuestas").rglob("*.json"))
HOY = "2026-10-14"
tmp = tempfile.TemporaryDirectory()
ruta = Path(tmp.name) / "interfaz.db"
con = crear(ruta)
for f in ["2026-09-01", "2026-10-06", "2026-10-09", "2026-10-10", "2026-10-11", "2026-10-13", "2026-10-14"]:
    cargar_edicion(con, f, "x", RAIZ / "banco_pruebas" / f)
uno = lambda sql, *p: con.execute(sql, p).fetchone()[0]

# 1. Formatos. Meses siempre en palabras y montos a la chilena.
revisar("formatos. fecha larga y corta con el día", (D.larga("2026-11-16"), D.corta("2026-11-16")) == ("Lunes 16 de Noviembre de 2026", "Lun. 16 Nov."))
revisar("formatos. vale vista de un día con horario", D.texto_vv("2026-11-13 09:00", "2026-11-13 12:00") == "Vie. 13 Nov. de 09:00 a 12:00")
revisar("formatos. vale vista con desde estimado", D.texto_vv("2026-10-18", "2026-11-05 14:00", "estimado_dia_siguiente_edicion")
        == "Desde Dom. 18 Oct. hasta Jue. 5 Nov. a las 14:00 (el desde es estimado)")
# 18 de Octubre (corrección de Diego). "Calificados al momento de hacerse el llamado" es entrega en el remate y la causa lo dice claro.
r5107 = uno("SELECT r.id FROM remates r JOIN avisos a ON a.id = r.aviso_id JOIN ediciones e ON e.id = a.edicion_id "
            "WHERE a.rol = '5107' AND a.anio = '2022' AND e.fecha = '2026-10-14'")
f5107 = D.armar(con, r5107)
revisar("formatos. vale vista en el remate (C-5107-2022 del 14-10) dice que se entrega en el mismo remate",
        f5107["vv_txt"] == "Jue. 29 Oct. a las 13:00. " + D.EN_EL_REMATE and f5107["vv_color"] == "verde"
        and not [x for x in f5107["alertas"] if "Falla de la IA" in x["texto"]], f5107["vv_txt"])
din = {"CLP": D.dinero({"minimo_monto": 93895646, "minimo_moneda": "CLP", "garantia_porcentaje": 10, "garantia_base": "minimo"}),
       "UF": D.dinero({"minimo_monto": 983.8089, "minimo_moneda": "UF", "garantia_porcentaje": 10, "garantia_base": "minimo"}),
       "20": D.dinero({"minimo_monto": 5119.97, "minimo_moneda": "UF", "garantia_porcentaje": 20, "garantia_base": "minimo"}),
       "tas": D.dinero({"minimo_monto": 1000, "minimo_moneda": "CLP", "garantia_porcentaje": 10, "garantia_base": "tasacion"}),
       "nada": D.dinero({"minimo_monto": 1000, "minimo_moneda": "CLP"})}
revisar("tipo de entrega del vale vista (22 de Octubre). en el remate, un día, rango y sin fecha",
        [D.tipo_vv("2026-10-29 13:00", "2026-10-29 13:00", "en_el_remate"), D.tipo_vv("2026-10-29 12:00", "2026-10-29 14:00", "fecha_fija"),
         D.tipo_vv(None, "2026-10-29 14:00", "dia_anterior"), D.tipo_vv("2026-10-19", "2026-11-05 14:00", "dias_habiles_antes"), D.tipo_vv(None, None)]
        == ["remate", "dia", "dia", "rango", None])
revisar("monto del vale vista en pesos", (din["CLP"]["minimo"], din["CLP"]["monto"], din["CLP"]["uf"]) == ("$93.895.646", "$9.389.565", None), str(din["CLP"]))
revisar("monto del vale vista en UF, con el número para el cálculo por UF", (din["UF"]["monto"], din["UF"]["uf"]) == ("98,3809 UF", 98.3809), str(din["UF"]))
revisar("garantía del 20% destacada", (din["20"]["monto"], din["20"]["otro_porcentaje"]) == ("1.023,994 UF", "20%"), str(din["20"]))
revisar("garantía sobre la tasación y sin dato", din["tas"]["monto"] == "10% de la tasación (el aviso no da el monto)" and din["nada"]["monto"] == "Sin dato")
revisar("modalidad. martillo, computador y signo (el mixto va con signo)", [D.modo(x) for x in ("presencial", "zoom", "en_linea", "mixta", "sin_dato", None)]
        == ["pres", "virt", "virt", "nose", "nose", "nose"])

# 2. Buscador. Vigentes de todas las ediciones, la publicación más nueva de cada propiedad.
b = D.buscar(con, HOY, limite=10000)
vig = uno("SELECT COUNT(*) FROM (SELECT COALESCE(bien_id, -remate_id) k, MAX(edicion) FROM v_buscador GROUP BY k HAVING "
          "(SELECT fecha_remate FROM v_buscador v2 WHERE COALESCE(v2.bien_id, -v2.remate_id) = k ORDER BY edicion DESC, remate_id DESC LIMIT 1) >= ? "
          "OR (SELECT fecha_remate FROM v_buscador v2 WHERE COALESCE(v2.bien_id, -v2.remate_id) = k ORDER BY edicion DESC, remate_id DESC LIMIT 1) IS NULL)", HOY)
revisar("buscador. un resultado por propiedad, solo vigentes", b["total"] == vig and all((r["fecha_remate"] or "9") >= HOY for r in b["resultados"])
        and len({r["bien_id"] for r in b["resultados"] if r["bien_id"]}) == len([r for r in b["resultados"] if r["bien_id"]]), f"{b['total']} contra {vig}")
fechas = [r["fecha_remate"] for r in b["resultados"]]
revisar("buscador. los que tienen fecha van primero y en orden, los sin fecha al final",
        any(f is None for f in fechas) and fechas == sorted([f for f in fechas if f]) + [None] * fechas.count(None),
        str(fechas[:3]))
# Dirección o comuna (pedido de Diego, 22 de Octubre). Sin tildes ni mayúsculas, y solo trae lo que la contiene.
_com = next(r["direccion"].split(",")[-1].strip() for r in b["resultados"] if r["direccion"] and not r["direccion"].startswith("El programa") and "," in r["direccion"])
_bd = D.buscar(con, HOY, limite=10000, direccion=_com.upper())
revisar("buscador. dirección o comuna, en mayúsculas igual encuentra y solo trae lo que la contiene",
        0 < _bd["total"] < b["total"] and all(D.normalizar(_com) in D.normalizar(r["direccion"]) for r in _bd["resultados"]), f"{_com} {_bd['total']} de {b['total']}")
revisar("buscador. con pasados trae más", D.buscar(con, HOY, pasados=True)["total"] > b["total"])
r9 = D.buscar(con, HOY, rol="9854")["resultados"]
revisar("buscador. rol 9854 es la publicación del 10-10 y trae los 3 avisos, el del 1 Sep. como llamado anterior",
        len(r9) == 1 and r9[0]["edicion"] == "2026-10-10" and [(p["edicion"], p["ant"]) for p in r9[0]["pubs"]]
        == [("2026-09-01", True), ("2026-10-09", False), ("2026-10-10", False)] and r9[0]["pubs"][1]["href"].startswith(D.BASE_URL + "/2026/10/09/"),
        str([(p["edicion"], p["ant"]) for p in r9[0]["pubs"]] if r9 else r9))
# Corrección 11 de Noviembre. El tribunal ahora viene de una lista fija y se compara entero, ya no un pedazo escrito.
t21 = D.buscar(con, HOY, tribunal="21° Juzgado Civil de Santiago")["resultados"]
revisar("buscador. tribunal 21 solo trae el 21° Civil", t21 and all(r["tribunal"] == "21° Juzgado Civil de Santiago" for r in t21), str(len(t21)))
# 11 de Noviembre (Diego). Lista fija de tribunales, día del remate y modalidad.
_t1 = D.buscar(con, HOY, tribunal="1° Juzgado Civil de Santiago", limite=10000)["resultados"]
revisar("buscador. el 1° Civil no trae el 11°, el 21° ni otros que terminan en 1", _t1 and {r["tribunal"] for r in _t1} == {"1° Juzgado Civil de Santiago"}, str({r["tribunal"] for r in _t1}))
_lt = D.tribunales(con)
revisar("buscador. lista fija con los civiles de Santiago primero y en orden de número", _lt == sorted(_lt, key=D.orden_tribunal) and _lt[0].startswith("1° Juzgado Civil de Santiago")
        and [x for x in _lt if x.endswith("Civil de Santiago")] == _lt[:len([x for x in _lt if x.endswith("Civil de Santiago")])] and "tribunales" in D.estado(con, HOY), str(_lt[:12]))
_todo = D.buscar(con, HOY, limite=10000, pasados=True)["resultados"]
_dias = {}
for r in _todo:
    if r["fecha_remate"]:
        _dias.setdefault(r["fecha_remate"][:10], []).append(r)
_dia = max(_dias, key=lambda d: len(_dias[d]))
_fd = D.buscar(con, HOY, fecha=_dia, limite=10000)
revisar("día. trae todos los remates de ese día y solo de ese día, aunque ya haya pasado", _fd["total"] == len(_dias[_dia]) and all(r["fecha_remate"][:10] == _dia for r in _fd["resultados"]), f"{_dia} {_fd['total']} {len(_dias[_dia])}")
_m = {k: D.buscar(con, HOY, fecha=_dia, modalidad=k, limite=10000)["resultados"] for k in ("ambas", "presencial", "video", "mixta")}
_sd = [r for r in _fd["resultados"] if r["modalidad"] in (None, "sin_dato")]
revisar("modalidad. presencial, video y mixto traen solo lo suyo y los sin modalidad siempre, al fondo",
        all({r["modalidad"] or "sin_dato" for r in _m[k]} <= D.MODALIDADES[k] | {"sin_dato"} for k in _m)
        and all([r["modalidad"] in (None, "sin_dato") for r in _m[k]] == sorted(r["modalidad"] in (None, "sin_dato") for r in _m[k]) for k in _m)
        and all(len([r for r in _m[k] if r["modalidad"] in (None, "sin_dato")]) == len(_sd) for k in _m), str({k: len(v) for k, v in _m.items()}))
revisar("día. un día que ya pasó hace meses se muestra igual", D.buscar(con, "2027-06-01", fecha=_dia, limite=10000)["total"] == len(_dias[_dia]))
_sdm = lambda r: r["modalidad"] in (None, "sin_dato")
_d2 = [d for d, rs in sorted(_dias.items()) if any(_sdm(a) and not _sdm(b) for i, a in enumerate(rs) for b in rs[i + 1:])]
_a2 = D.buscar(con, HOY, fecha=_d2[0], modalidad="ambas", limite=10000)["resultados"] if _d2 else []
revisar("modalidad. en un día donde un sin modalidad venía antes, ahora queda al fondo", _a2 and [_sdm(r) for r in _a2] == sorted(_sdm(r) for r in _a2), str(_d2[:3]))
revisar("modalidad. ambas es la suma de presencial, video y mixto sin repetir los sin modalidad",
        len(_m["ambas"]) == len(_m["presencial"]) + len(_m["video"]) + len(_m["mixta"]) - 2 * len(_sd) and len(_m["ambas"]) == _fd["total"])
revisar("modalidad. zoom y en línea van en videoconferencia", D.MODALIDADES["video"] == {"zoom", "en_linea"} and D.MODALIDADES["presencial"] == {"presencial"} and D.MODALIDADES["mixta"] == {"mixta"})
revisar("buscador. año 2019 solo trae roles de 2019", all(r["anio"] == "2019" for r in D.buscar(con, HOY, anio="2019")["resultados"]))
e13 = D.buscar(con, HOY, edicion="2026-10-13", pasados=True)["resultados"]
revisar("buscador. con edición, solo lo publicado ese día", e13 and all(r["edicion"] == "2026-10-13" for r in e13), str(len(e13)))

# 3. Agendar, avisos grandes y visto.
rid9 = r9[0]["remate_id"]
D.agendar(con, rid9)
lote1 = [r for r in D.buscar(con, HOY, rol="20712")["resultados"] if r["inmueble"] == "lote 1"][0]
D.agendar(con, lote1["remate_id"])
e = D.estado(con, HOY)
revisar("agenda. las dos causas agendadas, ordenadas por fecha del remate", [a["rol"] for a in e["agenda"]] == ["C-20712-2024", "C-9854-2025"], str([a["rol"] for a in e["agenda"]]))
revisar("aviso de fechas cambiadas con su tabla (lote 1 del 12° Civil)", e["titulo_cambios"] == "FECHAS DE REMATES HAN SIDO CAMBIADAS EN DIFERENTES AVISOS"
        and e["cambios"][0]["filas"] == [{"campo": "Fecha del remate", "a": "Lunes 20 de Octubre de 2025", "b": "Martes 20 de Octubre de 2026"}]
        and e["cambios"][0]["titulo"].endswith("· lote 1"), json.dumps(e["cambios"], ensure_ascii=False)[:300])
pa, pb = e["cambios"][0].get("pub_a") or {}, e["cambios"][0].get("pub_b") or {}
revisar("aviso de fechas cambiadas con el link al aviso de cada lado (pedido de Diego, 21 de Octubre)",
        e["cambios"][0]["antes"] == f"Aviso del {pa.get('texto')}" and e["cambios"][0]["despues"] == f"Aviso del {pb.get('texto')}"
        and f"/{pa.get('edicion', 'x').replace('-', '/')}/" in (pa.get("href") or "") and f"/{pb.get('edicion', 'x').replace('-', '/')}/" in (pb.get("href") or "")
        and pa.get("edicion") != pb.get("edicion"), json.dumps([pa, pb], ensure_ascii=False))
revisar("nuevo llamado con el link al aviso de cada lado", all((x.get("pub_a") or {}).get("href") and (x.get("pub_b") or {}).get("href") for x in e["llamados"]) and e["llamados"] != [])
ll = e["llamados"]
revisar("aviso de nuevo llamado aparte, con fecha, mínimo y monto del vale vista", len(ll) == 1 and ll[0]["filas"][0]["b"] == "Viernes 23 de Octubre de 2026"
        and ll[0]["filas"][3] == {"campo": "Monto del vale vista", "a": "$8.418.561", "b": "$8.654.282"}, json.dumps(ll, ensure_ascii=False)[:300])
revisar("la causa agendada lleva la marca de fecha cambiada y la de nuevo llamado", [(a["cambio_fecha"], a["nuevo_llamado"]) for a in e["agenda"]] == [(True, False), (False, True)])
D.visto(con, "cambios", [lote1["bien_id"]]); D.visto(con, "llamado")
RP.registrar_cambios(con, "2026-10-11", "y")
e = D.estado(con, HOY)
revisar("visto. los dos avisos grandes desaparecen y siguen vistos después de rehacer los cambios", e["cambios"] == [] and e["llamados"] == [])
revisar("sincronización. la franja negra con los días que faltan", e["franja_negra"][0] == "SIN SINCRONIZAR. La última edición cargada es la del miércoles 14 de Octubre de 2026."
        and "Falta la edición del lunes 12 de Octubre de 2026." in e["franja_negra"], str(e["franja_negra"]))
# CORRECCIÓN del 5 de Noviembre, noche (pedido de Diego). En Octubre ya no sale el aviso de feriados provisorios, sale desde el 20 de diciembre.
revisar("la franja ámbar no avisa los feriados provisorios en Octubre", not any("provisorios" in x for x in e["franja_ambar"]), str(e["franja_ambar"][-1:]))
revisar("la franja ámbar avisa los feriados provisorios desde el 20 de diciembre", any("provisorios" in x for x in D.estado(con, "2026-12-20")["franja_ambar"]))

# 4. Vale vista entregado y quitar con la X.
D.marcar(con, "vv_entregado", True, bien_id=lote1["bien_id"])
revisar("vale vista entregado", [a["vv_entregado"] for a in D.estado(con, HOY)["agenda"] if a["bien_id"] == lote1["bien_id"]] == [True])
D.quitar(con, bien_id=r9[0]["bien_id"])
revisar("quitar. sale de la agenda y queda anotada con su última edición", all(a["bien_id"] != r9[0]["bien_id"] for a in D.estado(con, HOY)["agenda"])
        and uno("SELECT ultima_edicion FROM agenda_quitados WHERE bien_id = ?", r9[0]["bien_id"]) == "2026-10-10")
revisar("quitar. una republicación del mismo remate no avisa", D.estado(con, HOY)["quitados"] == [])
with con:
    con.execute("UPDATE agenda_quitados SET ultima_edicion = '2026-09-01' WHERE bien_id = ?", (r9[0]["bien_id"],))   # como si la hubiera quitado el 1 Sep.
q = D.estado(con, HOY)["quitados"]
revisar("quitar. si vuelve con un nuevo llamado, avisa", len(q) == 1 and q[0]["texto"] == "Volvió a publicarse con un nuevo llamado el 9 Oct. Remate el Vie. 23 Oct.", str(q))
D.ignorar_quitado(con, r9[0]["bien_id"])
revisar("quitar. 'No, gracias' apaga el aviso", D.estado(con, HOY)["quitados"] == [])

# 5. Causa a mano.
try:
    D.agregar_manual(con, {"trib": "x"}); sin_fecha = False
except D.ErrorDato as ex:
    sin_fecha = str(ex) == "Falta la fecha del remate."
revisar("a mano. sin fecha del remate no se agrega", sin_fecha)
m1 = D.agregar_manual(con, {"trib": "1° Juzgado Civil de Rancagua", "rol": "123", "anio": "2025", "fecha": "2026-11-20", "hora": "10:00", "mod": "pres", "vh": "2026-11-19"})["manual_id"]
m2 = D.agregar_manual(con, {"trib": "3° Juzgado de Familia de Santiago", "rol": "C-9854", "anio": "2025", "fecha": "2026-10-23", "mod": "virt"})["manual_id"]
ag = {a.get("manual_id"): a for a in D.estado(con, HOY)["agenda"] if a["tipo"] == "manual"}
revisar("a mano. aparece en la agenda con su ventana del vale vista", ag[m1]["vv_txt"] == "Jue. 19 Nov." and ag[m1]["publicado"] == [] and ag[m1]["mod"] == "pres", str(ag[m1]["vv_txt"]))
# 5 de Noviembre. Dirección en las causas a mano (aprobado por Diego). Sin dirección dice que falta, con dirección la muestra.
m3 = D.agregar_manual(con, {"trib": "2° Juzgado Civil de Santiago", "fecha": "2026-11-25", "direccion": "  Calle Los Aromos 123, Maipú "})["manual_id"]
ag3 = {a.get("manual_id"): a for a in D.estado(con, HOY)["agenda"] if a["tipo"] == "manual"}
revisar("a mano. la dirección escrita aparece en la causa, sin espacios de más", ag3[m3]["direccion"] == "Calle Los Aromos 123, Maipú", ag3[m3]["direccion"])
revisar("a mano. sin dirección lo dice", ag3[m1]["direccion"] == "Agregada a mano, sin dirección.", ag3[m1]["direccion"])
D.quitar(con, None, m3)
m4 = D.agregar_manual(con, {"trib": "2° Juzgado Civil de Santiago", "fecha": "2026-11-18", "vh": "2026-11-17", "monto": "56,162976 UF (10% del mínimo de 561,62976 UF)"})["manual_id"]
ag4 = {a.get("manual_id"): a for a in D.estado(con, HOY)["agenda"] if a["tipo"] == "manual"}
revisar("UF. una causa a mano con monto en UF lo entrega para pasarlo a pesos", ag4[m4]["uf"] == 56.162976 and ag4[m1]["uf"] is None, str((ag4[m4]["uf"], ag4[m1]["uf"])))
D.quitar(con, None, m4)
# Una base anterior al 5 de Noviembre recibe la columna vacía al abrirse, sin cambiar sus datos.
import shutil, sqlite3 as _sq
_vieja = Path(tmp.name) / "vieja_sin_direccion.db"
shutil.copy(RAIZ / "agendar_remates_vacia_antes_carga_21oct.db", _vieja)
_c = _sq.connect(_vieja); _antes_col = "direccion" in [r[1] for r in _c.execute("PRAGMA table_info(agenda_manual)")]; _c.close()
_c = crear(_vieja); _c.close(); _c = crear(_vieja)
revisar("base anterior. recibe la columna dirección al abrirse y abrir dos veces no falla",
        not _antes_col and "direccion" in [r[1] for r in _c.execute("PRAGMA table_info(agenda_manual)")])
_c.close()
revisar("a mano. si salió publicada, ofrece cambiarla por la del diario", len(ag[m2]["publicado"]) == 1 and ag[m2]["publicado"][0]["remate_id"] == rid9
        and ag[m2]["publicado"][0]["texto"] == "Salió publicada en El Mercurio el 10 Oct., remate el Vie. 23 Oct.", str(ag[m2]["publicado"]))
D.marcar(con, "vv_entregado", True, manual_id=m2)
D.reemplazar_manual(con, m2, rid9)
ag = D.estado(con, HOY)["agenda"]
revisar("a mano. al cambiarla queda la del diario, con lo que Diego marcó", [(a["tipo"], a["vv_entregado"]) for a in ag if a.get("bien_id") == r9[0]["bien_id"]] == [("diario", True)]
        and not any(a.get("manual_id") == m2 for a in ag))
D.ignorar_publicado(con, m1)
D.quitar(con, manual_id=m1)
revisar("a mano. la X la borra", not any(a.get("manual_id") == m1 for a in D.estado(con, HOY)["agenda"]))
# F2-04 (30 de Octubre). El C-20712-2024 del 6 de Octubre imprime el remate el 20 de Octubre de 2025, antes de la edición.
# Con hoy 6 de Octubre y el filtro de esa edición antes no salía. Ahora sale con su alerta roja. Una fecha pasada de verdad
# (anterior a hoy y no a su edición) sigue escondida, y la ventana de 60 días deja fuera un aviso errado muy viejo.
_err = D.buscar(con, "2026-10-06", rol="20712", edicion="2026-10-06")
revisar("F2-04. fecha anterior a la edición. la propiedad sale en el buscador con la alerta roja", _err["total"] == 4
        and all(x["fecha_remate"] == "2025-10-20" and any(al["tipo"] == "error_escritura" for al in x["alertas"]) for x in _err["resultados"]), str(_err["total"]))
revisar("F2-04. un aviso con fecha errada de hace más de 60 días ya no sale", D.buscar(con, "2026-12-10", rol="20712", edicion="2026-10-06")["total"] == 0)
revisar("F2-04. con hoy el 21 de Octubre un remate del 20 que de verdad pasó no sale", all(
        x["fecha_remate"] >= "2026-10-21" or x["fecha_remate"] < x["edicion"] for x in D.buscar(con, "2026-10-21", limite=1000)["resultados"] if x["fecha_remate"]))
con.close()

# 6. Servidor local. Página, datos y una acción, en un puerto libre de este PC.
srv = servidor(ruta, 0)
hilo = threading.Thread(target=srv.serve_forever, daemon=True); hilo.start()
url = f"http://127.0.0.1:{srv.server_address[1]}"
def get(p):
    with urllib.request.urlopen(url + p, timeout=20) as r:
        return r.read().decode("utf-8")
def post(p, d):
    req = urllib.request.Request(url + p, data=json.dumps(d).encode(), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as er:
        return json.loads(er.read())
html = get("/")
revisar("servidor. entrega la página", "<title>Agenda de remates</title>" in html)
revisar("página. no carga programas de internet (funciona sin conexión)", not re.search(r"<script[^>]+src=", html))
# Ficha (5 de Noviembre). El recuadro Remate va en planilla con día, hora, modalidad con su ícono y dirección.
_rem = html[html.index("<h3>Remate</h3>"):html.index("</section>", html.index("<h3>Remate</h3>"))]
revisar("ficha. el recuadro Remate va en planilla con día, hora, modalidad con ícono y dirección",
        'class="planilla grande"' in _rem and all(f'<td class="k">{k}</td>' in _rem for k in ("DÍA", "HORA", "MODALIDAD", "DIRECCIÓN"))
        and "diaLargo(it.fecha_remate" in _rem and "${SVG[it.mod](20)}" in _rem and "${E(it.direccion)}" in _rem and ".planilla.grande{font-size:16px;table-layout:auto}" in html)
# Cabecera (5 de Noviembre, noche, pedido de Diego). Sin el título "Agendar Remates", con la leyenda y los botones chicos arriba,
# y Volver a hoy y Mes siguiente dentro de la cabecera del mes grande, no en una fila propia.
_cen = html[html.index("function renderCentro("):html.index("function icoVV(")]
_mes = html[html.index("function mes("):html.index("function tablaCmp(")]
revisar("cabecera. sin el título Agendar Remates y con los botones chicos",
        "Agendar Remates</div>" not in _cen and ".cab .btn2,.nav .btn2{min-height:28px" in html and "padding:10px 28px 48px" in html)
revisar("cabecera. Volver a hoy y Mes siguiente van en la cabecera del mes grande y no en una fila propia",
        'data-acc="mesHoy"' not in _cen and 'data-acc="mesHoy"' in _mes and "${g?`<div class=\"nav\">" in _mes)
# Ficha (6 de Noviembre). Cómo llenar el vale vista, con nombre en palabras, RUT, monto, tipo, a la orden de quién y la frase del aviso.
# Corrección 11 de Noviembre. formaHTML recibe vista para poner el botón Imprimir vale vista solo en las causas agendadas.
revisar("ficha. muestra cómo llenar el vale vista", "${formaHTML(it,vista)}" in html and all(f'<td class="k">{k}</td>' in html for k in ("A NOMBRE DE", "RUT", "MONTO", "TIPO", "A LA ORDEN"))
        and "EL AVISO DICE" in html)
# Ficha (5 de Noviembre). Dinero y Entrega del vale vista también en planilla.
revisar("ficha. Dinero y Entrega del vale vista van en planilla con sus filas",
        all(f'<td class="k">{k}</td>' in html for k in ("MÍNIMO", "GARANTÍA", "VALE VISTA", "TIPO", "FECHA", "LLEGADA"))
        and 'aria-label="Dinero del remate"' in html and 'aria-label="Entrega del vale vista"><tbody>' in html
        and '<div class="vvmonto">${E(it.monto)}</div>${pesosHTML(it)}' in html)
# Botón Revisar ficha en Buscar remates (pedido de Diego, 10 de Noviembre). Va al lado de Agregar al calendario y abre la misma ficha
# de siempre sin agendar nada. Esa vista no lleva la casilla de vale vista entregado ni Quitar del calendario. Una causa que ya está
# en el calendario abre su ficha normal. Probado además con la página corriendo en node con datos de una copia (bitácora del 10).
_res = html[html.index("function tarjetaRes("):html.index("function renderRes(")]
_fic = html[html.index("function fichaHTML("):html.index("function irAFicha(")]
revisar("buscador. cada tarjeta lleva Revisar ficha, junto a Agregar al calendario o a Ya está en tu calendario",
        _res.count("Revisar ficha</button>") == 2 and 'data-acc="fichaRes" data-rid="${it.remate_id}"' in _res
        and 'data-acc="ficha" data-k="b${it.bien_id}"' in _res and _res.index('data-acc="agendar"') < _res.index('data-acc="fichaRes"'))
revisar("buscador. Revisar ficha no agenda nada (solo redibuja el centro) y la ficha vista no trae casilla de entregado ni Quitar",
        "else if(a==='fichaRes'){" in html and "/api/" not in html[html.index("else if(a==='fichaRes'){"):html.index("else if(a==='cerrarFicha')")]
        and "UI.vista=it;UI.verFicha=true;renderCentro();irAFicha();" in html and "fichaHTML(it,!!UI.vista)" in html
        and "${vista?'':`<label class=\"chk\"" in _fic and "${vista?'':`<div class=\"fila\" style=\"justify-content:flex-start\"><button" in _fic
        and "NO ESTÁ EN TU CALENDARIO" in _fic)
# Estilo A de Diego (5 de Noviembre). Cada causa agendada muestra sus datos en planilla, con la dirección.
_tarj = html[html.index("function renderIzq("):html.index("function iso(")]
# CORRECCIÓN del 5 de Noviembre, noche (pedido de Diego). La tarjeta se simplifica. Vale vista, monto y avisos quedan solo en la ficha.
revisar("causas agendadas. la tarjeta va en planilla con tribunal, dirección y remate, sin vale vista, monto ni avisos",
        'class="planilla"' in _tarj and all(f'<td class="k">{k}</td>' in _tarj for k in ("TRIBUNAL", "DIRECCIÓN", "REMATE"))
        and not any(f'<td class="k">{k}</td>' in _tarj for k in ("VALE VISTA", "MONTO VV", "AVISOS")) and "${E(it.direccion)}" in _tarj)
# F3-07 (30 de Octubre). Medido con Chromium aparte. Aquí se revisa que el aviso siga en la página y que el latido no lo calle.
revisar("F3-07. la página avisa cuando la agenda se cerró (dos latidos fallidos y al volver a la pestaña)",
        'id="cerrada"' in html and "La agenda se cerró" in html and "LATIDO.fallas>=2" in html
        and "fetch('/api/latido',{cache:'no-store'}).catch(()=>{})" not in html and "visibilitychange" in html)
est = json.loads(get(f"/api/estado?hoy={HOY}"))
revisar("servidor. estado con agenda, franjas y feriados", {"agenda", "franja_negra", "franja_ambar", "cambios", "llamados", "quitados", "feriados"} <= set(est))
bus = json.loads(get(f"/api/buscar?hoy={HOY}&rol=6443"))
revisar("servidor. buscador", bus["total"] >= 1 and all("6443" in r["rol"] for r in bus["resultados"]), str(bus["total"]))
r = post("/api/agendar", {"remate_id": bus["resultados"][0]["remate_id"]})
est = json.loads(get(f"/api/estado?hoy={HOY}"))
revisar("servidor. agendar desde la página", r.get("ok") and any("6443" in a["rol"] for a in est["agenda"]), str(r))
revisar("ficha. el estado entrega cómo llenar el vale vista de cada causa", all(x.get("vv_forma") and x["vv_forma"]["rut"] for x in est["agenda"]), str([x.get("vv_forma") for x in est["agenda"]])[:300])
revisar("causas agendadas. el estado entrega la dirección de cada causa del diario", all(x["direccion"] for x in est["agenda"] if x["tipo"] == "diario"), str([x["direccion"] for x in est["agenda"]]))
revisar("servidor. un pedido malo devuelve el error en palabras", post("/api/manual", {}) == {"ok": False, "error": "Falta la fecha del remate."})
# F3-03 (4 de Noviembre). Un error del programa sigue llegando a la página y además queda anotado. Con pythonw el stderr del
# servidor es logs/servidor.log, aquí se captura el stderr mientras dura cada pedido.
import io
def con_registro(f):
    viejo, sys.stderr = sys.stderr, io.StringIO()
    try:
        return f(), sys.stderr.getvalue()
    finally:
        sys.stderr = viejo
def get_json(p):
    try:
        return json.loads(get(p))
    except urllib.error.HTTPError as er:
        return json.loads(er.read())
_r, _reg = con_registro(lambda: get_json("/api/estado?hoy=malo"))
revisar("F3-03. un error del programa en GET sigue llegando a la página igual que antes",
        _r.get("ok") is False and _r.get("error", "").startswith("Error del programa. ValueError."), str(_r))
revisar("F3-03. y queda anotado con la hora, la ruta y el detalle", _reg.startswith("--- ") and "error en GET /api/estado" in _reg
        and "Traceback" in _reg and "ValueError" in _reg, _reg[-200:])
_r, _reg = con_registro(lambda: post("/api/marcar", {"campo": "vv_entregado"}))
revisar("F3-03. un pedido incompleto en POST sigue llegando a la página igual que antes", _r == {"ok": False, "error": "Pedido incompleto. 'valor'"}, str(_r))
revisar("F3-03. y queda anotado, porque también puede ser un error del programa", "error en POST /api/marcar" in _reg and "KeyError" in _reg, _reg[-200:])
_r, _reg = con_registro(lambda: post("/api/manual", {}))
revisar("F3-03. un dato faltante con su mensaje en palabras no se anota como error", _r.get("error") == "Falta la fecha del remate." and _reg == "", _reg[-200:])
# UF del día (pedido de Diego, 5 de Noviembre). Sin internet, con fuentes de mentira. Ninguna llamada sale del PC.
import datetime as _dt
from interfaz import uf as U
from interfaz.datos import uf_de_texto
MIND = '{"serie": [{"fecha": "2026-11-05T03:00:00.000Z", "valor": 41274.2}, {"fecha": "2026-11-04T03:00:00.000Z", "valor": 41268.88}]}'
FIND = '{"serie": [{"fecha": "2026-11-05", "valor": 41274.2}]}'
pedidas = []
def fuente(respuestas):
    def abrir(url):
        pedidas.append(url)
        r = respuestas.get(url.split("/")[2])
        if isinstance(r, Exception): raise r
        return r
    return abrir
revisar("UF. lee la más reciente de mindicador con fecha y hora", U.leer_serie(MIND) == ("2026-11-05", 41274.2))
revisar("UF. si mindicador falla usa findic", U.buscar_internet(fuente({"mindicador.cl": OSError("sin red"), "findic.cl": FIND})) == ("2026-11-05", 41274.2, "findic.cl"))
revisar("UF. una respuesta rota (serie vacía o valor absurdo) no se usa", U.buscar_internet(fuente({"mindicador.cl": '{"serie": []}', "findic.cl": '{"serie": [{"fecha": "2026-11-05", "valor": 3}]}'})) is None)
_ruf = Path(tmp.name) / "uf_guardada.json"
_ah = _dt.datetime(2026, 11, 5, 10, 0)
pedidas.clear()
r1 = U.obtener(_ruf, "2026-11-05", fuente({"mindicador.cl": MIND}), _ah)
r2 = U.obtener(_ruf, "2026-11-05", fuente({"mindicador.cl": MIND}), _ah)
revisar("UF. la busca una sola vez al día", r1 == r2 == {"valor": 41274.2, "fecha": "2026-11-05", "fuente": "mindicador.cl", "manual": False} and len(pedidas) == 1, str((r1, pedidas)))
pedidas.clear()
r3 = U.obtener(_ruf, "2026-11-06", fuente({"mindicador.cl": OSError("x"), "findic.cl": OSError("x")}), _ah + _dt.timedelta(days=1))
r4 = U.obtener(_ruf, "2026-11-06", fuente({}), _ah + _dt.timedelta(days=1, minutes=10))
revisar("UF. sin internet queda la última con su fecha y no reintenta antes de 30 minutos", r3["valor"] == 41274.2 and r3["fecha"] == "2026-11-05" and r4 == r3 and len(pedidas) == 2, str((r3, pedidas)))
U.guardar_manual(_ruf, 41300.5, "2026-11-06")
revisar("UF. la escrita a mano manda", U.obtener(_ruf, "2026-11-06", fuente({}), _ah) == {"valor": 41300.5, "fecha": "2026-11-06", "fuente": "escrita a mano", "manual": True})
U.guardar_manual(_ruf, None, "2026-11-06")
revisar("UF. al borrarla vuelve la automática", U.obtener(_ruf, "2026-11-06", fuente({}), _ah + _dt.timedelta(days=1, minutes=10))["manual"] is False)
try:
    U.guardar_manual(_ruf, 41.27, "2026-11-06"); _rech = False
except ValueError:
    _rech = True
revisar("UF. un valor que no es UF en pesos se rechaza", _rech)
# 11 de Noviembre. Tabla del SII con la UF de los días que vienen (extracto real de la página que Diego guardó).
SII = (RAIZ / "banco_pruebas" / "uf_sii_2026_extracto.htm").read_text(encoding="utf-8")
_tab = U.leer_tabla_sii(SII, 2026)
revisar("UF SII. lee noviembre y diciembre hasta el 9, sin los días vacíos", (len(_tab), _tab["2026-11-18"], _tab["2026-12-09"], "2026-12-10" in _tab, _tab["2026-11-01"]) == (39, 41357.3, 41501.94, False, 41252.94), str(len(_tab)))
_crudo = U.leer_tabla_sii((RAIZ / "banco_pruebas" / "uf_sii_2026_crudo_python.htm").read_text(encoding="utf-8"), 2026)
revisar("UF SII. lee también lo que recibe Python (comillas simples)", _crudo == _tab, str(len(_crudo)))
_rsii = Path(tmp.name) / "uf_sii.json"
pedidas.clear()
_t1 = U.tabla_sii(_rsii, "2026-11-11", fuente({"www.sii.cl": SII}), _ah)
_t2 = U.tabla_sii(_rsii, "2026-11-11", fuente({"www.sii.cl": SII}), _ah)
revisar("UF SII. entrega de hoy en adelante y la busca una sola vez al día", min(_t1) == "2026-11-11" and max(_t1) == "2026-12-09" and _t1 == _t2 and pedidas == ["https://www.sii.cl/valores_y_fechas/uf/uf2026.htm"], str((min(_t1), max(_t1), pedidas)))
pedidas.clear()
U.tabla_sii(_rsii, "2026-11-11", fuente({"www.sii.cl": SII}), _ah + _dt.timedelta(hours=3))
revisar("UF SII. ya leída hoy, no la vuelve a pedir horas después", pedidas == [], str(pedidas))
revisar("UF SII. solo hasta 45 días desde hoy", max(U.tabla_sii(_rsii, "2026-11-01", fuente({}), _ah)) == "2026-12-09" and max(U.tabla_sii(_rsii, "2026-10-01", fuente({}), _ah + _dt.timedelta(days=1))) <= "2026-11-15")
pedidas.clear()
_rsii2 = Path(tmp.name) / "uf_sii2.json"
_t3 = U.tabla_sii(_rsii2, "2026-12-20", fuente({"www.sii.cl": OSError("sin red")}), _ah)
revisar("UF SII. en diciembre pide también el año siguiente y sin internet entrega vacío sin caerse", _t3 == {} and pedidas == ["https://www.sii.cl/valores_y_fechas/uf/uf2026.htm", "https://www.sii.cl/valores_y_fechas/uf/uf2027.htm"], str(pedidas))
pedidas.clear()
_r3 = Path(tmp.name) / "uf_sii3.json"
_t4 = U.tabla_sii(_r3, "2026-12-20", fuente({"www.sii.cl": SII}), _ah)
U.tabla_sii(_r3, "2026-12-20", fuente({"www.sii.cl": SII}), _ah + _dt.timedelta(hours=3))
revisar("UF SII. una página que no trae el día de hoy no se guarda como leída y se vuelve a pedir", _t4 == {} and len(pedidas) == 4, str(pedidas))
revisar("UF. la cifra en UF de una causa a mano se lee del monto escrito", (uf_de_texto("56,162976 UF (10% del mínimo de 561,62976 UF)"), uf_de_texto("1.234,5 UF"), uf_de_texto("$7.500.000"), uf_de_texto(None)) == (56.162976, 1234.5, None, None))
srv.RequestHandlerClass.uf_abrir = staticmethod(fuente({"mindicador.cl": MIND}))
_get_uf = json.loads(get("/api/uf"))
revisar("UF. el servidor la entrega en /api/uf y la guarda junto a la base", _get_uf.get("valor") and (Path(ruta).parent / "uf_guardada.json").exists(), str(_get_uf))
revisar("UF. el servidor guarda la escrita a mano y rechaza una mala con su motivo",
        post("/api/uf", {"valor": 41300.5}).get("manual") is True and post("/api/uf", {"valor": 5}).get("ok") is False and post("/api/uf", {"valor": None}).get("manual") is False)
_tar = html[html.index("function renderIzq("):html.index("function iso(")]
revisar("UF. la ficha y el buscador muestran el monto en pesos y la ficha el valor de la UF (la tarjeta ya no lleva monto)",
        "${pesosHTML(it)}" not in _tar and html.count("${pesosHTML(it)}") >= 2 and "${ufHTML(it)}<h3>Dinero</h3>" in html and "provisoria para la entrega" in html)
revisar("UF SII. la página usa la UF del día del remate publicada por el SII y la escrita a mano sigue mandando",
        "UF.tabla[r]" in html and "publicada por el SII" in html and "sii=!UF.manual&&UF.tabla" in html and "tabla" in json.loads(get("/api/uf")))
# 11 de Noviembre (pedido de Diego). Imprimir vale vista. Papeleta .docx con la plantilla del banco, uno o varios vales.
import zipfile as _zf
def _pap(vales):
    req = urllib.request.Request(url + "/api/papeleta", data=json.dumps({"vales": vales}).encode(), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.headers.get("Content-Disposition"), r.read()
    except urllib.error.HTTPError as er:
        return er.code, None, er.read()
_v1 = {"a_nombre_de": "Segundo Juzgado Civil de Santiago", "rut": "60.306.002-4", "monto": 3000000, "tipo": "endosable", "rol": "C-8034-2020"}
_v2 = {"a_nombre_de": "Décimo Primer Juzgado Civil de Santiago", "rut": "60.306.011-3", "monto": 1749349, "tipo": "", "rol": "C-1-2025"}
_c, _cd, _b = _pap([_v1, _v2])
_doc = _zf.ZipFile(io.BytesIO(_b)).read("word/document.xml").decode("utf-8") if _c == 200 else ""
_txt = _re.sub(r"<[^>]+>", lambda m: "|" if m.group(0) == "</w:p>" else "", _doc).strip()
revisar("papeleta. el servidor entrega el docx para descargar con el rol en el nombre", _c == 200 and 'filename="VV_C-8034-2020_C-1-2025.docx"' in (_cd or ""), str(_c))
revisar("papeleta. dos vales con su título N°1 y N°2, las cuatro líneas y dos líneas en blanco entre ellos",
        _txt.startswith("Vale Vista a nombre de tercero N°1|A Nombre de: Segundo Juzgado Civil de Santiago|RUT: 60.306.002-4|Monto: $3.000.000|Tipo: Endosable (no nominativo)|||Vale Vista a nombre de tercero N°2|"), _txt[:300])
revisar("papeleta. sin tipo la línea Tipo va en blanco", "Monto: $1.749.349|Tipo: |" in _txt, _txt[-120:])
revisar("papeleta. mismo formato de la plantilla (viñeta, Arial, etiqueta en negrita subrayada)",
        _doc.count('<w:pStyle w:val="Listaconvietas"/><w:spacing w:after="120"/></w:pPr>') == 8 and _doc.count('<w:u w:val="single"/>') == 8 and "<w:sectPr" in _doc)
revisar("papeleta. sin vales responde el error en palabras", _pap([])[0] == 400)
revisar("papeleta. la plantilla va dentro de interfaz", (RAIZ / "interfaz" / "plantilla_vale_vista.docx").exists())
srv.shutdown(); srv.server_close()
# Pantalla. Botón en la caja Cómo llenar el vale vista, solo para causas agendadas. Monto mínimo o uno escrito, y el + con las demás agendadas.
_fh = html[html.index("function formaHTML("):html.index("function fichaHTML(")]
revisar("papeleta. botón Imprimir vale vista solo fuera de la vista del buscador", "${vista||UI.pap?'':`<button class=\"btn2\" data-acc=\"papAbrir\"" in _fh and ">Imprimir vale vista</button>" in _fh and "${vista?'':papHTML()}" in _fh)
revisar("papeleta. pregunta si mantener el monto mínimo o escribir otro, con el + y GENERAR DOCX",
        "Mantener el monto mínimo" in html and "data-pap-monto" in html and "+ Agregar otro vale vista de tus causas agendadas" in html and ">GENERAR DOCX</button>" in html and "!usados.includes(clave(it))" in html)
revisar("papeleta. el monto mínimo usa la UF del día del remate y suma las costas enteras",
        "return v?Math.ceil(ufVV(it)*v)+(it.costas||0):null;" in html and "return it.monto_clp||null;" in html)
revisar("papeleta. un monto escrito menor que el mínimo se rechaza", "if(m&&monto<m)return" in html)
# 11 de Noviembre (Diego). Buscador y calendario.
revisar("buscador. tribunal en lista fija, sin escribir", "${tribF()}" in html and "campoF('trib'" not in html and '<select class="campo" data-filtro="trib"' in html and "'trib'" in html[html.index("document.addEventListener('input'"):])
revisar("buscador. abre con la última edición cargada una sola vez", "if(!UI.fIni){UI.fIni=true;UI.f.edicion=EST.ediciones[0]||'';}" in html)
revisar("buscador. día del remate y modalidad, y con un día elegido busca en todas las ediciones", 'type="date" data-filtro="fecha"' in html and "${modF(f.mod,'b')}" in html
        and "if(t.value&&UI.f.edicion){UI.f.edicion=''" in html and "fecha:f.fecha,mod:f.mod" in html)
revisar("modalidad. cuatro botones, Ambas, Presencial, Videoconferencia y Mixto", "const MODS=[['ambas','Ambas'],['presencial','Presencial'],['video','Videoconferencia'],['mixta','Mixto']];" in html)
revisar("modalidad. los sin modalidad llevan borde amarillo", "const sd=!it.modalidad||it.modalidad==='sin_dato'" in html and "border:2px solid var(--famb-borde)" in html)
revisar("calendario. un clic en el día muestra sus remates en la zona de la ficha con el subfiltro", 'data-acc="dia" data-d="${d}"' in html and "h+=diaHTML();" in html and "${modF(D.mod,'d')}" in html
        and "else if(a==='dia'){" in html and "fecha:D.d,mod:D.mod" in html and "if(UI.dia)await cargarDia(false);" in html)
revisar("calendario. Revisar ficha también encuentra los remates de la lista del día", "...(UI.dia&&UI.dia.res&&UI.dia.res.resultados||[])].find(" in html)
# RUT de los 30 civiles de Santiago, revisados uno por uno en pjud.cl el 11 de Noviembre (pedido de Diego). Ninguno distinto.
_PJUD = ["60306001-6", "60306002-4", "60306003-2", "60306004-0", "60306005-9", "60306006-7", "60306007-5", "60306008-3", "60309014-4", "60306010-5",
         "60306011-3", "60306012-1", "60306013-K", "60306014-8", "60306062-8", "60306064-4", "60306066-0", "60306056-3", "60306076-8", "61962700-8",
         "60306065-2", "60306057-1", "60306058-K", "61933300-4", "60306072-5", "60306069-5", "60306070-9", "60306073-3", "60306074-1", "60306075-K"]
from motor import forma_vale_vista as _FV
revisar("RUT. los 30 civiles de Santiago iguales a pjud.cl", all(_FV.TABLA[f"{n}° Juzgado Civil de Santiago"]["rut"].replace(".", "") == _PJUD[n - 1] for n in range(1, 31)))
revisar("filtro. ya no está Filtrar por tribunal en Causas agendadas", "Filtrar por tribunal" not in html and "ftrib" not in html)
# Costas (decisión de Diego, 11 de Noviembre). En UF el vale vista es el 10% de las UF más las costas enteras.
_d = D.dinero({"minimo_monto": 344.0359, "minimo_moneda": "UF", "minimo_costas_clp": 328400, "garantia_porcentaje": 10, "garantia_base": "minimo"})
revisar("costas. en UF el monto dice las costas y las entrega aparte", _d["monto"] == "34,4036 UF más $328.400 de costas" and _d["costas"] == 328400 and abs(_d["uf_vv"] - 34.40359) < 1e-9, str(_d))
# Con una UF de $41.302,34 el 10% da los $1.420.949 del ejemplo de Diego.
revisar("costas. con la UF del ejemplo de Diego da el 10% más las costas",
        math.ceil(_d["uf_vv"] * 41302.34) == 1420949 and math.ceil(_d["uf_vv"] * 41302.34) + _d["costas"] == 1749349)
_d = D.dinero({"minimo_monto": 93895646, "minimo_moneda": "CLP", "minimo_costas_clp": 500000, "garantia_porcentaje": 10, "garantia_base": "minimo"})
revisar("costas. en pesos no se suman y el monto va en número", _d["costas"] is None and _d["monto_clp"] == 9389565 and "costas" not in _d["monto"], str(_d))
revisar("costas. en las causas a mano se leen del texto", D.costas_de_texto("56,1 UF más $323.600 de costas") == 323600 and D.costas_de_texto("56,1 UF") is None
        and D.pesos_de_texto("$7.500.000") == 7500000 and D.pesos_de_texto("56,1 UF más $3 de costas") is None)
# Hacia arriba, igual que el monto de la papeleta, porque es un mínimo.
revisar("costas. la ficha suma las costas al monto en pesos, hacia arriba", "Math.ceil(ufVV(it)*sii)+(it.costas||0)" in html and "Math.ceil(ufVV(it)*UF.valor)+(it.costas||0)" in html and "de costas`" in html)

despues = sorted(p.name for p in (RAIZ / "ia_respuestas").rglob("*.json"))
revisar("candado. no se llamó a Haiku (ia_respuestas sin cambios)", antes == despues)
# 11 de Noviembre (pedido de Diego). Historial de causas agendadas, con la fecha y hora exacta de cuando se quitó. En una copia de la base.
import sqlite3 as _sqh
_rh = Path(tmp.name) / "historial.db"
_src = _sqh.connect(ruta); _dst = _sqh.connect(_rh); _src.backup(_dst); _dst.close(); _src.close()
_ch = crear(_rh)
_ch.execute("DELETE FROM agenda"); _ch.execute("DELETE FROM agenda_manual"); _ch.execute("DELETE FROM agenda_quitados"); _ch.execute("DELETE FROM agenda_historial")
_ch.execute("DELETE FROM meta WHERE clave = 'historial_reconstruido'"); _ch.commit()
_rems = [r[0] for r in _ch.execute("SELECT remate_id FROM v_buscador WHERE bien_id IS NOT NULL GROUP BY bien_id ORDER BY remate_id LIMIT 3")]
# Lo que había antes del historial. Una agendada, una a mano y una quitada.
_ch.execute("INSERT INTO agenda(bien_id, remate_base_id, agregado_en) SELECT bien_id, id, '2026-11-05T21:12:17' FROM remates WHERE id = ?", (_rems[0],))
_ch.execute("INSERT INTO agenda_quitados(bien_id, quitado_en, ultima_edicion) SELECT bien_id, '2026-11-06T13:09:26', '2026-10-14' FROM remates WHERE id = ?", (_rems[1],))
_ch.commit()
D.agregar_manual(_ch, {"fecha": "2026-11-18", "rol": "8034", "anio": "2020", "trib": "2° Juzgado Civil de Santiago", "direccion": "calle Carlos Condell 696", "monto": "56 UF"})
_ch.execute("DELETE FROM agenda_historial"); _ch.commit()
revisar("historial. se arma una sola vez con lo que ya estaba guardado", D.reconstruir_historial(_ch) == 3 and D.reconstruir_historial(_ch) == 0)
_h = D.historial(_ch)["historial"]
revisar("historial. lo reconstruido conserva las fechas guardadas y lo más nuevo va arriba",
        [(x["accion"], x["cuando"], x["reconstruido"]) for x in _h][1:] == [("quitada", "2026-11-06T13:09:26", 1), ("agendada", "2026-11-05T21:12:17", 1)]
        and _h[1]["cuando_txt"] == "Viernes 6 de Noviembre de 2026 a las 13:09" and _h[1]["puede_volver"] and not _h[2]["puede_volver"], str(_h))
D.agendar(_ch, _rems[2]); D.agendar(_ch, _rems[2])
_bien2 = _ch.execute("SELECT bien_id FROM remates WHERE id = ?", (_rems[2],)).fetchone()[0]
D.quitar(_ch, bien_id=_bien2)
_h = D.historial(_ch)["historial"]
revisar("historial. agendar dos veces la misma deja una sola fila y quitarla deja la hora exacta",
        [x["accion"] for x in _h if x["bien_id"] == _bien2] == ["quitada", "agendada"] and _re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d", _h[0]["cuando"])
        and _h[0]["rol"] and _h[0]["tribunal"] and _h[0]["puede_volver"] and _h[0]["remate_id"] == _rems[2] and not _h[1]["puede_volver"], str(_h[:2]))
D.agendar(_ch, _rems[2]); D.quitar(_ch, bien_id=_bien2)
_h = D.historial(_ch)["historial"]
revisar("historial. quitada dos veces, el botón va solo en la última", [x["puede_volver"] for x in _h if x["bien_id"] == _bien2] == [True, False, False, False], str([(x["accion"], x["puede_volver"]) for x in _h if x["bien_id"] == _bien2]))
_ch.execute("INSERT INTO agenda(bien_id, remate_base_id, agregado_en) VALUES (?,?,?)", (_bien2, _rems[2], "2026-11-11T10:00:00")); _ch.commit()
revisar("historial. si la causa ya está agendada otra vez no ofrece volver a agendarla", not any(x["puede_volver"] for x in D.historial(_ch)["historial"] if x["bien_id"] == _bien2))
_mid = _ch.execute("SELECT id FROM agenda_manual").fetchone()[0]
D.agregar_manual(_ch, {"fecha": "2026-12-01", "rol": "1", "anio": "2025", "trib": "3° Juzgado Civil de Santiago"})   # otra causa a mano, para que el número no se repita por casualidad
D.quitar(_ch, manual_id=_mid)
_h = D.historial(_ch)["historial"]
revisar("historial. una causa a mano quitada queda con sus datos y se puede volver a agendar igual",
        _h[0]["accion"] == "quitada" and _h[0]["tipo"] == "manual" and _h[0]["rol"] == "C-8034-2020" and _h[0]["puede_volver"] and "datos_manual" not in _h[0])
D.restaurar_manual(_ch, _h[0]["id"])
_m = _ch.execute("SELECT id, rol, anio, direccion, monto_vv, fecha_remate FROM agenda_manual").fetchall()
_h = D.historial(_ch)["historial"]
revisar("historial. al volver a agendarla queda igual, con su mismo número, y el botón desaparece",
        [x for x in _m if x[1] == "8034"] == [(_mid, "8034", "2020", "calle Carlos Condell 696", "56 UF", "2026-11-18")] and _h[0]["accion"] == "agendada" and not any(x["puede_volver"] for x in _h if x["tipo"] == "manual"), str(_m))
try:
    D.restaurar_manual(_ch, 99999); _err_h = False
except D.ErrorDato:
    _err_h = True
revisar("historial. sin datos guardados responde en palabras", _err_h)
D.reemplazar_manual(_ch, _mid, _rems[1])
_h = D.historial(_ch)["historial"]
revisar("historial. cambiar la causa a mano por la publicada deja las dos cosas", [x["accion"] + x["tipo"] for x in _h[:2]] == ["quitadamanual", "agendadaremate"], str([(x["accion"], x["tipo"]) for x in _h[:3]]))
_ch.close()
revisar("historial. botón en Causas agendadas, panel con la fecha y hora y volver a agendar", 'data-acc="historial"' in html and "UI.panel==='historial'" in html
        and "${E(x.cuando_txt)}" in html and 'data-acc="restaurarM"' in html and "x.puede_volver?" in html and "if(UI.panel==='historial')await cargarHist();" in html)
_srvt = Path(__file__).resolve().parent.parent / "interfaz" / "servidor.py"
revisar("historial. el servidor lo entrega y lo arma al abrir, después del respaldo", '"/api/historial"' in _srvt.read_text(encoding="utf-8") and '"/api/restaurar_manual"' in _srvt.read_text(encoding="utf-8")
        and _srvt.read_text(encoding="utf-8").index("respaldar(ruta_base)") < _srvt.read_text(encoding="utf-8").index("D.reconstruir_historial(con)"))
tmp.cleanup()
# Descarte encendido otra vez. El aviso de Familia del C-9854-2025 (9 de Octubre, aviso 24) queda descartado y fuera del buscador.
_CARGA.NO_CIVIL = _NO_CIVIL_REAL
_tmp_fam = tempfile.TemporaryDirectory()
_F = crear(Path(_tmp_fam.name) / "familia.db")
cargar_edicion(_F, "2026-10-09", "x", RAIZ / "banco_pruebas" / "2026-10-09")
revisar("descarte encendido. el aviso de Familia C-9854-2025 queda descartado con su motivo y no está en el buscador",
        _F.execute("SELECT filtro_estado, filtro_motivos FROM avisos WHERE rol = '9854' AND anio = '2025'").fetchall() == [("descartado", "tribunal no civil")]
        and _F.execute("SELECT COUNT(*) FROM v_buscador WHERE rol = '9854'").fetchone()[0] == 0)
_F.close(); _tmp_fam.cleanup()
# Servidor único y apagado solo (pedido de Diego, 29 de Octubre). Un segundo servidor en el mismo puerto no puede arrancar.
from interfaz import servidor as SV
revisar("servidor. sin reuso de puerto (en Windows dejaba abrir varios)", SV.ServidorUnico.allow_reuse_address is False)
revisar("servidor. se apaga solo pasado el plazo sin señal, y no antes", SV.debe_apagarse(0, 181) and not SV.debe_apagarse(0, 179))
_s1 = SV.servidor(Path(tempfile.mkdtemp()) / "a.db", 0)
try:
    SV.servidor(Path(tempfile.mkdtemp()) / "b.db", _s1.server_address[1]).server_close()
    _segundo = True
except OSError:
    _segundo = False
_s1.server_close()
revisar("servidor. un segundo servidor en el mismo puerto falla", _segundo is False)
# Respaldo diario (F3-01, 30 de Octubre). Una copia por día junto a la base, solo las últimas 14, y nunca de una base dañada.
import sqlite3 as _sq
from db.respaldo import respaldar, carpeta_de
_tr = Path(tempfile.mkdtemp())
_b = _tr / "base.db"
crear(_b).close()
_sv = SV.servidor(_b, 0); _sv.server_close()
_R = carpeta_de(_b)
revisar("respaldo. al abrir la agenda queda la copia de hoy junto a la base", [p.name for p in _R.glob("*.db")] == [f"base_{SV.hoy_chile()}.db"])
_sv = SV.servidor(_b, 0); _sv.server_close()
revisar("respaldo. una segunda apertura el mismo día no hace otra copia", len(list(_R.glob("*.db"))) == 1)
_c = _sq.connect(next(_R.glob("*.db")))
revisar("respaldo. la copia es una base sana con sus feriados", _c.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        and _c.execute("SELECT COUNT(*) FROM feriados").fetchone()[0] > 0)
_c.close()
for _d in range(1, 17):
    respaldar(_b, hoy=f"2026-09-{_d:02d}")
_quedan = sorted(p.name for p in _R.glob("base_*.db"))
revisar("respaldo. quedan solo los últimos 14 días", len(_quedan) == 14 and _quedan[0] == "base_2026-09-04.db", str(len(_quedan)))
_b.write_bytes(_b.read_bytes()[:4096] + b"\x00basura" * 2000)
try:
    respaldar(_b, hoy="2026-12-31"); _lanzo = False
except _sq.DatabaseError:
    _lanzo = True
revisar("respaldo. una base dañada no se guarda y no borra los buenos", _lanzo and sorted(p.name for p in _R.glob("base_*.db")) == _quedan
        and not list(_R.glob("*.tmp")))
try:
    SV.main(["--base", str(_b), "--puerto", "0", "--sin-navegador", "--sin-apagado"]); _cayo = False
except Exception:
    _cayo = True
_pag = _R / "BASE_DANADA.html"
_txt = _pag.read_text(encoding="utf-8") if _pag.exists() else ""
revisar("respaldo. con la base dañada la agenda no queda muda, deja la página con los respaldos y meses en palabras",
        not _cayo and "base está dañada" in _txt and "4 de Septiembre de 2026" in _txt and "2026-09" not in _txt)
# Pregunta 6 al abogado, respondida el 4 de Noviembre. Llegar media hora antes de que abra la entrega, porque es por orden de llegada.
from interfaz.datos import nota_llegada
revisar("llegada. 3° Civil sin hora leída dice las 10:30", nota_llegada("3° Juzgado Civil de Santiago").startswith("Llega a las 10:30"))
revisar("llegada. con hora de apertura leída del aviso resta media hora", nota_llegada("21° Juzgado Civil de Santiago", "2026-11-05 10:00", "texto").startswith("Llega a las 09:30"))
revisar("llegada. un desde estimado no se toma como hora de apertura", nota_llegada("1° Juzgado Civil de Santiago", "2026-11-02 10:00", "estimado_dia_siguiente_edicion").startswith("Llega media hora antes de que abra"))
revisar("llegada. entrega en el remate, media hora antes del remate", nota_llegada(None, None, None, "en_el_remate", "13:00").startswith("Llega a las 12:30, media hora antes del remate"))
revisar("llegada. todas dicen que es por orden de llegada", all("orden de llegada" in nota_llegada(*a) for a in [("x",), ("3° Juzgado Civil de Santiago",)]))
print("\nRESULTADO.", "TODO OK" if not FALLAS else f"{len(FALLAS)} fallas")
sys.exit(1 if FALLAS else 0)

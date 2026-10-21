"""Prueba 17. Interfaz (18 de Octubre). Datos de la página, acciones de Diego y el servidor local, sin internet ni Haiku.
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_interfaz
Carga en una base temporal las 7 ediciones del banco con las respuestas guardadas. Hoy se fija en el 14 de Octubre de 2026.
"""
import json, re, sys, tempfile, threading, urllib.request
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
revisar("buscador. con pasados trae más", D.buscar(con, HOY, pasados=True)["total"] > b["total"])
r9 = D.buscar(con, HOY, rol="9854")["resultados"]
revisar("buscador. rol 9854 es la publicación del 10-10 y trae los 3 avisos, el del 1 Sep. como llamado anterior",
        len(r9) == 1 and r9[0]["edicion"] == "2026-10-10" and [(p["edicion"], p["ant"]) for p in r9[0]["pubs"]]
        == [("2026-09-01", True), ("2026-10-09", False), ("2026-10-10", False)] and r9[0]["pubs"][1]["href"].startswith(D.BASE_URL + "/2026/10/09/"),
        str([(p["edicion"], p["ant"]) for p in r9[0]["pubs"]] if r9 else r9))
t21 = D.buscar(con, HOY, tribunal="21")["resultados"]
revisar("buscador. tribunal 21 solo trae el 21° Civil", t21 and all("21" in r["tribunal"] for r in t21), str(len(t21)))
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
revisar("la franja ámbar avisa los feriados provisorios", any("provisorios" in x for x in e["franja_ambar"]), str(e["franja_ambar"][-1:]))

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
est = json.loads(get(f"/api/estado?hoy={HOY}"))
revisar("servidor. estado con agenda, franjas y feriados", {"agenda", "franja_negra", "franja_ambar", "cambios", "llamados", "quitados", "feriados"} <= set(est))
bus = json.loads(get(f"/api/buscar?hoy={HOY}&rol=6443"))
revisar("servidor. buscador", bus["total"] >= 1 and all("6443" in r["rol"] for r in bus["resultados"]), str(bus["total"]))
r = post("/api/agendar", {"remate_id": bus["resultados"][0]["remate_id"]})
est = json.loads(get(f"/api/estado?hoy={HOY}"))
revisar("servidor. agendar desde la página", r.get("ok") and any("6443" in a["rol"] for a in est["agenda"]), str(r))
revisar("servidor. un pedido malo devuelve el error en palabras", post("/api/manual", {}) == {"ok": False, "error": "Falta la fecha del remate."})
srv.shutdown(); srv.server_close()

despues = sorted(p.name for p in (RAIZ / "ia_respuestas").rglob("*.json"))
revisar("candado. no se llamó a Haiku (ia_respuestas sin cambios)", antes == despues)
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
print("\nRESULTADO.", "TODO OK" if not FALLAS else f"{len(FALLAS)} fallas")
sys.exit(1 if FALLAS else 0)

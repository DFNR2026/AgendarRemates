"""Parte 3.7a. Prueba SIN internet del verificador y del cálculo del vale vista (motor\\vale_vista.py).
1. Con las respuestas ideales armadas desde el banco del 14 de Octubre, resolver() debe dar el mismo desde, hasta y color
   que el banco (56 avisos visibles, el 9 queda fuera porque ahora debe salir en rojo por contradicción).
2. Casos que deben quedar en rojo (frase inventada, hora fuera de la frase, lecturas distintas, devolución,
   sin_dato con plazo en el aviso, contradicción, fecha fija anterior a la edición, año sin feriados).
3. La cita acepta solo diferencias de espacios y devuelve el texto tal como está en el aviso.
"""
import json, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.cortador import construir_rollo, cortar
from motor.orden_columnas import leer_pagina
from motor import vale_vista as V
from db.carga import es_partidor

fallas = []
B = RAIZ / "banco_pruebas" / "2026-10-14"
rollo, m = construir_rollo([(n, leer_pagina(B / f"mercurio_2026-10-14_{n}.txt")) for n in ("B11", "C8")])
av = {a.orden: a for a in cortar(rollo, m)}
banco = json.loads((B / "banco_nivel2_2026-10-14.json").read_text(encoding="utf-8"))["avisos"]


def ideal(v):
    regla = v["regla"]
    hh = v["vv_hasta"][11:] if v.get("vv_hasta") and len(v["vv_hasta"]) > 10 else None
    hd = v["vv_desde"][11:] if v.get("vv_desde_origen") == "texto" and len(v["vv_desde"]) > 10 else None
    if regla in ("horas_antes", "en_el_remate"):
        hh = None
    if regla == "en_el_remate":
        hd = None
    return {"regla": regla, "dias": v.get("dias"), "horas": v.get("horas"), "fecha": v["vv_hasta"][:10] if regla == "fecha_fija" else None,
            "hora_desde": hd, "hora_hasta": hh, "frase_regla": v.get("cita"), "frases_extra": v.get("citas_extra", []), "contradiccion": None}


medidos = 0
for x in banco:
    n, v, t = x["n"], x["vale_vista"], av[x["n"]].texto
    if es_partidor(None, t) or v["regla"] == "fecha_dicha_en_aviso":
        continue
    medidos += 1
    r = ideal(v)
    if n == 29:   # 16-10. La cita del banco es corta y no trae el verbo de entrega que ahora se exige. Se usa la frase completa del aviso.
        r["frase_regla"] = "Postores deben presentar en secretaría del tribunal, al momento de efectuarse el llamado a remate"
    res = V.resolver([r, r], t, x["fecha_remate"]["valor"], x["hora_remate"]["valor"], "2026-10-14")
    esp = {"calculado": "verde", "revisar": "ambar", "sin_dato": "sin_dato"}[v["vv_estado"]]
    if (res["color"], res["vv_desde"], res["vv_hasta"]) != (esp, v["vv_desde"], v["vv_hasta"]):
        fallas.append(f"14-10 aviso {n}. Esperado {esp} {v['vv_desde']} {v['vv_hasta']}, obtenido {res['color']} {res['vv_desde']} {res['vv_hasta']} {res['motivos']}")
if medidos != 56:
    fallas.append(f"Se esperaban 56 avisos medidos del 14 de Octubre y fueron {medidos}")

# Aviso 9 del 14 de Octubre, contradicción (de 11 a 14 y hasta las 12). Debe quedar en rojo.
t9 = av[9].texto
r9 = {"regla": "dias_habiles_antes", "dias": 1, "horas": None, "fecha": None, "hora_desde": "11:00", "hora_hasta": "14:00",
      "frase_regla": "deberán comparecer al Tribunal el día hábil anterior al día de la subasta, esto es, el viernes anterior, de 11 a 14 hrs.",
      "frases_extra": [], "contradiccion": "hasta las 12 hrs. del día hábil anterior a la fecha fijada para el remate"}
if V.resolver([r9, r9], t9, "2026-11-09", "13:40", "2026-10-14")["color"] != "rojo":
    fallas.append("Aviso 9 con contradicción no quedó en rojo")

# Casos que deben quedar en rojo, sobre el aviso 1 del 14 de Octubre
x1 = next(x for x in banco if x["n"] == 1)
t1, f1, h1 = av[1].texto, x1["fecha_remate"]["valor"], x1["hora_remate"]["valor"]
base = ideal(x1["vale_vista"])
def rojo(nombre, r, lecturas=None, fecha=f1, edicion="2026-10-14"):
    res = V.resolver(lecturas or [r, r], t1, fecha, h1, edicion)
    if res["color"] != "rojo":
        fallas.append(f"{nombre} debía quedar en rojo y quedó {res['color']}")
rojo("frase inventada", {**base, "frase_regla": "deberá ser entregado hasta las 14:00 horas del día hábil anterior al remate en Huérfanos"})
rojo("hora fuera de la frase", {**base, "hora_hasta": "13:00"})
rojo("lecturas distintas", base, [base, {**base, "hora_hasta": "13:00"}])
rojo("regla otra", {**base, "regla": "otra"})
rojo("regla sin sus palabras", {**base, "regla": "martes_o_jueves_anterior"})
rojo("días que no están en la frase", {**base, "dias": 3})
rojo("sin_dato con plazo en el aviso", {**base, "regla": "sin_dato", "frase_regla": None, "hora_hasta": None, "dias": None})
rojo("año sin feriados", base, fecha="2028-01-05")   # 17-10. Era 2027, pero ya están cargados los feriados 2027 (provisorios)
rojo("remate anterior a la edición", base, fecha="2026-10-01")
t27 = av[27].texto
r27 = {**base, "regla": "en_el_remate", "dias": None, "hora_hasta": None, "hora_desde": None,
       "frase_regla": "Los vales vista recepcionados serán calificados al momento de hacerse el llamado al remate.", "frases_extra": []}
# CORRECCIÓN de Diego (18 de Octubre). Antes esta frase debía quedar en rojo. Ahora SÍ vale como entrega en el remate.
x27 = V.resolver([r27, r27], t27, "2026-10-29", "13:00", "2026-10-14")
if x27["color"] == "rojo" or x27.get("vv_hasta") != "2026-10-29 13:00":
    fallas.append(f"Aviso 27, 'serán calificados al momento del llamado' no quedó como entrega en el remate {x27.get('color')} {x27.get('vv_hasta')}")
# Y "calificar" sin el llamado sigue en rojo (la corrección es solo para esa frase).
f_cal = "Los vales vista serán calificados en la audiencia de remate."   # trae "audiencia", así que solo la regla de calificar la deja en rojo
r_cal = {**r27, "frase_regla": f_cal}
if V.resolver([r_cal, r_cal], t27 + " " + f_cal, "2026-10-29", "13:00", "2026-10-14")["color"] != "rojo":
    fallas.append("'calificados' sin el llamado no quedó en rojo")
# 10 de Noviembre (aprobado por Diego). Las instrucciones congeladas le dicen a la IA que esa frase da sin_dato (ejemplo 9). Si la IA
# responde sin_dato y el aviso trae la frase exacta, el código la lee como entrega en el remate y cita la oración completa.
# Antes salía el mensaje falso "El aviso no dice cuándo" (C-23164-2024 y C-6843-2024 del 10° Civil, 7 avisos de 28 con la frase).
_sd27 = {**base, "regla": "sin_dato", "dias": None, "hora_hasta": None, "hora_desde": None, "frase_regla": None, "frases_extra": []}
x27s = V.resolver([_sd27, dict(_sd27)], t27, "2026-10-29", "13:00", "2026-10-14")
if not (x27s["regla"] == "en_el_remate" and x27s["color"] == "verde" and x27s.get("vv_hasta") == "2026-10-29 13:00"
        and x27s["cita"] == r27["frase_regla"] and x27s["cita"] in t27):
    fallas.append(f"sin_dato de la IA con la frase del llamado no quedó como entrega en el remate {x27s.get('regla')} {x27s.get('color')} {x27s.get('cita')}")
# Sin la frase exacta, el sin_dato de la IA sigue siendo sin_dato. "calificados en la audiencia" no es la frase.
_t_sin = "REMATE. Se rematará el inmueble. Todo postor debe acompañar vale vista endosable a la orden del tribunal por el 10% del mínimo."
for _nombre, _t in (("sin la frase", _t_sin), ("con calificados en la audiencia", _t_sin + " " + f_cal)):
    _x = V.resolver([_sd27, dict(_sd27)], _t, "2026-10-29", "13:00", "2026-10-14")
    if not (_x["color"] == "sin_dato" and _x["regla"] == "sin_dato" and _x.get("vv_hasta") is None):
        fallas.append(f"sin_dato de la IA {_nombre} dejó de ser sin_dato {_x.get('regla')} {_x.get('color')}")
# Día de la semana. Aviso 34 del 14-10 ("el día viernes anterior") leído como día anterior da el miércoles. Debe quedar en rojo.
x34 = next(x for x in banco if x["n"] == 34)
r34 = {**ideal(x34["vale_vista"]), "regla": "dia_anterior"}
if V.resolver([r34, r34], av[34].texto, x34["fecha_remate"]["valor"], x34["hora_remate"]["valor"], "2026-10-14")["color"] != "rojo":
    fallas.append("Aviso 34 leído como día anterior (viernes en la frase, miércoles en el cálculo) no quedó en rojo")
t56 = av[56].texto
x56 = next(x for x in banco if x["n"] == 56)
r56 = ideal(x56["vale_vista"])
if V.resolver([r56, r56], t56, x56["fecha_remate"]["valor"], x56["hora_remate"]["valor"], "2026-11-20")["color"] != "rojo":
    fallas.append("Plazo que queda antes de la edición o después del remate no quedó en rojo")

# Cita con diferencias de espacios. Se acepta y se guarda como está en el aviso (aviso 10, 'serentregado').
t10 = av[10].texto
f = V.buscar_frase("deberá ser entregado materialmente en el tribunal", t10)
if f != "deberá serentregado materialmente en el tribunal":
    fallas.append(f"buscar_frase con espacios dio {f!r}")
if V.buscar_frase("deberá ser entregada materialmente en el tribunal", t10) is not None:
    fallas.append("buscar_frase aceptó una letra distinta")

# La devolución no es entrega (aviso 30 del 14 de Octubre si existe la frase de restitución en algún aviso)
for x in banco:
    t = av[x["n"]].texto
    import re
    mm = re.search(r"[^.]{0,60}(?:restituid|devuelt)[^.]{0,80}", t)
    if mm:
        rr = {**base, "frase_regla": mm.group(0), "hora_hasta": None}
        if V.verificar(rr, t)["ok"]:
            fallas.append(f"Una frase de devolución pasó la verificación (aviso {x['n']})")
        break

# F1-01 (30 de Octubre). Viernes, martes o jueves que caen en feriado. La entrega se adelanta y nunca queda en el feriado.
_F15 = dict(regla="viernes_anterior", dias=None, horas=None, fecha=None, hora_desde="12:00", hora_hasta="13:00",
            frase_regla="los postores deberán comparecer al Tribunal el día viernes anterior a la fecha de la subasta, de 12:00 a 13:00 horas, a fin de entregar el vale vista",
            frases_extra=["En caso de recaer dicho viernes en día feriado, la entrega deberá efectuarse el día hábil anterior en el mismo horario."], contradiccion=None)
_F27 = dict(_F15, hora_desde=None, hora_hasta=None, frases_extra=[],
            frase_regla="el que deberá ser entregado materialmente en la Secretaría del Tribunal hasta el día viernes de la semana anterior a efectuarse la subasta")
_F21 = dict(_F15, regla="martes_o_jueves_anterior", hora_desde="10:00", hora_hasta="12:00", frases_extra=[],
            frase_regla="deberán asistir a las dependencias del Tribunal los días martes y jueves, anterior a la realización de la subasta, según correspondiere, entre las 10:00 y las 12:00 horas")
def _vv(r, remate):
    t = "Garantía vale vista. " + r["frase_regla"] + ". " + " ".join(r["frases_extra"])
    x = V.resolver([r, r], t, remate, "12:00", "2026-11-20")
    return (x["vv_hasta"], x["color"], x["preguntas"])
for _r, _rem, _esp in [
        (_F15, "2026-12-29", ("2026-12-24 13:00", "verde", [])),       # viernes 25 de Diciembre, Navidad. El aviso dice día hábil anterior
        (_F15, "2027-03-30", ("2027-03-25 13:00", "verde", [])),       # viernes 26 de Marzo de 2027, Viernes Santo
        (_F15, "2027-01-05", ("2026-12-31 13:00", "verde", [])),       # viernes 1 de Enero, año nuevo
        # CORRECCIÓN del 4 de Noviembre. El abogado respondió la pregunta 12 para el viernes ("siempre el día antes") y la 5
        # ("lo ideal es siempre llevarlo el día martes"). Antes se esperaba ("2026-12-24", "ambar", [12]), ("2026-12-03 12:00",
        # "ambar", [5, 12]) y ("2026-12-10 12:00", "ambar", [5]). Las fechas no cambian.
        (_F27, "2026-12-28", ("2026-12-24", "verde", [])),             # 27° Civil, viernes 25 feriado, al día hábil anterior
        (_F21, "2026-12-09", ("2026-12-03 12:00", "ambar", [12])),     # martes 8 de Diciembre, Inmaculada Concepción. Al jueves anterior
        (_F15, "2026-12-15", ("2026-12-11 13:00", "verde", [])),       # sin feriado, no cambia
        (_F21, "2026-12-15", ("2026-12-10 12:00", "verde", []))]:      # sin feriado, no cambia
    if _vv(_r, _rem) != _esp:
        fallas.append(f"F1-01. remate {_rem} {_r['regla']} dio {_vv(_r, _rem)} y se esperaba {_esp}")
for _fecha, _color in [("2026-12-25", "rojo"), ("2026-12-26", "rojo"), ("2026-12-24", "verde")]:
    _r = dict(_F15, regla="fecha_fija", fecha=_fecha, hora_desde=None, hora_hasta="12:00", frases_extra=[],
              frase_regla=f"deberán acreditarse a más tardar el {int(_fecha[8:])} de diciembre de 2026 hasta las 12:00 horas")
    _x = V.resolver([_r, _r], "Garantía vale vista. " + _r["frase_regla"], "2026-12-29", "12:00", "2026-11-20")
    if _x["color"] != _color:
        fallas.append(f"F1-01. fecha fija {_fecha} dio {_x['color']} y se esperaba {_color}")
# Respuestas del abogado del 4 de Noviembre. Pregunta 5. El plazo del 21° Civil no cambia y se recomienda el martes hábil
# antes del remate (el 8 de Diciembre es feriado, así que para el 9 y el 15 de Diciembre es el martes 1 y el martes 15 no cuenta).
from motor.procesar_edicion import bloque_vale_vista
for _rem, _mar in [("2026-12-15", "2026-12-01"), ("2026-12-09", "2026-12-01"), ("2026-11-12", "2026-11-10"), ("2026-11-09", "2026-11-03")]:
    _t = "Garantía vale vista. " + _F21["frase_regla"] + "."
    _x = V.resolver([_F21, _F21], _t, _rem, "12:00", "2026-11-02")
    if _x.get("martes_recomendado") != _mar:
        fallas.append(f"Pregunta 5. remate {_rem} dio martes recomendado {_x.get('martes_recomendado')} y se esperaba {_mar}")
_b = bloque_vale_vista(V.resolver([_F21, _F21], "Garantía vale vista. " + _F21["frase_regla"] + ".", "2026-11-12", "12:00", "2026-11-02"))
if [a[1] for a in _b["alertas"]] != ["El abogado recomienda llevar el vale vista un martes. Para este remate es el martes 10 de Noviembre de 2026."]:
    fallas.append(f"Pregunta 5. alerta de la recomendación {_b['alertas']}")
_b = bloque_vale_vista(V.resolver([_F15, _F15], "Garantía vale vista. " + _F15["frase_regla"] + ".", "2026-12-15", "12:00", "2026-11-02"))
if any("martes" in a[1] for a in _b["alertas"]):
    fallas.append("Pregunta 5. la recomendación del martes salió en un aviso que no es de martes y jueves")
# Regla de la secretaria del 24° Civil (decisión de Diego del 6 de Noviembre, motor\reglas_tribunal.py). Sin internet.
from types import SimpleNamespace
from motor import reglas_tribunal as RT
from motor.procesar_edicion import bloque_vale_vista, extraer_avisos
F, H = "2026-11-25", "15:00"
def bl(color, regla=None, cita=None, desde=None, hasta=None, estado=None, motivos=None):
    return bloque_vale_vista({"regla": regla, "cita": cita, "citas_extra": [], "vv_desde": desde, "vv_desde_origen": "texto" if desde else None,
                              "vv_hasta": hasta, "vv_estado": estado, "color": color, "motivos": motivos or [], "preguntas": [], "contradiccion": None})
b = RT.vale_vista_24(bl("sin_dato", "sin_dato"), F, H)
if not (b["color"] == "verde" and b["vv_estado"] == "calculado" and b["regla"] == "en_el_remate" and b["vv_desde"] == b["vv_hasta"] == "2026-11-25 15:00"
        and [x[1] for x in b["alertas"]] == [RT.VV_SECRETARIA]):
    fallas.append(f"24° Civil. aviso que no dice nada debe quedar en el remate, en verde, con la alerta de la secretaria {b}")
b = RT.vale_vista_24(bl("rojo", "otra", "frase", motivos=["Las dos lecturas de la IA no coinciden."]), F, None)
if not (b["color"] == "ambar" and b["vv_estado"] == "revisar" and b["vv_hasta"] == F and b["regla"] == "en_el_remate"
        and [x[1] for x in b["alertas"]] == [RT.VV_SECRETARIA_ROJO]):
    fallas.append(f"24° Civil. lectura fallida debe quedar en ámbar con la fecha del remate y la alerta de revisar el aviso {b}")
v = bl("verde", "dia_anterior", "el día anterior", "2026-11-24", "2026-11-24", "calculado")
b = RT.vale_vista_24(v, F, H)
if not (b["vv_hasta"] == "2026-11-24" and b["color"] == "verde" and ("contradiccion", RT.VV_SECRETARIA_CONTRA, "el día anterior") in b["alertas"]):
    fallas.append(f"24° Civil. aviso con otra regla debe mantener su fecha y alertar la contradicción {b}")
v = bl("verde", "en_el_remate", "al momento de la subasta", "2026-11-25 15:00", "2026-11-25 15:00", "calculado")
if RT.vale_vista_24(v, F, H) != v:
    fallas.append("24° Civil. aviso que dice lo mismo que la secretaria no debe cambiar")
v = bl("sin_dato", "sin_dato")
if RT.vale_vista_24(v, None, None) != v:
    fallas.append("24° Civil. sin fecha del remate el bloque no debe cambiar")
ex = {"modalidad": {"valor": "sin_dato", "cita": None}, "alertas": [("revisar_lectura", RT.MOD_SIN_DATO)]}
m = RT.modalidad_24(ex)
if not (m["modalidad"]["valor"] == "presencial" and m["alertas"] == [("condicion_especial", RT.MOD_SECRETARIA)]):
    fallas.append(f"24° Civil. modalidad sin dato debe pasar a presencial con la alerta de la secretaria {m}")
m = RT.modalidad_24({"modalidad": {"valor": "zoom", "cita": "zoom"}, "alertas": []})
if not (m["modalidad"]["valor"] == "zoom" and m["alertas"] == [("contradiccion", RT.MOD_SECRETARIA_CONTRA.format("por Zoom"))]):
    fallas.append(f"24° Civil. un aviso por Zoom debe mantenerse y alertar la contradicción {m}")
p24 = {"modalidad": {"valor": "presencial", "cita": "presencial"}, "alertas": []}
if RT.modalidad_24(p24) != p24:
    fallas.append("24° Civil. un aviso presencial no debe cambiar")
txt = ("REMATE: VIGÉSIMO CUARTO JUZGADO CIVIL DE SANTIAGO, Huérfanos 1409 piso 10, Rol C-1234-2024. Se rematará el 25 de noviembre "
       "de 2026, a las 15:00 horas, el inmueble de calle Uno 1, comuna de Maipú. Mínimo $50.000.000. Garantía 10% del mínimo.")
otro = txt.replace("VIGÉSIMO CUARTO", "VIGÉSIMO TERCER")
ea = extraer_avisos([SimpleNamespace(orden=1, texto=txt), SimpleNamespace(orden=2, texto=otro)], "2026-11-06")
if not (ea[1]["tribunal"] == RT.TRIB_24 and ea[1]["modalidad"]["valor"] == "presencial" and ("condicion_especial", RT.MOD_SECRETARIA) in ea[1]["alertas"]
        and ea[2]["modalidad"]["valor"] == "sin_dato"):
    fallas.append(f"24° Civil. la carga debe aplicar la modalidad de la secretaria solo al 24° {ea[1]['tribunal']} {ea[1]['modalidad']} {ea[2]['modalidad']}")
# La carga y el retomar aplican la regla al 24° y no a otro tribunal. La IA se reemplaza por lecturas fijas de "sin_dato"
# (iguales a las guardadas de C-30048-2018), así la prueba no llama a Haiku ni escribe en ia_respuestas.
import tempfile, sqlite3
from motor import procesar_edicion as PE
_sd = {"regla": "sin_dato", "dias": None, "horas": None, "fecha": None, "hora_desde": None, "hora_hasta": None, "frase_regla": None, "frases_extra": [], "contradiccion": None}
_leer_real = V.leer_con_ia
V.leer_con_ia = lambda texto, cliente=None, lecturas=2: {"lecturas": [dict(_sd), dict(_sd)], "uso": []}
try:
    avs = [SimpleNamespace(orden=1, texto=txt), SimpleNamespace(orden=2, texto=otro)]
    ex2 = extraer_avisos(avs, "2026-11-06")
    PE.agregar_vale_vista(avs, ex2, "2026-11-06")
    if not (ex2[1]["vale_vista"]["regla"] == "en_el_remate" and ex2[1]["vale_vista"]["vv_hasta"] == "2026-11-25 15:00"
            and ex2[2]["vale_vista"]["color"] == "sin_dato"):
        fallas.append(f"24° Civil. la carga debe aplicar la regla del vale vista solo al 24° {ex2[1]['vale_vista']['regla']} {ex2[2]['vale_vista']['color']}")
    from db.crear_base import crear
    from db.carga import VV_NO_LEIDO
    with tempfile.TemporaryDirectory() as _tmp:
        cx = crear(Path(_tmp) / "r.db")
        cx.execute("INSERT INTO ediciones(fecha, leida_en, estado) VALUES ('2026-11-06', '2026-11-06T05:00:00', 'ok')")
        ed = cx.execute("SELECT id FROM ediciones").fetchone()[0]
        cols = {r[1] for r in cx.execute("PRAGMA table_info(avisos)")}
        for o, tx, tr in ((1, txt, RT.TRIB_24), (2, otro, "23° Juzgado Civil de Santiago")):
            cx.execute("INSERT INTO avisos(edicion_id, orden, texto, tribunal, filtro_estado) VALUES (?,?,?,?, 'pasa')", (ed, o, tx, tr))
            aid = cx.execute("SELECT max(id) FROM avisos").fetchone()[0]
            cx.execute("INSERT INTO remates(aviso_id, sub_orden, fecha_remate, hora_remate, modalidad) VALUES (?,1,'2026-11-25','15:00','presencial')", (aid,))
            cx.execute("INSERT INTO alertas(aviso_id, sub_orden, tipo, texto, origen) VALUES (?,1,'dato_faltante',?,'codigo')", (aid, VV_NO_LEIDO))
        cx.commit()
        PE.retomar_vale_vista(cx, "2026-11-06", None)
        rr = dict(cx.execute("SELECT a.orden, r.vv_regla FROM remates r JOIN avisos a ON a.id = r.aviso_id").fetchall())
        if rr != {1: "en_el_remate", 2: "sin_dato"}:
            fallas.append(f"24° Civil. retomar debe aplicar la regla del vale vista solo al 24° {rr}")
        cx.close()
except Exception as e:
    fallas.append(f"24° Civil. la prueba de la carga y el retomar se cayó {type(e).__name__} {e}")
finally:
    V.leer_con_ia = _leer_real
# Regla del secretario del 11° Civil (6 de Noviembre, tarde). Mismo cálculo que el 24°, con sus propios textos.
b = RT.vale_vista_secretaria(bl("sin_dato", "sin_dato"), F, H, RT.TRIB_11)
if not (b["regla"] == "en_el_remate" and b["color"] == "verde" and b["alertas"][-1][1].startswith("Regla del secretario del 11° Civil.")):
    fallas.append(f"11° Civil. aviso que no dice nada debe quedar en el remate con la regla del secretario {b}")
v = bl("sin_dato", "sin_dato")
if RT.vale_vista_secretaria(v, F, H, "23° Juzgado Civil de Santiago") != v:
    fallas.append("Un tribunal sin regla confirmada no debe cambiar")
if RT.vale_vista_secretaria(bl("sin_dato", "sin_dato"), F, H, RT.TRIB_24) != RT.vale_vista_24(bl("sin_dato", "sin_dato"), F, H):
    fallas.append("24° Civil. la regla general debe dar lo mismo que la del 24°")

# Forma del vale vista y cómo llenarlo (pedido de Diego, 6 de Noviembre). Frases reales de los avisos.
from motor import forma_vale_vista as FV
casos = [
    ("En cuanto a la garantía, esta se efectuará mediante vale vista nominativo al Tribunal por un monto equivalente al 10% del mínimo.", ("nominativo", "tribunal")),
    ("Todo postor deberá acompañar materialmente vale vista endosable a la orden del tribunal equivalente al 20% del precio mínimo.", ("endosable", "tribunal")),
    ("Postores acompañar vale vista endosable orden Tribunal por 10% mínimo subasta.", ("endosable", "tribunal")),
    ("Interesados deberán entregar vale vista a la orden del Tribunal, nominativo o endosable, por el 10% del mínimo.", ("nominativo_o_endosable", "tribunal")),
    ("Ésta caución se constituirá mediante un vale vista tomado a propia orden, susceptible de ser endosado al momento de la subasta.", ("endosable", "postor")),
    ("Garantía mediante un vale vista por el 10% del mínimo tomado a nombre Décimo Tercer Juzgado Civil de Santiago.", (None, "tribunal")),
    ("Todo postor deberá entregar materialmente vale vista equivalente al 10% del mínimo, por orden de llegada en el tribunal.", (None, None)),
    ("Mínimo $66.762.980. La garantía será mediante vale vista endosable a nombre del 1° Juzgado Civil de Santiago, Rut N° 60.306.001-6.", ("endosable", "tribunal")),
]
for frase, esperado in casos:
    f = FV.leer(frase)
    if (f["tipo"], f["orden"]) != esperado:
        fallas.append(f"Forma del vale vista. {esperado} y salió {(f['tipo'], f['orden'])} en {frase[:60]}")
if "$66.762.980" in (FV.leer(casos[-1][0])["cita"] or "") or "60.306.001-6" not in (FV.leer(casos[-1][0])["cita"] or ""):
    fallas.append("Forma del vale vista. la cita debe ser la oración completa sin cortar en los puntos de los números")
def dvf(n):
    s, m = 0, 2
    for d in reversed(n):
        s += int(d) * m; m = 2 if m == 7 else m + 1
    r = 11 - s % 11
    return "0" if r == 11 else "K" if r == 10 else str(r)
if len(FV.TABLA) != 30 or any(dvf(r["rut"].split("-")[0].replace(".", "")) != r["rut"].split("-")[1] for r in FV.TABLA.values()):
    fallas.append(f"RUT. la tabla debe traer los 30 civiles de Santiago con su dígito verificador correcto ({len(FV.TABLA)})")
if (FV.TABLA["5° Juzgado Civil de Santiago"]["rut"], FV.TABLA["15° Juzgado Civil de Santiago"]["rut"], FV.TABLA["24° Juzgado Civil de Santiago"]["rut"]) != ("60.306.005-9", "60.306.062-8", "61.933.300-4"):
    fallas.append("RUT. el 5°, el 15° y el 24° deben ir como los corrigió Diego y el PDF")
c11 = FV.como_llenar(FV.TRIB_11, "El vale vista deberá presentarse en el remate.")
if not (c11["a_nombre_de"] == "Décimo Primer Juzgado Civil de Santiago" and c11["rut"] == "60.306.011-3" and c11["tipo"] == "nominativo"
        and "secretario" in c11["tipo_txt"] and c11["llevar"] and c11["orden_txt"] == "A la orden del tribunal"):
    fallas.append(f"11° Civil. sin decirlo el aviso, el vale vista es nominativo a la orden del tribunal con la cédula por ambos lados {c11}")
c11 = FV.como_llenar(FV.TRIB_11, "Garantía mediante vale vista endosable a la orden del tribunal.")
if not (c11["tipo"] == "endosable" and c11["alertas"]):
    fallas.append(f"11° Civil. si el aviso dice endosable se deja y se alerta {c11}")
cm = FV.como_llenar("2° Juzgado Civil de Santiago", None)
if not (cm["tipo_txt"].startswith("Sin dato") and cm["rut"] == "60.306.002-4" and cm["a_nombre_de"] == "Segundo Juzgado Civil de Santiago"):
    fallas.append(f"Causa a mano. sin aviso debe decir sin dato y traer el RUT de la tabla {cm}")
print("\n".join(fallas) if fallas else f"{medidos} avisos del 14 de Octubre y casos en rojo revisados.")
print("RESULTADO.", "FALLAS" if fallas else "TODO OK")
sys.exit(1 if fallas else 0)

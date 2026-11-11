"""Prueba de la extracción por código (parte 3.6) contra el banco del 14 de Octubre, que es el banco de AJUSTE.
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_extraccion
Falla si algún dato sale EQUIVOCADO o si los aciertos bajan del mínimo logrado. El banco de validación (6 de Octubre)
no se usa aquí. Se mide aparte con pruebas.medir_extraccion 06, solo al final.
"""
import json, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.cortador import construir_rollo, cortar
from motor.orden_columnas import leer_pagina
from motor.extraccion import extraer
from db.carga import es_partidor, normalizar

MINIMOS = {"fecha_remate": 60, "hora_remate": 60, "minimo": 61, "garantia": 61, "modalidad": 59, "tribunal": 61}   # logrados el 2026-10-15 (etapas 1 a 5). Tribunal sin contar partidores, que se descartan. Solo pueden subir.


def _resumen_minimo(m):
    els = m.get("lista") or [m]
    if all(e.get("monto") is None for e in els): return None
    return [(round(e["monto"], 6), e.get("moneda"), e.get("costas_clp")) for e in els]

D = RAIZ / "banco_pruebas" / "2026-10-14"
r, m = construir_rollo([(n, leer_pagina(D / f"mercurio_2026-10-14_{n}.txt")) for n in ("B11", "C8")])
av = {a.orden: a for a in cortar(r, m)}
banco = json.loads((D / "banco_nivel2_2026-10-14.json").read_text(encoding="utf-8"))["avisos"]

fallas, aciertos = [], {c: 0 for c in MINIMOS}
for e in banco:
    todo = extraer(av[e["n"]].texto, "2026-10-14")
    x = {"fecha_remate": todo["fecha_remate"], "hora_remate": todo["hora_remate"], "alertas": todo["alertas"]}
    mc = {"minimo": todo["minimo"], "alertas": []}
    x["minimo"] = {"valor": _resumen_minimo(mc["minimo"]), "cita": (mc["minimo"].get("lista") or [mc["minimo"]])[0].get("cita")}
    e = dict(e, minimo={"valor": _resumen_minimo(e["minimo"])})
    gx = todo["garantia"]
    x["garantia"] = {"valor": (gx["porcentaje"], gx["base"], gx["monto"]), "cita": gx["cita"]}
    ge = e["garantia"]
    e = dict(e, garantia={"valor": (ge.get("porcentaje"), ge.get("base") or "sin_dato", ge.get("monto"))})
    mo = todo["modalidad"]
    x["modalidad"] = {"valor": None if mo["valor"] == "sin_dato" else mo["valor"], "cita": mo["cita"]}
    e = dict(e, modalidad={"valor": None if e["modalidad"]["valor"] in (None, "sin_dato") else e["modalidad"]["valor"]})
    tr = todo["tribunal"]
    x["tribunal"] = {"valor": normalizar(tr["valor"]) if tr["valor"] else None, "cita": tr["cita"]}
    e = dict(e, tribunal={"valor": normalizar(e["tribunal"])})
    if es_partidor(None, av[e["n"]].texto):
        x["tribunal"]["valor"] = e["tribunal"]["valor"]
    for c in MINIMOS:
        esperado, obtenido = e[c]["valor"], x[c]["valor"]
        if obtenido is not None and obtenido != esperado:
            fallas.append(f"EQUIVOCADO {c} aviso {e['n']} esperado {esperado} obtenido {obtenido}")
        if obtenido == esperado:
            aciertos[c] += 1
        if obtenido is not None and x[c]["cita"] is not None and x[c]["cita"] not in av[e["n"]].texto:
            fallas.append(f"cita que no está en el aviso {c} aviso {e['n']}")
# Casos fijos de tribunal, tomados de textos reales de otras ediciones (cada uno motivó una regla)
CASOS_TRIBUNAL = {
    "EN AUTOS ROL C-2237-2025, del 2° Juzgado de Letras Civil de Chillán, caratulados": "2° Juzgado Civil de Chillán",
    "7° JUZGADO CIVIL, EN calle Huérfanos 1409, piso 2, Santiago, se rematará": "7° Juzgado Civil de Santiago",
    "EXTRACTO 17° JUZGADO DE LEtras de Santiago. Causa hipotecaria": "17° Juzgado Civil de Santiago",
    "EXTRACTO JUZGADO DE LETRAS de Cobranza Laboral de Temuco. Rit C-357- 2024.": "Juzgado de Cobranza Laboral de Temuco",
    "REMATE ANTE EL JUZgado de Letras del Trabajo de San Bernardo, Urmeneta 467": "Juzgado de Letras del Trabajo de San Bernardo",
    "REMATE ANTE DÉCIMO QUINTO (15°) JUZGADO CIVIL DE SANTIAGO, Huérfanos": "15° Juzgado Civil de Santiago",
    "VIGÉSIMO CUARTO JUZgado Civil de Santiago, Huérfanos 1409": "24° Juzgado Civil de Santiago",
    "REMATE 1° JUZGADO CIVIL DE SAN Miguel, Ureta Cox 855": "1° Juzgado Civil de San Miguel",
    # 16-10, rol 6108-2025 (traído del Mercurio el 18 de Octubre)
    "6° JUZGADO CIVIL DE Santiago Causa Rol: C-6108-2025 Caratulado: Banco Itaú Chile SA./ Bosque Petreles S.A decretó": "6° Juzgado Civil de Santiago",
    # 16-10, rol 14842-2019 (traído del Mercurio el 18 de Octubre)
    "REMATE; 15° TRIBUNAL CIVIL DE Santiago, Huérfanos N° 1409, día 03 de noviembre de 2026": "15° Juzgado Civil de Santiago",
    # 16-10, rol 1177-2025 (traído del Mercurio el 18 de Octubre)
    "EXTRACTO 3°JUZGADO CIVIL DE Viña del Mar Banco de Chile con Hinojosa, Rol C-1177-2025, fijó remate": "3° Juzgado Civil de Viña del Mar",
}
for texto, esperado in CASOS_TRIBUNAL.items():
    obtenido = extraer(texto)["tribunal"]["valor"]
    if obtenido != esperado:
        fallas.append(f"tribunal fijo. '{texto[:40]}' dio {obtenido} y debía dar {esperado}")
print(f"casos fijos de tribunal {len(CASOS_TRIBUNAL)}")

# Parte 3.7b (17 de Octubre). Inscripción en el Conservador, casos reales de las ediciones capturadas. Solo identifica la
# propiedad (decisión de Diego), no filtra. Se esperan fojas, número y año sin puntos.
from motor.extraccion import inscripcion, minimo_y_costas
CASOS_INSCRIPCION = {
    # 01-09 aviso 44
    "Inscripción a Fojas 7.694, Número 6.390 del Registro de Propiedad del año 2009 del Conservador de Bienes Raíces de La Serena. Mínimo":
        "fojas 7694 n 6390 2009",
    # 01-09 aviso 50, el año va después del conservador
    "Inscripción a fojas 39.341, número 59.430 del Registro de Propiedad del Conservador de Bienes Raíces de Santiago correspondiente al año 2010. Mínimo":
        "fojas 39341 n 59430 2010",
    # 06-10 aviso 73, "N" pegado al número y "vuelta"
    "inscrito a fojas 57.106 N81.820 del Registro de Propiedad del año 2017": "fojas 57106 n 81820 2017",
    "inscrito a fojas 5.431 vuelta N° 6.193 del Registro de Propiedad del año 2017": "fojas 5431 n 6193 2017",
    # 09-10 aviso 83, dos inscripciones (depto y bodega) que comparten el año
    "inscrito a fojas 44321, número 64342 y fojas 44321, número 64343 respectivamente, Registro Propiedad año 2023, Conservador":
        "fojas 44321 n 64342 2023 + fojas 44321 n 64343 2023",
    # 14-10 aviso 30, "bajo el N°"
    "inscritos a nombre de CE Inmobiliaria III S.A. a fojas 44773 bajo el N° 66273 del Registro de Propiedad del Conservador de Bienes Raíces de Santiago correspondiente al año 2015":
        "fojas 44773 n 66273 2015",
    # formas vistas el 17 de Octubre
    "a Fojas 5914v N° 6254, en el Registro de Propiedad del Conservador de Bienes Raíces de Antofagasta del año 2016.": "fojas 5914 n 6254 2016",
    "la inscripción de fojas 24.045 No. 38.549 del Registro de Propiedad del Conservador de Bienes Raíces de Santiago del año 2.007.": "fojas 24045 n 38549 2007",
    "inscrito a fojas 14. 515 N° 13.762 del registro de propiedad correspondiente al año 2008": "fojas 14515 n 13762 2008",
    "Propiedad inscrita fojas Fs. 76060 N° 106266 Registro Propiedad Conservador Bienes Raíces Santiago del año 2025.": "fojas 76060 n 106266 2025",
    "Fojas 77233, Número 112258, del Registro de Propiedad del 2021, del Conservador": "fojas 77233 n 112258 2021",
    # 06-10 aviso 53, tres inscripciones con el año al final
    "fojas 79793, n° 112451, fojas 79794 n° 112452, y fojas 79795, n° 112453, todas del registro de propiedad del año 2020 del Conservador":
        "fojas 79793 n 112451 2020 + fojas 79794 n 112452 2020 + fojas 79795 n 112453 2020",
    # inventado a propósito. La hipoteca no identifica la propiedad
    "inscrito a fojas 100 número 200 del Registro de Propiedad del año 2010, y la hipoteca a fojas 300 número 400 del Registro de Hipotecas del año 2011.":
        "fojas 100 n 200 2010",
    "El inmueble no trae inscripción en este aviso.": None,
}
for texto, esperado in CASOS_INSCRIPCION.items():
    obtenido = inscripcion(texto)["clave"]
    if obtenido != esperado:
        fallas.append(f"inscripción. '{texto[:50]}' dio {obtenido} y debía dar {esperado}")
for el in inscripcion(" ".join(CASOS_INSCRIPCION))["inscripcion"]:
    if el["cita"] not in " ".join(CASOS_INSCRIPCION):
        fallas.append(f"inscripción. cita que no está en el texto ({el['cita'][:50]})")
alerta = inscripcion("fojas 68126 N° 102.893, Registro Propiedad año 2033, Conservador Bienes Raíces Santiago", "2026-10-09")["alertas"]
if not (alerta and alerta[0][0] == "error_escritura"):
    fallas.append("inscripción. año 2033 sin alerta de error de escritura (09-10 aviso 119)")
print(f"casos fijos de inscripción {len(CASOS_INSCRIPCION)}")
# Marcha blanca del 17 de Octubre. Las alertas muestran las fechas con el mes en palabras, nunca en número (pedido de Diego).
_al = extraer("REMATE 28° JUZGADO CIVIL DE Santiago, se rematará el día 26 de mayo de 2026, a las 13:50 horas. Mínimo $ 1.000.000.", "2026-10-15")["alertas"]
if not any(t == "La fecha del remate (26 de Mayo de 2026) es anterior a la edición del diario (15 de Octubre de 2026)." for _, t in _al):
    fallas.append(f"alerta de fecha pasada sin el mes en palabras {_al}")

# Etiqueta de cada mínimo en las listas (17 de Octubre). Primero la nombrada junto al mínimo, si no, la primera después
# del mínimo anterior. 14-10 aviso 30 (lote 4) y 06-10 aviso 73 (departamento 41) quedaban con la pieza equivocada.
lista30 = [x["inmueble"] for x in extraer(av[30].texto)["minimo"]["lista"]]
if lista30 != ["lote 1", "lote 2", "lote 3", "lote 4"]:
    fallas.append(f"etiqueta. aviso 30 del 14-10 dio {lista30}")
T73 = ("se rematarán, en forma presencial, el día 5 de noviembre de 2026, a las 12:30 horas, los siguientes inmuebles: 1) Departamento N° 41 "
       "del 4 piso, bodega N° 41 del subterráneo y estacionamiento N° 22, del edificio ubicado en Avenida Holanda N° 280. Mínimo para "
       "comenzar las posturas: $130.690.779.- y 2) Departamento N° 31 del 3er piso del edificio ubicado en Avenida Perú N° 674-680. "
       "Mínimo para comenzar las posturas: $ 92.362.264.-.")
lista73 = [x["inmueble"] for x in minimo_y_costas(T73)["minimo"].get("lista", [])]
if lista73 != ["departamento 41", "departamento 31"]:
    fallas.append(f"etiqueta. aviso 73 del 06-10 dio {lista73}")
print("etiquetas de listas. aviso 30 del 14-10", lista30, "y aviso 73 del 06-10", lista73)
# Decisión de Diego del 18 de Octubre (opción C). Una fecha anterior a la edición no cuenta para la regla de los dos avisos pegados.
# Caso real del 09-10 (rol C-22836-2024). "según resolución del 4 de septiembre de 2026" daba una falsa alarma y borraba todo el aviso.
from motor.procesar_edicion import desde_captura
_, _, _a09, _ = desde_captura("2026-10-09", RAIZ / "banco_pruebas" / "2026-10-09")
_x = [extraer(a.texto, "2026-10-09") for a in _a09 if a.rol == "22836"]
if not (_x and not _x[0]["pegado"] and _x[0]["fecha_remate"]["valor"] == "2026-11-04" and _x[0]["tribunal"]["valor"]):
    fallas.append(f"pegado falso del 09-10 rol 22836-2024 {[(x['pegado'], x['fecha_remate']['valor'], x['tribunal']['valor']) for x in _x]}")
# El pegado real del 16-10 (Buin con Viña del Mar, comienzo y final reales unidos) sigue marcado, porque sus dos fechas son futuras.
_peg = ("REMATE: 2° JUZGADO DE LETRAS de Buin subastará el 4 de noviembre de 2026, a las 13:00 horas, a través de la plataforma digital zoom. "
        "Demás bases y antecedentes constan en causa Rol C-1442-2024, caratulada ‘Banco del Estado de Chile con Instalación de Calefacción Acugas Ltda.’. "
        "Banco de Chile con Hinojosa, Rol C-1177-2025, fijó remate para el 10 de noviembre de 2026, a las 9.30 horas para inmueble de calle")
if not extraer(_peg, "2026-10-16")["pegado"]:
    fallas.append("el pegado real de Buin con Viña del Mar dejó de marcarse")
print("dos fechas. 09-10 rol 22836-2024 sin falsa alarma", bool(_x) and not _x[0]["pegado"], "| pegado real de Buin con Viña del Mar marcado", extraer(_peg, "2026-10-16")["pegado"])
# Modalidad (18 de Octubre, aprobado por Diego). Una comparación hipotética no hace mixto un remate por Zoom (17-10, rol 435-2024).
# Un remate que de verdad ofrece las dos formas sigue mixto (16-10, Cobranza de Concepción, rol 770-2014).
from motor.extraccion import modalidad
CASOS_MODALIDAD = {
    "El remate decretado precedentemente se realizará mediante la plataforma virtual ‘zoom’, debiendo contar las partes con computador. "
    "Se insta a las partes a comparecer puntualmente a la hora señalada en la presente resolución, en los mismos términos que si esta "
    "se hiciere de forma presencial en dependencias del tribunal, bajo apercibimiento de realizarse la diligencia solo con quienes asistan.": "zoom",
    "Ingenieria y Servicios Mecanicos Ltda., vía plataforma Zoom o en forma presencial, 11/11/2026, 10:00 horas, Rematará inmueble": "mixta",
}
for texto, esperado in CASOS_MODALIDAD.items():
    obtenido = modalidad(texto)["modalidad"]["valor"]
    if obtenido != esperado:
        fallas.append(f"modalidad. '{texto[:50]}' dio {obtenido} y debía dar {esperado}")
print(f"casos fijos de modalidad {len(CASOS_MODALIDAD)}")
# Garantía con el porcentaje impreso sin el signo % (18 de Octubre, aprobado por Diego). Caso inventado, porque el real es del
# banco de validación (06-10 rol 8679-2024, "garantía equivalente al 20 del mínimo"). Con signo se sigue leyendo igual.
from motor.extraccion import garantia
_g = garantia("los postores deberán constituir garantía equivalente al 15 del mínimo fijado, mediante vale vista endosable a la orden del Tribunal.")
if not (_g["garantia"]["porcentaje"] == 15 and _g["garantia"]["base"] == "minimo" and any(t == "error_escritura" for t, _ in _g["alertas"])):
    fallas.append(f"garantía sin signo %. dio {_g}")
_g2 = garantia("deberán rendir garantía por el 10% del mínimo, mediante vale vista. Plazo de 15 días.")
if not (_g2["garantia"]["porcentaje"] == 10 and not any(t == "error_escritura" for t, _ in _g2["alertas"])):
    fallas.append(f"garantía con signo %. dio {_g2}")
print("garantía sin signo %", _g["garantia"]["porcentaje"], [t for t, _ in _g["alertas"]])
# F2-02 (1 de Noviembre). Una fecha que va después de "deberá ser entregado" es la entrega del vale vista y no otro remate.
# C-5618-2025 del 25 de Octubre (aviso 59) quedaba como pegado, sin fecha ni tribunal. El 22 de Octubre aviso 81 es un pegado
# real (29° Civil C-11540-2023 con el juicio arbitral Esparza/Torres) y debe seguir marcado. Capturas en banco_pruebas.
from motor.procesar_edicion import desde_captura
def _aviso(f, o):
    return [a for a in desde_captura(f, RAIZ / "banco_pruebas" / f)[2] if a.orden == o][0].texto
x = extraer(_aviso("2026-10-25", 59), "2026-10-25")
ok = (not x["pegado"] and x["fecha_remate"]["valor"] == "2026-12-10" and x["hora_remate"]["valor"] == "13:00"
      and (x["tribunal"]["valor"] or "").startswith("13"))
print(("OK    " if ok else "FALLA ") + "F2-02. C-5618-2025 ya no es pegado y lee el 10 de Diciembre a las 13 en el 13° Civil")
if not ok: fallas.append("F2-02 falso pegado")
ok = extraer(_aviso("2026-10-22", 81), "2026-10-22")["pegado"]
print(("OK    " if ok else "FALLA ") + "F2-02. el pegado real del 22 de Octubre aviso 81 sigue marcado")
if not ok: fallas.append("F2-02 pegado real")
# 10 de Noviembre (aprobado por Diego). Fechas de remate que el programa no leía. Textos reales de la base, del 24 de Octubre al 10 de
# Noviembre. Cada caso es una regla distinta de motor\\extraccion.py y cada uno tiene su mutación anotada en la bitácora del 10.
from motor.extraccion import fecha_y_hora
def _fh(texto, edicion, fecha, hora, tipo_alerta=None, nombre=""):
    r = fecha_y_hora(texto, edicion)
    ok = (r["fecha_remate"]["valor"] == fecha and r["hora_remate"]["valor"] == hora and (r["fecha_remate"]["cita"] is None or r["fecha_remate"]["cita"] in texto)
          and (tipo_alerta is None or any(t == tipo_alerta for t, _ in r["alertas"])))
    print(("OK    " if ok else "FALLA ") + "fecha. " + nombre)
    if not ok: fallas.append(f"fecha. {nombre} dio {r['fecha_remate']['valor']} {r['hora_remate']['valor']} {r['alertas']}")
    return r
_T10 = "REMATE: 10° JUZGADO CIVIL SANtiago, ubicado en Huérfanos N° 1409, 3° Piso, rematará19 noviembre 2026 a las 13:00 horas. Departamento numero 2113"
_fh(_T10, "2026-10-24", "2026-11-19", "13:00", "detalle_menor", "día pegado a la palabra anterior (C-23164-2024, 10° Civil) con su alerta menor")
_fh(_T10.replace("rematará19", "rematará 19"), "2026-10-24", "2026-11-19", "13:00", None, "el mismo aviso bien escrito se lee igual")
if any(t == "detalle_menor" for t, _ in fecha_y_hora(_T10.replace("rematará19", "rematará 19"), "2026-10-24")["alertas"]):
    fallas.append("fecha. el aviso bien escrito recibió la alerta de día pegado")
_fh("REMATE. 11° JUZGADO CIVIL SANtiago, Huérfanos 1409, Piso 3, próximo 1° de Diciembre de 2026 a las 13:00 hrs., se remata de manera presencial",
    "2026-11-09", "2026-12-01", "13:00", None, "día con signo de ordinal (C-316-2024, 11° Civil)")
_T20 = ("caratulada “Vilchez con Vial y Consultores Asociados Ltda. y otra“, Rol C-35.144-2017, ha fijado audiencia para el día 24 de noviembre de 2026, "
        "a las 13:00 horas, con el objeto de proceder a la subasta, en forma telemática")
_fh(_T20, "2026-10-26", "2026-11-24", "13:00", None, "fecha antes del verbo, segunda pasada (C-35144-2017, 20° Civil)")
_fh("ANTE EL 1° JUZGADO DE CIVIL DE Santiago, Huérfanos 1409, piso 16. Con fecha martes 26 de enero del año 2027, a las 13:00 horas, se llevará a efecto la subasta",
    "2026-10-27", "2027-01-26", "13:00", None, "fecha antes del verbo con el año siguiente (C-10624-2025, 1° Civil)")
_fh("Por resolución de fecha 4 de septiembre de 2026, a las 13:00 horas, el tribunal ordenó la subasta del inmueble de autos.",
    "2026-10-09", None, None, "revisar_lectura", "una fecha anterior a la edición no cuenta en la segunda pasada (inventado a propósito)")
_T6843 = ("10° JUZGADO CIVIL DE SANTIAGO, Huérfanos 1409, 3° piso, comuna de Santiago, Región Metropolitana, se rematará de forma presencial, en las dependencias "
          "del Tribunal, el día 19 de noviembre a las 13:00 horas, la parcela número diecisiete")
_r = _fh(_T6843, "2026-10-30", "2026-11-19", "13:00", "error_escritura", "aviso sin año (C-6843-2024, 10° Civil) con alerta de error de escritura")
if not any("no dice el año del remate (19 de noviembre). Se tomó 2026" in t for _, t in _r["alertas"]):
    fallas.append(f"fecha. texto de la alerta de aviso sin año {_r['alertas']}")
_fh("se rematará el día 15 de enero a las 12:00 horas, el inmueble de autos", "2026-12-20", "2027-01-15", "12:00", "error_escritura",
    "aviso sin año de diciembre con remate en enero queda en el año siguiente (duda de Diego, inventado a propósito)")
_fh("se rematará el día 20 de diciembre a las 12:00 horas, el inmueble de autos", "2026-12-20", "2026-12-20", "12:00", "error_escritura",
    "aviso sin año con remate el mismo día de la edición queda en ese año (inventado a propósito)")
_fh(_T6843, None, None, None, "revisar_lectura", "sin fecha de edición no se asume ningún año")
_fh("se rematará el inmueble de autos. El vale vista deberá ser entregado el 18 de noviembre en la secretaría.", "2026-10-30", None, None, "revisar_lectura",
    "una fecha sin año después de entregar es del vale vista y no del remate (inventado a propósito)")
_r = _fh("se rematará el día 19 de noviembre de 2026 a las 13:00 horas. La audiencia de remate del 20 de noviembre queda sin efecto.", "2026-10-30", "2026-11-19", "13:00", None,
         "si hay una fecha completa de remate, la fecha sin año no se usa (inventado a propósito)")
if any(t == "error_escritura" for t, _ in _r["alertas"]):
    fallas.append("fecha. un aviso con fecha completa recibió la alerta de aviso sin año")
_r = _fh("REMATE: DÉCIMO SEGUNDO JUZgado Civil Santiago, Huérfanos 1409, 4° piso, el 25 de noviembre de 20026 a las 13:45 horas, mediante videoconferencia",
         "2026-11-06", "2026-11-25", "13:45", "error_escritura", "año mal impreso 20026 (C-10957-2025, 12° Civil) con alerta de error de escritura")
if not any("imprime mal el año del remate (25 de noviembre de 20026). Se tomó 2026" in t for _, t in _r["alertas"]):
    fallas.append(f"fecha. texto de la alerta de año mal impreso {_r['alertas']}")
_fh("ANTE EL JUZGADO LETRAS PEÑAflor, ubicado en Maria Ester Garay 135, Peñaflor, en proceso cumplimiento laboral, caratulado ’Varas / Maestranza Abitech SpA’, "
    "Rit N° C-10-2025, rematase el día 20 de Noviembre de 2026 a las 12:00 horas, los derechos", "2026-11-03", "2026-11-20", "12:00", None,
    "verbo rematase (C-10-2025, Juzgado de Letras de Peñaflor)")
_fh("Huérfanos 1409, 5° piso. Remátese 11 de noviembre de 2026, a las 13:30 horas, mediante plataforma Zoom", "2026-10-15", "2026-11-11", "13:30", None,
    "verbo remátese (C-18936-2024, edición del 15 de Octubre)")
# 11 de Noviembre. Verbo rematar en infinitivo. Texto real completo de C-17087-2016 del 2° Civil (ediciones del 7 al 10 de Noviembre).
# Sin el infinitivo el programa tomaba el 3 de Octubre de 2024 del informe de tasación (bitácora del 10, punto 30, y del 11).
_T17087 = "2° JUZGADO CIVIL DE SANTIAGO, causa Rol C-17.087-2016, caratulada ’Eurocapital S.A. con Ingeniería, Obras y Projectos Movterra Limitada’ Extracto. Remate En causa ejecutiva ante el 2° Juzgado Civil de Santiago, ubicado en calle Huérfanos 1409, piso 7, comuna de Santiago, causa Rol C-17.087- 2016, caratulada ’Eurocapital S.A. con Ingeniería, Obras y Projectos Movterra Limitada’, se dispuso rematar el día 1 de diciembre de 2026, a las 12:00 horas, por sistema de videoconferencia, a través de la plataforma Zoom, el inmueble ubicado en El Lote N° 24, formado del Lote Veinticuatro de la subdivisión del lote b), ubicado en un retazo de terreno ubicado en el título Pichinal, comuna de San Fabián, Región de Ñuble, la cual se encuentra Inscrita a fojas 6624 número 4594 del Registro de Propiedad del Conservador de Bienes Raíces de San Carlos correspondiente al año 2015, en el estado material y jurídico en que se encuentra, con todos sus usos, costumbres y servidumbres, y todo lo que esté en el plantado, cercado o construido. El precio mínimo para hacer las posturas en el remate y para adjudicarse la propiedad será la cantidad de $114.367.353, correspondiente a cuatro novenos del valor comercial del inmueble conforme al informe de tasación emitido con fecha 3 de octubre de 2024. De conformidad a lo establecido en el artículo 29 de Ley 21.389, no se admitirá la participación como postores de personas que cuenten con inscripción vigente en calidad de deudores en el Registro Nacional de Deudores de Alimentos. Para participar en la subasta, todo postor, a excepción del ejecutante, deberá rendir la garantía para participar en la subasta, equivalente al 10% del mínimo fijado, mediante vale vista bancario a la orden del tribunal, tomado por la persona que comparecerá a la subasta, o por el representante legal, en caso de que esta fuera persona jurídica, garantía que se imputará al precio del remate, o se hará efectiva en la forma legal. Los interesados deberán presentar el vale vista en dependencias del tribunal, el día hábil anterior a la fecha fijada para el remate, entre las 12:00 y 14:00 horas, debiendo entregar copia de su carnet de identidad, además de señalar el nombre completo del postor, su mail y teléfono, a fin de coordinar su participación vía correo electrónico y recibir el link con la invitación del remate a efectuarse por videoconferencia a través de la plataforma Zoom. Demás antecedentes en bases de la subasta en Secretaría del Tribunal."
_r = _fh(_T17087, "2026-11-07", "2026-12-01", "12:00", None, "verbo rematar en infinitivo, no la fecha de la tasación (C-17087-2016, 2° Civil)")
if _r["alertas"]:
    fallas.append(f"fecha. C-17087-2016 dejó alertas {_r['alertas']}")
_fh("JUEZ PARTIDOR CRISTIAN LAUbrie Pino, procederá a rematar el día 17 de noviembre de 2026, a las 16:00 horas: Inmueble ubicado en calle Jorge Cáceres N° 750",
    "2026-10-30", "2026-11-17", "16:00", None, "procederá a rematar (juez partidor del 30 de Octubre)")
# 11 de Noviembre. Resguardo de la fecha anterior a la edición (decisión de Diego). Se le quita el verbo al texto real de C-17087-2016
# (cambiado por una frase más larga para que la fecha buena siga fuera de la ventana) y la primera pasada vuelva a caer en la tasación, y el resguardo debe tomar la futura con hora y alertar.
_r = _fh(_T17087.replace("se dispuso rematar el día", "se dispuso fijar audiencia el día"), "2026-11-07", "2026-12-01", "12:00", "revisar_lectura",
         "resguardo. fecha anterior a la edición con otra futura con hora (C-17087-2016 sin verbo)")
if not any("anterior a la edición (3 de Octubre de 2024)" in t and "1 de Diciembre de 2026" in t for _, t in _r["alertas"]):
    fallas.append(f"fecha. texto de la alerta del resguardo {_r['alertas']}")
if any(t == "error_escritura" for t, _ in _r["alertas"]):
    fallas.append("fecha. el resguardo dejó además la alerta de fecha anterior a la edición")
_fh("REMATE. ANTE EL 28° JUZGADO CIvil Santiago, Huérfanos 1409, se subastará el día 06 de noviembre de 2024, a las 13:10 horas, por videoconferencia",
    "2026-10-28", "2024-11-06", "13:10", "error_escritura", "resguardo. aviso mal impreso sin otra fecha futura sigue con su alerta (C-18503-2019, 28° Civil)")
for c, n in aciertos.items():
    print(f"{c:12} aciertos {n} de {len(banco)} (mínimo {MINIMOS[c]})")
    if n < MINIMOS[c]: fallas.append(f"{c} bajó a {n} aciertos")
for f in fallas: print("FALLA", f)
print("\nRESULTADO.", "TODO OK" if not fallas else f"{len(fallas)} fallas")
sys.exit(1 if fallas else 0)

"""Parte 3.7a. Mide la regla del vale vista (IA más verificador más cálculo) contra un banco.

Uso (desde D:\\Agendar_Remates).
  .venv\\Scripts\\python -m pruebas.medir_vale_vista 14            usa solo respuestas guardadas (sin internet)
  .venv\\Scripts\\python -m pruebas.medir_vale_vista 14 --llamar   llama a Haiku para lo que falte y lo guarda
14 = banco de AJUSTE (2026-10-14). 06 = banco de VALIDACIÓN (2026-10-06), que se corre UNA sola vez con las
instrucciones congeladas y la aprobación de Diego.
La fecha y la hora del remate se toman del banco, para medir solo el vale vista.

Clasificación por remate.
  acierto. Mismo color y mismo desde y hasta.
  ambar_de_mas. Lo anotado es verde y el programa da ámbar con las mismas fechas (más prudente, no es error).
  no_leido. El programa da rojo o sin_dato cuando lo anotado tiene fechas (Diego lo lee en el aviso, no es error).
  EQUIVOCADO. El programa da verde o ámbar con fechas distintas, o verde cuando lo anotado es ámbar, rojo o sin_dato,
             o ámbar cuando lo anotado es rojo o sin_dato.
"""
import json, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.cortador import construir_rollo, cortar
from motor.orden_columnas import leer_pagina
from motor import vale_vista as V
from db.carga import es_partidor

PRECIO = {"entrada": 0.10, "salida": 0.50, "cache_lectura": 0.01, "cache_escritura": 0.125}   # dólares por millón, Haiku 5.5 (16-10-2026)
COLOR = {"calculado": "verde", "revisar": "ambar", "sin_dato": "sin_dato", "rojo": "rojo"}


def cargar(cual):
    if cual == "14":
        d, pags, edicion = RAIZ / "banco_pruebas" / "2026-10-14", ("B11", "C8"), "2026-10-14"
        banco = json.loads((d / "banco_nivel2_2026-10-14.json").read_text(encoding="utf-8"))["avisos"]
        esperado = {}
        for x in banco:
            v = x["vale_vista"]
            e = {"color": COLOR[v["vv_estado"]], "desde": v["vv_desde"], "hasta": v["vv_hasta"], "fecha": x["fecha_remate"]["valor"],
                 "hora": x["hora_remate"]["valor"], "alternativa": None}
            if v["regla"] == "fecha_dicha_en_aviso":      # aviso 9, contradicción interna. Ahora se espera rojo
                e.update(color="rojo", desde=None, hasta=None)
            esperado[x["n"]] = e
    else:
        d, pags, edicion = RAIZ / "banco_pruebas" / "2026-10-06", ("B7", "B8", "B9", "B10"), "2026-10-06"
        banco = json.loads((d / "banco_vale_vista_2026-10-06.json").read_text(encoding="utf-8"))["avisos"]
        esperado = {x["n"]: {"color": COLOR.get(x["vv_estado"], x["vv_estado"]), "desde": x["vv_desde"], "hasta": x["vv_hasta"],
                             "fecha": x["fecha_remate"], "hora": x["hora_remate"], "alternativa": x.get("lectura_alternativa_aceptada")}
                    for x in banco}
    rollo, m = construir_rollo([(n, leer_pagina(d / f"mercurio_{edicion}_{n}.txt")) for n in pags])
    av = {a.orden: a for a in cortar(rollo, m)}
    return d, edicion, av, esperado


def clasificar(res, e):
    pc, ec = res["color"], e["color"]
    if e["alternativa"] and res.get("regla") == e["alternativa"]:
        return "acierto"
    mismas = (res["vv_desde"], res["vv_hasta"]) == (e["desde"], e["hasta"])
    if pc == ec and (mismas or pc in ("rojo", "sin_dato")):
        return "acierto"
    if pc in ("rojo", "sin_dato"):
        return "no_leido" if ec in ("verde", "ambar") else "acierto"
    if pc == "ambar" and ec == "verde" and mismas:
        return "ambar_de_mas"
    return "EQUIVOCADO"


def main():
    cual = sys.argv[1] if len(sys.argv) > 1 else "14"
    llamar = "--llamar" in sys.argv
    d, edicion, av, esperado = cargar(cual)
    cliente = V.cliente_desde_config() if llamar else None
    lineas, cuenta, uso = [], {}, {k: 0 for k in PRECIO}
    for n in sorted(esperado):
        e, a = esperado[n], av[n]
        if e["color"] == "no_se_mide" or es_partidor(None, a.texto):
            continue
        g = V.leer_con_ia(a.texto, cliente) if llamar else V.leer_guardada(a.texto)
        if not g:
            lineas.append(f"{n:>3} SIN RESPUESTA GUARDADA"); cuenta["sin_respuesta"] = cuenta.get("sin_respuesta", 0) + 1; continue
        for u in g.get("uso", []):
            for k in uso: uso[k] += u.get(k, 0)
        res = V.resolver(g["lecturas"], a.texto, e["fecha"], e["hora"], edicion)
        c = clasificar(res, e)
        cuenta[c] = cuenta.get(c, 0) + 1
        lineas.append(f"{n:>3} {c:<12} programa {res['color']:<8} {res.get('regla')} {res['vv_desde']} -> {res['vv_hasta']} {res['preguntas'] or ''}"
                      f" | anotado {e['color']} {e['desde']} -> {e['hasta']}" + (f" | {'; '.join(res['motivos'])}" if res["motivos"] else "")
                      + (f" | errores IA {g['errores']}" if g.get("errores") else ""))
    costo = sum(uso[k] * PRECIO[k] / 1e6 for k in PRECIO)
    resumen = (f"Banco {edicion}. Modelo {V.MODELO}, instrucciones {V.VERSION_INSTRUCCIONES}. "
               + ", ".join(f"{k} {v}" for k, v in sorted(cuenta.items()))
               + f". Tokens entrada {uso['entrada']}, salida {uso['salida']}, caché leída {uso['cache_lectura']}, caché escrita {uso['cache_escritura']}."
               + f" Costo de las llamadas guardadas {costo:.4f} dólares.")
    salida = resumen + "\n\n" + "\n".join(lineas) + "\n"
    print(salida)
    (d / f"MEDICION_VV_{edicion}_{V.VERSION_INSTRUCCIONES}.txt").write_text(salida, encoding="utf-8")


if __name__ == "__main__":
    main()

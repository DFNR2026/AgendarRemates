"""Mide el cortador contra el inventario correcto del banco de pruebas.
Correr desde D:\\Agendar_Remates con. python -m pruebas.test_cortador  (agrega -v para ver el detalle)"""
import json, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.cortador import construir_rollo, cortar
from motor.orden_columnas import leer_pagina

B = RAIZ / "banco_pruebas"
VERBOSO = "-v" in sys.argv

def paginas_0806():
    out = []
    for n in (11, 12, 13):
        a = (B / f"2026-08-06/payload_B-20260806-0{n}.0.txt").read_text(encoding="utf-8")
        b = (B / f"2026-08-06/payload_B-20260806-0{n}.1.txt").read_text(encoding="utf-8")
        out.append((f"B{n}", a + b[2000:]))
    return out

def paginas_1014():
    return [("B11", (B / "2026-10-14/mercurio_2026-10-14_B11.txt").read_text(encoding="utf-8")),
            ("C8", (B / "2026-10-14/mercurio_2026-10-14_C8.txt").read_text(encoding="utf-8"))]

def paginas_1014_posicion():
    # Mismas dos páginas, ordenadas por la posición impresa (.geo.json capturado el 2026-10-15; el .txt es idéntico al del banco)
    return [("B11", leer_pagina(B / "2026-10-14/mercurio_2026-10-14_B11.txt")),
            ("C8", leer_pagina(B / "2026-10-14/mercurio_2026-10-14_C8.txt"))]

fallas = 0
for etiqueta, paginas in (("2026-08-06", paginas_0806()), ("2026-10-14", paginas_1014()),
                          ("2026-10-14 (orden por posición)", paginas_1014_posicion())):
    fecha = etiqueta[:10]
    inv = json.loads((B / fecha / f"inventario_correcto_{fecha}.json").read_text(encoding="utf-8"))["avisos"]
    rollo, marcas = construir_rollo(paginas)
    avisos = cortar(rollo, marcas)
    esperados = [a["rol"] for a in inv if a["rol"]]
    sin_rol_esperados = sum(1 for a in inv if not a["rol"])
    aislados = {f"{a.rol}-{a.anio}" for a in avisos if len(a.roles) == 1}
    todos = {f"{n}-{y}" for a in avisos for _, n, y in a.roles}
    no_aislados = [r for r in esperados if r not in aislados]
    inventados = sorted(todos - set(esperados))
    sin_rol = [a for a in avisos if not a.roles]
    dudosos = [a for a in avisos if a.revisar or len(a.roles) > 1]
    print(f"\n=== {etiqueta} ===")
    print(f"Avisos esperados {len(inv)} ({len(esperados)} con rol, {sin_rol_esperados} sin rol) | avisos cortados {len(avisos)}")
    print(f"Roles aislados correctamente {len(esperados) - len(no_aislados)} de {len(esperados)}")
    print(f"Roles inventados {len(inventados)} {inventados}")
    print(f"Trozos sin rol {len(sin_rol)} (esperados {sin_rol_esperados})")
    print(f"Trozos marcados para revisión o con dos roles {len(dudosos)}")
    if no_aislados: print("  NO AISLADOS.", no_aislados)
    for a in sin_rol if VERBOSO or len(sin_rol) != sin_rol_esperados else []:
        print(f"  sin rol #{a.orden} {a.paginas} {a.texto[:110]!r} ... {a.texto[-60:]!r}")
    for a in dudosos:
        print(f"  dudoso #{a.orden} {a.roles} {a.revisar} {a.texto[:90]!r}")
    if no_aislados or inventados or len(sin_rol) != sin_rol_esperados or dudosos:
        fallas += 1
# --- Orden por posición. Casos reales donde el orden del visor falla ---------------------------------
def _cortar_sola(nombre):
    t = leer_pagina(B / f"2026-10-11/mercurio_2026-10-11_{nombre}.txt")
    rollo, marcas = construir_rollo([(nombre, t)])
    return rollo, cortar(rollo, marcas)

# F9 del 2026-10-11. El visor entrega las columnas 1,2,4,5,6,7,3 y deja 3 trozos dudosos.
# Por posición solo debe quedar dudoso el primero (empieza en minúscula porque viene de F8, que aquí no se incluye).
rollo, avisos = _cortar_sola("F09")
dudosos = [a.orden for a in avisos if a.revisar or len(a.roles) > 1]
print(f"\n=== 2026-10-11 F9 sola (orden por posición) ===\nAvisos {len(avisos)} (esperados 19) | dudosos {dudosos} (esperado [1])")
if len(avisos) != 19 or dudosos != [1]:
    fallas += 1

# F15 del 2026-10-11. Al pie hay una franja "1300 EMPLEOS" que cruza las columnas. No debe mezclarse con los remates.
# Además trae tres avisos que antes salían pegados en un solo trozo (corregido el 2026-10-15):
# Temuco (RIT C-357-2024, sin cierre) | JUZGADO DE LETRAS DE COLINA (Rol C-10387-2019) | COMUNA PROVIDENCIA REMATA (partidor, sin rol).
rollo, avisos = _cortar_sola("F15")
intrusos = [w for w in ("Profesionales se necesitan", "MUNDO LABORAL", "EMPLEOS") if w in rollo]
dudosos = [a.orden for a in avisos if a.revisar or len(a.roles) > 1]
separados = (any(a.rol == "357" and len(a.roles) == 1 for a in avisos)
             and any(a.rol == "10387" and a.texto.startswith("JUZGADO DE LETRAS DE COLINA") and "REMATA" not in a.texto for a in avisos)
             and any(a.texto.startswith("COMUNA PROVIDENCIA REMATA") for a in avisos))
print(f"\n=== 2026-10-11 F15 sola (orden por posición) ===\nAvisos {len(avisos)} (esperados 12) | empleos dentro del rollo {intrusos} (esperado []) | dudosos {dudosos} (esperado []) | Temuco, Colina y partidor separados {separados}")
if len(avisos) != 12 or intrusos or dudosos or not separados:
    fallas += 1

# B11 del 2026-10-09. "entregado materialmente en la secretaría del tribunal" no es un cierre: el aviso del rol 1911-2020
# termina en "Secretaria." y el siguiente empieza en "POR RESOLUCIÓN DEL 1° JUZGADO" (rol 5598-2024).
# Quedan dudosos solo el 10 (un aviso que imprime dos roles, C-3673-2025 y C-14254-2025: errata del diario a revisar)
# y el 43 (termina cortado porque sigue en B12, que aquí no se incluye).
t = leer_pagina(B / "2026-10-09/mercurio_2026-10-09_B11.txt")
rollo, marcas = construir_rollo([("B11", t)])
avisos = cortar(rollo, marcas)
dudosos = [a.orden for a in avisos if a.revisar or len(a.roles) > 1]
ok_5598 = any(a.rol == "5598" and a.texto.startswith("POR RESOLUCIÓN DEL 1° JUZGADO") for a in avisos)
ok_1911 = any(a.rol == "1911" and a.texto.endswith("Secretaria.") for a in avisos)
print(f"\n=== 2026-10-09 B11 sola (orden por posición) ===\nAvisos {len(avisos)} (esperados 43) | dudosos {dudosos} (esperado [10, 43]) | 1911 y 5598 bien partidos {ok_1911 and ok_5598}")
if len(avisos) != 43 or dudosos != [10, 43] or not (ok_1911 and ok_5598):
    fallas += 1

print("\nRESULTADO.", "TODO OK" if not fallas else f"{fallas} ediciones con diferencias")
sys.exit(1 if fallas else 0)

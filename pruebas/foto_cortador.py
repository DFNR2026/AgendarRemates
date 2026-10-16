"""Foto del cortador en las 7 fechas capturadas (8 rollos, el 09-10 tiene B y G). No es una prueba de TODO OK.
Sirve para medir un cambio del cortador, comparando una foto de antes con una de después.
Uso. python -m pruebas.foto_cortador sacar NOMBRE          (guarda banco_pruebas/fotos_cortador/NOMBRE.json)
     python -m pruebas.foto_cortador comparar ANTES DESPUES (muestra cada aviso que cambió)
Lee capturas\\ (fuera de git). Por cada aviso guarda orden, posición en el rollo, rol, comienzo, final y huella del texto.
"""
import hashlib, json, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.cortador import construir_rollo, cortar
from motor.orden_columnas import leer_pagina

DIR = RAIZ / "banco_pruebas" / "fotos_cortador"


def rollos():
    for d in sorted((RAIZ / "capturas").iterdir()):
        fs = sorted(d.glob("*.txt"))
        letras = sorted({f.name[0] for f in fs})
        if d.name == "2026-10-09":                     # los viernes el cuerpo G repite al B. Se miden por separado
            for L in letras:
                yield f"{d.name} {L}", [f for f in fs if f.name[0] == L]
        else:
            yield d.name, fs


def sacar(nombre):
    foto = {}
    for etiqueta, fs in rollos():
        r, m = construir_rollo([(f.name[:3], leer_pagina(f)) for f in fs])
        foto[etiqueta] = [{"orden": a.orden, "inicio": a.inicio, "fin": a.inicio + len(a.texto), "rol": f"{a.rol}-{a.anio}" if a.rol else None,
                           "revisar": a.revisar, "comienzo": a.texto[:90], "final": a.texto[-60:],
                           "huella": hashlib.md5(a.texto.encode("utf-8")).hexdigest()} for a in cortar(r, m)]
    DIR.mkdir(parents=True, exist_ok=True)
    (DIR / f"{nombre}.json").write_text(json.dumps(foto, ensure_ascii=False, indent=1), encoding="utf-8")
    for e, avs in foto.items():
        print(f"{e:14} avisos {len(avs):4} | marcados para revisión {sum(1 for a in avs if a['revisar'])}")


def comparar(antes, despues):
    A = json.loads((DIR / f"{antes}.json").read_text(encoding="utf-8"))
    B = json.loads((DIR / f"{despues}.json").read_text(encoding="utf-8"))
    for e in A:
        ha, hb = {a["huella"] for a in A[e]}, {b["huella"] for b in B[e]}
        quitados = [a for a in A[e] if a["huella"] not in hb]
        nuevos = [b for b in B[e] if b["huella"] not in ha]
        print(f"\n=== {e}. {len(A[e])} a {len(B[e])} avisos. Cambian {len(quitados)} de antes por {len(nuevos)} de después")
        for a in quitados:
            print(f"  ANTES   #{a['orden']:3} rol {a['rol']} | {a['comienzo'][:70]!r} ... {a['final'][-40:]!r}")
        for b in nuevos:
            print(f"  DESPUÉS #{b['orden']:3} rol {b['rol']} | {b['comienzo'][:70]!r} ... {b['final'][-40:]!r} {('REVISAR ' + b['revisar']) if b['revisar'] else ''}")


if __name__ == "__main__":
    if sys.argv[1] == "sacar":
        sacar(sys.argv[2])
    else:
        comparar(sys.argv[2], sys.argv[3])

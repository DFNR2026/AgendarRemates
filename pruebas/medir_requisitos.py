"""Mide los requisitos para participar por tribunal, con motor\\requisitos.py. Nunca llama a Haiku ni escribe en la base.
Uso, siempre sobre una COPIA de la base (la real no se abre desde aquí).
  python -m pruebas.medir_requisitos RUTA_COPIA               muestra la tabla por tribunal
  python -m pruebas.medir_requisitos RUTA_COPIA --guardar     además escribe db\\requisitos_patron.json, que usa la ficha para la advertencia de patrón roto
  python -m pruebas.medir_requisitos RUTA_COPIA --frases      además escribe banco_pruebas\\requisitos\\frases_por_tribunal.txt, para releer a mano
Se cuenta por CAUSA y no por aviso (decisión de Diego, 13 de Noviembre). De cada causa vale su aviso más nuevo. Solo los Juzgados
Civiles de Santiago, que es donde se hizo la investigación."""
import collections, datetime as dt, difflib, json, re, sqlite3, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor import requisitos as R

MESES = "Enero Febrero Marzo Abril Mayo Junio Julio Agosto Septiembre Octubre Noviembre Diciembre".split()


def causas(ruta):
    con = sqlite3.connect(f"file:{Path(ruta).as_posix()}?mode=ro", uri=True)
    q = ("SELECT a.tribunal, a.rol, a.anio, e.fecha, a.texto FROM avisos a JOIN ediciones e ON e.id = a.edicion_id "
         "WHERE a.tribunal LIKE '%Juzgado Civil de Santiago' AND a.filtro_estado != 'descartado' ORDER BY e.fecha, a.id")
    ult = {}
    for trib, rol, anio, fecha, texto in con.execute(q):
        ult[(trib, rol, anio)] = (fecha, texto)          # queda el aviso más nuevo de cada causa
    con.close()
    por = collections.defaultdict(list)
    for (trib, rol, anio), (fecha, texto) in ult.items():
        por[trib].append({"rol": f"{rol}-{anio}", "fecha": fecha, "texto": texto, "req": R.leer(texto)})
    return por


def numero(t):
    return int(re.match(r"(\d+)", t).group(1))


def tabla(por):
    out = {}
    for trib in sorted(por, key=numero):
        cuenta = collections.Counter()
        for c in por[trib]:
            for k in {r["clave"] for r in c["req"]}:
                cuenta[k] += 1
        out[trib] = {"causas": len(por[trib]), "requisitos": {k: cuenta[k] for k in R.ORDEN if cuenta[k]}}
    return out


def frases(por, destino):
    """Las frases de requisito de cada tribunal, juntando las casi iguales, con su n de causas. Es lo que se lee a mano."""
    lineas = []
    for trib in sorted(por, key=numero):
        grupos = []
        for c in por[trib]:
            for r in c["req"]:
                k = re.sub(r"\d+", "#", r["frase"].lower())
                for g in grupos:
                    if g[0] == r["clave"] and difflib.SequenceMatcher(None, g[1], k, autojunk=False).quick_ratio() > 0.8 \
                            and difflib.SequenceMatcher(None, g[1], k, autojunk=False).ratio() > 0.72:
                        g[3].add(c["rol"])
                        break
                else:
                    grupos.append([r["clave"], k, r, {c["rol"]}])
        grupos.sort(key=lambda g: (R.ORDEN.index(g[0]), -len(g[3])))
        lineas.append(f"\n##### {trib}. {len(por[trib])} causas")
        for clave, _, r, roles in grupos:
            lineas.append(f"[{clave} n={len(roles)}] ({', '.join(sorted(roles)[:3])}) {r['detalle']}"
                          + (f" | plazo. {r['plazo']}" if r["plazo"] else "") + (f" | correo. {r['correo']}" if r["correo"] else "")
                          + f"\n    “{r['frase']}”")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return len(lineas)


def main(argv):
    if not argv or argv[0].startswith("--"):
        print(__doc__)
        return 2
    ruta = Path(argv[0])
    if ruta.resolve() == (RAIZ / "agendar_remates.db").resolve():
        print("Esa es la base real. Saca una copia y mide sobre la copia.")
        return 2
    por = causas(ruta)
    t = tabla(por)
    claves = [k for k in R.ORDEN if any(k in v["requisitos"] for v in t.values())]
    print("tribunal".ljust(8), "n".rjust(3), " ".join(k[:8].ljust(8) for k in claves))
    for trib, v in t.items():
        print((str(numero(trib)) + "°").ljust(8), str(v["causas"]).rjust(3), " ".join(str(v["requisitos"].get(k, 0)).ljust(8) for k in claves))
    print("\nPatrones fuertes (", int(R.UMBRAL * 100), "% y al menos", R.MIN_CAUSAS, "causas )")
    datos = {"tribunales": t}
    for trib in t:
        f = R.fuertes(trib, datos)
        if f:
            print(" ", str(numero(trib)) + "°", ", ".join(f"{k} {si} de {n}" for k, si, n in f))
    fechas = sorted(c["fecha"] for cs in por.values() for c in cs)
    if "--guardar" in argv:
        h = dt.date.today()
        datos = {"medido_el": f"{h.day} de {MESES[h.month - 1]} de {h.year}", "ediciones": [fechas[0], fechas[-1]],
                 "causas": sum(v["causas"] for v in t.values()), "cuenta_por": "causa, con su aviso más nuevo", "tribunales": t}
        (RAIZ / "db" / "requisitos_patron.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("\nEscrito db\\requisitos_patron.json")
    if "--frases" in argv:
        n = frases(por, RAIZ / "banco_pruebas" / "requisitos" / "frases_por_tribunal.txt")
        print("Escrito banco_pruebas\\requisitos\\frases_por_tribunal.txt,", n, "líneas")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

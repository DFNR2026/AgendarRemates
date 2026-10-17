"""Banco de rojos (idea de Diego del 17 de Octubre). Un registro por cada aviso cuyo vale vista quedó en rojo o sin dato,
para que Claude los analice cada semana y proponga mejoras con el total acumulado (nunca con el último caso).

El banco se arma leyendo una base YA cargada más las respuestas guardadas de Haiku. resolver() da siempre lo mismo con la
misma respuesta, así que los motivos técnicos se reconstruyen sin volver a llamar a la IA. Sirve igual después de una
carga, después de retomar y para llenar el banco con ediciones viejas.

Archivos banco_rojos\\rojos_AAAA-MM.jsonl (mes de la edición), un registro JSON por línea. Sin duplicados por
(edición, aviso, versión de las instrucciones). Si el mismo texto ya estaba en el banco con otra edición, el registro
nuevo queda marcado como republicación. El campo revision queda vacío para la revisión semanal.

Uso. python -m motor.banco_rojos AAAA-MM-DD RUTA_BASE
"""
import datetime as dt, hashlib, json, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor import vale_vista as V
from motor.procesar_edicion import traducir_motivo, texto_rojo

CARPETA = RAIZ / "banco_rojos"
COLOR_SQL = ("CASE WHEN r.vv_estado = 'revisar' AND r.vv_hasta IS NULL THEN 'rojo' "
             "WHEN r.vv_estado = 'sin_dato' THEN 'sin_dato' END")


def md5_codigo() -> str:
    return hashlib.md5((RAIZ / "motor" / "vale_vista.py").read_bytes()).hexdigest()


def registros_de_edicion(con, fecha: str) -> list:
    """Un registro por aviso visible de la edición con el vale vista en rojo o sin dato (leído por la IA)."""
    filas = con.execute(
        f"SELECT a.orden, a.texto, a.rol_impreso, a.tribunal, p.ruta, MIN(r.fecha_remate), MIN(r.hora_remate), {COLOR_SQL} AS color "
        "FROM avisos a JOIN ediciones e ON e.id = a.edicion_id JOIN remates r ON r.aviso_id = a.id "
        "LEFT JOIN paginas p ON p.id = a.pagina_inicio_id "
        "WHERE e.fecha = ? AND a.filtro_estado <> 'descartado' GROUP BY a.id HAVING color IS NOT NULL ORDER BY a.orden", (fecha,)).fetchall()
    codigo = md5_codigo()
    out = []
    for orden, texto, rol, tribunal, ruta, f, h, color in filas:
        g = V.leer_guardada(texto)
        if not g:          # no debería pasar (el color solo existe si la IA respondió), pero no se inventa nada
            continue
        res = V.resolver(g["lecturas"], texto, f, h, fecha)
        pares = [traducir_motivo(m) for m in res["motivos"]]
        out.append({
            "edicion": fecha, "orden": orden, "rol": rol, "tribunal": tribunal, "ruta_pagina": ruta,
            "fecha_remate": f, "hora_remate": h, "color": color,
            "grupo": texto_rojo(res["motivos"]).split(". ")[0] if color == "rojo" else "Sin dato",
            "motivos_simples": list(dict.fromkeys(s for _, s in pares)), "motivos_tecnicos": res["motivos"],
            "regla_ia": [x.get("regla") for x in g["lecturas"]], "lecturas": g["lecturas"],
            "huella": V.huella(texto), "modelo": V.MODELO, "version_instrucciones": V.VERSION_INSTRUCCIONES, "md5_vale_vista": codigo,
            "texto": texto, "republicacion_de": None, "registrado_en": None, "revision": {},
        })
    return out


def _leer(carpeta: Path) -> list:
    out = []
    for p in sorted(carpeta.glob("rojos_*.jsonl")):
        out += [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    return out


def registrar(registros: list, carpeta: Path = CARPETA, ahora: str | None = None) -> dict:
    """Agrega los registros al banco. No repite (edición, aviso, versión). Marca la republicación por huella del texto."""
    carpeta.mkdir(parents=True, exist_ok=True)
    viejos = _leer(carpeta)
    claves = {(x["edicion"], x["orden"], x["version_instrucciones"]) for x in viejos}
    primera = {}
    for x in sorted(viejos, key=lambda x: x["edicion"]):
        primera.setdefault(x["huella"], x["edicion"])
    ahora = ahora or dt.datetime.now().isoformat(timespec="seconds")
    nuevos = repetidos = republicados = 0
    for r in registros:
        k = (r["edicion"], r["orden"], r["version_instrucciones"])
        if k in claves:
            repetidos += 1; continue
        r = dict(r, registrado_en=ahora)
        if primera.get(r["huella"], r["edicion"]) != r["edicion"]:
            r["republicacion_de"] = primera[r["huella"]]; republicados += 1
        primera.setdefault(r["huella"], r["edicion"])
        with open(carpeta / f"rojos_{r['edicion'][:7]}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        claves.add(k); nuevos += 1
    return {"nuevos": nuevos, "repetidos": repetidos, "republicaciones": republicados}


def desde_captura(fecha: str, carpeta_captura: Path | None = None) -> list:
    """Carga la edición capturada en una base temporal SOLO con respuestas guardadas (nunca llama a Haiku) y devuelve
    sus registros. Sirve para llenar el banco con ediciones viejas sin tocar ninguna base."""
    import tempfile
    from db.crear_base import crear
    from motor.procesar_edicion import cargar_edicion
    with tempfile.TemporaryDirectory() as t:
        con = crear(Path(t) / "temporal.db")
        try:
            cargar_edicion(con, fecha, dt.datetime.now().isoformat(timespec="seconds"), carpeta_captura, cliente=None)
            return registros_de_edicion(con, fecha)
        finally:
            con.close()


if __name__ == "__main__":
    # python -m motor.banco_rojos AAAA-MM-DD RUTA_BASE                        registra desde una base ya cargada
    # python -m motor.banco_rojos AAAA-MM-DD --desde-captura [CARPETA]       registra desde capturas (solo lo guardado)
    # --banco CARPETA cambia la carpeta del banco (lo usan las pruebas)
    a = sys.argv[1:]
    banco = Path(a[a.index("--banco") + 1]) if "--banco" in a else CARPETA
    if not a or a[0].startswith("--"):
        raise SystemExit("Uso. python -m motor.banco_rojos AAAA-MM-DD RUTA_BASE | AAAA-MM-DD --desde-captura [CARPETA]")
    fecha = a[0]
    if "--desde-captura" in a:
        k = a.index("--desde-captura")
        carpeta = Path(a[k + 1]) if len(a) > k + 1 and not a[k + 1].startswith("--") else None
        regs = desde_captura(fecha, carpeta)
    else:
        from db.crear_base import crear
        ruta = Path(a[1])
        if not ruta.exists():
            raise SystemExit(f"No existe la base {ruta}.")
        con = crear(ruta); regs = registros_de_edicion(con, fecha); con.close()
    print(fecha, registrar(regs, banco))

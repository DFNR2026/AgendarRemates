"""Une el motor con la base (paso 4 del ESTADO, 16 de Octubre). Lectura ya hecha -> corte -> extracción por código -> carga.

traducir() pasa lo que entrega motor.extraccion.extraer() al formato que espera db.carga.guardar_edicion()
(el del banco nivel 2). La carga guarda las citas con método 'codigo' y las alertas del código con su tipo.
Todavía no hay vale vista ni dirección (parte 3.7), así que cada remate queda con la alerta de vale vista no leído.

Uso. python -m motor.procesar_edicion AAAA-MM-DD RUTA_BASE   (desde D:\\Agendar_Remates)
Lee capturas\\AAAA-MM-DD (páginas y navegacion.json que guarda el lector). No carga en agendar_remates.db
hasta que Diego lo apruebe. Una edición con dos rollos (B y G los viernes) se rechaza, porque unirlos sin duplicar
es un paso aparte.
"""
import json, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from motor.cortador import construir_rollo, cortar, roles_en
from motor.orden_columnas import leer_pagina
from motor.extraccion import extraer
from db.carga import guardar_edicion

CAPTURAS = RAIZ / "capturas"


def traducir(x: dict) -> dict:
    """Salida de extraer() -> formato del banco nivel 2 (sin vale_vista ni dirección, que son de la parte 3.7)."""
    return {"tribunal": (x.get("tribunal") or {}).get("valor"),
            "fecha_remate": x["fecha_remate"], "hora_remate": x["hora_remate"], "modalidad": x["modalidad"],
            "plataforma": x.get("plataforma"), "minimo": x["minimo"], "garantia": x["garantia"],
            "alertas": list(x.get("alertas") or []), "dudas": []}


def extraer_avisos(avisos: list, fecha: str) -> dict:
    """{orden: datos traducidos} para todos los avisos del cortador."""
    return {a.orden: traducir(extraer(a.texto, fecha)) for a in avisos}


def desde_captura(fecha: str, carpeta: Path | None = None):
    """Arma edición, páginas y avisos desde capturas\\FECHA (navegacion.json del lector)."""
    d = carpeta or (CAPTURAS / fecha)
    nav = json.loads((d / "navegacion.json").read_text(encoding="utf-8"))
    if len(nav["rollos"]) != 1:
        raise ValueError(f"La edición {fecha} tiene {len(nav['rollos'])} rollos ({nav['rollos']}). Unirlos sin duplicar es un paso aparte. No se cargó nada.")
    por_nombre = {p["pagina"]: p for p in nav["paginas_con_remates"]}
    orden = nav["rollos"][0]
    paginas = [{"nombre": n, "cuerpo": n[0], "numero": int(n[1:]), "id_pagina": por_nombre[n]["id"], "orden_rollo": k,
                "texto": (d / por_nombre[n]["archivo"]).read_text(encoding="utf-8")}
               for k, n in enumerate(orden, start=1)]
    rollo, marcas = construir_rollo([(n, leer_pagina(d / por_nombre[n]["archivo"])) for n in orden])
    avisos = cortar(rollo, marcas)
    cuerpos = " ".join(f"{c}{v.split('n=')[-1]}" for c, v in sorted(nav["cuerpos"].items()))
    edicion = {"fecha": fecha, "leida_en": nav["leida_en"], "estado": "con_alarmas" if nav.get("alarmas") else "ok",
               "cuerpos_revisados": cuerpos, "roles_en_texto": len({(r[1], r[2]) for r in roles_en(rollo)})}
    return edicion, paginas, avisos


def cargar_edicion(con, fecha: str, ahora: str, carpeta: Path | None = None) -> dict:
    edicion, paginas, avisos = desde_captura(fecha, carpeta)
    return guardar_edicion(con, edicion, paginas, avisos, extraer_avisos(avisos, fecha), ahora, metodo="codigo")


if __name__ == "__main__":
    import datetime as dt
    from db.crear_base import crear, BASE
    if len(sys.argv) < 3:
        raise SystemExit("Uso. python -m motor.procesar_edicion AAAA-MM-DD RUTA_BASE")
    ruta = Path(sys.argv[2])
    if ruta.resolve() == BASE.resolve():
        raise SystemExit("Por ahora solo en bases de prueba. La base real espera la aprobación de Diego.")
    print(cargar_edicion(crear(ruta), sys.argv[1], dt.datetime.now().isoformat(timespec="seconds")))

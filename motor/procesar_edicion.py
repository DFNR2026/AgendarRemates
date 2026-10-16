"""Une el motor con la base (paso 4 del ESTADO, 16 de Octubre). Lectura ya hecha -> corte -> extracción por código -> carga.

traducir() pasa lo que entrega motor.extraccion.extraer() al formato que espera db.carga.guardar_edicion()
(el del banco nivel 2). La carga guarda las citas con método 'codigo' y las alertas del código con su tipo.
Todavía no hay vale vista ni dirección (parte 3.7), así que cada remate queda con la alerta de vale vista no leído.

Uso. python -m motor.procesar_edicion AAAA-MM-DD RUTA_BASE   (desde D:\\Agendar_Remates)
Lee capturas\\AAAA-MM-DD (páginas y navegacion.json que guarda el lector). No carga en agendar_remates.db
hasta que Diego lo apruebe. Una edición con dos rollos (B y G los viernes) se une sin duplicar por la huella del texto
de cada aviso (16 de Octubre, ver unir_rollos).
"""
import json, re, sys
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


def huella(texto: str) -> str:
    """Solo letras y números en minúscula. Ignora espacios, guiones y signos, que cambian entre la lectura de B y la de G
    (2026-10-09. 7 de 127 avisos con diferencias de espacios, 127 de 127 iguales con esta huella)."""
    return re.sub(r"[\W_]+", "", texto.lower())


def unir_rollos(cortados: list) -> tuple:
    """cortados = [avisos del cortador por rollo], en el orden de la navegación. El primero es el principal.
    Un aviso de otro rollo con gemelo (misma huella) en el principal no se carga, solo se cuenta. Las repeticiones se
    cuentan, así dos avisos iguales de verdad no se funden en uno. Un aviso sin gemelo se carga después de los del
    principal, con alerta. Si los gemelos imprimen el rol distinto, el aviso del principal lleva una alerta.
    Devuelve (avisos, alertas_extra {orden: [(tipo, texto)]}, resumen)."""
    avisos = list(cortados[0])
    alertas, resumen = {}, []
    for k, otro in enumerate(cortados[1:], start=2):
        libres = {}
        for a in avisos[:len(cortados[0])]:
            libres.setdefault(huella(a.texto), []).append(a)
        unidos = espacios = 0
        solos = []
        for b in otro:
            gem = libres.get(huella(b.texto))
            if gem:
                a = gem.pop(0)
                unidos += 1
                espacios += a.texto != b.texto
                if (a.rol_impreso or "") != (b.rol_impreso or ""):
                    alertas.setdefault(a.orden, []).append(("revisar_lectura",
                        f"El cuerpo {b.paginas[0][0]} imprime este rol distinto ({b.rol_impreso}, aquí {a.rol_impreso}). Revisa el aviso en la página."))
            else:
                solos.append(b)
        for b in solos:
            b.orden = len(avisos) + 1
            avisos.append(b)
            alertas.setdefault(b.orden, []).append(("revisar_lectura",
                f"Aviso que solo aparece en el cuerpo {b.paginas[0][0]}. No tiene gemelo en el cuerpo {cortados[0][0].paginas[0][0]}."))
        c1, c2 = cortados[0][0].paginas[0][0], otro[0].paginas[0][0] if otro else "?"
        resumen.append(f"Cuerpo {c2} repite al {c1}. {unidos} de {len(otro)} avisos unidos por huella del texto. "
                       f"{espacios} con diferencias de espacios. {len(solos)} solo en {c2}.")
    return avisos, alertas, resumen


def desde_captura(fecha: str, carpeta: Path | None = None):
    """Arma edición, páginas, avisos y alertas de la unión desde capturas\\FECHA (navegacion.json del lector).
    Con varios rollos (B y G los viernes) se cortan por separado y se unen sin duplicar (unir_rollos)."""
    d = carpeta or (CAPTURAS / fecha)
    nav = json.loads((d / "navegacion.json").read_text(encoding="utf-8"))
    if not nav["rollos"]:
        raise ValueError(f"La edición {fecha} no tiene rollos de remates. No se cargó nada.")
    por_nombre = {p["pagina"]: p for p in nav["paginas_con_remates"]}
    paginas, cortados, roles = [], [], set()
    for rollo_nombres in nav["rollos"]:
        for n in rollo_nombres:
            paginas.append({"nombre": n, "cuerpo": n[0], "numero": int(n[1:]), "id_pagina": por_nombre[n]["id"],
                            "orden_rollo": len(paginas) + 1, "texto": (d / por_nombre[n]["archivo"]).read_text(encoding="utf-8")})
        rollo, marcas = construir_rollo([(n, leer_pagina(d / por_nombre[n]["archivo"])) for n in rollo_nombres])
        cortados.append(cortar(rollo, marcas))
        roles |= {(r[1], r[2]) for r in roles_en(rollo)}
    avisos, alertas, resumen = unir_rollos(cortados)
    alarmas = list(nav.get("alarmas") or []) + resumen
    solo_otro = len(avisos) > len(cortados[0])
    cuerpos = " ".join(f"{c}{v.split('n=')[-1]}" for c, v in sorted(nav["cuerpos"].items()))
    edicion = {"fecha": fecha, "leida_en": nav["leida_en"], "estado": "con_alarmas" if nav.get("alarmas") or solo_otro else "ok",
               "cuerpos_revisados": cuerpos, "roles_en_texto": len(roles), "alarmas": "\n".join(alarmas) or None}
    return edicion, paginas, avisos, alertas


def cargar_edicion(con, fecha: str, ahora: str, carpeta: Path | None = None) -> dict:
    edicion, paginas, avisos, alertas = desde_captura(fecha, carpeta)
    extraido = extraer_avisos(avisos, fecha)
    for orden, extra in alertas.items():
        extraido[orden]["alertas"] += extra
    return guardar_edicion(con, edicion, paginas, avisos, extraido, ahora, metodo="codigo")


if __name__ == "__main__":
    import datetime as dt
    from db.crear_base import crear, BASE
    if len(sys.argv) < 3:
        raise SystemExit("Uso. python -m motor.procesar_edicion AAAA-MM-DD RUTA_BASE")
    ruta = Path(sys.argv[2])
    if ruta.resolve() == BASE.resolve():
        raise SystemExit("Por ahora solo en bases de prueba. La base real espera la aprobación de Diego.")
    print(cargar_edicion(crear(ruta), sys.argv[1], dt.datetime.now().isoformat(timespec="seconds")))

"""Une el motor con la base (paso 4 del ESTADO, 16 de Octubre). Lectura ya hecha -> corte -> extracción por código -> carga.

traducir() pasa lo que entrega motor.extraccion.extraer() al formato que espera db.carga.guardar_edicion()
(el del banco nivel 2). La carga guarda las citas con método 'codigo' y las alertas del código con su tipo.
Todavía no hay vale vista ni dirección (parte 3.7), así que cada remate queda con la alerta de vale vista no leído.

Uso. python -m motor.procesar_edicion AAAA-MM-DD RUTA_BASE [--sin-ia]   (desde D:\\Agendar_Remates)
Desde la parte 3.7a cada aviso pasa por Haiku para la regla del vale vista (agregar_vale_vista). Necesita internet y la
clave en config.py. Si no hay cómo llamar a Haiku, la carga sigue con las respuestas guardadas y el resto queda como
vale vista no leído. --sin-ia carga como antes, sin vale vista.
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
from db.carga import guardar_edicion, es_partidor

CAPTURAS = RAIZ / "capturas"

# Vale vista leído por la IA (parte 3.7a, diseño aprobado por Diego, bitácora del 16, punto 42). Colores sin cambiar el
# esquema. calculado = verde, revisar con vv_hasta = ámbar, revisar sin vv_hasta = rojo, sin_dato = sin dato.
VV_ROJO = "La IA no pudo confirmar la regla del vale vista. Revísala en el aviso."
VV_CONTRADICCION = "El aviso da dos plazos u horarios distintos para la entrega del vale vista."
VV_ERROR_ESCRITURA = "El aviso pide el vale vista en una fecha anterior a la edición. Posible error de escritura del aviso."


def _preguntas_texto(p: list) -> str:
    if len(p) == 1:
        return f"Fecha del vale vista provisoria. Depende de la pregunta {p[0]} al abogado."
    return f"Fecha del vale vista provisoria. Depende de las preguntas {', '.join(map(str, p[:-1]))} y {p[-1]} al abogado."


def bloque_vale_vista(res: dict) -> dict:
    """Resultado de motor.vale_vista.resolver() -> bloque 'vale_vista' para db.carga (formato del banco más 'metodo' y
    'alertas'). Las citas van con método ia (la frase ya viene tal como está en el aviso). En rojo nunca se guardan fechas."""
    from motor.vale_vista import NO_ENCONTRADA
    color, cita = res["color"], res.get("cita")
    b = {"metodo": "ia", "regla": res.get("regla"), "cita": cita, "citas_extra": list(res.get("citas_extra") or []),
         "vv_desde": res.get("vv_desde"), "vv_desde_origen": res.get("vv_desde_origen"), "vv_hasta": res.get("vv_hasta"),
         "vv_estado": res.get("vv_estado"), "color": color, "alertas": []}
    if color == "verde":
        b["vv_estado"] = "calculado"
    elif color == "ambar":
        b["vv_estado"] = "revisar"
        b["alertas"].append(("condicion_especial", _preguntas_texto(res.get("preguntas") or []), cita))
    elif color == "sin_dato":
        b.update(vv_estado="sin_dato", vv_desde=None, vv_desde_origen=None, vv_hasta=None)
        b["alertas"].append(("dato_faltante", NO_ENCONTRADA, None))
    else:                                            # rojo
        b.update(vv_estado="revisar", vv_desde=None, vv_desde_origen=None, vv_hasta=None)
        b["alertas"].append(("revisar_lectura", " ".join([VV_ROJO] + list(res.get("motivos") or [])), cita))
    if res.get("contradiccion"):                     # contradicción real (ya se descartaron correo, escrito, OJV y cupón)
        b["alertas"].append(("contradiccion", VV_CONTRADICCION, res["contradiccion"]))
    if any("Posible error de escritura" in m for m in res.get("motivos") or []):
        b["alertas"].append(("error_escritura", VV_ERROR_ESCRITURA, cita))
    return b


def traducir(x: dict) -> dict:
    """Salida de extraer() -> formato del banco nivel 2 (sin vale_vista ni dirección, que son de la parte 3.7)."""
    return {"tribunal": (x.get("tribunal") or {}).get("valor"),
            "fecha_remate": x["fecha_remate"], "hora_remate": x["hora_remate"], "modalidad": x["modalidad"],
            "plataforma": x.get("plataforma"), "minimo": x["minimo"], "garantia": x["garantia"],
            "alertas": list(x.get("alertas") or []), "dudas": [], "pegado": bool(x.get("pegado"))}


def extraer_avisos(avisos: list, fecha: str) -> dict:
    """{orden: datos traducidos} para todos los avisos del cortador."""
    return {a.orden: traducir(extraer(a.texto, fecha)) for a in avisos}


def agregar_vale_vista(avisos: list, extraido: dict, fecha: str, cliente=None) -> dict:
    """Parte 3.7a. Agrega a cada aviso el bloque 'vale_vista' leído por Haiku (motor.vale_vista), después de extraer(),
    con la fecha y la hora del remate que dio el código. Se saltan los avisos de partición y los marcados como pegados.
    Usa primero las respuestas guardadas (ia_respuestas\\vale_vista). Si no hay respuesta guardada y Haiku no está
    disponible (sin cliente, sin internet, sin saldo o cualquier error), ese aviso queda SIN bloque y la carga pone la
    alerta de siempre (vale vista no leído). Nunca se cae la carga por la IA.
    Devuelve un resumen {leidos, sin_ia, saltados, colores, errores}."""
    from motor import vale_vista as V
    resumen = {"leidos": 0, "sin_ia": 0, "saltados": 0, "colores": {}, "errores": []}
    for a in avisos:
        ex = extraido[a.orden]
        if ex.get("pegado") or es_partidor(ex.get("tribunal"), a.texto):
            resumen["saltados"] += 1; continue
        try:
            g = V.leer_con_ia(a.texto, cliente)
        except Exception as e:
            resumen["sin_ia"] += 1; resumen["errores"].append(f"aviso {a.orden}. {type(e).__name__}. {str(e)[:120]}"); continue
        if len(g.get("lecturas") or []) < 2:
            resumen["sin_ia"] += 1; resumen["errores"].append(f"aviso {a.orden}. {' '.join(g.get('errores') or ['Faltan lecturas de la IA.'])[:200]}"); continue
        res = V.resolver(g["lecturas"], a.texto, (ex.get("fecha_remate") or {}).get("valor"), (ex.get("hora_remate") or {}).get("valor"), fecha)
        ex["vale_vista"] = bloque_vale_vista(res)
        resumen["leidos"] += 1
        resumen["colores"][res["color"]] = resumen["colores"].get(res["color"], 0) + 1
    return resumen


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


def cargar_edicion(con, fecha: str, ahora: str, carpeta: Path | None = None, cliente=None, usar_ia: bool = True) -> dict:
    """usar_ia=False deja el vale vista sin leer (como antes de la parte 3.7a). Con usar_ia=True y cliente=None solo se usan
    las respuestas guardadas (así corren las pruebas sin internet)."""
    edicion, paginas, avisos, alertas = desde_captura(fecha, carpeta)
    extraido = extraer_avisos(avisos, fecha)
    for orden, extra in alertas.items():
        extraido[orden]["alertas"] += extra
    vv = agregar_vale_vista(avisos, extraido, fecha, cliente) if usar_ia else None
    res = guardar_edicion(con, edicion, paginas, avisos, extraido, ahora, metodo="codigo")
    if vv is not None:
        res["vale_vista"] = vv
    return res


def cliente_o_nada():
    """Cliente de Haiku desde config.py, o (None, motivo) si no se puede crear (sin paquete anthropic, sin clave, error)."""
    from motor import vale_vista as V
    try:
        return V.cliente_desde_config(), None
    except Exception as e:
        return None, f"No se pudo crear el cliente de Haiku ({type(e).__name__}). Se usan solo las respuestas guardadas."


if __name__ == "__main__":
    import datetime as dt
    from db.crear_base import crear, BASE
    if len(sys.argv) < 3:
        raise SystemExit("Uso. python -m motor.procesar_edicion AAAA-MM-DD RUTA_BASE")
    ruta = Path(sys.argv[2])
    if ruta.resolve() == BASE.resolve():
        raise SystemExit("Por ahora solo en bases de prueba. La base real espera la aprobación de Diego.")
    usar_ia = "--sin-ia" not in sys.argv
    cliente, motivo = cliente_o_nada() if usar_ia else (None, None)
    if motivo:
        print("AVISO.", motivo)
    print(cargar_edicion(crear(ruta), sys.argv[1], dt.datetime.now().isoformat(timespec="seconds"), cliente=cliente, usar_ia=usar_ia))

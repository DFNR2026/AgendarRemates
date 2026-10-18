"""Estado de sincronización de la base (18 de Octubre, aprobado por Diego).
La interfaz lo consulta al abrir. Si falta la edición de hoy o algún día reciente, muestra la franja negra "SIN SINCRONIZAR",
que no se puede cerrar mientras siga el problema. Si una edición reciente quedó cargada pero incompleta (avisos sin leer por
la IA, o sin la sección de remates), muestra una franja ámbar más suave. Solo lee la base, nunca la cambia.
"""
import datetime as dt
from motor.republicaciones import fecha_legible
from motor.procesar_edicion import VV_ALARMA, DIR_ALARMA, SIN_REMATES

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
VENTANA = 7          # días hacia atrás desde hoy que se revisan (incluido hoy). Puesto por Claude, a confirmar con Diego.
_INCOMPLETA = (VV_ALARMA, DIR_ALARMA, SIN_REMATES[:12])


def dia_largo(f: str) -> str:
    """'2026-10-18' da 'domingo 18 de Octubre de 2026'."""
    return f"{DIAS[dt.date.fromisoformat(f).weekday()]} {fecha_legible(f)}"


def estado_sincronizacion(con, hoy: str, ventana: int = VENTANA) -> dict:
    """hoy en formato AAAA-MM-DD (fecha de Chile). Devuelve ultima, faltan, incompletas, al_dia, franja_negra y franja_ambar
    (listas de líneas para la interfaz). No cuenta como faltantes los días anteriores a la primera edición cargada."""
    eds = {f: (estado, alarmas) for f, estado, alarmas in con.execute("SELECT fecha, estado, alarmas FROM ediciones")}
    h = dt.date.fromisoformat(hoy)
    dias = [(h - dt.timedelta(days=k)).isoformat() for k in range(ventana)]
    primera = min(eds) if eds else hoy
    faltan = sorted(d for d in dias if d not in eds and d >= primera)
    incompletas = []
    for d in sorted(dias):
        if d in eds:
            estado, alarmas = eds[d]
            lineas = [x for x in (alarmas or "").splitlines() if x.startswith(_INCOMPLETA)]
            if estado == "fallida" or lineas:
                incompletas.append({"fecha": d, "lineas": lineas or ["La lectura de esta edición quedó fallida."]})
    ultima = max(eds) if eds else None
    negra = []
    if not eds:
        negra = ["SIN SINCRONIZAR. La base no tiene ninguna edición cargada."]
    elif faltan:
        negra = [f"SIN SINCRONIZAR. La última edición cargada es la del {dia_largo(ultima)}."]
        negra += [f"Falta la edición de hoy, {dia_largo(d)}." if d == hoy else f"Falta la edición del {dia_largo(d)}." for d in faltan]
    ambar = [f"La edición del {dia_largo(x['fecha'])} está cargada pero incompleta. {l}" for x in incompletas for l in x["lineas"]]
    return {"ultima": ultima, "faltan": faltan, "incompletas": incompletas, "al_dia": not negra and not ambar,
            "franja_negra": negra, "franja_ambar": ambar}

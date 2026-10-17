"""Feriados nacionales de Chile calculados desde las reglas de la ley (17 de Octubre de 2026).
Uso provisorio mientras no exista la lista oficial del año. Se valida reproduciendo la lista oficial de 2026.
Reglas usadas (supuestas de conocimiento general, por eso se validan contra 2026).
- Fijos. 1 Ene, 1 May, 21 May, 16 Jul, 15 Ago, 18 y 19 Sep, 1 Nov, 8 Dic, 25 Dic.
- Semana Santa. Viernes y Sábado Santo según el domingo de Pascua (cálculo gregoriano).
- Pueblos Indígenas (Ley 21.357). Día del solsticio de invierno, que en Chile cae el 20 o el 21 de junio.
- San Pedro y San Pablo (29 Jun) y Encuentro de Dos Mundos (12 Oct), Ley 19.668. Martes, miércoles o jueves pasan al lunes
  de esa misma semana, viernes pasa al lunes siguiente (VERIFICADO en dt.gob.cl, artículo 60252, el 17 de Octubre. La
  primera versión de Claude movía el jueves hacia adelante, error corregido).
- Iglesias Evangélicas (31 Oct), Ley 20.299. Martes pasa al viernes anterior, miércoles pasa al viernes siguiente.
- 17 de septiembre si es lunes y 20 de septiembre si es viernes (Ley 20.983).
Uso. python db/feriados_calculo/calcular_feriados.py AÑO
"""
import datetime as dt, sys

def pascua(a):
    """Domingo de Pascua, algoritmo gregoriano anónimo (Meeus, Jones y Butcher). La primera versión de Claude estaba mal
    escrita y corría Semana Santa un día. Lo atrapó la validación contra la lista oficial de 2026 (17 de Octubre)."""
    g = a % 19; b, c = divmod(a, 100); d, e = divmod(b, 4); f = (b + 8) // 25; h = (b - f + 1) // 3
    x = (19 * g + b - d - h + 15) % 30; i, k = divmod(c, 4); l = (32 + 2 * e + 2 * i - x - k) % 7
    m = (g + 11 * x + 22 * l) // 451; n = x + l - 7 * m + 114
    return dt.date(a, n // 31, n % 31 + 1)

def a_lunes(d):
    w = d.weekday()
    return d - dt.timedelta(days=w) if w in (1, 2, 3) else d + dt.timedelta(days=3) if w == 4 else d

def evangelicas(d):
    w = d.weekday()
    return d - dt.timedelta(days=4) if w == 1 else d + dt.timedelta(days=2) if w == 2 else d

def solsticio(a):
    # El solsticio de junio cae el 20 o 21 en hora de Chile. Valores conocidos de tablas astronómicas (UTC):
    # 2026 21 Jun 08:24, 2027 21 Jun 14:11. En Chile (UTC-4) siguen siendo el 21.
    return {2026: dt.date(2026, 6, 21), 2027: dt.date(2027, 6, 21)}[a]

def feriados(a):
    p = pascua(a)
    out = [(dt.date(a, 1, 1), "Año Nuevo"), (p - dt.timedelta(days=2), "Viernes Santo"), (p - dt.timedelta(days=1), "Sábado Santo"),
           (dt.date(a, 5, 1), "Día Nacional del Trabajo"), (dt.date(a, 5, 21), "Día de las Glorias Navales"),
           (solsticio(a), "Día Nacional de los Pueblos Indígenas"), (a_lunes(dt.date(a, 6, 29)), "San Pedro y San Pablo"),
           (dt.date(a, 7, 16), "Día de la Virgen del Carmen"), (dt.date(a, 8, 15), "Asunción de la Virgen"),
           (dt.date(a, 9, 18), "Independencia Nacional"), (dt.date(a, 9, 19), "Día de las Glorias del Ejército"),
           (a_lunes(dt.date(a, 10, 12)), "Encuentro de Dos Mundos"), (evangelicas(dt.date(a, 10, 31)), "Día de las Iglesias Evangélicas y Protestantes"),
           (dt.date(a, 11, 1), "Día de Todos los Santos"), (dt.date(a, 12, 8), "Inmaculada Concepción"), (dt.date(a, 12, 25), "Navidad")]
    if dt.date(a, 9, 17).weekday() == 0: out.append((dt.date(a, 9, 17), "Feriado adicional de Fiestas Patrias"))
    if dt.date(a, 9, 20).weekday() == 4: out.append((dt.date(a, 9, 20), "Feriado adicional de Fiestas Patrias"))
    return sorted(out)

# Casos reales del traslado al lunes, para probar a_lunes. 2021, 2022 y 2024 vistos en titulares de prensa (meganoticias.cl y
# t13.cl) el 17 de Octubre. 2023 (jueves 29 de junio pasado al lunes 26) es de memoria de Claude, SUPUESTO.
CASOS_LUNES = {"2021-10-12": "2021-10-11", "2022-10-12": "2022-10-10", "2023-06-29": "2023-06-26", "2024-10-12": "2024-10-12"}


if __name__ == "__main__":
    for d, n in feriados(int(sys.argv[1])):
        print(d.isoformat(), n, ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"][d.weekday()])

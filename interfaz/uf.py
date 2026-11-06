"""Valor de la UF para pasar a pesos el vale vista en UF (pedido de Diego, 5 de Noviembre).
Ninguna fuente gratis publica la UF de días futuros (verificado el 5 de Noviembre en mindicador.cl, findic.cl e
indicadoreconomico.cl), así que se usa la UF de hoy y la página la marca provisoria cuando la entrega es otro día.
Se busca una vez al día, primero en mindicador.cl (responde desde el PC de Diego) y si falla en findic.cl. Si las dos fallan
se usa la última guardada con su fecha. Diego puede escribirla a mano, y ese valor manda hasta que lo borre.
Todo queda en uf_guardada.json (fuera de git). No toca la base de datos."""
import datetime as dt
import json
import urllib.request
from pathlib import Path

FUENTES = [("mindicador.cl", "https://mindicador.cl/api/uf"), ("findic.cl", "https://findic.cl/api/uf")]
REINTENTO_MIN = 30          # si internet falla, no se vuelve a intentar antes de 30 minutos. Puesto por Claude.
ESPERA_SEG = 6              # tiempo máximo por fuente. Puesto por Claude.


def leer_serie(texto):
    """De la respuesta de mindicador o findic ({"serie": [{"fecha", "valor"}]}) saca (fecha AAAA-MM-DD, valor) más reciente.
    mindicador escribe la fecha con hora en UTC (2026-11-05T03:00:00.000Z), que en Chile sigue siendo el mismo día."""
    serie = json.loads(texto).get("serie") or []
    pares = [(str(s["fecha"])[:10], float(s["valor"])) for s in serie if s.get("fecha") and s.get("valor")]
    return max(pares) if pares else None


def abrir_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": "AgendaRemates/1.0"})
    with urllib.request.urlopen(req, timeout=ESPERA_SEG) as r:
        return r.read().decode("utf-8")


def buscar_internet(abrir=abrir_url):
    """(fecha, valor, fuente) de la primera fuente que responda bien, o None."""
    for nombre, url in FUENTES:
        try:
            par = leer_serie(abrir(url))
            if par and 10000 < par[1] < 1000000:          # una UF fuera de ese rango es una respuesta rota
                return par[0], round(par[1], 2), nombre
        except Exception:
            continue
    return None


def _leer(ruta):
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _escribir(ruta, datos):
    Path(ruta).write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")


def obtener(ruta, hoy, abrir=abrir_url, ahora=None):
    """Devuelve {valor, fecha, fuente, manual} o {valor: None} si nunca se pudo saber. Busca en internet solo si la
    guardada no es de hoy y no se intentó hace menos de REINTENTO_MIN minutos."""
    ahora = ahora or dt.datetime.now()
    g = _leer(ruta)
    if g.get("manual"):
        return {"valor": g["manual"]["valor"], "fecha": g["manual"]["fecha"], "fuente": "escrita a mano", "manual": True}
    auto = g.get("auto") or {}
    intento = g.get("intento")
    reciente = intento and (ahora - dt.datetime.fromisoformat(intento)).total_seconds() < REINTENTO_MIN * 60
    if auto.get("fecha") != hoy and not reciente:
        r = buscar_internet(abrir)
        g["intento"] = ahora.isoformat(timespec="seconds")
        if r:
            auto = g["auto"] = {"fecha": r[0], "valor": r[1], "fuente": r[2]}
        try:
            _escribir(ruta, g)
        except Exception:
            pass
    if not auto.get("valor"):
        return {"valor": None, "fecha": None, "fuente": None, "manual": False}
    return {"valor": auto["valor"], "fecha": auto["fecha"], "fuente": auto["fuente"], "manual": False}


def guardar_manual(ruta, valor, hoy):
    """Guarda la UF escrita por Diego. Con valor vacío vuelve a la automática."""
    g = _leer(ruta)
    if valor in (None, "", 0):
        g.pop("manual", None)
    else:
        v = float(valor)
        if not 10000 < v < 1000000:
            raise ValueError("El valor de la UF no parece correcto. Escríbelo en pesos, por ejemplo 41.274,20.")
        g["manual"] = {"valor": round(v, 2), "fecha": hoy}
    _escribir(ruta, g)

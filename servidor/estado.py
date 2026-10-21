"""Memoria de Agendar_Remates en Supabase Storage, proyecto Agendar_Calendario, bucket privado "agendar" (20 de Octubre).

Copia adaptada de D:\\Mercurio\\servidor\\estado.py (solo de consulta), más listar() para el PC.
La dirección y la clave vienen de SUPABASE_URL y SUPABASE_KEY (secretos de GitHub en la nube, config.py en el PC).
Nunca se imprimen.
"""
from __future__ import annotations
import json, os, urllib.error, urllib.parse, urllib.request
from pathlib import Path

BUCKET = "agendar"


def _base() -> str:
    return os.environ["SUPABASE_URL"].strip().rstrip("/")


def _url(remoto: str) -> str:
    return f"{_base()}/storage/v1/object/{BUCKET}/{urllib.parse.quote(remoto)}"


def _cabeceras() -> dict:
    k = os.environ["SUPABASE_KEY"].strip()
    return {"apikey": k, "Authorization": f"Bearer {k}"}


def existe(remoto: str) -> bool:
    req = urllib.request.Request(_url(remoto), headers=_cabeceras(), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status == 200
    except urllib.error.HTTPError as e:
        if e.code in (400, 404):
            return False
        raise


def bajar(remoto: str, local: Path) -> None:
    req = urllib.request.Request(_url(remoto), headers=_cabeceras(), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            Path(local).write_bytes(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Supabase no entregó {remoto} (respuesta {e.code}). {e.read()[:300]!r}") from None


def leer_texto(remoto: str) -> str:
    req = urllib.request.Request(_url(remoto), headers=_cabeceras(), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Supabase no entregó {remoto} (respuesta {e.code}). {e.read()[:300]!r}") from None


def subir(local: Path, remoto: str, tipo: str = "application/octet-stream") -> None:
    datos = Path(local).read_bytes()
    cab = _cabeceras() | {"Content-Type": tipo, "x-upsert": "true"}
    req = urllib.request.Request(_url(remoto), data=datos, headers=cab, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            if r.status != 200:
                raise RuntimeError(f"Supabase no guardó {remoto} (respuesta {r.status})")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Supabase no guardó {remoto} (respuesta {e.code}). {e.read()[:300]!r}") from None


def subir_texto(texto: str, remoto: str) -> None:
    tmp = Path("_texto_tmp.txt")
    tmp.write_text(texto, encoding="utf-8")
    try:
        subir(tmp, remoto, "text/plain; charset=utf-8")
    finally:
        tmp.unlink(missing_ok=True)


def listar(prefijo: str) -> list:
    """Nombres de los archivos bajo prefijo (por ejemplo 'marcas/'), sin el prefijo."""
    cuerpo = json.dumps({"prefix": prefijo, "limit": 1000, "offset": 0}).encode("utf-8")
    cab = _cabeceras() | {"Content-Type": "application/json"}
    req = urllib.request.Request(f"{_base()}/storage/v1/object/list/{BUCKET}", data=cuerpo, headers=cab, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return [x["name"] for x in json.loads(r.read().decode("utf-8")) if x.get("id")]
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Supabase no listó {prefijo} (respuesta {e.code}). {e.read()[:300]!r}") from None

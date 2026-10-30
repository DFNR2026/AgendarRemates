"""Respaldo diario de la base (30 de Octubre, hallazgo F3-01 de la auditoría).
Lo llama el servidor de la agenda al abrirse, antes de tocar la base. Guarda una copia por día en la carpeta 'respaldos'
que queda junto a la base (D:\\Agendar_Remates\\respaldos para la base real) y deja solo las últimas GUARDAR.
La copia se hace con la función de respaldo de SQLite (sirve aunque la base esté abierta) y se revisa con quick_check
antes de guardarla. Si la base está dañada no se guarda nada y no se borra ningún respaldo bueno.
"""
import datetime as dt
import sqlite3
from pathlib import Path

GUARDAR = 14          # días de respaldo que se conservan. Puesto por Claude, sugerencia del auditor.


def carpeta_de(ruta_base):
    return Path(ruta_base).parent / "respaldos"


def respaldar(ruta_base, hoy=None, guardar=GUARDAR):
    """Devuelve la ruta del respaldo nuevo, o None si la base no existe o ya hay respaldo de hoy.
    Lanza sqlite3.DatabaseError si la copia no pasa la revisión (base dañada)."""
    ruta_base = Path(ruta_base)
    if not ruta_base.exists():
        return None
    hoy = hoy or dt.date.today().isoformat()
    carpeta = carpeta_de(ruta_base)
    destino = carpeta / f"{ruta_base.stem}_{hoy}.db"
    if destino.exists():
        return None
    carpeta.mkdir(exist_ok=True)
    temporal = carpeta / f"{ruta_base.stem}_{hoy}.tmp"
    origen = sqlite3.connect(ruta_base.resolve().as_uri() + "?mode=ro", uri=True)
    copia = sqlite3.connect(temporal)
    try:
        origen.backup(copia)
        revision = copia.execute("PRAGMA quick_check").fetchone()[0]
    except sqlite3.DatabaseError:
        revision = "error al copiar"
    finally:
        copia.close()
        origen.close()
    if revision != "ok":
        temporal.unlink(missing_ok=True)
        raise sqlite3.DatabaseError(f"La base {ruta_base.name} no pasó la revisión ({revision}). No se guardó respaldo.")
    temporal.replace(destino)
    viejos = sorted(carpeta.glob(f"{ruta_base.stem}_????-??-??.db"))
    for p in viejos[:-guardar]:
        p.unlink()
    return destino


def pagina_base_danada(ruta_base, error):
    """Escribe en la carpeta de respaldos una página que explica que la base está dañada y qué respaldos hay.
    La abre el servidor en el navegador en vez de quedar mudo (F3-01, 30 de Octubre). Devuelve su ruta."""
    import html
    from interfaz.datos import larga
    ruta_base = Path(ruta_base)
    carpeta = carpeta_de(ruta_base)
    carpeta.mkdir(exist_ok=True)
    dias = sorted((p.stem[len(ruta_base.stem) + 1:] for p in carpeta.glob(f"{ruta_base.stem}_????-??-??.db")), reverse=True)
    lista = "".join(f"<li>{html.escape(larga(d))}</li>" for d in dias) or "<li>No hay respaldos guardados.</li>"
    pagina = carpeta / "BASE_DANADA.html"
    pagina.write_text(f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>La agenda no pudo abrir</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;background:#1d2024;color:#e8eaed;max-width:720px;margin:40px auto;padding:0 16px;line-height:1.5}}
h1{{color:#ff6b6b}}code{{background:#2b3036;padding:2px 6px}}</style></head><body>
<h1>La agenda no pudo abrir porque la base está dañada</h1>
<p>No se cambió nada. La base es <code>{html.escape(str(ruta_base))}</code>.</p>
<p>Detalle del error. {html.escape(str(error))}</p>
<p>Los respaldos están en <code>{html.escape(str(carpeta))}</code>. Hay de estos días.</p><ul>{lista}</ul>
<p>Pídele a Claude que revise la base y la reponga desde el respaldo más nuevo que esté sano.</p>
</body></html>""", encoding="utf-8")
    return pagina

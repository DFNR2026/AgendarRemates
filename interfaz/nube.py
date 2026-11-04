"""Mitad del PC del lector diario (20 de Octubre, diseño de Diego en la bitácora del 20).

Al abrir la agenda (o con "Actualizar ahora") baja de Supabase las ediciones que la nube ya leyó y que la base de este PC
no tiene, y las carga SOLO con las respuestas de Haiku guardadas. Nunca llama a Haiku y nunca crea el cliente.
Candado de la base real. Si la base es agendar_remates.db, no carga nada mientras config.py no diga
CARGA_REAL_APROBADA = True (la primera carga real espera la aprobación de Diego).
Necesita en config.py SUPABASE_URL y SUPABASE_KEY (las mismas del proyecto Agendar_Calendario).
"""
from __future__ import annotations
import datetime as dt, importlib.util, json, os, shutil, socket, tempfile, threading, urllib.error, zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIAS_ATRAS = 30          # cuántos días hacia atrás se buscan ediciones en la nube. Confirmado por Diego el 22 de Octubre.
CANDADO = threading.Lock()


def leer_config(raiz: Path = RAIZ) -> dict:
    p = raiz / "config.py"
    if not p.exists():
        return {}
    spec = importlib.util.spec_from_file_location("config_nube", p)
    c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c)
    return {"url": getattr(c, "SUPABASE_URL", ""), "clave": getattr(c, "SUPABASE_KEY", ""),
            "aprobada": bool(getattr(c, "CARGA_REAL_APROBADA", False))}


def _extraer(zbytes_path: Path, destino: Path, prefijo: str, solo_nuevos: bool) -> int:
    """Saca del zip solo lo que empieza con prefijo y sin rutas raras. Con solo_nuevos no pisa lo que ya existe."""
    n = 0
    with zipfile.ZipFile(zbytes_path) as z:
        for nombre in z.namelist():
            if not nombre.startswith(prefijo) or ".." in nombre or nombre.startswith("/") or nombre.endswith("/"):
                continue
            final = destino / nombre
            if solo_nuevos and final.exists():
                continue
            final.parent.mkdir(parents=True, exist_ok=True)
            final.write_bytes(z.read(nombre))
            n += 1
    return n


class CapturaIncompleta(Exception):
    pass


def captura_completa(carpeta: Path, fecha: str) -> bool:
    """F2-08 (1 de Noviembre). La captura sirve si se puede armar entera (navegacion.json y todas sus páginas).
    Se usa la misma función de la carga, así no hay dos listas de archivos que puedan quedar distintas."""
    from motor.procesar_edicion import desde_captura
    try:
        desde_captura(fecha, carpeta)
        return True
    except (OSError, KeyError, ValueError, TypeError):
        return False


def _anotar(donde, e):
    """F3-03 (4 de Noviembre). Los errores de Actualizar también quedan en logs/servidor.log, con la misma función del
    servidor. Nunca cambia lo que se le responde a la página."""
    try:
        from interfaz.servidor import anotar_error
        anotar_error(donde, e)
    except Exception:
        pass


def texto_error(e: Exception) -> str:
    """F2-08. Solo un error de red se muestra como falta de internet. Antes cualquier error con "Errno" (por ejemplo un
    archivo que falta en una captura a medias) decía "Revisa que el PC tenga internet"."""
    t = str(e)
    if isinstance(e, (urllib.error.URLError, ConnectionError, TimeoutError, socket.timeout, socket.gaierror)) or \
            any(x in t for x in ("urlopen", "timed out", "Name or service", "getaddrinfo")):
        return "No se pudo conectar con Supabase. Revisa que el PC tenga internet."
    if isinstance(e, (CapturaIncompleta, FileNotFoundError, zipfile.BadZipFile)):
        return "La captura de esa edición está incompleta o dañada. Se volverá a bajar la próxima vez que se actualice."
    return f"Error del programa. {type(e).__name__}. {t}"


def actualizar(ruta_base, hoy: str, E=None, raiz: Path = RAIZ, base_real: Path | None = None, conf: dict | None = None) -> dict:
    """Devuelve {ok, cargadas, retomadas, problemas, error, bloqueo}. Nunca se cae, el error va en el texto."""
    from db.crear_base import crear, BASE
    from motor.sincronizacion import dia_largo
    base_real = base_real or BASE
    out = {"ok": True, "cargadas": [], "retomadas": [], "problemas": [], "error": None, "bloqueo": None}
    conf = conf if conf is not None else leer_config(raiz)
    if Path(ruta_base).resolve() == Path(base_real).resolve() and not conf.get("aprobada"):
        out["bloqueo"] = ("La carga en la base real espera tu aprobación. Hasta entonces la agenda real no se actualiza. "
                          "Para probar usa la agenda de prueba.")
        return out
    if E is None:
        if not conf.get("url") or not conf.get("clave"):
            return out | {"ok": False, "error": "Falta la dirección o la clave de Supabase en config.py."}
        os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"] = conf["url"], conf["clave"]
        from servidor import estado as E
    with CANDADO:
        try:
            return _actualizar(ruta_base, hoy, E, raiz, crear, dia_largo, out)
        except Exception as e:
            _anotar("Actualizar", e)
            return out | {"ok": False, "error": texto_error(e)}


def _actualizar(ruta_base, hoy, E, raiz, crear, dia_largo, out):
    from motor.procesar_edicion import cargar_edicion, retomar_vale_vista, retomar_direccion, VV_ALARMA, DIR_ALARMA
    from motor.republicaciones import registrar_cambios
    h = dt.date.fromisoformat(hoy)
    desde = (h - dt.timedelta(days=DIAS_ATRAS)).isoformat()
    fechas = sorted(n[:-5] for n in E.listar("marcas/") if n.endswith(".json") and desde <= n[:-5] <= hoy)
    con = crear(ruta_base)
    try:
        locales = {f: (a or "") for f, a in con.execute("SELECT fecha, alarmas FROM ediciones")}
        cargar, retomar, marcas = [], [], {}
        for f in fechas:
            m = json.loads(E.leer_texto(f"marcas/{f}.json"))
            marcas[f] = m
            if f not in locales:
                if m.get("estado") == "fallida":
                    out["problemas"].append(f"La nube no pudo leer la edición del {dia_largo(f)}. {m.get('motivo') or ''}".strip())
                else:
                    cargar.append(f)
            elif m.get("estado") == "listo" and any(l.startswith((VV_ALARMA, DIR_ALARMA)) for l in locales[f].splitlines()):
                retomar.append(f)
        if not cargar and not retomar:
            return out
        tmp = Path(tempfile.mkdtemp())
        try:
            if E.existe("estado/ia_respuestas.zip"):
                E.bajar("estado/ia_respuestas.zip", tmp / "ia.zip")
                _extraer(tmp / "ia.zip", raiz, "ia_respuestas/", solo_nuevos=True)
            ahora = dt.datetime.now().isoformat(timespec="seconds")
            for f in cargar:
                # F2-08 (1 de Noviembre). Una captura completa que ya está en el PC no se pisa. Una a medias (corte de luz
                # mientras se extraía) se vuelve a bajar. Se extrae en la carpeta temporal y se mueve entera al final, así
                # nunca queda otra a medias. Si una edición falla se avisa y se sigue con las demás.
                carpeta = raiz / "capturas" / f
                try:
                    if not captura_completa(carpeta, f):
                        E.bajar(f"capturas/{f}.zip", tmp / f"{f}.zip")
                        _extraer(tmp / f"{f}.zip", tmp / "nueva", f"capturas/{f}/", solo_nuevos=False)
                        nueva = tmp / "nueva" / "capturas" / f
                        if not captura_completa(nueva, f):
                            raise CapturaIncompleta(f)
                        if carpeta.exists():
                            shutil.move(str(carpeta), str(tmp / f"a_medias_{f}"))
                        carpeta.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(nueva), str(carpeta))
                    cargar_edicion(con, f, ahora, carpeta, cliente=None, usar_ia=True)
                except Exception as e:
                    _anotar(f"Actualizar, edición del {dia_largo(f)}", e)
                    out["problemas"].append(f"La edición del {dia_largo(f)} no se pudo cargar. {texto_error(e)}")
                    continue
                out["cargadas"].append(f)
                if marcas[f].get("estado") == "incompleta":
                    out["problemas"].append(f"La edición del {dia_largo(f)} llegó incompleta desde la nube. {marcas[f].get('motivo') or ''}".strip())
            for f in retomar:
                retomar_vale_vista(con, f, None)
                retomar_direccion(con, f, None)
                registrar_cambios(con, f, ahora)
                out["retomadas"].append(f)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return out
    finally:
        con.close()

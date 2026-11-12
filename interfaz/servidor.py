"""Servidor local de la agenda (18 de Octubre). Solo usa lo que trae Python, así funciona igual en otro PC.
Uso (lo corre el archivo 'Abrir Agenda.bat', Diego no escribe comandos).
    python -m interfaz.servidor [--base RUTA] [--puerto 8765] [--sin-navegador]
Escucha solo en este PC (127.0.0.1). Si ya está corriendo, solo abre el navegador.
Desde el 29 de Octubre (pedido de Diego). Un solo servidor por puerto (en Windows el servidor de Python dejaba abrir varios a la vez),
corre sin ventana (pythonw) y se apaga solo cuando la página deja de dar señales (Chrome cerrado). Los errores quedan en logs/servidor.log.
"""
import datetime as dt
import json
import sqlite3
import sys
import socket
import threading
import time
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from db.crear_base import crear, BASE
from db.respaldo import respaldar, pagina_base_danada
from interfaz import datos as D
from interfaz import uf as U

PAGINA = Path(__file__).resolve().parent / "agenda.html"
APAGAR_SIN_SENAL = 180     # segundos sin señal de la página para apagarse (Chrome cerrado). La página avisa cada 30. Puesto por Claude.
ULTIMA_SENAL = [time.monotonic()]


def debe_apagarse(ultima, ahora, limite=APAGAR_SIN_SENAL):
    """True cuando la página lleva más de 'limite' segundos sin dar señales."""
    return ahora - ultima > limite


class ServidorUnico(ThreadingHTTPServer):
    """Un solo servidor por puerto. HTTPServer trae allow_reuse_address, que en Windows deja que un segundo servidor
    ocupe el mismo puerto (causa de las ventanas repetidas, 29 de Octubre). Sin eso, el segundo falla y solo abre el navegador."""
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):          # solo existe en Windows
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def anotar_error(donde, e):
    """F3-03 (4 de Noviembre). Deja la hora, dónde pasó y el detalle del error en logs/servidor.log (con pythonw el stderr va
    a ese archivo, ver _registro). La página solo lo muestra unos segundos. Nunca detiene la respuesta."""
    try:
        print(f"--- {dt.datetime.now().isoformat(timespec='seconds')} error en {donde}", file=sys.stderr)
        traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)
        sys.stderr.flush()
    except Exception:
        pass


def hoy_chile():
    """La fecha del PC de Diego, que está en hora de Chile."""
    return dt.date.today().isoformat()


class Manejador(BaseHTTPRequestHandler):
    ruta_base = BASE
    uf_ruta = RAIZ / "uf_guardada.json"      # 5 de Noviembre. UF del día, fuera de la base y de git
    uf_abrir = staticmethod(U.abrir_url)

    def log_message(self, *a):          # sin ruido en la ventana
        pass

    def _con(self):
        con = sqlite3.connect(self.ruta_base)
        con.execute("PRAGMA foreign_keys = ON")
        return con

    def _json(self, obj, codigo=200):
        cuerpo = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self):
        ULTIMA_SENAL[0] = time.monotonic()
        u = urlparse(self.path)
        if u.path == "/api/latido":                          # la página sigue abierta
            return self._json({"ok": True})
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path in ("/", "/index.html"):
                cuerpo = PAGINA.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(cuerpo)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(cuerpo)
                return
            if u.path == "/api/uf":                   # 11 de Noviembre. Con la tabla del SII de los días que vienen
                return self._json({**U.obtener(self.uf_ruta, hoy_chile(), self.uf_abrir), "tabla": U.tabla_sii(self.uf_ruta, hoy_chile(), self.uf_abrir)})
            con = self._con()
            try:
                hoy = q.get("hoy") or hoy_chile()
                if u.path == "/api/estado":
                    return self._json(D.estado(con, hoy))
                if u.path == "/api/buscar":
                    return self._json(D.buscar(con, hoy, q.get("trib", ""), q.get("rol", ""), q.get("anio", ""),
                                               q.get("edicion", ""), q.get("pasados") == "1", direccion=q.get("dir", "")))
            finally:
                con.close()
            self._json({"ok": False, "error": "No existe esa dirección."}, 404)
        except D.ErrorDato as e:
            self._json({"ok": False, "error": str(e)}, 400)
        except Exception as e:                  # se muestra en la página y queda en logs/servidor.log (F3-03)
            anotar_error(f"GET {u.path}", e)
            self._json({"ok": False, "error": f"Error del programa. {type(e).__name__}. {e}"}, 500)

    def do_POST(self):
        ULTIMA_SENAL[0] = time.monotonic()
        u = urlparse(self.path)
        try:
            largo = int(self.headers.get("Content-Length") or 0)
            p = json.loads(self.rfile.read(largo) or b"{}")
            if u.path == "/api/actualizar":          # mitad del PC del lector diario (20 de Octubre)
                from interfaz import nube
                return self._json(nube.actualizar(self.ruta_base, hoy_chile()))
            if u.path == "/api/uf":                   # UF escrita a mano por Diego, o vacía para volver a la automática
                try:
                    U.guardar_manual(self.uf_ruta, p.get("valor"), hoy_chile())
                except ValueError as e:
                    raise D.ErrorDato(str(e))
                return self._json({**U.obtener(self.uf_ruta, hoy_chile(), self.uf_abrir), "tabla": U.tabla_sii(self.uf_ruta, hoy_chile(), self.uf_abrir)})
            con = self._con()
            try:
                acciones = {
                    "/api/agendar": lambda: D.agendar(con, int(p["remate_id"])),
                    "/api/quitar": lambda: D.quitar(con, p.get("bien_id"), p.get("manual_id")),
                    "/api/marcar": lambda: D.marcar(con, p["campo"], p["valor"], p.get("bien_id"), p.get("manual_id")),
                    "/api/visto": lambda: D.visto(con, p["tipo"], p.get("bienes")),
                    "/api/manual": lambda: D.agregar_manual(con, p),
                    "/api/reemplazar_manual": lambda: D.reemplazar_manual(con, int(p["manual_id"]), int(p["remate_id"])),
                    "/api/ignorar_publicado": lambda: D.ignorar_publicado(con, int(p["manual_id"])),
                    "/api/ignorar_quitado": lambda: D.ignorar_quitado(con, int(p["bien_id"])),
                }
                if u.path not in acciones:
                    return self._json({"ok": False, "error": "No existe esa acción."}, 404)
                r = acciones[u.path]()
                return self._json({"ok": True, **(r or {})})
            finally:
                con.close()
        except D.ErrorDato as e:
            self._json({"ok": False, "error": str(e)}, 400)
        except (KeyError, ValueError, TypeError) as e:     # también puede ser un error del programa, por eso se anota (F3-03)
            anotar_error(f"POST {u.path}", e)
            self._json({"ok": False, "error": f"Pedido incompleto. {e}"}, 400)
        except Exception as e:
            anotar_error(f"POST {u.path}", e)
            self._json({"ok": False, "error": f"Error del programa. {type(e).__name__}. {e}"}, 500)


def servidor(ruta_base, puerto=8765):
    """Respalda la base una vez al día, la crea o actualiza (agrega las tablas nuevas sin borrar nada) y devuelve el servidor
    listo, sin arrancarlo. El respaldo va antes de crear() para guardar la base tal como estaba (F3-01, 30 de Octubre)."""
    respaldar(ruta_base)
    crear(ruta_base).close()
    clase = type("ManejadorBase", (Manejador,), {"ruta_base": Path(ruta_base), "uf_ruta": Path(ruta_base).parent / "uf_guardada.json"})
    return ServidorUnico(("127.0.0.1", puerto), clase)


def vigilar(srv, limite=APAGAR_SIN_SENAL):
    """Apaga el servidor cuando la página deja de dar señales. Mientras una actualización larga trabaja, cada pedido
    renueva la señal al empezar, y el apagado espera a que termine (shutdown no corta un pedido en curso)."""
    while True:
        time.sleep(15)
        if debe_apagarse(ULTIMA_SENAL[0], time.monotonic(), limite):
            srv.shutdown()
            return


def _registro():
    """Con pythonw no hay ventana, así que los errores van a logs/servidor.log."""
    if sys.stdout is None or sys.stderr is None:
        (RAIZ / "logs").mkdir(exist_ok=True)
        f = open(RAIZ / "logs" / "servidor.log", "a", encoding="utf-8", buffering=1)
        f.write(f"\n--- {dt.datetime.now().isoformat(timespec='seconds')} arranque\n")
        sys.stdout = sys.stdout or f
        sys.stderr = sys.stderr or f


def _anotar_arranque():
    """Diagnóstico del 31 de Octubre. La agenda abre una ventana negra aunque el .bat usa pythonw. Anota qué Python la abrió
    y si tiene consola, para encontrar la causa con evidencia. Nunca detiene el arranque."""
    try:
        (RAIZ / "logs").mkdir(exist_ok=True)
        with open(RAIZ / "logs" / "arranque.txt", "a", encoding="utf-8") as f:
            f.write(f"{dt.datetime.now().isoformat(timespec='seconds')} | ejecutable {sys.executable} | base {sys.base_prefix} | "
                    f"sin consola {sys.stdout is None} | argumentos {sys.argv}\n")
    except Exception:
        pass


def main(argv):
    _anotar_arranque()
    _registro()
    ruta = Path(argv[argv.index("--base") + 1]) if "--base" in argv else BASE
    if not ruta.is_absolute():
        ruta = RAIZ / ruta
    puerto = int(argv[argv.index("--puerto") + 1]) if "--puerto" in argv else 8765
    url = f"http://127.0.0.1:{puerto}/"
    try:
        srv = servidor(ruta, puerto)
    except sqlite3.DatabaseError as e:         # base dañada. Antes quedaba mudo (F3-01, 30 de Octubre)
        print(f"La base {ruta.name} está dañada. {e}")
        pagina = pagina_base_danada(ruta, e)
        if "--sin-navegador" not in argv:
            webbrowser.open(pagina.as_uri())
        return
    except OSError:
        print("La agenda ya está abierta. Se abre el navegador.")
        if "--sin-navegador" not in argv:
            webbrowser.open(url)
        return
    print(f"Agenda de remates en {url}  (base {ruta.name}). Se apaga sola al cerrar el navegador.")
    if "--sin-navegador" not in argv:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    ULTIMA_SENAL[0] = time.monotonic()
    if "--sin-apagado" not in argv:
        limite = int(argv[argv.index("--apagar-en") + 1]) if "--apagar-en" in argv else APAGAR_SIN_SENAL   # solo para probar
        threading.Thread(target=vigilar, args=(srv, limite), daemon=True).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == "__main__":
    main(sys.argv[1:])

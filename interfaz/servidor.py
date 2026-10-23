"""Servidor local de la agenda (18 de Octubre). Solo usa lo que trae Python, así funciona igual en otro PC.
Uso (lo corre el archivo 'Abrir Agenda.bat', Diego no escribe comandos).
    python -m interfaz.servidor [--base RUTA] [--puerto 8765] [--sin-navegador]
Escucha solo en este PC (127.0.0.1). Si ya está corriendo, solo abre el navegador.
"""
import datetime as dt
import json
import sqlite3
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from db.crear_base import crear, BASE
from interfaz import datos as D

PAGINA = Path(__file__).resolve().parent / "agenda.html"


def hoy_chile():
    """La fecha del PC de Diego, que está en hora de Chile."""
    return dt.date.today().isoformat()


class Manejador(BaseHTTPRequestHandler):
    ruta_base = BASE

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
        u = urlparse(self.path)
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
        except Exception as e:                  # se muestra en la página para poder reportarlo
            self._json({"ok": False, "error": f"Error del programa. {type(e).__name__}. {e}"}, 500)

    def do_POST(self):
        u = urlparse(self.path)
        try:
            largo = int(self.headers.get("Content-Length") or 0)
            p = json.loads(self.rfile.read(largo) or b"{}")
            if u.path == "/api/actualizar":          # mitad del PC del lector diario (20 de Octubre)
                from interfaz import nube
                return self._json(nube.actualizar(self.ruta_base, hoy_chile()))
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
        except (KeyError, ValueError, TypeError) as e:
            self._json({"ok": False, "error": f"Pedido incompleto. {e}"}, 400)
        except Exception as e:
            self._json({"ok": False, "error": f"Error del programa. {type(e).__name__}. {e}"}, 500)


def servidor(ruta_base, puerto=8765):
    """Crea o actualiza la base (agrega las tablas nuevas sin borrar nada) y devuelve el servidor listo, sin arrancarlo."""
    crear(ruta_base).close()
    clase = type("ManejadorBase", (Manejador,), {"ruta_base": Path(ruta_base)})
    return ThreadingHTTPServer(("127.0.0.1", puerto), clase)


def main(argv):
    ruta = Path(argv[argv.index("--base") + 1]) if "--base" in argv else BASE
    if not ruta.is_absolute():
        ruta = RAIZ / ruta
    puerto = int(argv[argv.index("--puerto") + 1]) if "--puerto" in argv else 8765
    url = f"http://127.0.0.1:{puerto}/"
    try:
        srv = servidor(ruta, puerto)
    except OSError:
        print("La agenda ya está abierta. Se abre el navegador.")
        if "--sin-navegador" not in argv:
            webbrowser.open(url)
        return
    print(f"Agenda de remates en {url}  (base {ruta.name}). Cierra esta ventana para apagarla.")
    if "--sin-navegador" not in argv:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main(sys.argv[1:])

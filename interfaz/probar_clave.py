"""F3-08 (1 de Noviembre). Prueba la clave de Supabase de config.py sin mostrarla. Lee (listar, existe, bajar) y además
intenta subir un archivo chico a pruebas/. Con la clave de solo lectura la lectura debe funcionar y la subida debe fallar.
Escribe el resultado en logs\\prueba_clave.txt. No toca la base ni las capturas.
Uso. Doble clic en "Probar clave Supabase.bat"."""
import datetime as dt, os, sys, tempfile, traceback
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from interfaz.nube import leer_config

def main():
    lineas = [f"Prueba de la clave de Supabase, {dt.datetime.now().isoformat(timespec='seconds')}"]
    conf = leer_config()
    k = (conf.get("clave") or "").strip()
    tipo = "publicable" if k.startswith("sb_publishable_") else "secreta" if k.startswith("sb_secret_") else ("vacía" if not k else "otra")
    lineas.append(f"Clave en config.py de tipo {tipo}, largo {len(k)}")
    os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"] = conf.get("url") or "", k
    from servidor import estado as E
    for nombre, f in [("listar marcas", lambda: f"{len(E.listar('marcas/'))} marcas"),
                      ("existe ia_respuestas.zip", lambda: str(E.existe("estado/ia_respuestas.zip"))),
                      ("bajar una marca", lambda: (lambda n: (E.bajar(f"marcas/{n}", Path(tempfile.gettempdir()) / "marca_prueba.json"), f"bajó marcas/{n}")[1])(sorted(E.listar("marcas/"))[-1])),
                      ("subir pruebas/prueba_clave_pc.txt (debe FALLAR con la de solo lectura)", lambda: (E.subir_texto("prueba", "pruebas/prueba_clave_pc.txt"), "SE PUDO SUBIR")[1])]:
        try:
            lineas.append(f"OK    {nombre}. {f()}")
        except Exception as e:
            lineas.append(f"ERROR {nombre}. {type(e).__name__}. {str(e)[:200]}")
    (RAIZ / "logs").mkdir(exist_ok=True)
    (RAIZ / "logs" / "prueba_clave.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))

if __name__ == "__main__":
    main()

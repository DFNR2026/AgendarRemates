"""Diagnóstico de la tabla del SII (11 de Noviembre). Lo corre Diego en su PC con el Python de la agenda. No cambia nada de la agenda.
Intenta bajar la página del SII igual que la agenda, escribe el resultado en SII\\diag_resultado.txt y guarda lo recibido en
SII\\crudo_python.htm. Uso. .venv\\Scripts\\python -m pruebas.diag_sii"""
import sys, traceback
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from interfaz import uf as U
out = []
url = U.URL_SII.format(2026)
try:
    html = U.abrir_url(url)
    (RAIZ / "SII").mkdir(exist_ok=True)
    (RAIZ / "SII" / "crudo_python.htm").write_text(html, encoding="utf-8")
    t = U.leer_tabla_sii(html, 2026)
    out.append(f"Bajó {len(html)} caracteres. Días leídos {len(t)}. 18 de Noviembre {t.get('2026-11-18')}")
except Exception as e:
    out.append(f"ERROR {type(e).__name__} {e}")
    out.append(traceback.format_exc())
txt = "\n".join(out)
(RAIZ / "SII").mkdir(exist_ok=True)
(RAIZ / "SII" / "diag_resultado.txt").write_text(txt, encoding="utf-8")
print(txt)

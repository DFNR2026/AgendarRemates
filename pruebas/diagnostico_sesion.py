"""Diagnóstico de solo lectura. ¿El navegador del programa tiene sesión de suscriptor y el visor entrega el texto?
Uso. .venv\\Scripts\\python -m pruebas.diagnostico_sesion
No hace login ni clics. Solo abre una página conocida, espera y anota lo que ve. Deja captura en logs\\diag_*.png"""
import asyncio, json, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import config
from playwright.async_api import async_playwright

URL = f"{config.MERCURIO_BASE_URL}/2026/10/14/B/B-20261014-011#zoom=page-width"
JS = r"""() => {
  const app = window.PDFViewerApplication;
  const tl = document.querySelector('div.textLayer');
  const btn = document.querySelector('#openPram');
  const modales = [...document.querySelectorAll('.modal.in, .modal.show, [role=dialog]')]
     .filter(m => m.offsetParent !== null).map(m => (m.id || m.className) + ' :: ' + (m.innerText || '').slice(0, 120));
  return {
    titulo: document.title,
    boton_login_visible: !!(btn && btn.offsetParent !== null),
    boton_login_texto: btn ? btn.innerText.trim().slice(0, 40) : null,
    hay_PDFViewerApplication: !!app,
    hay_pdfDocument: !!(app && app.pdfDocument),
    url_pdf_sin_parametros: app && app.url ? app.url.split('?')[0] : null,
    textLayer_caracteres: tl ? tl.innerText.length : null,
    canvas_ancho: (document.querySelector('canvas') || {}).width || null,
    modales_visibles: modales,
    cookies_cantidad: document.cookie ? document.cookie.split(';').length : 0,
  };
}"""

async def main():
    async with async_playwright() as pw:
        ctx = await pw.chromium.launch_persistent_context(str(config.PERFIL_NAVEGADOR), headless=False)
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        errores = []
        page.on("console", lambda m: errores.append(f"{m.type}: {m.text[:160]}") if m.type in ("error", "warning") else None)
        await page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
        for seg in (5, 15, 30):
            await page.wait_for_timeout((seg - (0 if seg == 5 else {15: 5, 30: 15}[seg])) * 1000)
            estado = await page.evaluate(JS)
            print(f"--- a los {seg} s ---")
            print(json.dumps(estado, ensure_ascii=False, indent=1))
            await page.screenshot(path=str(RAIZ / "logs" / f"diag_{seg}s.png"))
        print("--- errores de consola del sitio (máx 15) ---")
        for e in errores[:15]:
            print(e)
        await ctx.close()

asyncio.run(main())

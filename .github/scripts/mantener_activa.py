"""Abre la app en un navegador real para que Streamlit Cloud no la duerma.

Streamlit Cloud duerme las apps sin visitas (una petición HTTP simple no
cuenta: hace falta una sesión del navegador). Este script la abre, la despierta
si estaba dormida y espera a que cargue la interfaz. Sale con error si la app
no responde, para que el workflow lo deje a la vista.
"""

import os
import sys
import time

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

URL = os.environ.get("APP_URL", "https://agroshift.streamlit.app")
TEXTO_APP = "Tu región de un vistazo"  # aparece cuando la app terminó de cargar
ESPERA_CARGA_S = 180


def texto_de_la_app(page):
    """Texto de la app, que Streamlit Cloud muestra dentro de un iframe."""
    for frame in page.frames:
        try:
            texto = frame.inner_text("body", timeout=2000)
        except Exception:
            continue
        if TEXTO_APP in texto or "What is AgroShift" in texto:
            return texto
    return ""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60_000)

        boton = page.get_by_role("button", name="Yes, get this app back up!")
        try:
            boton.wait_for(timeout=15_000)
            print("La app estaba dormida: despertándola…")
            boton.click()
        except PlaywrightTimeout:
            print("La app estaba despierta.")

        limite = time.time() + ESPERA_CARGA_S
        while time.time() < limite:
            if texto_de_la_app(page):
                # Mantener la sesión unos segundos para que cuente como visita.
                page.wait_for_timeout(15_000)
                print("App activa y cargada.")
                browser.close()
                return 0
            page.wait_for_timeout(3_000)

        page.screenshot(path="fallo.png")
        browser.close()
        print(f"La app no cargó en {ESPERA_CARGA_S} s.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

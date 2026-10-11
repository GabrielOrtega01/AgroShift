"""AgroShift — apoyo a la decisión para rotación de cultivos con datos NASA.

Punto de entrada de Streamlit. La lógica de negocio vive en
`python/agroshift/` y la presentación en `ui/`; este archivo sólo arma
la página: encabezado, selector de región, barra lateral y pestañas.
"""

import sys
from pathlib import Path

import streamlit as st

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "python"))
sys.path.insert(0, str(RAIZ))

from agroshift.regions import REGIONS  # noqa: E402
from ui import theme  # noqa: E402
from ui.components import hero, html  # noqa: E402
from ui.data import cargar_region  # noqa: E402
from ui.views import agua, clima, cultivos, inicio, metodologia, rotacion  # noqa: E402

st.set_page_config(
    page_title="AgroShift · Qué sembrar y cuándo",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="auto",
)
theme.aplicar_tema()


def selector_de_region() -> str:
    """Primer paso del flujo. Va en la página principal (no en la barra
    lateral) para que sea visible también en el celular."""
    with st.container(border=True):
        return st.radio(
            "📍 ¿Dónde está tu finca?",
            list(REGIONS),
            format_func=lambda s: REGIONS[s].nombre_corto,
            horizontal=True,
            key="region",
            help="Cada región tiene su propio clima e historial de datos.",
        )


def barra_lateral(slug: str) -> None:
    r = REGIONS[slug]
    with st.sidebar:
        st.markdown("## 🌱 AgroShift")
        st.caption("Qué sembrar y cuándo, con datos de la NASA")
        st.write("")
        st.markdown(f"**📍 {r.nombre}**")
        html(
            f"""
            <div class="as-card">
              <p><b>Clima:</b> {r.clima}<br>
              <b>Altitud:</b> {r.altitud_m:.0f} m s. n. m.<br>
              <b>Punto de referencia:</b> {r.latitud:.2f}°, {r.longitud:.2f}°</p>
            </div>
            """
        )
        st.divider()
        st.markdown("**¿Cómo se usa?**")
        st.markdown(
            "1. Elige tu región.\n"
            "2. Revisa clima, cultivos y agua.\n"
            "3. En **Mi rotación**, dinos qué priorizas."
        )
        st.divider()
        st.caption("Datos: NASA POWER · NASA SMAP · FAO ECOCROP")
        st.caption("NASA Space Apps Challenge 2026")


def main() -> None:
    region_previa = st.session_state.get("region", next(iter(REGIONS)))
    hero(
        "AgroShift",
        "Decide qué sembrar y en qué orden, usando el clima y la humedad del suelo "
        "medidos por satélites de la NASA.",
        ["🛰️ NASA POWER + SMAP", "🌾 FAO ECOCROP", "📅 Historial 2020–2025",
         f"📍 {REGIONS[region_previa].nombre_corto}"],
    )
    slug = selector_de_region()
    region = REGIONS[slug]
    barra_lateral(slug)

    try:
        data = cargar_region(slug)
    except FileNotFoundError:
        st.warning(
            f"Todavía no hay datos calculados para **{region.nombre}**. "
            f"Genera los datos con `python run_pipeline.py --region {slug}` e inténtalo de nuevo."
        )
        st.stop()

    t_inicio, t_clima, t_cultivos, t_agua, t_rotacion, t_info = st.tabs(
        ["🏠 Inicio", "🌤️ Mi clima", "🌾 Cultivos", "💧 Agua", "🔄 Mi rotación", "ℹ️ Cómo funciona"]
    )
    with t_inicio:
        inicio.render(data, region)
    with t_clima:
        clima.render(data, region)
    with t_cultivos:
        cultivos.render(data, region)
    with t_agua:
        agua.render(data, region)
    with t_rotacion:
        rotacion.render(data, region)
    with t_info:
        metodologia.render()


main()

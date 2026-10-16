"""AgroShift — apoyo a la decisión para rotación de cultivos con datos NASA.

Punto de entrada de Streamlit. La lógica de negocio vive en
`python/agroshift/` y la presentación en `ui/`; este archivo sólo arma
la página: encabezado, selectores de región e idioma, barra lateral y
pestañas.
"""

import sys
from pathlib import Path

import streamlit as st

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "python"))
sys.path.insert(0, str(RAIZ))


def _descartar_modulos_viejos() -> None:
    """Streamlit Cloud recarga app.py tras un despliegue pero conserva en
    memoria los módulos ya importados; sin esto, un cambio en `agroshift/` o
    `ui/` puede dar ImportError hasta reiniciar la app. Si los archivos
    cambiaron desde la última ejecución, se fuerza su reimportación."""
    archivos = [*(RAIZ / "ui").rglob("*.py"), *(RAIZ / "python" / "agroshift").rglob("*.py")]
    huella = max(a.stat().st_mtime_ns for a in archivos)
    if getattr(sys, "_agroshift_huella", None) == huella:
        return
    for nombre in [m for m in sys.modules if m.split(".")[0] in ("agroshift", "ui")]:
        del sys.modules[nombre]
    sys._agroshift_huella = huella


_descartar_modulos_viejos()

from agroshift.regions import REGIONS, regiones_con_resultados  # noqa: E402
from ui import theme  # noqa: E402
from ui.components import hero, html  # noqa: E402
from ui.data import cargar_region  # noqa: E402
from ui.i18n import IDIOMAS, region_clima, region_corto, region_nombre, region_zona, t  # noqa: E402
from ui.views import agua, clima, cultivos, inicio, metodologia, rotacion  # noqa: E402

st.set_page_config(
    page_title="AgroShift",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="auto",
)
theme.aplicar_tema()


def selectores() -> str:
    """Primer paso del flujo: región e idioma. Van en la página principal
    (no en la barra lateral) para que sean visibles también en el celular."""
    disponibles = regiones_con_resultados()
    grupos = list(dict.fromkeys(REGIONS[s].grupo for s in disponibles))
    with st.container(border=True):
        izq, der = st.columns([5, 1])
        grupo = izq.radio(
            t("sel.region"),
            grupos,
            horizontal=True,
            key="grupo",
            help=t("sel.region_ayuda"),
        )
        zonas = [s for s in disponibles if REGIONS[s].grupo == grupo]
        if len(zonas) > 1:
            slug = izq.radio(
                t("sel.zona", depto=grupo),
                zonas,
                format_func=lambda s: region_zona(REGIONS[s]),
                horizontal=True,
                key=f"zona_{grupo}",
            )
        else:
            slug = zonas[0]
        der.radio(
            t("sel.idioma"),
            IDIOMAS,
            format_func=str.upper,
            horizontal=True,
            key="idioma",
        )
    return slug


def barra_lateral(slug: str) -> None:
    r = REGIONS[slug]
    with st.sidebar:
        st.markdown("## 🌱 AgroShift")
        st.caption(t("side.lema"))
        st.write("")
        st.markdown(f"**📍 {region_nombre(r)}**")
        humedad = t("side.humedad_modelo") if r.humedad_modelada else t("side.humedad_smap")
        html(
            f"""
            <div class="as-card">
              <p><b>{t('side.clima')}:</b> {region_clima(r)}<br>
              <b>{t('side.altitud')}:</b> {t('side.altitud_valor', v=r.altitud_m)}<br>
              <b>{t('side.punto')}:</b> {r.latitud:.2f}°, {r.longitud:.2f}°<br>
              <b>{t('side.humedad')}:</b> {humedad}</p>
            </div>
            """
        )
        st.divider()
        st.markdown(f"**{t('side.como_se_usa')}**")
        st.markdown(t("side.pasos"))
        st.divider()
        st.caption(t("side.datos"))
        st.caption(t("side.reto"))


def main() -> None:
    # El encabezado va arriba pero depende de la región elegida más abajo: se reserva su lugar.
    cabecera = st.container()
    slug = selectores()
    region = REGIONS[slug]
    with cabecera:
        hero(
            "AgroShift",
            t("hero.subtitulo"),
            [t("hero.chip_nasa"), t("hero.chip_fao"), t("hero.chip_historial"), f"📍 {region_corto(region)}"],
        )
    barra_lateral(slug)

    try:
        data = cargar_region(slug)
    except FileNotFoundError:
        st.warning(t("app.sin_datos", region=region_nombre(region), slug=slug))
        st.stop()

    t_inicio, t_clima, t_cultivos, t_agua, t_rotacion, t_info = st.tabs(
        [t("tab.inicio"), t("tab.clima"), t("tab.cultivos"), t("tab.agua"), t("tab.rotacion"), t("tab.info")]
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
        metodologia.render(data, region)


main()

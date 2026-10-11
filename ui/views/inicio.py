"""Pestaña Inicio: qué es AgroShift y la foto rápida de la región."""

import pandas as pd
import plotly.express as px
import streamlit as st

from agroshift.crops import etiqueta
from agroshift.regions import REGIONS, Region
from ui import theme
from ui.components import kpi, lectura, semaforo, tarjeta


def _mapa(region: Region):
    filas = pd.DataFrame(
        [
            {
                "Región": r.nombre,
                "lat": r.latitud,
                "lon": r.longitud,
                "Selección": "Tu región" if r.slug == region.slug else "Otras regiones",
            }
            for r in REGIONS.values()
        ]
    )
    fig = px.scatter_map(
        filas, lat="lat", lon="lon", hover_name="Región", color="Selección",
        color_discrete_map={"Tu región": theme.VERDE, "Otras regiones": theme.TIERRA},
        zoom=4.4, center={"lat": 6.2, "lon": -74.6}, map_style="open-street-map",
    )
    fig.update_traces(marker=dict(size=16), hovertemplate="%{hovertext}<extra></extra>")
    theme.estilizar(fig, altura=330)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), legend=dict(y=0.02, x=0.02, bgcolor="rgba(255,255,255,.85)"))
    return fig


def render(data: dict, region: Region) -> None:
    ind = data["indicadores"]
    diario = data["diario"]
    compat = data["compatibilidad"].sort_values("compatibilidad_climatica", ascending=False)

    st.subheader("¿Qué es AgroShift?")
    st.markdown(
        "Una herramienta que te ayuda a decidir **qué sembrar y en qué orden**. "
        "Cruza el clima y la humedad del suelo que miden los satélites de la NASA "
        "con lo que necesita cada cultivo, y te propone **rotaciones** que "
        "aprovechan mejor el agua de tu región."
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        tarjeta("Elige tu región", "Usa el selector «¿Dónde está tu finca?» de arriba. Cada región tiene su propio clima e historial.", numero=1)
    with c2:
        tarjeta("Conoce tu clima y tus cultivos", "Revisa lluvias, temperaturas y qué cultivos se adaptan mejor.", numero=2)
    with c3:
        tarjeta("Recibe tu rotación", "Dinos qué es importante para ti y te mostramos las mejores opciones y cuándo iniciarlas.", numero=3)

    st.write("")
    st.subheader("Tu región de un vistazo")
    st.caption(region.nombre)

    n_anios = diario["anio"].nunique()
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi("🌡️ Temperatura media", f"{ind['temperatura_media_anual']:.1f}", "°C", "Promedio de todo el historial")
    with k2:
        kpi("🌧️ Lluvia al año", f"{ind['precipitacion_acumulada']:.0f}", "mm", "Promedio anual (NASA POWER)")
    with k3:
        kpi("☔ Días de lluvia", f"{ind['dias_lluviosos']:.0f}", "al año", "Días con 1 mm o más")
    with k4:
        kpi("🗓️ Historial", f"{n_anios}", "años", f"{diario['anio'].min()} a {diario['anio'].max()}, datos diarios")

    st.write("")
    izq, der = st.columns([1.05, 1])
    with izq:
        st.markdown("#### Lectura rápida")
        lectura(
            "🌧️",
            f"En promedio llueve <b>{ind['precipitacion_acumulada']:.0f} mm al año</b>. "
            f"El mes más lluvioso es <b>{ind['mes_mayor_precipitacion']}</b> "
            f"({ind['precipitacion_mes_mayor']:.0f} mm) y el más seco "
            f"<b>{ind['mes_menor_precipitacion']}</b> ({ind['precipitacion_mes_menor']:.0f} mm).",
        )
        lectura(
            "🌡️",
            f"Las temperaturas van de <b>{ind['temperatura_minima_anual']:.0f} °C</b> a "
            f"<b>{ind['temperatura_maxima_anual']:.0f} °C</b>. El mes más cálido es "
            f"<b>{ind['mes_mas_calido']}</b> y el más fresco <b>{ind['mes_mas_frio']}</b>.",
        )
        lectura(
            "🌱",
            f"La humedad del suelo es más alta en <b>{ind['mes_mayor_humedad_suelo']}</b> "
            f"y más baja en <b>{ind['mes_menor_humedad_suelo']}</b>: "
            "ahí conviene vigilar el riego.",
        )
        mejor = compat.iloc[0]
        lectura(
            "🌾",
            f"El cultivo mejor adaptado a este clima es <b>{etiqueta(mejor['nombre'])}</b> "
            f"({mejor['compatibilidad_climatica']:.0f} % de compatibilidad).",
        )
    with der:
        st.plotly_chart(_mapa(region), width="stretch", config={"displayModeBar": False})

    st.write("")
    st.markdown("#### Los 3 cultivos que mejor se adaptan")
    columnas = st.columns(3)
    for col, (_, fila) in zip(columnas, compat.head(3).iterrows()):
        nivel, color = semaforo(fila["compatibilidad_climatica"])
        with col:
            st.markdown(
                f"""<div class="as-card">
<div class="as-muted">{nivel}</div>
<div class="as-big" style="color:{color}">{fila['compatibilidad_climatica']:.0f}%</div>
<h4>{etiqueta(fila['nombre'])}</h4>
<p>Ciclo de {fila['ciclo_min_dias']:.0f}–{fila['ciclo_max_dias']:.0f} días</p>
</div>""",
                unsafe_allow_html=True,
            )
    st.info("Siguiente paso: abre la pestaña **🔄 Mi rotación** y dinos qué es importante para ti.")

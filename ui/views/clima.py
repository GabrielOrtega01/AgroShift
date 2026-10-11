"""Pestaña Mi clima: temperatura, lluvia y humedad del suelo."""

import plotly.graph_objects as go
import streamlit as st

from agroshift.recommender import MESES
from agroshift.regions import Region
from ui import theme

_CONFIG = {"displayModeBar": False}


def render(data: dict, region: Region) -> None:
    mensual = data["mensual"].sort_values("mes")
    diario = data["diario"]
    meses = [MESES[m - 1] for m in mensual["mes"]]
    a0, a1 = diario["anio"].min(), diario["anio"].max()

    st.subheader("El clima de tu región mes a mes")
    st.caption(
        f"Promedios de {a0} a {a1} (NASA POWER para el clima y NASA SMAP para la humedad del suelo). "
        "Úsalos para saber cuándo esperar lluvias y cuándo vigilar el riego."
    )

    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_scatter(x=meses, y=mensual["temperatura_maxima"], name="Máxima",
                        line=dict(color=theme.SOL, width=1.5))
        fig.add_scatter(x=meses, y=mensual["temperatura_minima"], name="Mínima",
                        line=dict(color=theme.AGUA, width=1.5),
                        fill="tonexty", fillcolor="rgba(249,168,37,.15)")
        fig.add_scatter(x=meses, y=mensual["temperatura_media"], name="Media",
                        line=dict(color=theme.VERDE, width=3.5))
        fig.update_layout(title="🌡️ Temperatura (°C)", yaxis_title="°C", hovermode="x unified")
        st.plotly_chart(theme.estilizar(fig), width="stretch", config=_CONFIG)
        st.caption("La franja muestra el rango entre la mínima y la máxima de cada mes.")

    with c2:
        lluvia = mensual["precipitacion_total"]
        colores = [theme.AGUA if v < lluvia.max() else theme.VERDE_OSCURO for v in lluvia]
        fig = go.Figure(go.Bar(x=meses, y=lluvia, marker_color=colores, name="Lluvia",
                               hovertemplate="%{x}: %{y:.0f} mm<extra></extra>"))
        fig.update_layout(title="🌧️ Lluvia por mes (mm)", yaxis_title="mm")
        st.plotly_chart(theme.estilizar(fig, leyenda=False), width="stretch", config=_CONFIG)
        st.caption("La barra más oscura es el mes más lluvioso.")

    c3, c4 = st.columns(2)
    with c3:
        fig = go.Figure()
        fig.add_scatter(x=meses, y=mensual["humedad_superficial_media"], name="Superficie (0–5 cm)",
                        line=dict(color=theme.TIERRA, width=3), mode="lines+markers")
        fig.add_scatter(x=meses, y=mensual["humedad_raiz_media"], name="Zona de raíces (hasta 1 m)",
                        line=dict(color=theme.VERDE, width=3), mode="lines+markers")
        fig.update_layout(title="🌱 Humedad del suelo (m³/m³)", hovermode="x unified")
        st.plotly_chart(theme.estilizar(fig), width="stretch", config=_CONFIG)
        st.caption("Más alto = suelo más húmedo. La zona de raíces es la que usan los cultivos.")

    with c4:
        por_anio = diario.groupby("anio")["PRECTOTCORR"].sum().reset_index()
        promedio = por_anio["PRECTOTCORR"].mean()
        colores = [theme.AGUA if v >= promedio else theme.SOL for v in por_anio["PRECTOTCORR"]]
        fig = go.Figure(go.Bar(x=por_anio["anio"], y=por_anio["PRECTOTCORR"], marker_color=colores,
                               hovertemplate="%{x}: %{y:.0f} mm<extra></extra>"))
        fig.add_hline(y=promedio, line_dash="dash", line_color=theme.TEXTO_SUAVE,
                      annotation_text=f"Promedio {promedio:.0f} mm", annotation_position="top left")
        fig.update_layout(title="📆 Lluvia total por año (mm)", yaxis_title="mm",
                          xaxis=dict(dtick=1))
        st.plotly_chart(theme.estilizar(fig, leyenda=False), width="stretch", config=_CONFIG)
        st.caption("Azul: año más lluvioso que el promedio. Naranja: año más seco.")

    with st.expander("Ver la tabla de datos mensuales"):
        st.dataframe(
            mensual[["nombre_mes", "temperatura_media", "temperatura_minima", "temperatura_maxima",
                     "precipitacion_total", "humedad_raiz_media"]].rename(columns={
                "nombre_mes": "Mes", "temperatura_media": "Temp. media (°C)",
                "temperatura_minima": "Temp. mínima (°C)", "temperatura_maxima": "Temp. máxima (°C)",
                "precipitacion_total": "Lluvia (mm)", "humedad_raiz_media": "Humedad raíces (m³/m³)",
            }).round(2),
            hide_index=True, width="stretch",
        )

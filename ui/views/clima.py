"""Pestaña Mi clima: temperatura, lluvia y humedad del suelo."""

import plotly.graph_objects as go
import streamlit as st

from agroshift.regions import Region
from ui import theme
from ui.components import aviso
from ui.i18n import meses_cortos, t

_CONFIG = {"displayModeBar": False}


def render(data: dict, region: Region) -> None:
    mensual = data["mensual"].sort_values("mes")
    diario = data["diario"]
    nombres_mes = meses_cortos()
    meses = [nombres_mes[m - 1] for m in mensual["mes"]]
    a0, a1 = diario["anio"].min(), diario["anio"].max()

    st.subheader(t("clima.titulo"))
    st.caption(t("clima.intro", a0=a0, a1=a1, fuente=data["fuente_lluvia"].split(" (")[0]))
    if region.humedad_modelada:
        aviso(t("aviso.humedad_modelada"))

    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_scatter(x=meses, y=mensual["temperatura_maxima"], name=t("clima.maxima"),
                        line=dict(color=theme.SOL, width=1.5))
        fig.add_scatter(x=meses, y=mensual["temperatura_minima"], name=t("clima.minima"),
                        line=dict(color=theme.AGUA, width=1.5),
                        fill="tonexty", fillcolor="rgba(249,168,37,.15)")
        fig.add_scatter(x=meses, y=mensual["temperatura_media"], name=t("clima.media"),
                        line=dict(color=theme.VERDE, width=3.5))
        fig.update_layout(title=t("clima.grafica_temperatura"), yaxis_title="°C", hovermode="x unified")
        st.plotly_chart(theme.estilizar(fig), width="stretch", config=_CONFIG)
        st.caption(t("clima.nota_temperatura"))

    with c2:
        lluvia = mensual["precipitacion_total"]
        colores = [theme.AGUA if v < lluvia.max() else theme.VERDE_OSCURO for v in lluvia]
        fig = go.Figure(go.Bar(x=meses, y=lluvia, marker_color=colores, name=t("clima.lluvia"),
                               hovertemplate="%{x}: %{y:.0f} mm<extra></extra>"))
        fig.update_layout(title=t("clima.grafica_lluvia"), yaxis_title="mm")
        st.plotly_chart(theme.estilizar(fig, leyenda=False), width="stretch", config=_CONFIG)
        st.caption(t("clima.nota_lluvia"))

    c3, c4 = st.columns(2)
    with c3:
        fig = go.Figure()
        fig.add_scatter(x=meses, y=mensual["humedad_superficial_media"], name=t("clima.superficie"),
                        line=dict(color=theme.TIERRA, width=3), mode="lines+markers")
        fig.add_scatter(x=meses, y=mensual["humedad_raiz_media"], name=t("clima.raices"),
                        line=dict(color=theme.VERDE, width=3), mode="lines+markers")
        fig.update_layout(title=t("clima.grafica_humedad"), hovermode="x unified")
        st.plotly_chart(theme.estilizar(fig), width="stretch", config=_CONFIG)
        st.caption(t("clima.nota_humedad"))

    with c4:
        por_anio = diario.groupby("anio")["PRECTOTCORR"].sum().reset_index()
        promedio = por_anio["PRECTOTCORR"].mean()
        colores = [theme.AGUA if v >= promedio else theme.SOL for v in por_anio["PRECTOTCORR"]]
        fig = go.Figure(go.Bar(x=por_anio["anio"], y=por_anio["PRECTOTCORR"], marker_color=colores,
                               hovertemplate="%{x}: %{y:.0f} mm<extra></extra>"))
        fig.add_hline(y=promedio, line_dash="dash", line_color=theme.TEXTO_SUAVE,
                      annotation_text=t("clima.promedio", v=promedio), annotation_position="top left")
        fig.update_layout(title=t("clima.grafica_anual"), yaxis_title="mm", xaxis=dict(dtick=1))
        st.plotly_chart(theme.estilizar(fig, leyenda=False), width="stretch", config=_CONFIG)
        st.caption(t("clima.nota_anual"))

    with st.expander(t("clima.tabla")):
        st.dataframe(
            mensual[["nombre_mes", "temperatura_media", "temperatura_minima", "temperatura_maxima",
                     "precipitacion_total", "humedad_raiz_media"]]
            .assign(nombre_mes=lambda d: [nombres_mes[m - 1] for m in mensual["mes"]])
            .rename(columns={
                "nombre_mes": t("col.mes"), "temperatura_media": t("col.temp_media"),
                "temperatura_minima": t("col.temp_minima"), "temperatura_maxima": t("col.temp_maxima"),
                "precipitacion_total": t("col.lluvia_mm"), "humedad_raiz_media": t("col.humedad_raices"),
            }).round(2),
            hide_index=True, width="stretch",
        )

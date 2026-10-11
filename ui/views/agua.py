"""Pestaña Agua: lluvia recibida frente al agua que pide cada cultivo."""

import plotly.graph_objects as go
import streamlit as st

from agroshift.crops import etiqueta
from agroshift.regions import Region
from ui import theme
from ui.components import aviso

_CONFIG = {"displayModeBar": False}


def render(data: dict, region: Region) -> None:
    bh = data["balance"].copy()
    bh["etiqueta"] = bh["cultivo"].map(etiqueta)
    bh = bh.sort_values("precipitacion_menos_etc_mm")

    st.subheader("¿Alcanza el agua de la lluvia?")
    st.caption(
        "Para cada cultivo comparamos la lluvia que cae durante su ciclo con el agua que el "
        "cultivo necesita (evapotranspiración, ETc). Es el dato clave para decidir si necesitarás riego."
    )

    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_bar(y=bh["etiqueta"], x=bh["precipitacion_acumulada_mm"], name="Lluvia recibida",
                    orientation="h", marker_color=theme.AGUA)
        fig.add_bar(y=bh["etiqueta"], x=bh["ETc_acumulada_mm"], name="Agua que necesita",
                    orientation="h", marker_color=theme.SOL)
        fig.update_layout(barmode="group", title="Lluvia vs. agua que necesita el cultivo (mm por ciclo)")
        st.plotly_chart(theme.estilizar(fig, altura=420), width="stretch", config=_CONFIG)

    with c2:
        saldo = bh["precipitacion_menos_etc_mm"]
        fig = go.Figure(go.Bar(
            y=bh["etiqueta"], x=saldo, orientation="h",
            marker_color=[theme.VERDE if v >= 0 else theme.ALERTA for v in saldo],
            text=[f"{v:+.0f}" for v in saldo], textposition="outside",
            hovertemplate="%{y}: %{x:+.0f} mm<extra></extra>",
        ))
        fig.update_layout(title="Saldo de agua: lluvia − necesidad (mm)", xaxis_title="mm")
        st.plotly_chart(theme.estilizar(fig, altura=420, leyenda=False), width="stretch", config=_CONFIG)
        st.caption("Verde: sobra agua. Rojo: falta agua y probablemente necesitarás riego.")

    deficit = bh[bh["precipitacion_menos_etc_mm"] < 0]
    if deficit.empty:
        aviso(f"<b>Buenas noticias:</b> en {region.nombre_corto} la lluvia cubre, en promedio, "
              "la necesidad de agua de todos los cultivos analizados.", tipo="info")
    else:
        nombres = ", ".join(deficit["etiqueta"])
        aviso(f"<b>Atención:</b> con la lluvia sola, estos cultivos quedan con déficit de agua: "
              f"<b>{nombres}</b>. Considera riego o ajustar la fecha de siembra.")

    with st.expander("Ver el detalle por cultivo"):
        st.dataframe(
            bh[["etiqueta", "dias_simulados", "precipitacion_acumulada_mm", "ETc_acumulada_mm",
                "precipitacion_menos_etc_mm", "dias_con_demanda_no_cubierta_pct"]].rename(columns={
                "etiqueta": "Cultivo", "dias_simulados": "Días del ciclo",
                "precipitacion_acumulada_mm": "Lluvia (mm)", "ETc_acumulada_mm": "Necesidad (mm)",
                "precipitacion_menos_etc_mm": "Saldo (mm)",
                "dias_con_demanda_no_cubierta_pct": "Días con lluvia insuficiente (%)",
            }).round(1),
            hide_index=True, width="stretch",
        )
        st.caption(
            "«Días con lluvia insuficiente» cuenta los días en que la lluvia de ese día no alcanzó "
            "para el cultivo. El suelo guarda agua de días anteriores, así que un porcentaje alto "
            "no significa por sí solo que haya sequía."
        )

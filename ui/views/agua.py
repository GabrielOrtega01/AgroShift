"""Pestaña Agua: lluvia recibida frente al agua que pide cada cultivo."""

import plotly.graph_objects as go
import streamlit as st

from agroshift.regions import Region
from agroshift.water import balance_por_cultivo
from ui import theme
from ui.components import aviso
from ui.i18n import cultivo, region_corto, t

_CONFIG = {"displayModeBar": False}


def render(data: dict, region: Region) -> None:
    bh = balance_por_cultivo(data["etapas"])
    bh["etiqueta"] = bh["cultivo"].map(cultivo)
    bh = bh.sort_values("saldo_mm")
    anios = data["diario"]["anio"]

    st.subheader(t("agua.titulo"))
    st.caption(t("agua.intro", a0=anios.min(), a1=anios.max()))

    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_bar(y=bh["etiqueta"], x=bh["lluvia_mm"], name=t("agua.serie_lluvia"),
                    orientation="h", marker_color=theme.AGUA)
        fig.add_bar(y=bh["etiqueta"], x=bh["necesidad_mm"], name=t("agua.serie_necesidad"),
                    orientation="h", marker_color=theme.SOL)
        fig.update_layout(barmode="group", title=t("agua.grafica_comparacion"))
        st.plotly_chart(theme.estilizar(fig, altura=420), width="stretch", config=_CONFIG)

    with c2:
        saldo = bh["saldo_mm"]
        fig = go.Figure(go.Bar(
            y=bh["etiqueta"], x=saldo, orientation="h",
            marker_color=[theme.VERDE if v >= 0 else theme.ALERTA for v in saldo],
            text=[f"{v:+.0f}" for v in saldo], textposition="outside",
            hovertemplate="%{y}: %{x:+.0f} mm<extra></extra>",
        ))
        fig.update_layout(title=t("agua.grafica_saldo"), xaxis_title="mm")
        st.plotly_chart(theme.estilizar(fig, altura=420, leyenda=False), width="stretch", config=_CONFIG)
        st.caption(t("agua.leyenda_saldo"))

    deficit = bh[bh["saldo_mm"] < 0]
    if deficit.empty:
        aviso(t("agua.sin_deficit", region=region_corto(region)), tipo="info")
    else:
        aviso(t("agua.con_deficit", cultivos=", ".join(deficit["etiqueta"])))

    with st.expander(t("agua.detalle")):
        st.dataframe(
            bh[["etiqueta", "dias", "lluvia_mm", "necesidad_mm", "saldo_mm", "cobertura_pct"]].rename(columns={
                "etiqueta": t("col.cultivo"), "dias": t("col.dias_ciclo"),
                "lluvia_mm": t("col.lluvia_mm"), "necesidad_mm": t("col.necesidad_mm"),
                "saldo_mm": t("col.saldo_mm"), "cobertura_pct": t("col.cobertura_pct"),
            }).round(0),
            hide_index=True, width="stretch",
        )
        st.caption(t("agua.nota_cobertura"))

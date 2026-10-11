"""Pestaña Cultivos: qué tan bien se adapta cada cultivo al clima y al suelo."""

import plotly.graph_objects as go
import streamlit as st

from agroshift.recommender import estado_ph_cultivo
from agroshift.regions import Region
from ui import theme
from ui.components import aviso, html, kpi, semaforo
from ui.i18n import cultivo, t, textura

_FERTILIDAD = {"high": "fert.alta", "moderate": "fert.moderada", "low": "fert.baja"}


def _estado(valor: float, optimo: tuple[float, float], absoluto: tuple[float, float]) -> str:
    if optimo[0] <= valor <= optimo[1]:
        return t("estado.optimo")
    if absoluto[0] <= valor <= absoluto[1]:
        return t("estado.tolerable")
    return t("estado.fuera")


def _estado_extremos(puntaje: float) -> str:
    if puntaje >= 90:
        return t("estado.optimo")
    if puntaje >= 50:
        return t("estado.tolerable")
    return t("estado.fuera")


def _bloque_suelo(suelo) -> None:
    st.markdown(f"#### {t('cultivos.suelo_titulo')}")
    k1, k2, k3 = st.columns(3)
    with k1:
        kpi(t("suelo.ph"), f"{suelo.ph:.1f}", "", t("suelo.ph_ayuda"))
    with k2:
        kpi(t("suelo.textura"), textura(suelo.textura).capitalize(), "",
            t("suelo.textura_ayuda", arcilla=suelo.arcilla_pct, arena=suelo.arena_pct, limo=suelo.limo_pct))
    with k3:
        kpi(t("suelo.materia_organica"), f"{suelo.materia_organica_pct:.1f}", "%", t("suelo.mo_ayuda"))


def render(data: dict, region: Region) -> None:
    compat = data["compatibilidad"].sort_values("compatibilidad")
    suelo = data["suelo"]

    st.subheader(t("cultivos.titulo"))
    st.caption(t("cultivos.intro"))

    colores = [semaforo(v)[1] for v in compat["compatibilidad"]]
    fig = go.Figure(go.Bar(
        x=compat["compatibilidad"], y=[cultivo(n) for n in compat["nombre"]],
        orientation="h", marker_color=colores,
        text=[f"{v:.0f}%" for v in compat["compatibilidad"]], textposition="outside",
        hovertemplate="%{y}: %{x:.0f}%<extra></extra>",
    ))
    fig.update_layout(xaxis=dict(range=[0, 112], title=t("cultivos.eje")), yaxis_title=None)
    st.plotly_chart(theme.estilizar(fig, altura=380, leyenda=False), width="stretch",
                    config={"displayModeBar": False})
    leyenda = [("nivel.excelente", "80+", 90), ("nivel.buena", "60–79", 70),
               ("nivel.regular", "40–59", 50), ("nivel.baja", "<40", 20)]
    html(
        '<div class="as-muted">'
        + " &nbsp;·&nbsp; ".join(
            f'<span style="color:{semaforo(v)[1]}">●</span> {t(clave)} ({rango})' for clave, rango, v in leyenda
        )
        + "</div>"
    )

    st.divider()
    if suelo is not None:
        _bloque_suelo(suelo)
        st.write("")

    st.subheader(t("cultivos.detalle"))
    opciones = compat["nombre"].tolist()[::-1]
    elegido = st.selectbox(t("cultivos.selector"), opciones, format_func=cultivo, label_visibility="collapsed")
    f = compat[compat["nombre"] == elegido].iloc[0]
    nivel, color = semaforo(f["compatibilidad"])

    izq, der = st.columns([1, 2])
    with izq:
        st.markdown(
            f"""<div class="as-card as-card-top">
<div class="as-muted">{t('cultivos.compatibilidad')}</div>
<div class="as-big" style="color:{color}">{f['compatibilidad']:.0f}%</div>
<h4>{cultivo(elegido)} · {nivel}</h4>
<p>{t('cultivos.ciclo', min=f['ciclo_min_dias'], max=f['ciclo_max_dias'])}</p>
</div>""",
            unsafe_allow_html=True,
        )
    with der:
        sin_dato = t("cultivos.sin_suelo")
        ph_estado = "—"
        ph_region = sin_dato
        if suelo is not None:
            ph_region = f"{suelo.ph:.1f} ({t('suelo.estimado')})"
            ph_estado = t(f"estado.{estado_ph_cultivo(suelo.ph, f)}")
        fert = str(f["fertilidad_suelo_optima"]).lower()
        filas = [
            {
                t("col.variable"): t("var.temperatura"),
                t("col.necesita"): f"{f['temperatura_optima_min_c']:.0f}–{f['temperatura_optima_max_c']:.0f} °C",
                t("col.tu_region"): f"{f['temperatura_media_c']:.1f} °C",
                t("col.estado"): _estado(
                    f["temperatura_media_c"],
                    (f["temperatura_optima_min_c"], f["temperatura_optima_max_c"]),
                    (f["temperatura_absoluta_min_c"], f["temperatura_absoluta_max_c"]),
                ),
            },
            {
                t("col.variable"): t("var.extremos"),
                t("col.necesita"): t(
                    "var.extremos_necesita",
                    tmin=f["temperatura_absoluta_min_c"], tmax=f["temperatura_absoluta_max_c"],
                ),
                t("col.tu_region"): t("var.extremos_region", pct=f["dias_temperatura_absoluta_pct"]),
                t("col.estado"): _estado_extremos(f["dias_temperatura_absoluta_pct"]),
            },
            {
                t("col.variable"): t("var.lluvia"),
                t("col.necesita"): f"{f['precipitacion_optima_min_mm']:.0f}–{f['precipitacion_optima_max_mm']:.0f} mm",
                t("col.tu_region"): f"{f['precipitacion_anual_mm']:.0f} mm",
                t("col.estado"): _estado(
                    f["precipitacion_anual_mm"],
                    (f["precipitacion_optima_min_mm"], f["precipitacion_optima_max_mm"]),
                    (f["precipitacion_absoluta_min_mm"], f["precipitacion_absoluta_max_mm"]),
                ),
            },
            {
                t("col.variable"): t("var.ph"),
                t("col.necesita"): f"{f['ph_optimo_min']:.1f}–{f['ph_optimo_max']:.1f}",
                t("col.tu_region"): ph_region,
                t("col.estado"): ph_estado,
            },
            {
                t("col.variable"): t("var.fertilidad"),
                t("col.necesita"): t(_FERTILIDAD[fert]) if fert in _FERTILIDAD else fert,
                t("col.tu_region"): (
                    t("suelo.mo_valor", mo=suelo.materia_organica_pct) if suelo is not None else sin_dato
                ),
                t("col.estado"): "—",
            },
        ]
        st.dataframe(filas, hide_index=True, width="stretch")

    if region.altitud_m >= 2000:
        aviso(t("cultivos.aviso_helada", altitud=region.altitud_m))
    if suelo is None:
        aviso(t("cultivos.aviso_sin_suelo"), tipo="info")
    else:
        aviso(t("cultivos.aviso_suelo", n=suelo.muestras), tipo="info")

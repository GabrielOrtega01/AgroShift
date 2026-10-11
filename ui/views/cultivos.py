"""Pestaña Cultivos: qué tan bien se adapta cada cultivo al clima."""

import plotly.graph_objects as go
import streamlit as st

from agroshift.crops import etiqueta
from agroshift.regions import Region
from ui import theme
from ui.components import aviso, html, semaforo

_FERTILIDAD = {"high": "Alta", "moderate": "Moderada", "low": "Baja"}


def _estado(valor: float, opt: tuple[float, float], absoluto: tuple[float, float]) -> str:
    if opt[0] <= valor <= opt[1]:
        return "✅ Óptimo"
    if absoluto[0] <= valor <= absoluto[1]:
        return "⚠️ Tolerable"
    return "❌ Fuera de rango"


def render(data: dict, region: Region) -> None:
    compat = data["compatibilidad"].sort_values("compatibilidad_climatica")

    st.subheader("¿Qué cultivos se adaptan a tu clima?")
    st.caption(
        "El puntaje compara la temperatura y la lluvia de tu región con lo que cada cultivo "
        "necesita según la base de datos FAO ECOCROP."
    )

    colores = [semaforo(v)[1] for v in compat["compatibilidad_climatica"]]
    fig = go.Figure(go.Bar(
        x=compat["compatibilidad_climatica"], y=[etiqueta(n) for n in compat["nombre"]],
        orientation="h", marker_color=colores,
        text=[f"{v:.0f}%" for v in compat["compatibilidad_climatica"]], textposition="outside",
        hovertemplate="%{y}: %{x:.0f}%<extra></extra>",
    ))
    fig.update_layout(xaxis=dict(range=[0, 112], title="Compatibilidad climática (%)"), yaxis_title=None)
    st.plotly_chart(theme.estilizar(fig, altura=380, leyenda=False), width="stretch",
                    config={"displayModeBar": False})
    leyenda = [("Excelente", "80 o más", 90), ("Buena", "60–79", 70), ("Regular", "40–59", 50), ("Baja", "menos de 40", 20)]
    html(
        '<div class="as-muted">'
        + " &nbsp;·&nbsp; ".join(
            f'<span style="color:{semaforo(v)[1]}">●</span> {n} ({rango})' for n, rango, v in leyenda
        )
        + "</div>"
    )

    st.divider()
    st.subheader("Mira un cultivo en detalle")
    opciones = compat["nombre"].tolist()[::-1]
    elegido = st.selectbox("Cultivo", opciones, format_func=etiqueta, label_visibility="collapsed")
    f = compat[compat["nombre"] == elegido].iloc[0]
    nivel, color = semaforo(f["compatibilidad_climatica"])

    izq, der = st.columns([1, 2])
    with izq:
        st.markdown(
            f"""<div class="as-card as-card-top">
<div class="as-muted">Compatibilidad con tu clima</div>
<div class="as-big" style="color:{color}">{f['compatibilidad_climatica']:.0f}%</div>
<h4>{etiqueta(elegido)} · {nivel}</h4>
<p>Ciclo del cultivo: {f['ciclo_min_dias']:.0f} a {f['ciclo_max_dias']:.0f} días.</p>
</div>""",
            unsafe_allow_html=True,
        )
    with der:
        filas = [
            {
                "Variable": "🌡️ Temperatura media",
                "Lo que necesita": f"{f['temperatura_optima_min_c']:.0f}–{f['temperatura_optima_max_c']:.0f} °C",
                "Tu región": f"{f['temperatura_media_2020_c']:.1f} °C",
                "Estado": _estado(
                    f["temperatura_media_2020_c"],
                    (f["temperatura_optima_min_c"], f["temperatura_optima_max_c"]),
                    (f["temperatura_absoluta_min_c"], f["temperatura_absoluta_max_c"]),
                ),
            },
            {
                "Variable": "🌧️ Lluvia al año",
                "Lo que necesita": f"{f['precipitacion_optima_min_mm']:.0f}–{f['precipitacion_optima_max_mm']:.0f} mm",
                "Tu región": f"{f['precipitacion_anual_2020_mm']:.0f} mm",
                "Estado": _estado(
                    f["precipitacion_anual_2020_mm"],
                    (f["precipitacion_optima_min_mm"], f["precipitacion_optima_max_mm"]),
                    (f["precipitacion_absoluta_min_mm"], f["precipitacion_absoluta_max_mm"]),
                ),
            },
            {
                "Variable": "🧪 pH del suelo",
                "Lo que necesita": f"{f['ph_optimo_min']:.1f}–{f['ph_optimo_max']:.1f}",
                "Tu región": "Requiere análisis de suelo",
                "Estado": "—",
            },
            {
                "Variable": "🌱 Fertilidad del suelo",
                "Lo que necesita": _FERTILIDAD.get(str(f["fertilidad_suelo_optima"]).lower(), str(f["fertilidad_suelo_optima"])),
                "Tu región": "Requiere análisis de suelo",
                "Estado": "—",
            },
        ]
        st.dataframe(filas, hide_index=True, width="stretch")

    aviso(
        "<b>Ojo con el suelo:</b> AgroShift mide el clima y la humedad desde el espacio, pero "
        "no conoce el suelo de tu finca. Antes de sembrar, confirma el pH y la fertilidad con "
        "un análisis de suelo o con tu asistente técnico.",
        tipo="info",
    )

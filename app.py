import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))

from agroshift.regions import REGIONS  # noqa: E402
from agroshift.repository import DataRepository  # noqa: E402

st.set_page_config(
    page_title="AgroShift",
    page_icon="🌱",
    layout="wide",
)


@st.cache_data
def load_all(region_slug: str):
    repo = DataRepository(region=region_slug)
    return {
        "ambiental_mensual": repo.analysis("analisis_mensual_ambiental_2020.csv"),
        "ambiental_diario": repo.analysis("agroshift_environmental_2020.csv"),
        "indicadores": repo.analysis("indicadores_ambientales_2020.csv"),
        "compatibilidad": repo.analysis("compatibilidad_cultivos_ecocrop_2020.csv"),
        "balance_resumen": repo.analysis("balance_hidrico_resumen_2020.csv"),
        "escenarios": repo.analysis("escenarios_priorizados_2020_v9.csv"),
        "etapas_resumen": repo.analysis("resumen_etapas_rotacion_2020_v10.csv"),
    }


st.title("🌱 AgroShift")
st.caption(
    "Herramienta de apoyo a la decisión para rotación de cultivos, "
    "basada en datos de la NASA (POWER, SMAP) y FAO ECOCROP — "
    "NASA Space Apps Challenge 2026"
)

region_slugs = list(REGIONS.keys())
region_slug = st.selectbox(
    "📍 Región del agricultor",
    region_slugs,
    format_func=lambda s: REGIONS[s].nombre,
)
region = REGIONS[region_slug]
st.caption(f"Clima: {region.clima} · {region.latitud:.3f}, {region.longitud:.3f} · {region.altitud_m:.0f} m s.n.m.")

try:
    data = load_all(region_slug)
except FileNotFoundError:
    st.warning(
        f"Todavía no hay datos calculados para **{region.nombre}**. "
        "El pipeline puede seguir corriendo en segundo plano — intenta de nuevo en unos minutos, "
        "o corre `python run_pipeline.py --region "
        f"{region_slug}` para generarlos."
    )
    st.stop()

tab_resumen, tab_clima, tab_hidrico, tab_rotacion = st.tabs(
    ["📊 Resumen ambiental", "🌾 Compatibilidad de cultivos", "💧 Balance hídrico", "🔄 Rotaciones recomendadas"]
)

# ============================================================
# TAB 1 — RESUMEN AMBIENTAL
# ============================================================
with tab_resumen:
    ind = data["indicadores"].set_index("indicador")["valor"]
    ind_num = pd.to_numeric(ind, errors="coerce")

    diario = data["ambiental_diario"].copy()
    diario["fecha"] = pd.to_datetime(diario["fecha"])
    diario["anio"] = diario["fecha"].dt.year
    n_anios = diario["anio"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperatura media", f"{ind_num.get('temperatura_media_anual', 0):.1f} °C")
    c2.metric("Temperatura máxima", f"{ind_num.get('temperatura_maxima_anual', 0):.1f} °C")
    c3.metric("Precipitación media anual", f"{diario.groupby('anio')['PRECTOTCORR'].sum().mean():.0f} mm")
    c4.metric("Años de historial", f"{n_anios} ({diario['anio'].min()}–{diario['anio'].max()})")

    mensual = data["ambiental_mensual"]

    col1, col2 = st.columns(2)
    with col1:
        fig = px.line(
            mensual, x="nombre_mes", y=["temperatura_media", "temperatura_maxima", "temperatura_minima"],
            markers=True, title=f"Temperatura mensual promedio {diario['anio'].min()}–{diario['anio'].max()} (°C)",
        )
        fig.update_layout(legend_title_text="", xaxis_title="", yaxis_title="°C")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(mensual, x="nombre_mes", y="precipitacion_total", title="Precipitación mensual promedio (mm)")
        fig.update_layout(xaxis_title="", yaxis_title="mm")
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        fig = px.line(
            mensual, x="nombre_mes", y=["humedad_superficial_media", "humedad_raiz_media"],
            markers=True, title="Humedad del suelo (fracción volumétrica)",
        )
        fig.update_layout(legend_title_text="", xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    with col4:
        precip_anual = diario.groupby("anio")["PRECTOTCORR"].sum().reset_index()
        fig = px.bar(
            precip_anual, x="anio", y="PRECTOTCORR",
            title="Precipitación total por año (mm) — variabilidad interanual",
        )
        fig.update_layout(xaxis_title="", yaxis_title="mm", xaxis=dict(dtick=1))
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("Ver tabla completa"):
        st.dataframe(mensual, use_container_width=True)

# ============================================================
# TAB 2 — COMPATIBILIDAD DE CULTIVOS
# ============================================================
with tab_clima:
    compat = data["compatibilidad"].sort_values("compatibilidad_climatica", ascending=True)

    fig = px.bar(
        compat, x="compatibilidad_climatica", y="nombre", orientation="h",
        title="Compatibilidad climática por cultivo (%)",
        color="compatibilidad_climatica", color_continuous_scale="Greens",
        range_x=[0, 100],
    )
    fig.update_layout(yaxis_title="", xaxis_title="Compatibilidad (%)", coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Detalle por cultivo")
    cultivo_sel = st.selectbox("Selecciona un cultivo", compat["nombre"].tolist()[::-1])
    fila = compat[compat["nombre"] == cultivo_sel].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Compatibilidad climática", f"{fila['compatibilidad_climatica']:.1f}%")
    c2.metric("Temp. óptima", f"{fila['temperatura_optima_min_c']:.0f}–{fila['temperatura_optima_max_c']:.0f} °C")
    c3.metric("Precip. óptima", f"{fila['precipitacion_optima_min_mm']:.0f}–{fila['precipitacion_optima_max_mm']:.0f} mm")
    c4.metric("Ciclo del cultivo", f"{fila['ciclo_min_dias']:.0f}–{fila['ciclo_max_dias']:.0f} días")

    with st.expander("Ver tabla completa"):
        st.dataframe(data["compatibilidad"], use_container_width=True)

# ============================================================
# TAB 3 — BALANCE HÍDRICO
# ============================================================
with tab_hidrico:
    bh = data["balance_resumen"]

    fig = go.Figure()
    fig.add_bar(x=bh["cultivo"], y=bh["precipitacion_acumulada_mm"], name="Precipitación acumulada")
    fig.add_bar(x=bh["cultivo"], y=bh["ETc_acumulada_mm"], name="ETc acumulada (demanda hídrica)")
    fig.update_layout(barmode="group", title="Precipitación vs. demanda hídrica del cultivo (ETc)", yaxis_title="mm")
    st.plotly_chart(fig, use_container_width=True)

    fig2 = px.bar(
        bh.sort_values("dias_con_demanda_no_cubierta_pct"),
        x="dias_con_demanda_no_cubierta_pct", y="cultivo", orientation="h",
        title="% de días con demanda hídrica no cubierta por precipitación",
        color="dias_con_demanda_no_cubierta_pct", color_continuous_scale="Reds",
    )
    fig2.update_layout(yaxis_title="", xaxis_title="% de días", coloraxis_showscale=False)
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("Ver tabla completa"):
        st.dataframe(bh, use_container_width=True)

# ============================================================
# TAB 4 — ROTACIONES RECOMENDADAS (núcleo del recomendador)
# ============================================================
with tab_rotacion:
    st.subheader("Filtra por prioridad")
    st.caption(
        "El sistema evalúa cada escenario de rotación contra 4 criterios: disponibilidad de agua, "
        "balance hídrico, humedad del suelo y ajuste temporal. Elige qué priorizar."
    )

    esc = data["escenarios"].copy()

    col1, col2, col3, col4 = st.columns(4)
    f_agua = col1.checkbox("💧 Prioridad: Agua", value=False)
    f_balance = col2.checkbox("⚖️ Prioridad: Balance", value=False)
    f_humedad = col3.checkbox("🌱 Prioridad: Humedad", value=False)
    f_temporal = col4.checkbox("📅 Prioridad: Temporal", value=False)

    if f_agua:
        esc = esc[esc["cumple_prioridad_agua"]]
    if f_balance:
        esc = esc[esc["cumple_prioridad_balance"]]
    if f_humedad:
        esc = esc[esc["cumple_prioridad_humedad"]]
    if f_temporal:
        esc = esc[esc["cumple_prioridad_temporal"]]

    min_criterios = st.slider("Mínimo de criterios cumplidos", 0, 4, 2)
    esc = esc[esc["numero_criterios_cumplidos"] >= min_criterios]
    esc = esc.sort_values("numero_criterios_cumplidos", ascending=False)

    st.metric("Escenarios que cumplen los filtros", len(esc))

    st.dataframe(
        esc[[
            "rotacion", "fecha_inicio_escenario", "duracion_total_dias",
            "cobertura_precipitacion_pct", "balance_P_ETc_total_mm",
            "percentil_humedad_medio", "numero_criterios_cumplidos", "criterios_cumplidos",
        ]].rename(columns={
            "rotacion": "Rotación",
            "fecha_inicio_escenario": "Inicio",
            "duracion_total_dias": "Duración (días)",
            "cobertura_precipitacion_pct": "Cobertura precipitación (%)",
            "balance_P_ETc_total_mm": "Balance P-ETc (mm)",
            "percentil_humedad_medio": "Percentil humedad",
            "numero_criterios_cumplidos": "N° criterios",
            "criterios_cumplidos": "Criterios cumplidos",
        }),
        use_container_width=True,
        hide_index=True,
    )

    if not esc.empty:
        st.subheader("Detalle de la mejor rotación filtrada")
        top = esc.iloc[0]
        st.markdown(f"**{top['rotacion']}** — inicio {top['fecha_inicio_escenario']} · {top['duracion_total_dias']:.0f} días")

        etapas = data["etapas_resumen"]
        etapas_rot = etapas[etapas["rotacion"] == top["rotacion"]]
        if not etapas_rot.empty:
            st.dataframe(
                etapas_rot[[
                    "numero_etapa", "cultivo", "duracion_promedio_dias",
                    "precipitacion_promedio_mm", "ETc_promedio_mm", "cobertura_promedio_pct",
                ]].rename(columns={
                    "numero_etapa": "Etapa",
                    "cultivo": "Cultivo",
                    "duracion_promedio_dias": "Duración (días)",
                    "precipitacion_promedio_mm": "Precipitación (mm)",
                    "ETc_promedio_mm": "ETc (mm)",
                    "cobertura_promedio_pct": "Cobertura (%)",
                }),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.info("Ningún escenario cumple los filtros seleccionados. Prueba relajando los criterios.")

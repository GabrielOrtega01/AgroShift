"""Pestaña Inicio: qué es AgroShift y la foto rápida de la región."""

import pandas as pd
import plotly.express as px
import streamlit as st

from agroshift.regions import REGIONS, Region, regiones_con_resultados
from ui import theme
from ui.components import aviso, kpi, lectura, semaforo, tarjeta
from ui.i18n import cultivo, mes, region_corto, t


def _mapa(region: Region):
    propia, otras = t("inicio.mapa_tu_region"), t("inicio.mapa_otras")
    filas = pd.DataFrame(
        [
            {
                "Región": region_corto(r),
                "lat": r.latitud,
                "lon": r.longitud,
                "Selección": propia if r.slug == region.slug else otras,
            }
            for slug, r in REGIONS.items()
            if slug in regiones_con_resultados()
        ]
    )
    fig = px.scatter_map(
        filas, lat="lat", lon="lon", hover_name="Región", color="Selección",
        color_discrete_map={propia: theme.VERDE, otras: theme.TIERRA},
        zoom=5.0, map_style="open-street-map",
        center={"lat": float(filas["lat"].mean()), "lon": float(filas["lon"].mean())},
    )
    fig.update_traces(marker=dict(size=16), hovertemplate="%{hovertext}<extra></extra>")
    theme.estilizar(fig, altura=330)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), legend=dict(y=0.02, x=0.02, bgcolor="rgba(255,255,255,.85)"))
    return fig


def render(data: dict, region: Region) -> None:
    ind = data["indicadores"]
    diario = data["diario"]
    compat = data["compatibilidad"].sort_values("compatibilidad", ascending=False)

    st.subheader(t("inicio.que_es"))
    st.markdown(t("inicio.que_es_texto"))
    c1, c2, c3 = st.columns(3)
    with c1:
        tarjeta(t("inicio.paso1_titulo"), t("inicio.paso1_texto"), numero=1)
    with c2:
        tarjeta(t("inicio.paso2_titulo"), t("inicio.paso2_texto"), numero=2)
    with c3:
        tarjeta(t("inicio.paso3_titulo"), t("inicio.paso3_texto"), numero=3)

    st.write("")
    st.subheader(t("inicio.vistazo"))
    if region.humedad_modelada:
        aviso(t("aviso.humedad_modelada"))

    n_anios = diario["anio"].nunique()
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi(t("kpi.temperatura"), f"{ind['temperatura_media_anual']:.1f}", "°C", t("kpi.temperatura_ayuda"))
    with k2:
        kpi(t("kpi.lluvia"), f"{ind['precipitacion_acumulada']:.0f}", "mm",
            t("kpi.lluvia_ayuda", fuente=data["fuente_lluvia"].split(" (")[0]))
    with k3:
        kpi(t("kpi.dias_lluvia"), f"{ind['dias_lluviosos']:.0f}", t("kpi.al_anio"), t("kpi.dias_lluvia_ayuda"))
    with k4:
        kpi(t("kpi.historial"), f"{n_anios}", t("kpi.anios"),
            t("kpi.historial_ayuda", a0=diario["anio"].min(), a1=diario["anio"].max()))

    st.write("")
    izq, der = st.columns([1.05, 1])
    with izq:
        st.markdown(f"#### {t('inicio.lectura')}")
        lectura("🌧️", t(
            "inicio.lectura_lluvia", total=ind["precipitacion_acumulada"],
            mes_max=mes(ind["mes_mayor_precipitacion"]), v_max=ind["precipitacion_mes_mayor"],
            mes_min=mes(ind["mes_menor_precipitacion"]), v_min=ind["precipitacion_mes_menor"],
        ))
        lectura("🌡️", t(
            "inicio.lectura_temperatura", tmin=ind["temperatura_minima_anual"],
            tmax=ind["temperatura_maxima_anual"], caliente=mes(ind["mes_mas_calido"]),
            frio=mes(ind["mes_mas_frio"]),
        ))
        lectura("🌱", t(
            "inicio.lectura_suelo", alta=mes(ind["mes_mayor_humedad_suelo"]),
            baja=mes(ind["mes_menor_humedad_suelo"]),
        ))
        mejor = compat.iloc[0]
        lectura("🌾", t(
            "inicio.lectura_cultivo", cultivo=cultivo(mejor["nombre"]),
            pct=mejor["compatibilidad"],
        ))
    with der:
        st.plotly_chart(_mapa(region), width="stretch", config={"displayModeBar": False})

    st.write("")
    st.markdown(f"#### {t('inicio.top3')}")
    columnas = st.columns(3)
    for col, (_, fila) in zip(columnas, compat.head(3).iterrows()):
        nivel, color = semaforo(fila["compatibilidad"])
        with col:
            st.markdown(
                f"""<div class="as-card">
<div class="as-muted">{nivel}</div>
<div class="as-big" style="color:{color}">{fila['compatibilidad']:.0f}%</div>
<h4>{cultivo(fila['nombre'])}</h4>
<p>{t('inicio.ciclo', min=fila['ciclo_min_dias'], max=fila['ciclo_max_dias'])}</p>
</div>""",
                unsafe_allow_html=True,
            )
    st.info(t("inicio.siguiente"))

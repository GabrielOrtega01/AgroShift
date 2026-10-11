"""Pestaña Cómo funciona: metodología, fuentes, calidad de datos y límites."""

import streamlit as st

from agroshift.crops import CULTIVOS
from agroshift.recommender import PRIORIDADES
from agroshift.regions import REGIONS, Region, regiones_con_resultados
from ui.components import aviso, tarjeta
from ui.i18n import region_corto, t

REPOSITORIO = "https://github.com/GabrielOrtega01/AgroShift"
UMBRAL_DIFERENCIA_PCT = 30


def _calidad_lluvia(data: dict, region: Region) -> None:
    tabla = data["validacion_lluvia"]
    st.markdown(f"### {t('met.calidad_titulo')}")
    st.markdown(t("met.calidad_texto"))
    if tabla is None:
        st.caption(t("met.calidad_sin_datos"))
        return

    peor = tabla.loc[tabla["diferencia_pct"].abs().idxmax()]
    medio = tabla["diferencia_pct"].abs().mean()
    if medio >= UMBRAL_DIFERENCIA_PCT:
        aviso(t("met.calidad_alerta", region=region_corto(region), medio=medio,
                anio=int(peor["anio"]), dif=peor["diferencia_pct"]))
    else:
        aviso(t("met.calidad_ok", medio=medio), tipo="info")

    st.dataframe(
        tabla[["anio", "power_mm", "chirps_mm", "diferencia_pct"]].rename(columns={
            "anio": t("col.anio"), "power_mm": t("col.power_mm"),
            "chirps_mm": t("col.chirps_mm"), "diferencia_pct": t("col.diferencia_pct"),
        }),
        hide_index=True, width="stretch",
    )


def render(data: dict, region: Region) -> None:
    st.subheader(t("met.titulo"))
    st.markdown(t("met.intro"))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        tarjeta(t("met.p1_titulo"), t("met.p1_texto"), numero=1)
    with c2:
        tarjeta(t("met.p2_titulo"), t("met.p2_texto"), numero=2)
    with c3:
        tarjeta(t("met.p3_titulo"), t("met.p3_texto"), numero=3)
    with c4:
        tarjeta(t("met.p4_titulo"), t("met.p4_texto"), numero=4)

    st.write("")
    st.markdown(f"### {t('met.criterios_titulo')}")
    st.caption(t("met.criterios_nota"))
    columnas = st.columns(2)
    for i, p in enumerate(PRIORIDADES.values()):
        with columnas[i % 2]:
            tarjeta(t(f"prioridad.{p.clave}.nombre"), t(f"prioridad.{p.clave}.explicacion"), icono=p.icono)
            st.write("")

    st.markdown(f"### {t('met.fiabilidad_titulo')}")
    st.markdown(t("met.fiabilidad_texto"))

    st.markdown(f"### {t('met.clima_titulo')}")
    st.markdown(t("met.clima_texto"))

    st.markdown(f"### {t('met.fuentes_titulo')}")
    st.dataframe(
        [
            {t("col.fuente"): "NASA POWER", t("col.aporta"): t("met.fuente_power"), t("col.resolucion"): t("met.res_power")},
            {t("col.fuente"): "NASA SMAP L4", t("col.aporta"): t("met.fuente_smap"), t("col.resolucion"): t("met.res_smap")},
            {t("col.fuente"): "FAO ECOCROP", t("col.aporta"): t("met.fuente_ecocrop"), t("col.resolucion"): t("met.res_ecocrop")},
            {t("col.fuente"): "ISRIC SoilGrids", t("col.aporta"): t("met.fuente_suelo"), t("col.resolucion"): t("met.res_suelo")},
            {t("col.fuente"): "CHIRPS", t("col.aporta"): t("met.fuente_chirps"), t("col.resolucion"): t("met.res_chirps")},
        ],
        hide_index=True, width="stretch",
    )

    _calidad_lluvia(data, region)

    st.markdown(f"### {t('met.glosario_titulo')}")
    with st.expander(t("met.glosario_ver")):
        st.markdown(t("met.glosario_texto"))

    st.markdown(f"### {t('met.limites_titulo')}")
    n_regiones = len(regiones_con_resultados())
    n_modelo = sum(1 for s in regiones_con_resultados() if REGIONS[s].humedad_modelada)
    aviso(t("met.limites", regiones=n_regiones, modelo=n_modelo, cultivos=len(CULTIVOS)))

    st.write("")
    st.caption(t("met.pie", repo=REPOSITORIO))

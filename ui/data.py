"""Carga de datos por región para la interfaz."""

import pandas as pd
import streamlit as st

from agroshift.repository import DataRepository


def _numero_o_texto(valor):
    """La columna 'valor' mezcla números y textos (p. ej. nombres de mes)."""
    numero = pd.to_numeric(valor, errors="coerce")
    return valor if pd.isna(numero) else float(numero)


@st.cache_data(show_spinner="Cargando datos de la región…")
def cargar_region(region_slug: str) -> dict:
    repo = DataRepository(region=region_slug)

    diario = repo.analysis("agroshift_environmental_2020.csv").copy()
    diario["fecha"] = pd.to_datetime(diario["fecha"])
    diario["anio"] = diario["fecha"].dt.year

    indicadores = repo.analysis("indicadores_ambientales_2020.csv")
    indicadores = indicadores.set_index("indicador")["valor"]

    return {
        "diario": diario,
        "mensual": repo.analysis("analisis_mensual_ambiental_2020.csv"),
        "indicadores": {k: _numero_o_texto(v) for k, v in indicadores.items()},
        "compatibilidad": repo.analysis("compatibilidad_cultivos_ecocrop_2020.csv"),
        "balance": repo.analysis("balance_hidrico_resumen_2020.csv"),
        "escenarios": repo.analysis("escenarios_priorizados_2020_v9.csv"),
        "etapas": repo.analysis("resumen_etapas_rotacion_2020_v10.csv"),
    }

"""Carga de datos por región para la interfaz."""

import pandas as pd
import streamlit as st

from agroshift.config import settings
from agroshift.repository import DataRepository
from agroshift.soil import cargar_suelo


def _numero_o_texto(valor):
    """La columna 'valor' mezcla números y textos (p. ej. nombres de mes)."""
    numero = pd.to_numeric(valor, errors="coerce")
    return valor if pd.isna(numero) else float(numero)


def _validacion_lluvia(region_slug: str) -> pd.DataFrame | None:
    """Totales anuales NASA POWER vs CHIRPS (python/validar_precipitacion.py)."""
    ruta = settings.data_dir / "validation" / "precipitacion_anual.csv"
    if not ruta.exists():
        return None
    tabla = pd.read_csv(ruta)
    tabla = tabla[tabla["region"] == region_slug]
    return tabla if not tabla.empty else None


@st.cache_data(show_spinner=False)
def cargar_region(region_slug: str) -> dict:
    repo = DataRepository(region=region_slug)

    diario = repo.analysis("agroshift_environmental.csv").copy()
    diario["fecha"] = pd.to_datetime(diario["fecha"])
    diario["anio"] = diario["fecha"].dt.year

    indicadores = repo.analysis("indicadores_ambientales.csv")
    indicadores = indicadores.set_index("indicador")["valor"]

    compatibilidad = repo.analysis("compatibilidad_cultivos_ecocrop.csv").copy()
    # La compatibilidad "final" respeta el factor limitante (temperatura);
    # los CSV antiguos sólo traen la climática.
    compatibilidad["compatibilidad"] = compatibilidad.get(
        "compatibilidad_final", compatibilidad["compatibilidad_climatica"]
    )

    compatibilidad = repo.analysis("compatibilidad_cultivos_ecocrop.csv").copy()
    # La compatibilidad "final" respeta el factor limitante (temperatura);
    # los CSV antiguos sólo traen la climática.
    compatibilidad["compatibilidad"] = compatibilidad.get(
        "compatibilidad_final", compatibilidad["compatibilidad_climatica"]
    )

    return {
        "diario": diario,
        "mensual": repo.analysis("analisis_mensual_ambiental.csv"),
        "indicadores": {k: _numero_o_texto(v) for k, v in indicadores.items()},
        "compatibilidad": compatibilidad,
        "escenarios": repo.analysis("escenarios_app.csv.gz"),
        "etapas": repo.analysis("resumen_etapas_rotacion_v10.csv"),
        "suelo": cargar_suelo(region_slug),
        "fuente_lluvia": (
            str(diario["fuente_lluvia"].iloc[0]) if "fuente_lluvia" in diario.columns else "NASA POWER"
        ),
        "validacion_lluvia": _validacion_lluvia(region_slug),
    }

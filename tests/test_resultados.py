"""Comprobaciones sobre los CSV de resultados que lee la app."""

import pandas as pd
import pytest

from agroshift.config import settings
from agroshift.regions import REGIONS, regiones_con_resultados

COLUMNAS_ESCENARIOS = {
    "rotacion", "fecha_inicio_escenario", "numero_criterios_cumplidos",
    "cumple_prioridad_agua", "cumple_prioridad_balance", "cumple_prioridad_humedad",
    "cumple_prioridad_temporal", "cobertura_demanda_pct", "deficit_balance_mm",
    "percentil_humedad_medio", "duracion_total_dias", "numero_etapas",
}
COLUMNAS_COMPAT = {
    "nombre", "compatibilidad_climatica", "puntaje_temperatura_media",
    "compatibilidad_final", "precipitacion_anual_mm", "temperatura_media_c",
}

REGIONES = regiones_con_resultados()


def test_hay_regiones_con_resultados():
    assert len(REGIONES) >= 4


@pytest.mark.parametrize("slug", REGIONES)
def test_compatibilidad(slug):
    c = pd.read_csv(settings.analysis_dir / slug / "compatibilidad_cultivos_ecocrop.csv")
    assert COLUMNAS_COMPAT <= set(c.columns)
    assert c["compatibilidad_climatica"].between(0, 100).all()
    # la lluvia es anual (promedio), no la suma de todos los años
    assert 200 < c["precipitacion_anual_mm"].iloc[0] < 6000
    assert c["compatibilidad_final"].between(0, 100).all()
    # la final es el factor limitante: nunca supera a la compatibilidad climática
    assert (c["compatibilidad_final"] <= c["compatibilidad_climatica"] + 1e-6).all()


@pytest.mark.parametrize("slug", REGIONES)
def test_escenarios(slug):
    e = pd.read_csv(settings.analysis_dir / slug / "escenarios_app.csv.gz")
    assert COLUMNAS_ESCENARIOS <= set(e.columns)
    assert e["numero_criterios_cumplidos"].between(0, 4).all()
    assert len(e) > 1000
    assert e["rotacion"].nunique() > 50


@pytest.mark.parametrize("slug", REGIONES)
def test_historial_completo(slug):
    d = pd.read_csv(settings.analysis_dir / slug / "agroshift_environmental.csv", parse_dates=["fecha"])
    assert d["fecha"].dt.year.nunique() == 6
    assert d["fecha"].is_unique
    assert d[["T2M", "PRECTOTCORR", "sm_rootzone"]].notna().all().all()


def test_regiones_modelo_estan_marcadas():
    for slug in REGIONES:
        r = REGIONS[slug]
        assert (r.fuente_humedad == "modelo") == (r.fila_smap is None)

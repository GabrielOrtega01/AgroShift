"""Lluvia diaria del pipeline: NASA GPM IMERG ajustada a totales mensuales.

La fuente de lluvia es NASA GPM IMERG (satélite + pluviómetros, 0,1°,
descargada por el paso 20). Contrastada con CHIRPS y con climatologías
conocidas, IMERG sigue bien la variación en el tiempo pero tiene un sesgo
de magnitud grande en varias regiones de montaña (+80 % a +120 %). Por eso
se conserva su distribución diaria y se escala cada mes a los totales
mensuales de CHIRPS (ver python/validar_precipitacion.py).

Cadena de respaldo: IMERG ajustada → IMERG cruda → NASA POWER. NASA POWER
rellena además los días en que IMERG no publica archivo.
"""

import numpy as np
import pandas as pd

from agroshift.config import settings

FUENTE_POWER = "NASA POWER"
FUENTE_IMERG = "NASA GPM IMERG"
FUENTE_IMERG_AJUSTADA = "NASA GPM IMERG (ajustada a CHIRPS)"

FACTOR_MINIMO = 0.25
FACTOR_MAXIMO = 4.0


def ruta_imerg(region: str):
    return settings.data_dir / "imerg" / f"imerg_{region}.csv"


def ruta_totales_mensuales():
    return settings.data_dir / "validation" / "precipitacion_mensual.csv"


def cargar_lluvia_imerg(region: str) -> pd.DataFrame | None:
    """DataFrame con `fecha` (date) e `IMERG_PRECIP` (mm/día), o None."""
    ruta = ruta_imerg(region)
    if not ruta.exists():
        return None
    lluvia = pd.read_csv(ruta, parse_dates=["fecha"])
    lluvia["fecha"] = lluvia["fecha"].dt.date
    return lluvia[["fecha", "IMERG_PRECIP"]]


def cargar_totales_chirps(region: str) -> pd.Series | None:
    """Totales mensuales de CHIRPS (mm) con índice (año, mes), o None."""
    ruta = ruta_totales_mensuales()
    if not ruta.exists():
        return None
    tabla = pd.read_csv(ruta)
    tabla = tabla[tabla["region"] == region].dropna(subset=["chirps_mm"])
    if tabla.empty:
        return None
    return tabla.set_index(["anio", "mes"])["chirps_mm"]


def ajustar_a_totales_mensuales(
    lluvia: pd.Series, objetivo: pd.Series
) -> tuple[pd.Series, pd.Series]:
    """Escala la lluvia diaria de cada mes para que sume `objetivo`.

    `lluvia` tiene índice de fechas; `objetivo` índice (año, mes). Devuelve
    (lluvia ajustada, factor aplicado por (año, mes)). El factor se limita
    a [0,25; 4] y los meses sin objetivo o sin lluvia quedan sin cambio.
    """
    fechas = pd.to_datetime(lluvia.index)
    claves = pd.MultiIndex.from_arrays([fechas.year, fechas.month])
    total = lluvia.groupby(claves).transform("sum").to_numpy()
    meta = objetivo.reindex(claves).to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        factor = np.where((total > 0) & ~np.isnan(meta), meta / total, 1.0)
    factor = np.clip(factor, FACTOR_MINIMO, FACTOR_MAXIMO)
    ajustada = pd.Series(lluvia.to_numpy() * factor, index=lluvia.index)
    por_mes = pd.Series(factor, index=claves).groupby(level=[0, 1]).first()
    return ajustada, por_mes


def combinar_lluvia(
    power: pd.DataFrame,
    imerg: pd.DataFrame | None,
    totales_mensuales: pd.Series | None = None,
) -> pd.DataFrame:
    """Devuelve `power` con PRECTOTCORR tomada de IMERG cuando hay dato.

    Conserva la lluvia original de POWER en PRECTOTCORR_POWER y deja en
    `fuente_lluvia` de dónde salió la lluvia usada. `power` necesita las
    columnas `fecha` (date) y `PRECTOTCORR`.
    """
    resultado = power.copy()
    resultado["PRECTOTCORR_POWER"] = resultado["PRECTOTCORR"]
    resultado["fuente_lluvia"] = FUENTE_POWER
    if imerg is None:
        return resultado

    resultado = resultado.merge(imerg, on="fecha", how="left")
    hay = resultado["IMERG_PRECIP"].notna()
    if not hay.any():
        return resultado.drop(columns=["IMERG_PRECIP"])

    # IMERG donde existe; NASA POWER en los días sin archivo
    resultado["PRECTOTCORR"] = resultado["IMERG_PRECIP"].where(hay, resultado["PRECTOTCORR_POWER"])
    resultado["fuente_lluvia"] = FUENTE_IMERG

    if totales_mensuales is not None:
        serie = pd.Series(
            resultado["PRECTOTCORR"].to_numpy(), index=pd.to_datetime(resultado["fecha"])
        )
        ajustada, _ = ajustar_a_totales_mensuales(serie, totales_mensuales)
        resultado["PRECTOTCORR"] = ajustada.to_numpy()
        resultado["fuente_lluvia"] = FUENTE_IMERG_AJUSTADA
    return resultado.drop(columns=["IMERG_PRECIP"])

"""Ajuste de la temperatura de NASA POWER a la altitud del punto.

NASA POWER entrega, para cada punto, el valor de una celda de ~50 km con
su *elevación media* (p. ej. 2112 m para un punto del valle del Cauca que
está a 1000 m). La temperatura por tanto corresponde a esa elevación y no
a la del punto: sin ajuste, un valle sale frío y una meseta alta, cálida.

Se corrige con el gradiente térmico vertical estándar (6,5 °C/km) y se
conserva la presión de vapor real, de modo que la humedad relativa se
recalcula con la temperatura nueva (la evapotranspiración la usa).
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from agroshift.config import settings

GRADIENTE_C_POR_KM = 6.5


def ruta_metadatos(region: str) -> Path:
    return settings.data_dir / "power" / f"nasa_power_{region}_meta.json"


def cargar_elevacion_celda(region: str) -> float | None:
    """Elevación media (m) de la celda NASA POWER de la región, si se guardó."""
    ruta = ruta_metadatos(region)
    if not ruta.exists():
        return None
    return float(json.loads(ruta.read_text(encoding="utf-8"))["elevacion_celda_m"])


def _presion_vapor_saturacion(t):
    return 0.6108 * np.exp((17.27 * t) / (t + 237.3))


def _es_media(tmax, tmin):
    return (_presion_vapor_saturacion(tmax) + _presion_vapor_saturacion(tmin)) / 2


def corregir_por_altitud(
    clima: pd.DataFrame,
    elevacion_celda_m: float,
    altitud_punto_m: float,
    gradiente: float = GRADIENTE_C_POR_KM,
) -> pd.DataFrame:
    """Copia de `clima` con T2M, T2M_MAX, T2M_MIN y RH2M a la altitud del punto."""
    delta = gradiente * (elevacion_celda_m - altitud_punto_m) / 1000.0
    ajustado = clima.copy()

    es_antes = _es_media(clima["T2M_MAX"], clima["T2M_MIN"])
    presion_vapor = es_antes * clima["RH2M"] / 100.0

    for columna in ("T2M", "T2M_MAX", "T2M_MIN"):
        ajustado[columna] = clima[columna] + delta

    es_despues = _es_media(ajustado["T2M_MAX"], ajustado["T2M_MIN"])
    ajustado["RH2M"] = (100.0 * presion_vapor / es_despues).clip(lower=1.0, upper=100.0)
    return ajustado

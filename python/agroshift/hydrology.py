"""Hidrología básica reutilizable: ETo FAO-56 y humedad del suelo modelada.

`eto_penman_monteith` reproduce, vectorizado, el cálculo del script
08_calcular_evapotranspiracion_referencia.py (hay un test que compara
ambos). `humedad_suelo_modelada` estima la humedad del suelo con un
balance hídrico de balde (FAO-56, cap. 8) para regiones donde no se
descargó NASA SMAP; es una aproximación, no una medición.
"""

import numpy as np
import pandas as pd

ALBEDO = 0.23
SIGMA = 4.903e-9  # MJ K^-4 m^-2 día^-1
POROSIDAD = 0.45  # m³/m³, para convertir humedad en fracción de saturación


def _radiacion_extraterrestre(latitud: float, dia_ano: np.ndarray) -> np.ndarray:
    phi = np.deg2rad(latitud)
    dr = 1 + 0.033 * np.cos(2 * np.pi / 365 * dia_ano)
    delta = 0.409 * np.sin(2 * np.pi / 365 * dia_ano - 1.39)
    omega_s = np.arccos(-np.tan(phi) * np.tan(delta))
    return (24 * 60 / np.pi) * 0.0820 * dr * (
        omega_s * np.sin(phi) * np.sin(delta)
        + np.cos(phi) * np.cos(delta) * np.sin(omega_s)
    )


def _presion_vapor_saturacion(temperatura: pd.Series) -> pd.Series:
    return 0.6108 * np.exp((17.27 * temperatura) / (temperatura + 237.3))


def eto_penman_monteith(clima: pd.DataFrame, latitud: float, altitud_m: float) -> pd.Series:
    """ETo diaria (mm/día) FAO-56 Penman-Monteith.

    `clima` necesita: fecha, T2M, T2M_MAX, T2M_MIN, RH2M, WS10M y
    ALLSKY_SFC_SW_DWN (las variables de NASA POWER del pipeline).
    """
    t, tmax, tmin = clima["T2M"], clima["T2M_MAX"], clima["T2M_MIN"]
    fecha = pd.to_datetime(clima["fecha"])

    u2 = clima["WS10M"] * 4.87 / np.log(67.8 * 10.0 - 5.42)
    presion = 101.3 * ((293 - 0.0065 * altitud_m) / 293) ** 5.26
    gamma = 0.000665 * presion

    es = (_presion_vapor_saturacion(tmax) + _presion_vapor_saturacion(tmin)) / 2
    ea = es * clima["RH2M"] / 100
    delta = 4098 * es / (t + 237.3) ** 2

    ra = pd.Series(_radiacion_extraterrestre(latitud, fecha.dt.dayofyear.to_numpy()), index=clima.index)
    rso = (0.75 + 2e-5 * altitud_m) * ra
    rs = clima["ALLSKY_SFC_SW_DWN"]
    rns = (1 - ALBEDO) * rs
    rs_rso = (rs / rso).clip(upper=1.0)
    rnl = (
        SIGMA
        * (((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2)
        * (0.34 - 0.14 * np.sqrt(ea.clip(lower=0)))
        * (1.35 * rs_rso - 0.35)
    )
    rn = (rns - rnl).clip(lower=0)

    numerador = 0.408 * delta * rn + gamma * (900 / (t + 273)) * u2 * (es - ea)
    denominador = delta + gamma * (1 + 0.34 * u2)
    return (numerador / denominador).clip(lower=0)


def capacidad_campo_marchitez(
    arena_pct: float, arcilla_pct: float, materia_organica_pct: float
) -> tuple[float, float]:
    """(θ capacidad de campo, θ punto de marchitez) en m³/m³.

    Funciones de pedotransferencia de Saxton y Rawls (2006).
    """
    s, c, om = arena_pct / 100, arcilla_pct / 100, materia_organica_pct
    t1500 = (-0.024 * s + 0.487 * c + 0.006 * om + 0.005 * s * om
             - 0.013 * c * om + 0.068 * s * c + 0.031)
    marchitez = t1500 + (0.14 * t1500 - 0.02)
    t33 = (-0.251 * s + 0.195 * c + 0.011 * om + 0.006 * s * om
           - 0.027 * c * om + 0.452 * s * c + 0.299)
    campo = t33 + (1.283 * t33 ** 2 - 0.374 * t33 - 0.015)
    return float(campo), float(marchitez)


def _agotamiento(lluvia: np.ndarray, eto: np.ndarray, taw: float, p: float = 0.5) -> np.ndarray:
    """Agotamiento diario (mm) de un balde de capacidad `taw` (FAO-56)."""
    raw = p * taw
    dr = np.empty(len(lluvia))
    previo = 0.5 * taw
    for i, (llueve, demanda) in enumerate(zip(lluvia, eto)):
        ks = 1.0 if previo <= raw else max((taw - previo) / (taw - raw), 0.0)
        previo = min(max(previo - llueve + ks * demanda, 0.0), taw)
        dr[i] = previo
    return dr


def humedad_suelo_modelada(
    clima: pd.DataFrame,
    eto: pd.Series,
    campo: float = 0.30,
    marchitez: float = 0.14,
    profundidad_raiz_m: float = 1.0,
    profundidad_superficie_m: float = 0.05,
) -> pd.DataFrame:
    """Humedad diaria del suelo estimada con balance hídrico de balde.

    Devuelve las mismas columnas que el pipeline obtiene de NASA SMAP
    (sm_surface, sm_rootzone, *_wetness, soil_temp_layer1_celsius) para
    poder reutilizar el análisis sin cambios.
    """
    lluvia = clima["PRECTOTCORR"].to_numpy(dtype=float)
    demanda = eto.to_numpy(dtype=float)
    util = campo - marchitez

    out = {}
    for nombre, prof in (("sm_rootzone", profundidad_raiz_m), ("sm_surface", profundidad_superficie_m)):
        taw = util * prof * 1000
        agotado = _agotamiento(lluvia, demanda, taw)
        out[nombre] = campo - agotado / (prof * 1000)

    resultado = pd.DataFrame(out, index=clima.index)
    resultado["sm_surface_wetness"] = resultado["sm_surface"] / POROSIDAD
    resultado["sm_rootzone_wetness"] = resultado["sm_rootzone"] / POROSIDAD
    # La capa superficial del suelo sigue a la temperatura del aire con retraso
    resultado["soil_temp_layer1_celsius"] = clima["T2M"].ewm(span=7, adjust=False).mean()
    return resultado

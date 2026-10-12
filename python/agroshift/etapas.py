"""Cálculo de una etapa de rotación (cultivo + fecha de inicio + duración).

El resultado de una etapa depende sólo de (cultivo, fecha de inicio,
duración). `CalculadoraEtapas` calcula de una vez todas las ventanas
posibles de cada cultivo con NumPy; el generador de escenarios (paso 13)
la consulta ~150.000 veces. `calcular_etapa_referencia` es la
implementación original con pandas, más lenta, que se conserva como
referencia: hay pruebas que verifican que ambas dan lo mismo.
"""

import warnings

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

PERCENTILES = ("P10", "P25", "P50", "P75", "P90")
NIVELES_PERCENTIL = [10, 25, 50, 75, 90]


def calcular_etapa_referencia(
    cultivo,
    fecha_inicio,
    dias,
    df_ambiental,
    df_eto,
    perfiles_kc,
    percentiles_smap,
):
    """Implementación original (pandas, una etapa por llamada)."""

    fecha_fin = fecha_inicio + pd.Timedelta(days=dias - 1)
    fechas = pd.date_range(start=fecha_inicio, end=fecha_fin, freq="D")

    ambiental = (
        df_ambiental[df_ambiental["fecha"].isin(fechas)].copy().sort_values("fecha")
    )
    eto = df_eto[df_eto["fecha"].isin(fechas)].copy().sort_values("fecha")

    if len(ambiental) != dias or len(eto) != dias:
        return None

    ambiental = ambiental.set_index("fecha")
    eto = eto.set_index("fecha")

    perfil = perfiles_kc.get(cultivo, {})
    kc_values = []
    for dia in range(1, dias + 1):
        kc = perfil.get(dia)
        if kc is None:
            return None
        kc_values.append(kc)

    kc_series = pd.Series(kc_values, index=fechas)
    eto_series = eto["ETo"]
    etc = eto_series * kc_series
    precipitacion = ambiental["PRECTOTCORR"]
    sm_rootzone = ambiental["sm_rootzone"]

    balance_diario = precipitacion - etc
    demanda_no_cubierta = np.maximum(etc - precipitacion, 0)
    cobertura = (
        precipitacion.sum() / etc.sum() * 100 if etc.sum() > 0 else np.nan
    )

    sm_percentiles = np.interp(
        sm_rootzone,
        [percentiles_smap[k] for k in PERCENTILES],
        NIVELES_PERCENTIL,
    )
    dias_bajo_p10 = (sm_rootzone < percentiles_smap["P10"]).sum()
    temperatura = ambiental["T2M"]

    return {
        "cultivo": cultivo,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "dias": dias,
        "precipitacion_mm": precipitacion.sum(),
        "ETo_mm": eto_series.sum(),
        "ETc_mm": etc.sum(),
        "balance_P_ETc_mm": balance_diario.sum(),
        "demanda_no_cubierta_mm": demanda_no_cubierta.sum(),
        "cobertura_precipitacion_pct": cobertura,
        "temperatura_media_c": temperatura.mean(),
        "temperatura_min_c": temperatura.min(),
        "temperatura_max_c": temperatura.max(),
        "sm_rootzone_media": sm_rootzone.mean(),
        "sm_rootzone_min": sm_rootzone.min(),
        "sm_rootzone_max": sm_rootzone.max(),
        "percentil_humedad_medio": sm_percentiles.mean(),
        "percentil_humedad_min": sm_percentiles.min(),
        "percentil_humedad_max": sm_percentiles.max(),
        "dias_humedad_menor_P10": int(dias_bajo_p10),
        "porcentaje_dias_menor_P10": dias_bajo_p10 / dias * 100,
        "indicador_temperatura": np.nan,
    }


class CalculadoraEtapas:
    """Etapas de rotación precalculadas con NumPy.

    Misma salida que `calcular_etapa_referencia` para fechas de datos
    únicas (un registro por día), que es lo que produce el pipeline.
    """

    def __init__(self, df_ambiental, df_eto, perfiles_kc, percentiles_smap):
        self._perfiles_kc = perfiles_kc
        self._percentiles = percentiles_smap
        self._etapas = {}  # (cultivo, dias) -> tablas por posición de inicio

        inicio = min(df_ambiental["fecha"].min(), df_eto["fecha"].min())
        fin = max(df_ambiental["fecha"].max(), df_eto["fecha"].max())
        calendario = pd.date_range(inicio, fin, freq="D")

        amb = df_ambiental.drop_duplicates("fecha").set_index("fecha").reindex(calendario)
        eto = df_eto.drop_duplicates("fecha").set_index("fecha").reindex(calendario)

        self._inicio = calendario[0]
        self._presente = np.asarray(
            calendario.isin(df_ambiental["fecha"]) & calendario.isin(df_eto["fecha"])
        )
        self._precipitacion = amb["PRECTOTCORR"].to_numpy(float)
        self._sm = amb["sm_rootzone"].to_numpy(float)
        self._temperatura = amb["T2M"].to_numpy(float)
        self._eto = eto["ETo"].to_numpy(float)

    def _precalcular(self, cultivo, dias):
        perfil = self._perfiles_kc.get(cultivo, {})
        kc = [perfil.get(d) for d in range(1, dias + 1)]
        total = len(self._presente)

        if any(k is None for k in kc) or dias > total:
            return None

        kc = np.asarray(kc, dtype=float)
        validas = np.flatnonzero(
            sliding_window_view(self._presente, dias).all(axis=1)
        )
        if len(validas) == 0:
            return None

        def ventana(serie):
            return sliding_window_view(serie, dias)[validas]

        precipitacion = ventana(self._precipitacion)
        eto = ventana(self._eto)
        sm = ventana(self._sm)
        temperatura = ventana(self._temperatura)

        etc = eto * kc
        etc_suma = np.nansum(etc, axis=1)
        precipitacion_suma = np.nansum(precipitacion, axis=1)

        with np.errstate(divide="ignore", invalid="ignore"):
            cobertura = np.where(
                etc_suma > 0, precipitacion_suma / etc_suma * 100, np.nan
            )

        percentil = np.interp(
            sm.ravel(),
            [self._percentiles[k] for k in PERCENTILES],
            NIVELES_PERCENTIL,
        ).reshape(sm.shape)

        dias_bajo_p10 = (sm < self._percentiles["P10"]).sum(axis=1)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            tabla = {
                "precipitacion_mm": precipitacion_suma,
                "ETo_mm": np.nansum(eto, axis=1),
                "ETc_mm": etc_suma,
                "balance_P_ETc_mm": np.nansum(precipitacion - etc, axis=1),
                "demanda_no_cubierta_mm": np.nansum(
                    np.maximum(etc - precipitacion, 0), axis=1
                ),
                "cobertura_precipitacion_pct": cobertura,
                "temperatura_media_c": np.nanmean(temperatura, axis=1),
                "temperatura_min_c": np.nanmin(temperatura, axis=1),
                "temperatura_max_c": np.nanmax(temperatura, axis=1),
                "sm_rootzone_media": np.nanmean(sm, axis=1),
                "sm_rootzone_min": np.nanmin(sm, axis=1),
                "sm_rootzone_max": np.nanmax(sm, axis=1),
                "percentil_humedad_medio": percentil.mean(axis=1),
                "percentil_humedad_min": percentil.min(axis=1),
                "percentil_humedad_max": percentil.max(axis=1),
                "dias_humedad_menor_P10": dias_bajo_p10,
                "porcentaje_dias_menor_P10": dias_bajo_p10 / dias * 100,
            }

        fila_de_posicion = np.full(total - dias + 1, -1, dtype=np.int64)
        fila_de_posicion[validas] = np.arange(len(validas))
        return {"tabla": tabla, "fila": fila_de_posicion}

    def etapa(self, cultivo, fecha_inicio, dias):
        clave = (cultivo, dias)
        if clave not in self._etapas:
            self._etapas[clave] = self._precalcular(cultivo, dias)
        datos = self._etapas[clave]

        if datos is None:
            return None

        posicion = (fecha_inicio - self._inicio).days
        if posicion < 0 or posicion >= len(datos["fila"]):
            return None

        fila = datos["fila"][posicion]
        if fila < 0:
            return None

        t = datos["tabla"]
        return {
            "cultivo": cultivo,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_inicio + pd.Timedelta(days=dias - 1),
            "dias": dias,
            "precipitacion_mm": t["precipitacion_mm"][fila],
            "ETo_mm": t["ETo_mm"][fila],
            "ETc_mm": t["ETc_mm"][fila],
            "balance_P_ETc_mm": t["balance_P_ETc_mm"][fila],
            "demanda_no_cubierta_mm": t["demanda_no_cubierta_mm"][fila],
            "cobertura_precipitacion_pct": t["cobertura_precipitacion_pct"][fila],
            "temperatura_media_c": t["temperatura_media_c"][fila],
            "temperatura_min_c": t["temperatura_min_c"][fila],
            "temperatura_max_c": t["temperatura_max_c"][fila],
            "sm_rootzone_media": t["sm_rootzone_media"][fila],
            "sm_rootzone_min": t["sm_rootzone_min"][fila],
            "sm_rootzone_max": t["sm_rootzone_max"][fila],
            "percentil_humedad_medio": t["percentil_humedad_medio"][fila],
            "percentil_humedad_min": t["percentil_humedad_min"][fila],
            "percentil_humedad_max": t["percentil_humedad_max"][fila],
            "dias_humedad_menor_P10": int(t["dias_humedad_menor_P10"][fila]),
            "porcentaje_dias_menor_P10": t["porcentaje_dias_menor_P10"][fila],
            "indicador_temperatura": np.nan,
        }

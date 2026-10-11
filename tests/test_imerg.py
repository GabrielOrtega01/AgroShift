import datetime as dt

import numpy as np
import pandas as pd
import pytest

from agroshift.imerg import (
    FUENTE_IMERG,
    FUENTE_IMERG_AJUSTADA,
    FUENTE_POWER,
    ajustar_a_totales_mensuales,
    combinar_lluvia,
)


def _power(dias=60, lluvia=2.0):
    fechas = pd.date_range("2022-01-01", periods=dias)
    return pd.DataFrame({"fecha": fechas.date, "PRECTOTCORR": lluvia})


def _imerg(power, valor):
    return pd.DataFrame({"fecha": power["fecha"], "IMERG_PRECIP": valor})


def test_sin_imerg_conserva_power():
    r = combinar_lluvia(_power(), None)
    assert (r["PRECTOTCORR"] == 2.0).all()
    assert (r["fuente_lluvia"] == FUENTE_POWER).all()


def test_imerg_reemplaza_y_power_rellena_los_dias_sin_dato():
    power = _power()
    imerg = _imerg(power, 5.0).iloc[:-10]  # 10 días sin archivo
    r = combinar_lluvia(power, imerg)
    assert (r["PRECTOTCORR"].iloc[:-10] == 5.0).all()
    assert (r["PRECTOTCORR"].iloc[-10:] == 2.0).all()
    assert (r["PRECTOTCORR_POWER"] == 2.0).all()
    assert (r["fuente_lluvia"] == FUENTE_IMERG).all()


def test_ajuste_a_totales_mensuales_suma_el_objetivo():
    power = _power(dias=59)  # enero (31) + febrero (28)
    imerg = _imerg(power, 4.0)
    objetivo = pd.Series({(2022, 1): 62.0, (2022, 2): 56.0})  # mitad de lo que suma IMERG
    r = combinar_lluvia(power, imerg, objetivo)
    fechas = pd.to_datetime(r["fecha"])
    por_mes = r.groupby(fechas.dt.month)["PRECTOTCORR"].sum()
    assert por_mes[1] == pytest.approx(62.0)
    assert por_mes[2] == pytest.approx(56.0)
    assert (r["fuente_lluvia"] == FUENTE_IMERG_AJUSTADA).all()


def test_ajuste_conserva_la_distribucion_diaria():
    fechas = pd.date_range("2022-01-01", periods=31)
    lluvia = pd.Series(np.arange(31, dtype=float), index=fechas)
    ajustada, factor = ajustar_a_totales_mensuales(lluvia, pd.Series({(2022, 1): lluvia.sum() / 2}))
    assert ajustada.sum() == pytest.approx(lluvia.sum() / 2)
    assert (ajustada / lluvia.replace(0, np.nan)).dropna().round(6).nunique() == 1  # proporcional
    assert factor.iloc[0] == pytest.approx(0.5)


def test_factor_acotado_y_meses_sin_objetivo_quedan_igual():
    fechas = pd.date_range("2022-01-01", periods=59)
    lluvia = pd.Series(1.0, index=fechas)
    objetivo = pd.Series({(2022, 1): 31 * 100.0})  # pediría ×100: se limita a ×4
    ajustada, _ = ajustar_a_totales_mensuales(lluvia, objetivo)
    assert ajustada[:31].sum() == pytest.approx(31 * 4.0)
    assert (ajustada[31:] == 1.0).all()  # febrero sin objetivo
    assert isinstance(fechas[0].date(), dt.date)

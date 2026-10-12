"""La calculadora vectorizada debe dar lo mismo que la implementación original."""

import numpy as np
import pandas as pd
import pytest

from agroshift.etapas import CalculadoraEtapas, calcular_etapa_referencia

PERCENTILES = {"P10": 0.12, "P25": 0.15, "P50": 0.20, "P75": 0.26, "P90": 0.31}


@pytest.fixture(scope="module")
def datos():
    rng = np.random.default_rng(7)
    fechas = pd.date_range("2021-01-01", periods=400)
    ambiental = pd.DataFrame(
        {
            "fecha": fechas,
            "PRECTOTCORR": rng.gamma(0.8, 4.0, len(fechas)),
            "sm_rootzone": rng.uniform(0.08, 0.35, len(fechas)),
            "T2M": rng.normal(20, 3, len(fechas)),
        }
    )
    eto = pd.DataFrame({"fecha": fechas, "ETo": rng.uniform(2, 5, len(fechas))})
    # un hueco: faltan 5 días de ETo y 3 de ambiental
    eto = eto.drop(eto.index[100:105]).reset_index(drop=True)
    ambiental = ambiental.drop(ambiental.index[250:253]).reset_index(drop=True)
    perfiles = {
        "A": {d: 0.4 + 0.004 * d for d in range(1, 91)},
        "B": {d: 0.7 for d in range(1, 61)},
        "C": {d: 1.0 for d in range(1, 31) if d != 7},  # perfil con un día faltante
    }
    return ambiental, eto, perfiles


def _iguales(a, b):
    assert a.keys() == b.keys()
    for clave in a:
        x, y = a[clave], b[clave]
        if isinstance(x, (float, np.floating)) or isinstance(y, (float, np.floating)):
            if np.isnan(x):
                assert np.isnan(y), clave
            else:
                assert y == pytest.approx(x, rel=1e-12, abs=1e-12), clave
        else:
            assert x == y, clave


@pytest.mark.parametrize("cultivo,dias", [("A", 90), ("B", 60), ("A", 45)])
def test_equivale_a_la_implementacion_original(datos, cultivo, dias):
    ambiental, eto, perfiles = datos
    calculadora = CalculadoraEtapas(ambiental, eto, perfiles, PERCENTILES)

    for inicio in pd.date_range("2021-01-01", periods=380, freq="9D"):
        esperado = calcular_etapa_referencia(
            cultivo, inicio, dias, ambiental, eto, perfiles, PERCENTILES
        )
        obtenido = calculadora.etapa(cultivo, inicio, dias)
        if esperado is None:
            assert obtenido is None, inicio
        else:
            assert obtenido is not None, inicio
            _iguales(esperado, obtenido)


def test_perfil_incompleto_o_cultivo_desconocido_da_none(datos):
    ambiental, eto, perfiles = datos
    calculadora = CalculadoraEtapas(ambiental, eto, perfiles, PERCENTILES)
    assert calculadora.etapa("C", pd.Timestamp("2021-02-01"), 30) is None
    assert calculadora.etapa("Z", pd.Timestamp("2021-02-01"), 30) is None


def test_ventana_fuera_del_rango_da_none(datos):
    ambiental, eto, perfiles = datos
    calculadora = CalculadoraEtapas(ambiental, eto, perfiles, PERCENTILES)
    assert calculadora.etapa("B", pd.Timestamp("2020-12-01"), 60) is None
    assert calculadora.etapa("B", pd.Timestamp("2022-02-01"), 60) is None

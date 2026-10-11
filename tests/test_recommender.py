import pandas as pd
import pytest

from agroshift.recommender import (
    cultivos_no_aptos,
    estado_ph_cultivo,
    fiabilidad_por_mes,
    mascara_cumple,
    rankear_rotaciones,
    sin_permutaciones,
)


def _escenario(rotacion, fecha, criterios, **extra):
    base = {
        "rotacion": rotacion,
        "fecha_inicio_escenario": fecha,
        "numero_criterios_cumplidos": criterios,
        "cumple_prioridad_agua": criterios >= 1,
        "cumple_prioridad_balance": criterios >= 2,
        "cumple_prioridad_humedad": criterios >= 3,
        "cumple_prioridad_temporal": criterios >= 4,
        "cobertura_demanda_pct": 100.0,
        "deficit_balance_mm": 0.0,
        "percentil_humedad_medio": 50.0,
        "duracion_total_dias": 200,
        "numero_etapas": 2,
    }
    base.update(extra)
    return base


@pytest.fixture
def escenarios():
    filas = []
    # A→B: cumple 3+ criterios en 3 de 4 fechas (muy fiable)
    for fecha, c in [("2021-01-01", 4), ("2021-04-01", 4), ("2021-07-01", 4), ("2021-10-01", 1)]:
        filas.append(_escenario("A → B", fecha, c))
    # B→A: mismos cultivos en otro orden, algo peor
    for fecha, c in [("2021-01-01", 4), ("2021-04-01", 3), ("2021-07-01", 1), ("2021-10-01", 1)]:
        filas.append(_escenario("B → A", fecha, c))
    # C→D: nunca cumple 3 criterios
    for fecha in ["2021-01-01", "2021-04-01"]:
        filas.append(_escenario("C → D", fecha, 1))
    return pd.DataFrame(filas)


def test_mascara_respeta_prioridades_y_minimo(escenarios):
    m = mascara_cumple(escenarios, ["humedad"], 3)
    assert m.sum() == 5  # A→B ×3, B→A ×2 (4 y 3 criterios)
    assert not m[escenarios["rotacion"] == "C → D"].any()


def test_ranking_ordena_por_fiabilidad(escenarios):
    r = rankear_rotaciones(escenarios, [], 3)
    assert r["rotacion"].tolist() == ["A → B", "B → A"]
    assert r.loc[0, "fiabilidad"] == pytest.approx(75.0)
    assert r.loc[1, "fiabilidad"] == pytest.approx(50.0)


def test_ranking_descarta_rotaciones_que_nunca_cumplen(escenarios):
    assert "C → D" not in rankear_rotaciones(escenarios, [], 3)["rotacion"].tolist()
    assert "C → D" in rankear_rotaciones(escenarios, [], 1)["rotacion"].tolist()


def test_cultivos_requeridos_y_excluidos(escenarios):
    con_c = rankear_rotaciones(escenarios, [], 1, cultivos_requeridos=["C"])
    assert con_c["rotacion"].tolist() == ["C → D"]
    sin_d = rankear_rotaciones(escenarios, [], 1, cultivos_excluidos={"D"})
    assert "C → D" not in sin_d["rotacion"].tolist()


def test_compatibilidad_se_promedia_por_rotacion(escenarios):
    comp = {"A": 100.0, "B": 60.0, "C": 0.0, "D": 0.0}
    r = rankear_rotaciones(escenarios, [], 1, compatibilidad=comp)
    fila = r[r["rotacion"] == "A → B"].iloc[0]
    assert fila["compatibilidad_media"] == pytest.approx(80.0)


def test_sin_permutaciones_deja_la_mejor_de_cada_conjunto(escenarios):
    r = rankear_rotaciones(escenarios, [], 1)
    d = sin_permutaciones(r)
    conjuntos = [frozenset(x.split(" → ")) for x in d["rotacion"]]
    assert len(conjuntos) == len(set(conjuntos)) == 2
    assert "A → B" in d["rotacion"].tolist() and "B → A" not in d["rotacion"].tolist()


def test_fiabilidad_por_mes_cubre_12_meses(escenarios):
    f = fiabilidad_por_mes(escenarios, "A → B", [], 3)
    assert len(f) == 12 and f["mes_num"].tolist() == list(range(1, 13))
    assert f.loc[f["mes_num"] == 1, "fiabilidad"].iloc[0] == 100.0
    assert f.loc[f["mes_num"] == 10, "fiabilidad"].iloc[0] == 0.0
    assert f.loc[f["mes_num"] == 2, "fiabilidad"].isna().all()  # sin fechas ese mes


def test_cultivos_no_aptos_usa_compatibilidad_final_y_temperatura():
    c = pd.DataFrame(
        {
            "nombre": ["bien", "poca_compat", "mala_temp"],
            "compatibilidad_climatica": [90, 90, 90],
            "compatibilidad_final": [90, 40, 90],
            "puntaje_temperatura_media": [90, 90, 30],
        }
    )
    assert cultivos_no_aptos(c, 50) == {"poca_compat", "mala_temp"}
    assert cultivos_no_aptos(c, 0) == set()


def test_cultivos_no_aptos_sin_columna_final():
    c = pd.DataFrame(
        {"nombre": ["a", "b"], "compatibilidad_climatica": [90, 10], "puntaje_temperatura_media": [90, 90]}
    )
    assert cultivos_no_aptos(c, 50) == {"b"}


def test_estado_ph():
    cultivo = {"ph_optimo_min": 5.5, "ph_optimo_max": 7.0, "ph_absoluto_min": 4.5, "ph_absoluto_max": 8.0}
    assert estado_ph_cultivo(6.0, cultivo) == "optimo"
    assert estado_ph_cultivo(5.0, cultivo) == "tolerable"
    assert estado_ph_cultivo(3.9, cultivo) == "fuera"

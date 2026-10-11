import json

import pandas as pd
import pytest

from agroshift import crops
from agroshift.hydrology import (
    capacidad_campo_marchitez,
    eto_penman_monteith,
    humedad_suelo_modelada,
)
from agroshift.regions import REGIONS, Region, get_region, registrar_region
from agroshift.retry import con_reintentos
from agroshift.smap_sampling import un_granulo_por_dia
from agroshift.soil import clase_textural, estado_ph, materia_organica_pct
from agroshift.water import balance_por_cultivo


# ------------------------------------------------------------------ crops
def test_nombres_comunes_en_dos_idiomas():
    assert crops.nombre_comun("Coffea arabica") == "Café"
    assert crops.nombre_comun("Coffea arabica", "en") == "Coffee"
    assert crops.nombre_comun("Especie desconocida") == "Especie desconocida"


def test_rotacion_legible():
    assert crops.rotacion_legible("Zea mays → Oryza sativa", con_icono=False) == "Maíz → Arroz"
    assert crops.rotacion_legible("Zea mays → Oryza sativa", False, "en") == "Maize → Rice"
    assert crops.cultivos_de_rotacion("A → B → C") == ["A", "B", "C"]


# ------------------------------------------------------------------ regions
def test_regiones_base_son_smap():
    for slug in ("santander", "quindio", "cordoba", "boyaca"):
        r = get_region(slug)
        assert r.fuente_humedad == "smap" and r.fila_smap is not None


def test_region_desconocida_lista_opciones():
    with pytest.raises(ValueError, match="santander"):
        get_region("marte")


def test_registrar_region_modelo(tmp_path):
    ruta = tmp_path / "extras.json"
    nueva = Region("prueba_x", "Prueba (zona)", "clima", 4.0, -74.0, 500.0, fuente_humedad="modelo")
    try:
        registrar_region(nueva, ruta)
        guardado = json.loads(ruta.read_text(encoding="utf-8"))
        assert guardado[0]["slug"] == "prueba_x" and guardado[0]["fuente_humedad"] == "modelo"
        assert REGIONS["prueba_x"].humedad_modelada
        assert REGIONS["prueba_x"].nombre_corto == "Prueba"
    finally:
        REGIONS.pop("prueba_x", None)


def test_registrar_rechaza_smap_y_duplicadas(tmp_path):
    with pytest.raises(ValueError):
        registrar_region(Region("x", "X", "c", 1, 1, 1, 1, 1, "smap"), tmp_path / "e.json")
    with pytest.raises(ValueError):
        registrar_region(
            Region("santander", "S", "c", 1, 1, 1, fuente_humedad="modelo"), tmp_path / "e.json"
        )


# ------------------------------------------------------------------ retry
def test_reintentos_hasta_tener_exito(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    llamadas = []

    def inestable():
        llamadas.append(1)
        if len(llamadas) < 3:
            raise ConnectionError("red")
        return "ok"

    assert con_reintentos(inestable, intentos=4) == "ok"
    assert len(llamadas) == 3


def test_reintentos_agotados_relanza(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)

    def siempre_falla():
        raise ConnectionError("x")

    with pytest.raises(ConnectionError):
        con_reintentos(siempre_falla, intentos=2)


# ------------------------------------------------------------------ smap_sampling
class _Granulo:
    def __init__(self, nombre):
        self._n = nombre

    def data_links(self):
        return [f"https://x/y/{self._n}"]


def test_un_granulo_por_dia_elige_el_mas_cercano_a_las_13_30():
    nombres = [
        f"SMAP_L4_SM_gph_20210105T{h}_Vv8010_001.h5" for h in ("013000", "103000", "133000", "223000")
    ] + ["SMAP_L4_SM_gph_20210106T223000_Vv8010_001.h5", "otro_archivo.h5"]
    elegidos = un_granulo_por_dia([_Granulo(n) for n in nombres])
    enlaces = sorted(g.data_links()[0].split("/")[-1] for g in elegidos)
    assert enlaces == [
        "SMAP_L4_SM_gph_20210105T133000_Vv8010_001.h5",
        "SMAP_L4_SM_gph_20210106T223000_Vv8010_001.h5",
    ]


# ------------------------------------------------------------------ soil
@pytest.mark.parametrize(
    "arena,limo,arcilla,esperada",
    [
        (92, 5, 3, "arenoso"),
        (20, 20, 60, "arcilloso"),
        (40, 40, 20, "franco"),
        (10, 85, 5, "limoso"),
        (30, 34, 34, "franco arcilloso"),
        (60, 25, 15, "franco arenoso"),
    ],
)
def test_clase_textural(arena, limo, arcilla, esperada):
    assert clase_textural(arena, limo, arcilla) == esperada


def test_materia_organica_y_ph():
    assert materia_organica_pct(58.0) == pytest.approx(10.0, rel=0.01)
    assert estado_ph(6.2, (5.5, 7.0), (4.5, 8.0)) == "optimo"
    assert estado_ph(5.0, (5.5, 7.0), (4.5, 8.0)) == "tolerable"
    assert estado_ph(9.0, (5.5, 7.0), (4.5, 8.0)) == "fuera"


def test_pedotransferencia_da_valores_fisicos():
    campo, marchitez = capacidad_campo_marchitez(30, 34, 6)  # franco arcilloso
    assert 0.2 < campo < 0.5
    assert 0.05 < marchitez < 0.3
    assert campo > marchitez


# ------------------------------------------------------------------ hydrology
def _clima(n=120, lluvia=3.0):
    return pd.DataFrame(
        {
            "fecha": pd.date_range("2022-01-01", periods=n),
            "T2M": 20.0,
            "T2M_MAX": 26.0,
            "T2M_MIN": 14.0,
            "RH2M": 75.0,
            "WS10M": 2.0,
            "ALLSKY_SFC_SW_DWN": 18.0,
            "PRECTOTCORR": lluvia,
        }
    )


def test_eto_es_positiva_y_razonable():
    eto = eto_penman_monteith(_clima(), 5.0, 1000.0)
    assert (eto >= 0).all()
    assert 2 < eto.mean() < 6


def test_humedad_modelada_esta_acotada_y_responde_a_la_lluvia():
    seco = _clima(200, lluvia=0.0)
    humedo = _clima(200, lluvia=12.0)
    hs = humedad_suelo_modelada(seco, eto_penman_monteith(seco, 5, 1000), campo=0.30, marchitez=0.14)
    hh = humedad_suelo_modelada(humedo, eto_penman_monteith(humedo, 5, 1000), campo=0.30, marchitez=0.14)
    assert hs["sm_rootzone"].between(0.14, 0.30).all()
    assert hh["sm_rootzone"].between(0.14, 0.30).all()
    assert hh["sm_rootzone"].iloc[-1] > hs["sm_rootzone"].iloc[-1]
    columnas = {"sm_surface", "sm_rootzone", "sm_surface_wetness", "sm_rootzone_wetness",
                "soil_temp_layer1_celsius"}
    assert columnas <= set(hs.columns)


# ------------------------------------------------------------------ water
def test_balance_por_cultivo_pondera_por_escenarios():
    etapas = pd.DataFrame(
        {
            "cultivo": ["A", "A", "B"],
            "cantidad_registros": [1, 3, 5],
            "duracion_promedio_dias": [100, 200, 50],
            "precipitacion_promedio_mm": [100, 200, 10],
            "ETc_promedio_mm": [80, 160, 20],
            "balance_promedio_mm": [20, 40, -10],
            "cobertura_promedio_pct": [100, 120, 50],
        }
    )
    r = balance_por_cultivo(etapas).set_index("cultivo")
    assert r.loc["A", "lluvia_mm"] == pytest.approx((100 * 1 + 200 * 3) / 4)
    assert r.loc["A", "cobertura_pct"] == 100  # tope
    assert r.loc["B", "saldo_mm"] == -10
    assert r.loc["A", "escenarios"] == 4


# ------------------------------------------------------------------ downscaling
def test_correccion_por_altitud_valle_mas_calido_que_la_celda():
    from agroshift.downscaling import corregir_por_altitud

    clima = _clima(5)
    # celda a 2100 m, punto a 1000 m: 1,1 km más abajo → +7,15 °C
    c = corregir_por_altitud(clima, 2100.0, 1000.0)
    assert (c["T2M"] - clima["T2M"]).round(2).eq(7.15).all()
    assert (c["T2M_MAX"] - c["T2M_MIN"]).round(6).eq(12.0).all()  # el rango diurno se conserva
    assert (c["RH2M"] < clima["RH2M"]).all()  # aire más cálido con el mismo vapor = menos húmedo relativo
    assert c["RH2M"].between(1, 100).all()


def test_correccion_por_altitud_meseta_mas_fria_y_no_muta_entrada():
    from agroshift.downscaling import corregir_por_altitud

    clima = _clima(5)
    antes = clima.copy()
    c = corregir_por_altitud(clima, 1500.0, 2600.0)
    assert (c["T2M"] < clima["T2M"]).all()
    assert (c["RH2M"] > clima["RH2M"]).all()
    pd.testing.assert_frame_equal(clima, antes)


def test_sin_diferencia_de_altitud_no_cambia_nada():
    from agroshift.downscaling import corregir_por_altitud

    clima = _clima(5)
    c = corregir_por_altitud(clima, 800.0, 800.0)
    pd.testing.assert_series_equal(c["T2M"], clima["T2M"])
    assert c["RH2M"].round(6).eq(clima["RH2M"]).all()

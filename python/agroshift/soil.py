"""Suelo estimado de una región (ISRIC SoilGrids) y su lectura agronómica.

El pipeline guarda, por región, un CSV de una fila con el promedio de
0–30 cm (ver 18_descargar_suelo_soilgrids.py). SoilGrids es un modelo
global a 250 m: sirve como estimación regional, no reemplaza un análisis
de laboratorio de la finca.
"""

from dataclasses import dataclass

import pandas as pd

from agroshift.config import settings

FACTOR_MATERIA_ORGANICA = 1.724  # MO = carbono orgánico × 1,724 (Van Bemmelen)


@dataclass(frozen=True)
class Suelo:
    ph: float
    arcilla_pct: float
    arena_pct: float
    limo_pct: float
    carbono_organico_g_kg: float
    materia_organica_pct: float
    textura: str
    muestras: int


def materia_organica_pct(carbono_organico_g_kg: float) -> float:
    """g/kg de carbono orgánico -> % de materia orgánica del suelo."""
    return carbono_organico_g_kg * FACTOR_MATERIA_ORGANICA / 10


def clase_textural(arena: float, limo: float, arcilla: float) -> str:
    """Clase textural del triángulo USDA (arena, limo y arcilla en %)."""
    if limo + 1.5 * arcilla < 15:
        return "arenoso"
    if limo + 1.5 * arcilla >= 15 and limo + 2 * arcilla < 30:
        return "arenoso franco"
    if (7 <= arcilla < 20 and arena > 52 and limo + 2 * arcilla >= 30) or (
        arcilla < 7 and limo < 50 and limo + 2 * arcilla >= 30
    ):
        return "franco arenoso"
    if 7 <= arcilla < 27 and 28 <= limo < 50 and arena <= 52:
        return "franco"
    if (limo >= 50 and 12 <= arcilla < 27) or (50 <= limo < 80 and arcilla < 12):
        return "franco limoso"
    if limo >= 80 and arcilla < 12:
        return "limoso"
    if 20 <= arcilla < 35 and limo < 28 and arena > 45:
        return "franco arcillo arenoso"
    if 27 <= arcilla < 40 and 20 < arena <= 45:
        return "franco arcilloso"
    if 27 <= arcilla < 40 and arena <= 20:
        return "franco arcillo limoso"
    if arcilla >= 35 and arena > 45:
        return "arcillo arenoso"
    if arcilla >= 40 and limo >= 40:
        return "arcillo limoso"
    if arcilla >= 40 and arena <= 45 and limo < 40:
        return "arcilloso"
    return "franco"


def estado_ph(valor: float, optimo: tuple[float, float], absoluto: tuple[float, float]) -> str:
    """'optimo', 'tolerable' o 'fuera' según los rangos de ECOCROP."""
    if optimo[0] <= valor <= optimo[1]:
        return "optimo"
    if absoluto[0] <= valor <= absoluto[1]:
        return "tolerable"
    return "fuera"


def cargar_suelo(region: str) -> Suelo | None:
    """Suelo de la región, o None si aún no se descargó."""
    ruta = settings.data_dir / "soil" / f"suelo_{region}.csv"
    if not ruta.exists():
        return None
    f = pd.read_csv(ruta).iloc[0]
    return Suelo(
        ph=float(f["ph"]),
        arcilla_pct=float(f["arcilla_pct"]),
        arena_pct=float(f["arena_pct"]),
        limo_pct=float(f["limo_pct"]),
        carbono_organico_g_kg=float(f["carbono_organico_g_kg"]),
        materia_organica_pct=float(f["materia_organica_pct"]),
        textura=str(f["textura"]),
        muestras=int(f["muestras"]),
    )

"""Patrón Repository: aísla la app y el pipeline del detalle de I/O.

En vez de que cada consumidor llame pd.read_csv con una ruta construida
a mano, pide los datos por nombre lógico. Si mañana cambia el origen
(otro formato, una base de datos, un bucket remoto) solo cambia este
archivo.
"""

from functools import lru_cache

import pandas as pd

from agroshift.config import settings


class DataRepository:
    """Acceso de solo lectura a los resultados del pipeline de análisis."""

    def __init__(self, analysis_dir=None, crops_dir=None):
        self._analysis_dir = analysis_dir or settings.analysis_dir
        self._crops_dir = crops_dir or settings.crops_dir

    def analysis(self, filename: str) -> pd.DataFrame:
        return self._read(self._analysis_dir / filename)

    def crops(self, filename: str) -> pd.DataFrame:
        return self._read(self._crops_dir / filename)

    @staticmethod
    @lru_cache(maxsize=64)
    def _read(path) -> pd.DataFrame:
        if not path.exists():
            raise FileNotFoundError(
                f"No se encontró '{path.name}'. "
                f"¿Corriste el pipeline? Ver python/run_pipeline.py"
            )
        return pd.read_csv(path)

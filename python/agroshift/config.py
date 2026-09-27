"""Configuración centralizada del proyecto (patrón Singleton vía módulo).

Un único punto de verdad para rutas y parámetros geográficos/temporales,
en vez de repetirlos en cada script del pipeline. Se importa como:

    from agroshift.config import settings
    settings.analysis_dir / "archivo.csv"
"""

from dataclasses import dataclass, field
from pathlib import Path

PYTHON_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    # Región de estudio: Santander, Colombia
    latitud: float = 7.119
    longitud: float = -73.122

    # Año de referencia del análisis
    fecha_inicio: str = "2020-01-01"
    fecha_fin: str = "2020-12-31"

    # Rutas del proyecto
    python_dir: Path = field(default=PYTHON_DIR)
    data_dir: Path = field(default=PYTHON_DIR / "data")
    analysis_dir: Path = field(default=PYTHON_DIR / "data" / "analysis")
    crops_dir: Path = field(default=PYTHON_DIR / "data" / "crops")

    def path_in_analysis(self, filename: str) -> Path:
        return self.analysis_dir / filename

    def path_in_crops(self, filename: str) -> Path:
        return self.crops_dir / filename


settings = Settings()

"""Configuración centralizada de rutas del proyecto (patrón Singleton vía módulo).

Un único punto de verdad para las carpetas de datos, en vez de repetir
`BASE_DIR = Path(__file__)...` en cada script. Se importa como:

    from agroshift.config import settings
    settings.analysis_dir / "indicadores_ambientales.csv"

La región y el rango de fechas no viven aquí: los fija `run_pipeline.py`
(variables de entorno AGROSHIFT_REGION / AGROSHIFT_FECHA_*) y el registro
de regiones está en `agroshift/regions.py`.
"""

from dataclasses import dataclass, field
from pathlib import Path

PYTHON_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    python_dir: Path = field(default=PYTHON_DIR)
    data_dir: Path = field(default=PYTHON_DIR / "data")
    analysis_dir: Path = field(default=PYTHON_DIR / "data" / "analysis")
    crops_dir: Path = field(default=PYTHON_DIR / "data" / "crops")


settings = Settings()

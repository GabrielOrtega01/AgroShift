from pathlib import Path

from agroshift.config import settings
from agroshift.sources.base import DataSource


class PowerDataSource(DataSource):
    """Clima diario (temperatura, precipitación, humedad, viento, radiación)."""

    name = "NASA POWER"
    script = settings.python_dir / "01_descargar_nasa_power.py"

    def fetch(self) -> None:
        self._run_script()

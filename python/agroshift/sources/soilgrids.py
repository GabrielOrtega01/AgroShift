from agroshift.config import settings
from agroshift.sources.base import DataSource


class SoilGridsDataSource(DataSource):
    """Textura, pH y carbono orgánico del suelo (0-30 cm) por región."""

    name = "ISRIC SoilGrids"
    script = settings.python_dir / "18_descargar_suelo_soilgrids.py"

    def fetch(self) -> None:
        self._run_script()

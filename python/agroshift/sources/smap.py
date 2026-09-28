from agroshift.config import settings
from agroshift.sources.base import DataSource


class SmapDataSource(DataSource):
    """Humedad del suelo (superficial y zona radicular) vía NASA SMAP L4."""

    name = "NASA SMAP"
    script = settings.python_dir / "02_descargar_nasa_smap.py"

    def fetch(self) -> None:
        self._run_script()
        self.repair()

    def repair(self) -> None:
        """Recupera automáticamente cualquier día con menos de 8 observaciones."""
        self._run_script(settings.python_dir / "03_recuperar_smap_faltantes.py")

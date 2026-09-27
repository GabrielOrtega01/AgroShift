from agroshift.config import settings
from agroshift.sources.base import DataSource


class SmapDataSource(DataSource):
    """Humedad del suelo (superficial y zona radicular) vía NASA SMAP L4."""

    name = "NASA SMAP"
    script = settings.python_dir / "02_descargar_nasa_smap.py"

    def fetch(self) -> None:
        self._run_script()

    def repair(self) -> None:
        """Aplica los parches de datos faltantes ya documentados (enero 2020)."""
        for fix_script in (
            settings.python_dir / "03_corregir_smap_enero.py",
            settings.python_dir / "04_recuperar_smap_faltantes.py",
        ):
            self._run_script(fix_script)

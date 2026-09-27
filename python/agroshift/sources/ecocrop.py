from agroshift.config import settings
from agroshift.sources.base import DataSource


class EcocropDataSource(DataSource):
    """Catálogo y requerimientos agronómicos de cultivos (FAO ECOCROP)."""

    name = "FAO ECOCROP"
    script = settings.python_dir / "05_descargar_catalogo_ecocrop.py"

    def fetch(self) -> None:
        self._run_script()
        self._run_script(settings.python_dir / "06_extraer_caracteristicas_ecocrop.py")

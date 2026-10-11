"""Una etapa del pipeline: un script ya existente y su descripción."""

from dataclasses import dataclass
from pathlib import Path

from agroshift.config import settings


@dataclass(frozen=True)
class PipelineStep:
    name: str
    script: str  # nombre del archivo dentro de python/
    description: str
    # Un paso opcional puede fallar (p. ej. un servicio externo caído)
    # sin detener el resto del pipeline.
    opcional: bool = False

    @property
    def path(self) -> Path:
        return settings.python_dir / self.script

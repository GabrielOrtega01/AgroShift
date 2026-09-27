"""Una etapa del pipeline: un script ya existente y su descripción."""

from dataclasses import dataclass
from pathlib import Path

from agroshift.config import settings


@dataclass(frozen=True)
class PipelineStep:
    name: str
    script: str  # nombre del archivo dentro de python/
    description: str

    @property
    def path(self) -> Path:
        return settings.python_dir / self.script

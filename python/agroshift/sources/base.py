"""Patrón Strategy: cada origen de datos externo implementa la misma interfaz.

El pipeline solo conoce `DataSource.fetch()`; no le importa si por debajo
hay una API REST (NASA POWER), un buscador satelital (SMAP vía earthaccess)
o un scraper (FAO ECOCROP). Los scripts de descarga ya existentes y
probados (numerados 01-06 en python/) se reutilizan tal cual, ejecutándolos
como subprocesos — así no se reescribe lógica de red/parsing ya validada.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from agroshift.process import run_script


class DataSource(ABC):
    name: str
    script: Path

    @abstractmethod
    def fetch(self) -> None:
        """Descarga o actualiza los datos crudos de esta fuente."""

    def _run_script(self, script: Path | None = None) -> None:
        script = script or self.script
        if not script.exists():
            raise FileNotFoundError(f"{self.name}: no existe el script {script}")

        print(f"\n[{self.name}] ejecutando {script.name} ...")
        result = run_script(script)
        if result.returncode != 0:
            raise RuntimeError(
                f"[{self.name}] {script.name} terminó con código {result.returncode}"
            )

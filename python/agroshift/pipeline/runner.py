"""Patrón Pipeline (Chain of Responsibility): ejecuta las etapas en orden,
deteniéndose en el primer error y reportando qué se alcanzó a completar.

Cada etapa es un script standalone ya validado (ver python/01_*.py .. 18_*.py).
Este runner no conoce ni reescribe su lógica interna: solo orquesta el orden,
mide tiempos y centraliza el manejo de errores — la parte "de plomería" que
antes había que hacer a mano, corriendo cada script uno por uno.
"""

import time
from dataclasses import dataclass

from agroshift.pipeline.step import PipelineStep
from agroshift.process import run_script


@dataclass
class StepResult:
    step: PipelineStep
    ok: bool
    seconds: float


class Pipeline:
    def __init__(self, steps: list[PipelineStep]):
        self._steps = steps
        self.results: list[StepResult] = []

    def run_all(self, stop_on_error: bool = True) -> list[StepResult]:
        self.results = []
        for step in self._steps:
            print(f"\n{'=' * 70}\n[{step.name}] {step.description}\n{'=' * 70}")

            start = time.perf_counter()
            result = run_script(step.path)
            elapsed = time.perf_counter() - start
            ok = result.returncode == 0

            self.results.append(StepResult(step=step, ok=ok, seconds=elapsed))

            if not ok:
                print(f"\n[{step.name}] FALLÓ (código {result.returncode})")
                if stop_on_error:
                    break

        self._print_summary()
        return self.results

    def _print_summary(self) -> None:
        print(f"\n{'=' * 70}\nRESUMEN\n{'=' * 70}")
        for r in self.results:
            estado = "OK" if r.ok else "FALLÓ"
            print(f"  [{estado}] {r.step.name} ({r.seconds:.1f}s)")

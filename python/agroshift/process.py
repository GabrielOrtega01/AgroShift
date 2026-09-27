"""Ejecución compartida de scripts standalone como subprocesos.

Fuerza UTF-8 en stdout/stderr: varios scripts imprimen caracteres como ✓/✗
y en Windows el subproceso hereda por defecto la consola cp1252, que no
puede codificarlos y hace fallar el script con UnicodeEncodeError.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_script(script: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    return subprocess.run(
        [sys.executable, str(script)],
        cwd=script.parent,
        env=env,
    )

"""Rutas de importación para las pruebas (el código vive en python/ y ui/)."""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for ruta in (RAIZ / "python", RAIZ):
    if str(ruta) not in sys.path:
        sys.path.insert(0, str(ruta))

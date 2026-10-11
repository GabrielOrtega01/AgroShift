"""Exporta los escenarios en un archivo liviano para la app.

`escenarios_priorizados_v9.csv` pesa ~20 MB por región con 32 columnas, de
las cuales la app sólo usa las del recomendador. Este paso deja
`escenarios_app.csv.gz` (sin pérdida de filas, sólo esas columnas, comprimido)
para que el repositorio y el despliegue sean livianos.
"""

import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agroshift.regions import get_region

REGION = get_region(os.environ.get("AGROSHIFT_REGION", "santander"))
ANALYSIS_DIR = Path(__file__).resolve().parent / "data" / "analysis" / REGION.slug

ENTRADA = ANALYSIS_DIR / "escenarios_priorizados_v9.csv"
SALIDA = ANALYSIS_DIR / "escenarios_app.csv.gz"

COLUMNAS = [
    "rotacion",
    "fecha_inicio_escenario",
    "numero_etapas",
    "duracion_total_dias",
    "cobertura_demanda_pct",
    "deficit_balance_mm",
    "percentil_humedad_medio",
    "numero_criterios_cumplidos",
    "cumple_prioridad_agua",
    "cumple_prioridad_balance",
    "cumple_prioridad_humedad",
    "cumple_prioridad_temporal",
]

escenarios = pd.read_csv(ENTRADA, usecols=COLUMNAS)
escenarios = escenarios[COLUMNAS]
for columna in COLUMNAS[4:7]:
    escenarios[columna] = escenarios[columna].round(3)
escenarios.to_csv(SALIDA, index=False, compression="gzip")

print(f"Región: {REGION.nombre}")
print(f"Escenarios: {len(escenarios)}")
print(f"{ENTRADA.name}: {ENTRADA.stat().st_size / 1e6:.1f} MB -> {SALIDA.name}: {SALIDA.stat().st_size / 1e6:.2f} MB")

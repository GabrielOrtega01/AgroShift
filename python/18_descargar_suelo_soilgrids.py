"""Descarga el suelo de la región desde ISRIC SoilGrids v2 (250 m).

Toma varios puntos alrededor del punto de referencia (SoilGrids enmascara
píxeles urbanos o sin dato), promedia 0–30 cm ponderando por espesor de
capa y guarda una fila por región en data/soil/suelo_<region>.csv.

Uso (vía run_pipeline.py o directo):
    AGROSHIFT_REGION=quindio python 18_descargar_suelo_soilgrids.py
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agroshift.regions import get_region
from agroshift.retry import con_reintentos
from agroshift.soil import clase_textural, materia_organica_pct

REGION = get_region(os.environ.get("AGROSHIFT_REGION", "santander"))

BASE_DIR = Path(__file__).resolve().parent
SALIDA = BASE_DIR / "data" / "soil" / f"suelo_{REGION.slug}.csv"

API = "https://rest.isric.org/soilgrids/v2.0/properties/query"
PROPIEDADES = ["phh2o", "clay", "sand", "silt", "soc"]
CAPAS = {"0-5cm": 5, "5-15cm": 10, "15-30cm": 15}  # espesor en cm
PASO_GRADOS = 0.03          # ~3 km
MUESTRAS_OBJETIVO = 3
MAX_PUNTOS = 9


def consultar(latitud: float, longitud: float) -> dict[str, float] | None:
    """Promedio 0–30 cm por propiedad en un punto; None si está enmascarado."""
    parametros = (
        [("lon", longitud), ("lat", latitud)]
        + [("property", p) for p in PROPIEDADES]
        + [("depth", c) for c in CAPAS]
        + [("value", "mean")]
    )

    def _pedir():
        with urllib.request.urlopen(f"{API}?{urllib.parse.urlencode(parametros)}", timeout=180) as r:
            return json.load(r)

    datos = con_reintentos(_pedir, intentos=4, espera_base=15)
    resultado = {}
    for capa in datos["properties"]["layers"]:
        factor = capa["unit_measure"]["d_factor"]
        valores, pesos = [], []
        for profundidad in capa["depths"]:
            v = profundidad["values"]["mean"]
            if v is not None:
                valores.append(v / factor)
                pesos.append(CAPAS[profundidad["label"]])
        if not valores:
            return None
        resultado[capa["name"]] = float(np.average(valores, weights=pesos))
    return resultado


def main() -> None:
    desplazamientos = [(0, 0)] + [
        (dy * PASO_GRADOS, dx * PASO_GRADOS)
        for dy in (-1, 0, 1)
        for dx in (-1, 0, 1)
        if (dy, dx) != (0, 0)
    ]
    muestras = []
    for dy, dx in desplazamientos[:MAX_PUNTOS]:
        try:
            punto = consultar(REGION.latitud + dy, REGION.longitud + dx)
            estado = "ok" if punto else "sin dato (enmascarado)"
        except Exception as error:  # el servicio falla a ratos: seguir con otro punto
            punto = None
            estado = f"error de red ({type(error).__name__})"
        print(f"  ({REGION.latitud + dy:.3f}, {REGION.longitud + dx:.3f}): {estado}")
        if punto:
            muestras.append(punto)
        if len(muestras) >= MUESTRAS_OBJETIVO:
            break

    if not muestras:
        raise SystemExit(f"SoilGrids no devolvió datos para {REGION.nombre}")

    tabla = pd.DataFrame(muestras)
    mediana = tabla.median()
    arcilla, arena, limo = mediana["clay"], mediana["sand"], mediana["silt"]
    carbono = mediana["soc"]

    fila = {
        "region": REGION.slug,
        "ph": round(mediana["phh2o"], 2),
        "arcilla_pct": round(arcilla, 1),
        "arena_pct": round(arena, 1),
        "limo_pct": round(limo, 1),
        "carbono_organico_g_kg": round(carbono, 1),
        "materia_organica_pct": round(materia_organica_pct(carbono), 2),
        "textura": clase_textural(arena, limo, arcilla),
        "muestras": len(muestras),
        "profundidad_cm": "0-30",
        "fuente": "ISRIC SoilGrids v2.0",
    }
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([fila]).to_csv(SALIDA, index=False)
    print(f"\nSuelo de {REGION.nombre}:")
    for k, v in fila.items():
        print(f"  {k}: {v}")
    print(f"\nGuardado en {SALIDA}")


if __name__ == "__main__":
    main()

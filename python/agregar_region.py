"""Registra una región nueva (humedad del suelo modelada) y, si se pide,
corre su pipeline completo.

La humedad se estima con un balance hídrico a partir de NASA POWER (no se
descarga SMAP, que exige cuenta Earthdata y horas de descarga). Ver
docs/como_agregar_una_region.md.

Uso:
    python agregar_region.py --slug meta \\
        --nombre "Meta (piedemonte llanero)" \\
        --clima "Cálido y húmedo, arroz, palma y maíz" \\
        --latitud 4.15 --longitud -73.63 --altitud 467 --ejecutar
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

from agroshift.regions import Region, registrar_region

BASE = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--slug", required=True, help="identificador en minúsculas y sin tildes (p. ej. 'meta')")
    parser.add_argument("--nombre", required=True, help="nombre visible, p. ej. 'Meta (piedemonte llanero)'")
    parser.add_argument("--clima", required=True, help="descripción corta del clima y los cultivos típicos")
    parser.add_argument("--latitud", type=float, required=True)
    parser.add_argument("--longitud", type=float, required=True)
    parser.add_argument("--altitud", type=float, required=True, help="metros sobre el nivel del mar")
    parser.add_argument("--ejecutar", action="store_true", help="corre run_pipeline.py para la región")
    args = parser.parse_args()

    if not re.fullmatch(r"[a-z0-9_]+", args.slug):
        parser.error("--slug sólo admite minúsculas, números y guion bajo")
    if not (-90 <= args.latitud <= 90 and -180 <= args.longitud <= 180):
        parser.error("coordenadas fuera de rango")

    region = Region(
        slug=args.slug,
        nombre=args.nombre,
        clima=args.clima,
        latitud=args.latitud,
        longitud=args.longitud,
        altitud_m=args.altitud,
        fuente_humedad="modelo",
    )
    registrar_region(region)
    print(f"✓ Región '{region.slug}' registrada (humedad del suelo modelada).")

    if args.ejecutar:
        sys.exit(subprocess.call([sys.executable, str(BASE / "run_pipeline.py"), "--region", region.slug]))
    print(f"  Para calcularla: python run_pipeline.py --region {region.slug}")


if __name__ == "__main__":
    main()

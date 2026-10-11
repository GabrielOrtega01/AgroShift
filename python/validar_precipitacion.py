"""Contrasta la lluvia de NASA GPM IMERG y NASA POWER con CHIRPS.

NASA POWER devuelve para 2021 totales muy bajos en las 4 primeras regiones.
Este script baja los mosaicos mensuales de CHIRPS v2 (satélite +
pluviómetros, 0.05°, público y sin credenciales), toma el píxel de cada
región y compara totales mensuales y anuales con NASA POWER y con NASA GPM
IMERG (la lluvia que usa el pipeline, con POWER en los días sin dato).

La comparación diaria no es informativa (la lluvia tropical es muy local),
por eso se compara a escala mensual.

Salidas (data/validation/):
    precipitacion_anual.csv    total anual POWER vs CHIRPS por región y año
    precipitacion_mensual.csv  total mensual POWER vs CHIRPS

Uso:
    python validar_precipitacion.py
"""

import gzip
import io
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

from agroshift.imerg import cargar_lluvia_imerg
from agroshift.regions import REGIONS
from agroshift.retry import con_reintentos

BASE = Path(__file__).resolve().parent
SALIDA = BASE / "data" / "validation"
URL = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/tifs/chirps-v2.0.{anio}.{mes:02d}.tif.gz"
RESOLUCION = 0.05  # grados; la grilla cubre 50°S–50°N y 180°O–180°E
SIN_DATO = -9999.0


def pixel(latitud: float, longitud: float) -> tuple[int, int]:
    return int((50 - latitud) / RESOLUCION), int((longitud + 180) / RESOLUCION)


def _descargar(anio: int, mes: int) -> bytes:
    with urllib.request.urlopen(URL.format(anio=anio, mes=mes), timeout=180) as r:
        return r.read()


def valores_mes(anio: int, mes: int) -> dict[str, float]:
    contenido = con_reintentos(lambda: _descargar(anio, mes), intentos=5, espera_base=10)
    mosaico = np.array(Image.open(io.BytesIO(gzip.decompress(contenido))))
    valores = {}
    for region in REGIONS.values():
        fila, col = pixel(region.latitud, region.longitud)
        v = float(mosaico[fila, col])
        valores[region.slug] = np.nan if v == SIN_DATO else v
    return valores


def _ya_completo() -> bool:
    ruta = SALIDA / "precipitacion_mensual.csv"
    if not ruta.exists():
        return False
    tabla = pd.read_csv(ruta)
    return set(REGIONS) <= set(tabla["region"]) and tabla["imerg_mm"].notna().any()


def main() -> None:
    if _ya_completo() and "--forzar" not in sys.argv:
        print("precipitacion_mensual.csv ya incluye todas las regiones (use --forzar para rehacerlo).")
        return
    power = {}
    for region in REGIONS.values():
        serie = pd.read_csv(
            BASE / "data" / "power" / f"nasa_power_{region.slug}.csv", parse_dates=["DATE"]
        ).set_index("DATE")["PRECTOTCORR"]
        power[region.slug] = serie.groupby([serie.index.year, serie.index.month]).sum()

    imerg = {}
    for region in REGIONS.values():
        diaria = cargar_lluvia_imerg(region.slug)
        if diaria is None:
            continue
        bruta = pd.read_csv(
            BASE / "data" / "power" / f"nasa_power_{region.slug}.csv", parse_dates=["DATE"]
        ).set_index("DATE")["PRECTOTCORR"]
        iserie = pd.Series(
            diaria["IMERG_PRECIP"].to_numpy(), index=pd.to_datetime(diaria["fecha"])
        ).reindex(bruta.index)
        iserie = iserie.fillna(bruta)  # igual que el pipeline: POWER donde falta IMERG
        imerg[region.slug] = iserie.groupby([iserie.index.year, iserie.index.month]).sum()

    anios = sorted({a for serie in power.values() for a, _ in serie.index})
    filas = []
    for anio in anios:
        for mes in range(1, 13):
            chirps = valores_mes(anio, mes)
            for slug in REGIONS:
                filas.append(
                    {
                        "region": slug, "anio": anio, "mes": mes,
                        "power_mm": round(power[slug].get((anio, mes), np.nan), 1),
                        "imerg_mm": round(imerg[slug].get((anio, mes), np.nan), 1) if slug in imerg else np.nan,
                        "chirps_mm": round(chirps[slug], 1),
                    }
                )
        print(f"  CHIRPS {anio} descargado")

    mensual = pd.DataFrame(filas)
    anual = (
        mensual.groupby(["region", "anio"])[["power_mm", "imerg_mm", "chirps_mm"]]
        .sum(min_count=1)
        .reset_index()
    )
    anual["diferencia_power_pct"] = ((anual["power_mm"] / anual["chirps_mm"] - 1) * 100).round(1)
    anual["diferencia_imerg_pct"] = ((anual["imerg_mm"] / anual["chirps_mm"] - 1) * 100).round(1)

    SALIDA.mkdir(parents=True, exist_ok=True)
    mensual.to_csv(SALIDA / "precipitacion_mensual.csv", index=False)
    anual.to_csv(SALIDA / "precipitacion_anual.csv", index=False)

    print("\nTotales anuales (mm):")
    print(anual.to_string(index=False))
    print("\nCorrelación mensual contra CHIRPS (POWER | IMERG):")
    for slug, g in mensual.groupby("region"):
        print(f"  {slug:13s} {g['power_mm'].corr(g['chirps_mm']):.2f} | {g['imerg_mm'].corr(g['chirps_mm']):.2f}")
    print(f"\nGuardado en {SALIDA}")


if __name__ == "__main__":
    main()

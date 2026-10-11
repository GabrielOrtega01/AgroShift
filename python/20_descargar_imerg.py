"""Descarga la lluvia diaria de NASA GPM IMERG (Final Run v07) por región.

IMERG publica un archivo global por día (0,1°). Como un mismo archivo sirve
a todas las regiones, se leen una sola vez y se extrae la celda de cada
región registrada, leyendo sólo los bytes necesarios (sin bajar el archivo
completo). Guarda data/imerg/imerg_<region>.csv con fecha e IMERG_PRECIP
(mm/día) y reanuda desde `_progreso.csv` si se interrumpe.

Requiere sesión de NASA Earthdata con la aplicación «NASA GESDISC DATA
ARCHIVE» autorizada (earthaccess.login(persist=True)).
"""

import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import earthaccess
import h5py
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agroshift.regions import REGIONS
from agroshift.retry import con_reintentos

FECHA_INICIO = os.environ.get("AGROSHIFT_FECHA_INICIO", "2020-01-01")
FECHA_FIN = os.environ.get("AGROSHIFT_FECHA_FIN", "2025-12-31")

SALIDA = Path(__file__).resolve().parent / "data" / "imerg"
PROGRESO = SALIDA / "_progreso.csv"
PROCESOS = 8
LOTE = 20  # días por tarea
PATRON_FECHA = re.compile(r"\.(\d{8})-S")


def _fechas_del_rango() -> pd.DatetimeIndex:
    return pd.date_range(FECHA_INICIO, FECHA_FIN, freq="D")


def _csv_completo(slug: str, fechas: pd.DatetimeIndex) -> bool:
    ruta = SALIDA / f"imerg_{slug}.csv"
    if not ruta.exists():
        return False
    presentes = pd.to_datetime(pd.read_csv(ruta)["fecha"])
    return set(fechas) <= set(presentes)


def _buscar_granulos(inicio: str, fin: str):
    def buscar():
        return earthaccess.search_data(
            short_name="GPM_3IMERGDF", version="07", temporal=(inicio, fin)
        )

    return con_reintentos(buscar, intentos=5, espera_base=10)


def _fecha_de(granulo) -> pd.Timestamp:
    ur = granulo["umm"]["GranuleUR"]
    return pd.Timestamp(PATRON_FECHA.search(ur).group(1))


def _leer_lote(
    items: list[tuple[str, str]], celdas: dict[str, tuple[int, int]]
) -> dict[str, dict[str, float]]:
    """Lee los puntos de un lote de días. Corre en un proceso aparte, con su
    propia sesión de Earthdata. `items` = [(fecha ISO, URL del archivo)]."""
    earthaccess.login(strategy="netrc")
    resultado = {}
    for fecha, url in items:
        def abrir():
            return earthaccess.open([url])[0]

        try:
            archivo = con_reintentos(abrir, intentos=5, espera_base=8)
            with h5py.File(archivo, "r") as h:
                lluvia = h["precipitation"]
                valores = {}
                for slug, (j, i) in celdas.items():
                    v = float(lluvia[0, j, i])
                    valores[slug] = np.nan if v < -9000 else v
            resultado[fecha] = valores
        except Exception as error:  # un día fallido no tumba el lote
            print(f"  {fecha}: {type(error).__name__}", flush=True)
    return resultado


def main() -> None:
    fechas = _fechas_del_rango()
    regiones = list(REGIONS)
    pendientes = [s for s in regiones if not _csv_completo(s, fechas)]
    if not pendientes:
        print("IMERG: todas las regiones ya tienen el rango completo.")
        return

    SALIDA.mkdir(parents=True, exist_ok=True)
    earthaccess.login(strategy="netrc")

    print(f"Buscando gránulos IMERG {FECHA_INICIO} → {FECHA_FIN} ...")
    granulos = []
    for anio in sorted({f.year for f in fechas}):
        ini = max(pd.Timestamp(f"{anio}-01-01"), fechas.min()).strftime("%Y-%m-%d")
        fin = min(pd.Timestamp(f"{anio}-12-31"), fechas.max()).strftime("%Y-%m-%d")
        granulos += _buscar_granulos(ini, fin)
    por_fecha = {_fecha_de(g): g for g in granulos}
    print(f"Gránulos encontrados: {len(por_fecha)} de {len(fechas)} días")

    # Celda (lon, lat) de cada región en la grilla de 0,1°
    muestra = con_reintentos(lambda: earthaccess.open([next(iter(por_fecha.values()))])[0])
    with h5py.File(muestra, "r") as h:
        lat, lon = h["lat"][:], h["lon"][:]
    celdas = {}
    for slug in regiones:
        r = REGIONS[slug]
        celdas[slug] = (int(np.abs(lon - r.longitud).argmin()), int(np.abs(lat - r.latitud).argmin()))

    hechos: dict[pd.Timestamp, dict[str, float]] = {}
    if PROGRESO.exists():
        previo = pd.read_csv(PROGRESO, parse_dates=["fecha"]).set_index("fecha")
        if set(regiones) <= set(previo.columns):
            hechos = {f: previo.loc[f, regiones].to_dict() for f in previo.index}
            print(f"Reanudando: {len(hechos)} días ya leídos")

    por_leer = [f for f in sorted(por_fecha) if f not in hechos]
    print(f"Por leer: {len(por_leer)} días con {PROCESOS} procesos", flush=True)

    def guardar_progreso():
        tabla = pd.DataFrame.from_dict(hechos, orient="index")[regiones]
        tabla.index.name = "fecha"
        tabla.sort_index().to_csv(PROGRESO)

    urls = {f: por_fecha[f].data_links()[0] for f in por_leer}
    lotes = [
        [(f.strftime("%Y-%m-%d"), urls[f]) for f in por_leer[k:k + LOTE]]
        for k in range(0, len(por_leer), LOTE)
    ]
    with ProcessPoolExecutor(max_workers=PROCESOS) as pool:
        futuros = [pool.submit(_leer_lote, lote, celdas) for lote in lotes]
        for n, futuro in enumerate(as_completed(futuros), 1):
            for fecha, valores in futuro.result().items():
                hechos[pd.Timestamp(fecha)] = valores
            guardar_progreso()
            print(f"  lotes {n}/{len(lotes)} · {len(hechos)} días", flush=True)

    tabla = pd.DataFrame.from_dict(hechos, orient="index")[regiones].sort_index()
    for slug in regiones:
        salida = tabla[[slug]].rename(columns={slug: "IMERG_PRECIP"})
        salida.index.name = "fecha"
        salida.round(3).to_csv(SALIDA / f"imerg_{slug}.csv")
        faltan = int(salida["IMERG_PRECIP"].isna().sum()) + (len(fechas) - len(salida))
        print(f"{slug:13s} {len(salida)} días, {salida['IMERG_PRECIP'].sum() / (len(fechas) / 365.25):.0f} mm/año, "
              f"sin dato: {faltan}")


if __name__ == "__main__":
    main()

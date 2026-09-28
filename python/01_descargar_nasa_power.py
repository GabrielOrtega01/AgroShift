import os
import sys
import requests
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agroshift.regions import get_region

REGION = get_region(os.environ.get("AGROSHIFT_REGION", "santander"))


# ============================================================
# AGROSHIFT - NASA POWER
# Primera extracción de datos climáticos
# ============================================================

LATITUDE = REGION.latitud
LONGITUDE = REGION.longitud

# Periodo de análisis
START_DATE = os.environ.get("AGROSHIFT_FECHA_INICIO", "2020-01-01").replace("-", "")
END_DATE = os.environ.get("AGROSHIFT_FECHA_FIN", "2025-12-31").replace("-", "")

# Variables NASA POWER
PARAMETERS = [
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "PRECTOTCORR",
    "RH2M",
    "WS10M",
    "ALLSKY_SFC_SW_DWN"
]

URL = "https://power.larc.nasa.gov/api/temporal/daily/point"


def obtener_datos_nasa():
    params = {
        "parameters": ",".join(PARAMETERS),
        "community": "AG",
        "longitude": LONGITUDE,
        "latitude": LATITUDE,
        "start": START_DATE,
        "end": END_DATE,
        "format": "JSON"
    }

    print("Consultando NASA POWER...")
    print(f"Latitud: {LATITUDE}")
    print(f"Longitud: {LONGITUDE}")
    print(f"Periodo: {START_DATE} - {END_DATE}")

    response = requests.get(URL, params=params, timeout=60)

    response.raise_for_status()

    return response.json()


def convertir_dataframe(data):
    properties = data["properties"]

    parameter_data = properties["parameter"]

    df = pd.DataFrame(parameter_data)

    df.index.name = "DATE"

    df = df.reset_index()

    df["DATE"] = pd.to_datetime(df["DATE"], format="%Y%m%d")

    return df


def guardar_datos(df):
    output_dir = Path(__file__).resolve().parent / "data" / "power"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"nasa_power_{REGION.slug}.csv"

    df.to_csv(output_file, index=False)

    return output_file


def main():

    try:
        data = obtener_datos_nasa()

        df = convertir_dataframe(data)

        output_file = guardar_datos(df)

        print("\n==========================================")
        print("      AGROSHIFT - NASA POWER")
        print("==========================================")

        print(f"\nRegistros obtenidos: {len(df)}")
        print(f"Variables: {len(df.columns) - 1}")

        print("\nColumnas:")
        print(df.columns.tolist())

        print("\nPrimeros registros:")
        print(df.head())

        print("\nEstadística descriptiva:")
        print(df.describe())

        print(f"\nArchivo generado:")
        print(output_file)

        print("\nNASA POWER consultado correctamente.")


    except requests.exceptions.RequestException as error:

        print("\nERROR al consultar NASA POWER:")
        print(error)

    except Exception as error:

        print("\nERROR:")
        print(error)


if __name__ == "__main__":
    main()
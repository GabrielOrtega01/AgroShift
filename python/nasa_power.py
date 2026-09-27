import requests
import pandas as pd
from pathlib import Path


# ============================================================
# AGROSHIFT - NASA POWER
# Primera extracción de datos climáticos
# ============================================================

# Ubicación de prueba: Santander, Colombia
LATITUDE = 7.119
LONGITUDE = -73.122

# Periodo de análisis
START_DATE = "20200101"
END_DATE = "20251231"

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
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "nasa_power_santander.csv"

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
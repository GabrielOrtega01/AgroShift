import h5py
import numpy as np
from pathlib import Path

# ============================================================
# AGROSHIFT - EXTRACCIÓN DE PUNTO SMAP
# ============================================================

LATITUDE = 7.119
LONGITUDE = -73.122

SMAP_FILE = next(
    Path("data/smap").glob("*.h5")
)

print("==========================================")
print("       AGROSHIFT - PUNTO SMAP")
print("==========================================")

print(f"\nArchivo:")
print(SMAP_FILE)

print("\nUbicación objetivo:")
print(f"Latitud : {LATITUDE}")
print(f"Longitud: {LONGITUDE}")


with h5py.File(SMAP_FILE, "r") as hdf:

    # --------------------------------------------------------
    # Coordenadas
    # --------------------------------------------------------

    latitudes = hdf["cell_lat"][:]
    longitudes = hdf["cell_lon"][:]

    print("\n------------------------------------------")
    print("COORDENADAS")
    print("------------------------------------------")

    print(f"Forma latitudes : {latitudes.shape}")
    print(f"Forma longitudes: {longitudes.shape}")

    print(f"\nLatitud mínima : {np.nanmin(latitudes):.4f}")
    print(f"Latitud máxima : {np.nanmax(latitudes):.4f}")

    print(f"\nLongitud mínima: {np.nanmin(longitudes):.4f}")
    print(f"Longitud máxima: {np.nanmax(longitudes):.4f}")

    # --------------------------------------------------------
    # Buscar celda más cercana
    # --------------------------------------------------------

    distance = (
        (latitudes - LATITUDE) ** 2
        + (longitudes - LONGITUDE) ** 2
    )

    flat_index = np.nanargmin(distance)

    # Convertir índice plano a fila y columna
    row, column = np.unravel_index(
        flat_index,
        latitudes.shape
    )

    nearest_lat = latitudes[row, column]
    nearest_lon = longitudes[row, column]

    print("\n------------------------------------------")
    print("CELDA MÁS CERCANA")
    print("------------------------------------------")

    print(f"Fila   : {row}")
    print(f"Columna: {column}")

    print(f"Latitud : {nearest_lat:.6f}")
    print(f"Longitud: {nearest_lon:.6f}")

    print(
        f"\nDistancia aproximada en grados: "
        f"{np.sqrt(distance[row, column]):.6f}"
    )

    # --------------------------------------------------------
    # Variables principales
    # --------------------------------------------------------

    print("\n------------------------------------------")
    print("VARIABLES SMAP")
    print("------------------------------------------")

    variables = [
        "sm_surface",
        "sm_rootzone",
        "sm_surface_wetness",
        "sm_rootzone_wetness",
        "soil_temp_layer1"
    ]

    for variable in variables:

        dataset = hdf[f"Geophysical_Data/{variable}"]

        print(f"\n{variable}")
        print(f"  Forma: {dataset.shape}")
        print(f"  Tipo : {dataset.dtype}")

        value = dataset[row, column]

        print(f"  Valor en la celda: {value}")

print("\n==========================================")
print("EXTRACCIÓN FINALIZADA")
print("==========================================")
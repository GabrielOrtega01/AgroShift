import earthaccess
import h5py
from pathlib import Path

# ============================================================
# AGROSHIFT - INSPECCIÓN DE NASA SMAP
# ============================================================

LATITUDE = 7.119
LONGITUDE = -73.122

START_DATE = "2020-01-01"
END_DATE = "2020-01-01"

OUTPUT_DIR = Path("data") / "smap"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("==========================================")
print("      AGROSHIFT - INSPECCIÓN SMAP")
print("==========================================")

print("\nIniciando sesión en NASA Earthdata...")
earthaccess.login()

print("\nBuscando archivo SMAP...")

results = earthaccess.search_data(
    short_name="SPL4SMGP",
    temporal=(START_DATE, END_DATE),
    bounding_box=(
        LONGITUDE,
        LATITUDE,
        LONGITUDE,
        LATITUDE
    )
)

print(f"Archivos encontrados: {len(results)}")

if not results:
    raise RuntimeError("No se encontraron archivos SMAP.")

# Tomamos solamente el primer archivo
result = results[0]

print("\nDescargando solamente un archivo de prueba...")
print("Esto puede tardar unos minutos.")

files = earthaccess.download(
    [result],
    local_path=str(OUTPUT_DIR)
)

print("\nDescarga finalizada.")

if not files:
    raise RuntimeError("No se pudo descargar el archivo.")

file_path = Path(files[0])

print(f"\nArchivo descargado:")
print(file_path)

print("\n==========================================")
print("ESTRUCTURA DEL ARCHIVO HDF5")
print("==========================================")

with h5py.File(file_path, "r") as hdf:

    def mostrar_estructura(name, obj):
        if isinstance(obj, h5py.Dataset):
            print(f"[DATASET] {name}")
        else:
            print(f"[GRUPO]   {name}")

    hdf.visititems(mostrar_estructura)

print("\n==========================================")
print("INSPECCIÓN FINALIZADA")
print("==========================================")
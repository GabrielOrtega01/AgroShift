from pathlib import Path
import pandas as pd


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

POWER_FILE = (
    BASE_DIR
    / "data"
    / "nasa_power_santander.csv"
)

SMAP_FILE = (
    BASE_DIR
    / "data"
    / "analysis"
    / "smap_daily_santander.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "analysis"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# ARCHIVO DE SALIDA
# ============================================================

OUTPUT_FILE = (
    OUTPUT_DIR
    / "agroshift_environmental_data.csv"
)


# ============================================================
# CARGAR NASA POWER
# ============================================================

print("=" * 70)
print("INTEGRACIÓN DE DATOS NASA")
print("=" * 70)

print()
print("Cargando datos NASA POWER...")

if not POWER_FILE.exists():
    raise FileNotFoundError(
        f"No se encontró el archivo NASA POWER:\n{POWER_FILE}"
    )

power = pd.read_csv(POWER_FILE)

print(f"Registros NASA POWER: {len(power)}")


# ============================================================
# CARGAR SMAP
# ============================================================

print()
print("Cargando datos SMAP...")

if not SMAP_FILE.exists():
    raise FileNotFoundError(
        f"No se encontró el archivo SMAP:\n{SMAP_FILE}"
    )

smap = pd.read_csv(SMAP_FILE)

print(f"Registros SMAP: {len(smap)}")


# ============================================================
# REVISAR COLUMNAS
# ============================================================

print()
print("Columnas NASA POWER:")
print(power.columns.tolist())

print()
print("Columnas SMAP:")
print(smap.columns.tolist())


# ============================================================
# CONVERTIR FECHAS
# ============================================================

print()
print("Preparando fechas...")

power["fecha"] = pd.to_datetime(
    power["DATE"],
    errors="coerce"
).dt.date

smap["fecha"] = pd.to_datetime(
    smap["fecha"],
    errors="coerce"
).dt.date


# ============================================================
# VALIDAR FECHAS
# ============================================================

if power["fecha"].isna().any():
    print("ADVERTENCIA: existen fechas inválidas en NASA POWER.")

if smap["fecha"].isna().any():
    print("ADVERTENCIA: existen fechas inválidas en SMAP.")


# ============================================================
# SELECCIONAR VARIABLES NASA POWER
# ============================================================

columnas_power = [
    "fecha",
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "PRECTOTCORR",
    "RH2M",
    "WS10M",
    "ALLSKY_SFC_SW_DWN"
]

power = power[columnas_power].copy()


# ============================================================
# SELECCIONAR VARIABLES SMAP
# ============================================================

columnas_smap = [
    "fecha",
    "sm_surface",
    "sm_rootzone",
    "sm_surface_wetness",
    "sm_rootzone_wetness",
    "soil_temp_layer1_celsius",
    "observaciones_smap"
]

smap = smap[columnas_smap].copy()


# ============================================================
# INTEGRAR POWER + SMAP
# ============================================================

print()
print("Integrando NASA POWER + SMAP...")

integrado = pd.merge(
    power,
    smap,
    on="fecha",
    how="inner"
)


# ============================================================
# AGREGAR UBICACIÓN
# ============================================================

integrado.insert(
    1,
    "latitud",
    7.119
)

integrado.insert(
    2,
    "longitud",
    -73.122
)


# ============================================================
# ORDENAR
# ============================================================

integrado = integrado.sort_values("fecha").reset_index(drop=True)


# ============================================================
# MOSTRAR RESULTADO
# ============================================================

print()
print("=" * 70)
print("DATASET AMBIENTAL INTEGRADO")
print("=" * 70)

print()
print(integrado.to_string(index=False))


# ============================================================
# INFORMACIÓN DEL DATASET
# ============================================================

print()
print("=" * 70)
print("INFORMACIÓN DEL DATASET")
print("=" * 70)

print()
print(f"Registros integrados: {len(integrado)}")
print(f"Columnas: {len(integrado.columns)}")

print()
print("Periodo integrado:")

if not integrado.empty:
    print(
        f"{integrado['fecha'].min()} -> "
        f"{integrado['fecha'].max()}"
    )

print()
print("Valores faltantes por columna:")

print(
    integrado.isna().sum()
)


# ============================================================
# ESTADÍSTICAS
# ============================================================

print()
print("=" * 70)
print("ESTADÍSTICAS")
print("=" * 70)

columnas_numericas = [
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "PRECTOTCORR",
    "RH2M",
    "WS10M",
    "ALLSKY_SFC_SW_DWN",
    "sm_surface",
    "sm_rootzone",
    "sm_surface_wetness",
    "sm_rootzone_wetness",
    "soil_temp_layer1_celsius"
]

print()

print(
    integrado[columnas_numericas].describe()
)


# ============================================================
# GUARDAR DATASET
# ============================================================

integrado.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print()
print("=" * 70)
print("ARCHIVO GENERADO")
print("=" * 70)

print()
print(OUTPUT_FILE)

print()
print("Proceso terminado correctamente.")
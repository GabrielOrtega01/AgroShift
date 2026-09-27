from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "analysis"
    / "smap_timeseries_santander.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "analysis"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CARGAR DATOS SMAP
# ============================================================

print("Cargando datos SMAP...")

df = pd.read_csv(INPUT_FILE)

print(f"Registros cargados: {len(df)}")


# ============================================================
# CONVERTIR FECHA
# ============================================================

df["fecha_hora"] = pd.to_datetime(
    df["fecha_hora"],
    utc=True
)

# Crear fecha sin hora.
df["fecha"] = df["fecha_hora"].dt.date


# ============================================================
# VARIABLES PARA EL RESUMEN DIARIO
# ============================================================

variables = [
    "sm_surface",
    "sm_rootzone",
    "sm_surface_wetness",
    "sm_rootzone_wetness",
    "soil_temp_layer1_celsius"
]


# ============================================================
# RESUMEN DIARIO
# ============================================================

print()
print("Calculando promedios diarios...")

df_diario = (
    df
    .groupby("fecha")[variables]
    .mean()
    .reset_index()
)


# ============================================================
# CANTIDAD DE OBSERVACIONES
# ============================================================

observaciones = (
    df
    .groupby("fecha")
    .size()
    .reset_index(name="observaciones_smap")
)

df_diario = df_diario.merge(
    observaciones,
    on="fecha",
    how="left"
)


# ============================================================
# MOSTRAR RESULTADOS
# ============================================================

print()
print("=" * 70)
print("RESUMEN DIARIO SMAP")
print("=" * 70)

print()
print(df_diario.to_string(index=False))


# ============================================================
# ESTADÍSTICAS
# ============================================================

print()
print("=" * 70)
print("ESTADÍSTICAS DIARIAS")
print("=" * 70)

print()
print(df_diario[variables].describe())


# ============================================================
# GUARDAR CSV
# ============================================================

archivo_salida = (
    OUTPUT_DIR
    / "smap_daily_santander.csv"
)

df_diario.to_csv(
    archivo_salida,
    index=False,
    encoding="utf-8-sig"
)

print()
print("CSV diario guardado en:")

print(archivo_salida)


# ============================================================
# GRÁFICA
# ============================================================

plt.figure(figsize=(12, 6))

plt.plot(
    df_diario["fecha"],
    df_diario["sm_surface"],
    marker="o",
    label="Humedad superficial"
)

plt.plot(
    df_diario["fecha"],
    df_diario["sm_rootzone"],
    marker="o",
    label="Humedad zona radicular"
)

plt.title("Humedad diaria del suelo - SMAP")
plt.xlabel("Fecha")
plt.ylabel("Humedad (m³/m³)")
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()

grafica_salida = (
    OUTPUT_DIR
    / "smap_humedad_diaria.png"
)

plt.savefig(
    grafica_salida,
    dpi=150
)

plt.close()

print()
print("Gráfica guardada en:")
print(grafica_salida)

print()
print("Proceso terminado correctamente.")
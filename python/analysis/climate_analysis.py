import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================
# AGROSHIFT - ANÁLISIS CLIMÁTICO
# NASA POWER
# ============================================================

# ------------------------------------------------------------
# 1. RUTAS
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "nasa_power_santander.csv"
OUTPUT_DIR = BASE_DIR / "data" / "analysis"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# 2. CARGAR DATOS
# ------------------------------------------------------------

print("==========================================")
print("       AGROSHIFT - ANÁLISIS CLIMÁTICO")
print("==========================================")

print("\nCargando datos NASA POWER...")

df = pd.read_csv(DATA_FILE)

df["DATE"] = pd.to_datetime(df["DATE"])

# Crear variables de tiempo
df["YEAR"] = df["DATE"].dt.year
df["MONTH"] = df["DATE"].dt.month
df["MONTH_NAME"] = df["DATE"].dt.month_name()

print(f"Registros cargados: {len(df)}")
print(f"Fecha inicial: {df['DATE'].min().date()}")
print(f"Fecha final: {df['DATE'].max().date()}")


# ------------------------------------------------------------
# 3. ANÁLISIS DE TEMPERATURA
# ------------------------------------------------------------

print("\n------------------------------------------")
print("ANÁLISIS DE TEMPERATURA")
print("------------------------------------------")

temperature_stats = df[
    ["T2M", "T2M_MAX", "T2M_MIN"]
].describe()

print("\nEstadísticas:")
print(temperature_stats)

print("\nTemperatura promedio:")
print(f"{df['T2M'].mean():.2f} °C")

print("Temperatura máxima registrada:")
print(f"{df['T2M_MAX'].max():.2f} °C")

print("Temperatura mínima registrada:")
print(f"{df['T2M_MIN'].min():.2f} °C")


# Temperatura promedio por año
temperature_year = df.groupby("YEAR").agg(
    T2M=("T2M", "mean"),
    T2M_MAX=("T2M_MAX", "mean"),
    T2M_MIN=("T2M_MIN", "mean")
).reset_index()

print("\nTemperatura promedio por año:")
print(temperature_year)


# Temperatura promedio por mes
temperature_month = df.groupby("MONTH").agg(
    T2M=("T2M", "mean"),
    T2M_MAX=("T2M_MAX", "mean"),
    T2M_MIN=("T2M_MIN", "mean")
).reset_index()

print("\nTemperatura promedio por mes:")
print(temperature_month)


# ------------------------------------------------------------
# 4. ANÁLISIS DE PRECIPITACIÓN
# ------------------------------------------------------------

print("\n------------------------------------------")
print("ANÁLISIS DE PRECIPITACIÓN")
print("------------------------------------------")

annual_precipitation = df.groupby("YEAR").agg(
    PRECIPITATION_TOTAL=("PRECTOTCORR", "sum"),
    PRECIPITATION_MEAN=("PRECTOTCORR", "mean")
).reset_index()

print("\nPrecipitación anual:")
print(annual_precipitation)

print("\nPrecipitación total del periodo:")
print(f"{df['PRECTOTCORR'].sum():.2f} mm")

print("\nPrecipitación diaria promedio:")
print(f"{df['PRECTOTCORR'].mean():.2f} mm")


# Precipitación promedio por mes
monthly_precipitation = df.groupby("MONTH").agg(
    PRECIPITATION_TOTAL=("PRECTOTCORR", "sum"),
    PRECIPITATION_MEAN=("PRECTOTCORR", "mean")
).reset_index()

print("\nPrecipitación por mes:")
print(monthly_precipitation)


# ------------------------------------------------------------
# 5. DÍAS SECOS
# ------------------------------------------------------------

# Día seco: precipitación menor a 1 mm
dry_days = (df["PRECTOTCORR"] < 1).sum()

print("\nDías con precipitación menor a 1 mm:")
print(dry_days)


# ------------------------------------------------------------
# 6. DÍAS DE LLUVIA INTENSA
# ------------------------------------------------------------

# Umbral inicial de 20 mm/día
heavy_rain_days = (df["PRECTOTCORR"] >= 20).sum()

print("\nDías con precipitación >= 20 mm:")
print(heavy_rain_days)


# ------------------------------------------------------------
# 7. MES MÁS SECO Y MÁS LLUVIOSO
# ------------------------------------------------------------

driest_month = monthly_precipitation.loc[
    monthly_precipitation["PRECIPITATION_MEAN"].idxmin()
]

wettest_month = monthly_precipitation.loc[
    monthly_precipitation["PRECIPITATION_MEAN"].idxmax()
]

print("\nMes más seco:")
print(
    f"Mes {int(driest_month['MONTH'])} - "
    f"{driest_month['PRECIPITATION_MEAN']:.2f} mm/día"
)

print("\nMes más lluvioso:")
print(
    f"Mes {int(wettest_month['MONTH'])} - "
    f"{wettest_month['PRECIPITATION_MEAN']:.2f} mm/día"
)


# ------------------------------------------------------------
# 8. HUMEDAD RELATIVA
# ------------------------------------------------------------

print("\n------------------------------------------")
print("ANÁLISIS DE HUMEDAD")
print("------------------------------------------")

print(f"Humedad promedio: {df['RH2M'].mean():.2f} %")
print(f"Humedad mínima: {df['RH2M'].min():.2f} %")
print(f"Humedad máxima: {df['RH2M'].max():.2f} %")

humidity_month = df.groupby("MONTH").agg(
    RH2M=("RH2M", "mean")
).reset_index()

print("\nHumedad promedio por mes:")
print(humidity_month)


# ------------------------------------------------------------
# 9. RADIACIÓN SOLAR
# ------------------------------------------------------------

print("\n------------------------------------------")
print("ANÁLISIS DE RADIACIÓN SOLAR")
print("------------------------------------------")

print(
    f"Radiación solar promedio: "
    f"{df['ALLSKY_SFC_SW_DWN'].mean():.2f}"
)

print(
    f"Radiación solar mínima: "
    f"{df['ALLSKY_SFC_SW_DWN'].min():.2f}"
)

print(
    f"Radiación solar máxima: "
    f"{df['ALLSKY_SFC_SW_DWN'].max():.2f}"
)

solar_month = df.groupby("MONTH").agg(
    SOLAR_RADIATION=("ALLSKY_SFC_SW_DWN", "mean")
).reset_index()

print("\nRadiación solar promedio por mes:")
print(solar_month)


# ------------------------------------------------------------
# 10. CORRELACIONES
# ------------------------------------------------------------

print("\n------------------------------------------")
print("CORRELACIONES")
print("------------------------------------------")

correlation_columns = [
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "PRECTOTCORR",
    "RH2M",
    "WS10M",
    "ALLSKY_SFC_SW_DWN"
]

correlation_matrix = df[correlation_columns].corr()

print("\nMatriz de correlación:")
print(correlation_matrix)


# ------------------------------------------------------------
# 11. TENDENCIA DE TEMPERATURA
# ------------------------------------------------------------

print("\n------------------------------------------")
print("TENDENCIA CLIMÁTICA")
print("------------------------------------------")

year_temperature = df.groupby("YEAR")["T2M"].mean()

# Regresión lineal simple
x = year_temperature.index
y = year_temperature.values

slope, intercept = __import__("numpy").polyfit(x, y, 1)

print(
    f"Tendencia anual de temperatura: "
    f"{slope:.4f} °C/año"
)

print(
    f"Cambio estimado entre 2020 y 2025: "
    f"{slope * (2025 - 2020):.4f} °C"
)


# ------------------------------------------------------------
# 12. GUARDAR RESULTADOS
# ------------------------------------------------------------

temperature_year.to_csv(
    OUTPUT_DIR / "temperatura_anual.csv",
    index=False
)

temperature_month.to_csv(
    OUTPUT_DIR / "temperatura_mensual.csv",
    index=False
)

annual_precipitation.to_csv(
    OUTPUT_DIR / "precipitacion_anual.csv",
    index=False
)

monthly_precipitation.to_csv(
    OUTPUT_DIR / "precipitacion_mensual.csv",
    index=False
)

humidity_month.to_csv(
    OUTPUT_DIR / "humedad_mensual.csv",
    index=False
)

solar_month.to_csv(
    OUTPUT_DIR / "radiacion_mensual.csv",
    index=False
)

correlation_matrix.to_csv(
    OUTPUT_DIR / "correlaciones.csv"
)


# ------------------------------------------------------------
# 13. GRÁFICO 1 - TEMPERATURA ANUAL
# ------------------------------------------------------------

plt.figure(figsize=(10, 6))

plt.plot(
    temperature_year["YEAR"],
    temperature_year["T2M"],
    marker="o"
)

plt.title("Temperatura promedio anual")
plt.xlabel("Año")
plt.ylabel("Temperatura (°C)")
plt.grid(True)

plt.savefig(
    OUTPUT_DIR / "temperatura_anual.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ------------------------------------------------------------
# 14. GRÁFICO 2 - PRECIPITACIÓN ANUAL
# ------------------------------------------------------------

plt.figure(figsize=(10, 6))

plt.bar(
    annual_precipitation["YEAR"],
    annual_precipitation["PRECIPITATION_TOTAL"]
)

plt.title("Precipitación total anual")
plt.xlabel("Año")
plt.ylabel("Precipitación (mm)")
plt.grid(axis="y")

plt.savefig(
    OUTPUT_DIR / "precipitacion_anual.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ------------------------------------------------------------
# 15. GRÁFICO 3 - TEMPERATURA MENSUAL
# ------------------------------------------------------------

plt.figure(figsize=(10, 6))

plt.plot(
    temperature_month["MONTH"],
    temperature_month["T2M"],
    marker="o"
)

plt.title("Temperatura promedio por mes")
plt.xlabel("Mes")
plt.ylabel("Temperatura (°C)")
plt.xticks(range(1, 13))
plt.grid(True)

plt.savefig(
    OUTPUT_DIR / "temperatura_mensual.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ------------------------------------------------------------
# 16. GRÁFICO 4 - PRECIPITACIÓN MENSUAL
# ------------------------------------------------------------

plt.figure(figsize=(10, 6))

plt.bar(
    monthly_precipitation["MONTH"],
    monthly_precipitation["PRECIPITATION_MEAN"]
)

plt.title("Precipitación promedio por mes")
plt.xlabel("Mes")
plt.ylabel("Precipitación promedio (mm/día)")
plt.xticks(range(1, 13))
plt.grid(axis="y")

plt.savefig(
    OUTPUT_DIR / "precipitacion_mensual.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ------------------------------------------------------------
# 17. FINAL
# ------------------------------------------------------------

print("\n==========================================")
print("ANÁLISIS FINALIZADO")
print("==========================================")

print(f"\nResultados guardados en:")
print(OUTPUT_DIR)

print("\nArchivos generados:")
for file in sorted(OUTPUT_DIR.iterdir()):
    print(f" - {file.name}")
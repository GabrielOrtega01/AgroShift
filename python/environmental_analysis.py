from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
ANALYSIS_DIR = DATA_DIR / "analysis"

INPUT_FILE = ANALYSIS_DIR / "agroshift_environmental_data.csv"

ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 1. CARGAR DATOS
# ============================================================

print("=" * 60)
print("ANÁLISIS AMBIENTAL - AGROSHIFT")
print("=" * 60)

print(f"\nArchivo de entrada:")
print(INPUT_FILE)

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"No se encontró el archivo:\n{INPUT_FILE}"
    )

df = pd.read_csv(INPUT_FILE)

print(f"\nRegistros cargados: {len(df)}")
print(f"Columnas disponibles: {len(df.columns)}")


# ============================================================
# 2. PREPARAR FECHAS
# ============================================================

df["fecha"] = pd.to_datetime(
    df["fecha"],
    errors="coerce"
)

df = df.sort_values("fecha").reset_index(drop=True)

if df["fecha"].isna().any():
    raise ValueError("Existen fechas que no pudieron convertirse correctamente.")


# ============================================================
# 3. INFORMACIÓN GENERAL
# ============================================================

print("\n" + "=" * 60)
print("INFORMACIÓN GENERAL")
print("=" * 60)

print(f"Periodo analizado:")
print(f"{df['fecha'].min().date()} -> {df['fecha'].max().date()}")

print(f"\nLatitud: {df['latitud'].iloc[0]}")
print(f"Longitud: {df['longitud'].iloc[0]}")

print("\nValores faltantes:")
print(df.isna().sum())


# ============================================================
# 4. INDICADORES CLIMÁTICOS
# ============================================================

print("\n" + "=" * 60)
print("INDICADORES CLIMÁTICOS")
print("=" * 60)

temperatura_media = df["T2M"].mean()
temperatura_maxima = df["T2M_MAX"].max()
temperatura_minima = df["T2M_MIN"].min()

precipitacion_total = df["PRECTOTCORR"].sum()
precipitacion_media = df["PRECTOTCORR"].mean()
precipitacion_maxima = df["PRECTOTCORR"].max()

dias_secos = (df["PRECTOTCORR"] < 1).sum()
dias_con_lluvia = (df["PRECTOTCORR"] >= 1).sum()

humedad_relativa_media = df["RH2M"].mean()
radiacion_media = df["ALLSKY_SFC_SW_DWN"].mean()
viento_medio = df["WS10M"].mean()

print(f"\nTemperatura media: {temperatura_media:.2f} °C")
print(f"Temperatura máxima registrada: {temperatura_maxima:.2f} °C")
print(f"Temperatura mínima registrada: {temperatura_minima:.2f} °C")

print(f"\nPrecipitación acumulada: {precipitacion_total:.2f} mm")
print(f"Precipitación media diaria: {precipitacion_media:.2f} mm")
print(f"Precipitación máxima diaria: {precipitacion_maxima:.2f} mm")

print(f"\nDías secos (< 1 mm): {dias_secos}")
print(f"Días con lluvia (>= 1 mm): {dias_con_lluvia}")

print(f"\nHumedad relativa media: {humedad_relativa_media:.2f} %")
print(f"Radiación solar media: {radiacion_media:.2f} kWh/m²/día")
print(f"Velocidad del viento media: {viento_medio:.2f} m/s")


# ============================================================
# 5. INDICADORES DE HUMEDAD DEL SUELO
# ============================================================

print("\n" + "=" * 60)
print("INDICADORES DE HUMEDAD DEL SUELO - SMAP")
print("=" * 60)

humedad_superficial_media = df["sm_surface"].mean()
humedad_superficial_min = df["sm_surface"].min()
humedad_superficial_max = df["sm_surface"].max()

humedad_raiz_media = df["sm_rootzone"].mean()
humedad_raiz_min = df["sm_rootzone"].min()
humedad_raiz_max = df["sm_rootzone"].max()

saturacion_superficial_media = df["sm_surface_wetness"].mean()
saturacion_raiz_media = df["sm_rootzone_wetness"].mean()

temperatura_suelo_media = df["soil_temp_layer1_celsius"].mean()
temperatura_suelo_min = df["soil_temp_layer1_celsius"].min()
temperatura_suelo_max = df["soil_temp_layer1_celsius"].max()

print("\nHumedad superficial (0-5 cm):")
print(f"Media: {humedad_superficial_media:.4f} m³/m³")
print(f"Mínima: {humedad_superficial_min:.4f} m³/m³")
print(f"Máxima: {humedad_superficial_max:.4f} m³/m³")

print("\nHumedad zona radicular (0-100 cm):")
print(f"Media: {humedad_raiz_media:.4f} m³/m³")
print(f"Mínima: {humedad_raiz_min:.4f} m³/m³")
print(f"Máxima: {humedad_raiz_max:.4f} m³/m³")

print(f"\nSaturación relativa superficial media: "
      f"{saturacion_superficial_media:.4f}")

print(f"Saturación relativa zona radicular media: "
      f"{saturacion_raiz_media:.4f}")

print("\nTemperatura del suelo - capa 1:")
print(f"Media: {temperatura_suelo_media:.2f} °C")
print(f"Mínima: {temperatura_suelo_min:.2f} °C")
print(f"Máxima: {temperatura_suelo_max:.2f} °C")


# ============================================================
# 6. CAMBIO DE HUMEDAD DEL SUELO
# ============================================================

print("\n" + "=" * 60)
print("CAMBIO DE HUMEDAD DEL SUELO")
print("=" * 60)

humedad_superficial_inicial = df["sm_surface"].iloc[0]
humedad_superficial_final = df["sm_surface"].iloc[-1]

humedad_raiz_inicial = df["sm_rootzone"].iloc[0]
humedad_raiz_final = df["sm_rootzone"].iloc[-1]

cambio_superficial = (
    humedad_superficial_final - humedad_superficial_inicial
)

cambio_raiz = (
    humedad_raiz_final - humedad_raiz_inicial
)

print(
    f"\nCambio humedad superficial: "
    f"{cambio_superficial:.4f} m³/m³"
)

print(
    f"Cambio humedad zona radicular: "
    f"{cambio_raiz:.4f} m³/m³"
)


# ============================================================
# 7. CORRELACIONES
# ============================================================

print("\n" + "=" * 60)
print("CORRELACIONES")
print("=" * 60)

columnas_correlacion = [
    "T2M",
    "PRECTOTCORR",
    "RH2M",
    "ALLSKY_SFC_SW_DWN",
    "sm_surface",
    "sm_rootzone",
    "soil_temp_layer1_celsius"
]

correlaciones = df[columnas_correlacion].corr()

print("\nMatriz de correlación:")
print(correlaciones.round(3))

correlaciones.to_csv(
    ANALYSIS_DIR / "correlaciones_ambientales.csv"
)


# ============================================================
# 8. INDICADORES AGRÍCOLAS INICIALES
# ============================================================
#
# Estos indicadores son descriptivos.
# No representan todavía una recomendación de cultivo.
# Para eso posteriormente se incorporarán:
# - tipo de suelo
# - características de cada cultivo
# - necesidades hídricas
# - tolerancia térmica
# - prioridades del agricultor
#

print("\n" + "=" * 60)
print("INDICADORES AGRÍCOLAS INICIALES")
print("=" * 60)

if humedad_superficial_final < humedad_superficial_inicial:
    tendencia_humedad = "disminución"
elif humedad_superficial_final > humedad_superficial_inicial:
    tendencia_humedad = "aumento"
else:
    tendencia_humedad = "sin cambio"

print(
    f"\nTendencia observada de humedad superficial: "
    f"{tendencia_humedad}"
)

porcentaje_dias_secos = (
    dias_secos / len(df)
) * 100

print(
    f"Porcentaje de días secos: "
    f"{porcentaje_dias_secos:.2f} %"
)

print(
    f"Humedad superficial media: "
    f"{humedad_superficial_media:.4f} m³/m³"
)

print(
    f"Humedad de zona radicular media: "
    f"{humedad_raiz_media:.4f} m³/m³"
)


# ============================================================
# 9. CREAR TABLA DE INDICADORES
# ============================================================

indicadores = pd.DataFrame({
    "indicador": [
        "temperatura_media_c",
        "temperatura_maxima_c",
        "temperatura_minima_c",
        "precipitacion_total_mm",
        "precipitacion_media_diaria_mm",
        "precipitacion_maxima_diaria_mm",
        "dias_secos",
        "dias_con_lluvia",
        "humedad_relativa_media_pct",
        "radiacion_media_kwh_m2_dia",
        "viento_medio_m_s",
        "humedad_superficial_media_m3_m3",
        "humedad_superficial_min_m3_m3",
        "humedad_superficial_max_m3_m3",
        "humedad_raiz_media_m3_m3",
        "humedad_raiz_min_m3_m3",
        "humedad_raiz_max_m3_m3",
        "saturacion_superficial_media",
        "saturacion_raiz_media",
        "temperatura_suelo_media_c",
        "temperatura_suelo_min_c",
        "temperatura_suelo_max_c",
        "cambio_humedad_superficial_m3_m3",
        "cambio_humedad_raiz_m3_m3",
        "porcentaje_dias_secos"
    ],
    "valor": [
        temperatura_media,
        temperatura_maxima,
        temperatura_minima,
        precipitacion_total,
        precipitacion_media,
        precipitacion_maxima,
        dias_secos,
        dias_con_lluvia,
        humedad_relativa_media,
        radiacion_media,
        viento_medio,
        humedad_superficial_media,
        humedad_superficial_min,
        humedad_superficial_max,
        humedad_raiz_media,
        humedad_raiz_min,
        humedad_raiz_max,
        saturacion_superficial_media,
        saturacion_raiz_media,
        temperatura_suelo_media,
        temperatura_suelo_min,
        temperatura_suelo_max,
        cambio_superficial,
        cambio_raiz,
        porcentaje_dias_secos
    ]
})

indicadores.to_csv(
    ANALYSIS_DIR / "indicadores_ambientales.csv",
    index=False
)


# ============================================================
# 10. GRÁFICA DE PRECIPITACIÓN
# ============================================================

fig, ax = plt.subplots(figsize=(12, 6))

ax.bar(
    df["fecha"],
    df["PRECTOTCORR"],
    width=0.7
)

ax.set_title("Precipitación diaria - NASA POWER")
ax.set_xlabel("Fecha")
ax.set_ylabel("Precipitación (mm)")
ax.grid(True, alpha=0.3)

fig.autofmt_xdate()
fig.tight_layout()

fig.savefig(
    ANALYSIS_DIR / "precipitacion_diaria_agroshift.png",
    dpi=150,
    bbox_inches="tight"
)

plt.close(fig)


# ============================================================
# 11. GRÁFICA DE TEMPERATURA
# ============================================================

fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(
    df["fecha"],
    df["T2M"],
    marker="o",
    linewidth=1.5,
    label="Temperatura media"
)

ax.plot(
    df["fecha"],
    df["T2M_MAX"],
    marker="o",
    linewidth=1.5,
    label="Temperatura máxima"
)

ax.plot(
    df["fecha"],
    df["T2M_MIN"],
    marker="o",
    linewidth=1.5,
    label="Temperatura mínima"
)

ax.set_title("Temperatura diaria - NASA POWER")
ax.set_xlabel("Fecha")
ax.set_ylabel("Temperatura (°C)")
ax.grid(True, alpha=0.3)
ax.legend()

fig.autofmt_xdate()
fig.tight_layout()

fig.savefig(
    ANALYSIS_DIR / "temperatura_diaria_agroshift.png",
    dpi=150,
    bbox_inches="tight"
)

plt.close(fig)


# ============================================================
# 12. GRÁFICA DE HUMEDAD DEL SUELO
# ============================================================

fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(
    df["fecha"],
    df["sm_surface"],
    marker="o",
    linewidth=1.5,
    label="Humedad superficial (0-5 cm)"
)

ax.plot(
    df["fecha"],
    df["sm_rootzone"],
    marker="o",
    linewidth=1.5,
    label="Humedad zona radicular (0-100 cm)"
)

ax.set_title("Humedad del suelo - SMAP")
ax.set_xlabel("Fecha")
ax.set_ylabel("Humedad (m³/m³)")
ax.grid(True, alpha=0.3)
ax.legend()

fig.autofmt_xdate()
fig.tight_layout()

fig.savefig(
    ANALYSIS_DIR / "humedad_suelo_agroshift.png",
    dpi=150,
    bbox_inches="tight"
)

plt.close(fig)


# ============================================================
# 13. GRÁFICA COMBINADA: LLUVIA Y HUMEDAD DEL SUELO
# ============================================================

fig, ax1 = plt.subplots(figsize=(12, 6))

ax1.bar(
    df["fecha"],
    df["PRECTOTCORR"],
    width=0.7,
    alpha=0.5,
    label="Precipitación"
)

ax1.set_xlabel("Fecha")
ax1.set_ylabel("Precipitación (mm)")

ax2 = ax1.twinx()

ax2.plot(
    df["fecha"],
    df["sm_surface"],
    marker="o",
    linewidth=1.5,
    label="Humedad superficial"
)

ax2.plot(
    df["fecha"],
    df["sm_rootzone"],
    marker="o",
    linewidth=1.5,
    label="Humedad zona radicular"
)

ax2.set_ylabel("Humedad del suelo (m³/m³)")

ax1.set_title(
    "Relación entre precipitación y humedad del suelo"
)

ax1.grid(True, alpha=0.3)

fig.autofmt_xdate()
fig.tight_layout()

fig.savefig(
    ANALYSIS_DIR / "precipitacion_humedad_agroshift.png",
    dpi=150,
    bbox_inches="tight"
)

plt.close(fig)


# ============================================================
# 14. RESUMEN FINAL
# ============================================================

print("\n" + "=" * 60)
print("ANÁLISIS COMPLETADO")
print("=" * 60)

print("\nArchivos generados:")

archivos = [
    "correlaciones_ambientales.csv",
    "indicadores_ambientales.csv",
    "precipitacion_diaria_agroshift.png",
    "temperatura_diaria_agroshift.png",
    "humedad_suelo_agroshift.png",
    "precipitacion_humedad_agroshift.png"
]

for archivo in archivos:
    print(f"  - {ANALYSIS_DIR / archivo}")

print("\nProceso terminado correctamente.")

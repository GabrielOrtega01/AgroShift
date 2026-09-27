from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "analysis"
    / "agroshift_environmental_2020.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "analysis"
)

OUTPUT_INDICADORES = (
    OUTPUT_DIR
    / "indicadores_ambientales_2020.csv"
)

OUTPUT_MENSUAL = (
    OUTPUT_DIR
    / "analisis_mensual_ambiental_2020.csv"
)

OUTPUT_CORRELACIONES = (
    OUTPUT_DIR
    / "correlaciones_ambientales_2020.csv"
)


# ============================================================
# CARGAR DATASET
# ============================================================

print("=" * 70)
print("ANÁLISIS AMBIENTAL AGROSHIFT - 2020")
print("=" * 70)

print("\nCargando dataset...")

df = pd.read_csv(INPUT_FILE)

df["fecha"] = pd.to_datetime(
    df["fecha"],
    errors="coerce"
)

print(f"Registros cargados: {len(df)}")
print(f"Columnas: {len(df.columns)}")


# ============================================================
# VALIDACIÓN
# ============================================================

print("\n" + "=" * 70)
print("VALIDACIÓN DEL DATASET")
print("=" * 70)

print(
    f"\nPeriodo: "
    f"{df['fecha'].min().date()} -> "
    f"{df['fecha'].max().date()}"
)

print(f"Días analizados: {df['fecha'].nunique()}")

print(
    f"Valores faltantes: "
    f"{df.isna().sum().sum()}"
)

print(
    f"Registros duplicados: "
    f"{df.duplicated().sum()}"
)


# ============================================================
# CREAR VARIABLES DERIVADAS
# ============================================================

df["mes"] = df["fecha"].dt.month

df["nombre_mes"] = df["fecha"].dt.strftime("%B")

df["dia_semana"] = df["fecha"].dt.day_name()

df["dia_del_ano"] = df["fecha"].dt.dayofyear

# Indicador sencillo de día lluvioso
df["dia_lluvioso"] = (
    df["PRECTOTCORR"] >= 1.0
)

# Indicador de día seco
df["dia_seco"] = (
    df["PRECTOTCORR"] < 1.0
)


# ============================================================
# 1. ESTADÍSTICAS GENERALES
# ============================================================

print("\n" + "=" * 70)
print("1. ESTADÍSTICAS GENERALES")
print("=" * 70)


temperatura_media = df["T2M"].mean()
temperatura_maxima = df["T2M_MAX"].max()
temperatura_minima = df["T2M_MIN"].min()

precipitacion_total = df["PRECTOTCORR"].sum()
precipitacion_media = df["PRECTOTCORR"].mean()
precipitacion_maxima = df["PRECTOTCORR"].max()

humedad_relativa_media = df["RH2M"].mean()

viento_medio = df["WS10M"].mean()

radiacion_media = df["ALLSKY_SFC_SW_DWN"].mean()

humedad_superficial_media = df["sm_surface"].mean()
humedad_superficial_min = df["sm_surface"].min()
humedad_superficial_max = df["sm_surface"].max()

humedad_raiz_media = df["sm_rootzone"].mean()
humedad_raiz_min = df["sm_rootzone"].min()
humedad_raiz_max = df["sm_rootzone"].max()

temperatura_suelo_media = (
    df["soil_temp_layer1_celsius"].mean()
)

dias_lluviosos = df["dia_lluvioso"].sum()
dias_secos = df["dia_seco"].sum()

porcentaje_dias_secos = (
    dias_secos / len(df) * 100
)


print(f"\nTemperatura media: {temperatura_media:.2f} °C")
print(
    f"Temperatura máxima: "
    f"{temperatura_maxima:.2f} °C"
)
print(
    f"Temperatura mínima: "
    f"{temperatura_minima:.2f} °C"
)

print(
    f"\nPrecipitación acumulada: "
    f"{precipitacion_total:.2f} mm"
)

print(
    f"Precipitación media diaria: "
    f"{precipitacion_media:.2f} mm"
)

print(
    f"Precipitación máxima diaria: "
    f"{precipitacion_maxima:.2f} mm"
)

print(
    f"\nHumedad relativa media: "
    f"{humedad_relativa_media:.2f} %"
)

print(
    f"Viento medio: "
    f"{viento_medio:.2f} m/s"
)

print(
    f"Radiación media: "
    f"{radiacion_media:.2f} kWh/m²/día"
)

print(
    f"\nHumedad superficial del suelo: "
    f"{humedad_superficial_media:.4f} m³/m³"
)

print(
    f"Humedad superficial mínima: "
    f"{humedad_superficial_min:.4f} m³/m³"
)

print(
    f"Humedad superficial máxima: "
    f"{humedad_superficial_max:.4f} m³/m³"
)

print(
    f"\nHumedad de zona radicular: "
    f"{humedad_raiz_media:.4f} m³/m³"
)

print(
    f"Humedad radicular mínima: "
    f"{humedad_raiz_min:.4f} m³/m³"
)

print(
    f"Humedad radicular máxima: "
    f"{humedad_raiz_max:.4f} m³/m³"
)

print(
    f"\nTemperatura media del suelo: "
    f"{temperatura_suelo_media:.2f} °C"
)

print(
    f"\nDías lluviosos (>= 1 mm): "
    f"{dias_lluviosos}"
)

print(
    f"Días secos (< 1 mm): "
    f"{dias_secos}"
)

print(
    f"Porcentaje de días secos: "
    f"{porcentaje_dias_secos:.2f} %"
)


# ============================================================
# 2. ANÁLISIS MENSUAL
# ============================================================

print("\n" + "=" * 70)
print("2. ANÁLISIS MENSUAL")
print("=" * 70)

mensual = (
    df.groupby("mes")
    .agg(
        temperatura_media=("T2M", "mean"),
        temperatura_maxima=("T2M_MAX", "max"),
        temperatura_minima=("T2M_MIN", "min"),
        precipitacion_total=("PRECTOTCORR", "sum"),
        precipitacion_media=("PRECTOTCORR", "mean"),
        humedad_relativa_media=("RH2M", "mean"),
        viento_medio=("WS10M", "mean"),
        radiacion_media=("ALLSKY_SFC_SW_DWN", "mean"),
        humedad_superficial_media=("sm_surface", "mean"),
        humedad_superficial_min=("sm_surface", "min"),
        humedad_superficial_max=("sm_surface", "max"),
        humedad_raiz_media=("sm_rootzone", "mean"),
        humedad_raiz_min=("sm_rootzone", "min"),
        humedad_raiz_max=("sm_rootzone", "max"),
        temperatura_suelo_media=(
            "soil_temp_layer1_celsius",
            "mean"
        ),
        dias_lluviosos=("dia_lluvioso", "sum"),
        dias_secos=("dia_seco", "sum"),
    )
    .reset_index()
)

nombres_meses = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}

mensual["nombre_mes"] = mensual["mes"].map(
    nombres_meses
)

mensual = mensual[
    [
        "mes",
        "nombre_mes",
        "temperatura_media",
        "temperatura_maxima",
        "temperatura_minima",
        "precipitacion_total",
        "precipitacion_media",
        "humedad_relativa_media",
        "viento_medio",
        "radiacion_media",
        "humedad_superficial_media",
        "humedad_superficial_min",
        "humedad_superficial_max",
        "humedad_raiz_media",
        "humedad_raiz_min",
        "humedad_raiz_max",
        "temperatura_suelo_media",
        "dias_lluviosos",
        "dias_secos",
    ]
]

mensual.to_csv(
    OUTPUT_MENSUAL,
    index=False
)

print("\nResumen mensual:")

print(
    mensual[
        [
            "nombre_mes",
            "temperatura_media",
            "precipitacion_total",
            "humedad_superficial_media",
            "humedad_raiz_media",
        ]
    ].to_string(index=False)
)


# ============================================================
# 3. CORRELACIONES
# ============================================================

print("\n" + "=" * 70)
print("3. CORRELACIONES")
print("=" * 70)

variables = [
    "T2M",
    "PRECTOTCORR",
    "RH2M",
    "WS10M",
    "ALLSKY_SFC_SW_DWN",
    "sm_surface",
    "sm_rootzone",
    "soil_temp_layer1_celsius",
]

correlaciones = df[variables].corr()

correlaciones.to_csv(
    OUTPUT_CORRELACIONES
)

print("\nMatriz de correlaciones:")

print(
    correlaciones.round(3).to_string()
)


# ============================================================
# 4. CORRELACIONES MÁS IMPORTANTES
# ============================================================

pares = []

for i in range(len(variables)):
    for j in range(i + 1, len(variables)):

        variable_a = variables[i]
        variable_b = variables[j]

        correlacion = correlaciones.loc[
            variable_a,
            variable_b
        ]

        pares.append(
            {
                "variable_1": variable_a,
                "variable_2": variable_b,
                "correlacion": correlacion,
                "correlacion_absoluta": abs(correlacion),
            }
        )

pares_df = pd.DataFrame(pares)

pares_df = pares_df.sort_values(
    "correlacion_absoluta",
    ascending=False
)

print("\nPrincipales relaciones estadísticas:")

print(
    pares_df.head(10).round(3).to_string(
        index=False
    )
)


# ============================================================
# 5. INDICADORES AMBIENTALES
# ============================================================

print("\n" + "=" * 70)
print("4. INDICADORES AMBIENTALES")
print("=" * 70)

# Variación de humedad del suelo durante el año
cambio_humedad_superficial = (
    df.iloc[-1]["sm_surface"]
    - df.iloc[0]["sm_surface"]
)

cambio_humedad_raiz = (
    df.iloc[-1]["sm_rootzone"]
    - df.iloc[0]["sm_rootzone"]
)

# Mes con mayor y menor precipitación
mes_mayor_precipitacion = mensual.loc[
    mensual["precipitacion_total"].idxmax(),
    "nombre_mes"
]

valor_mayor_precipitacion = mensual[
    "precipitacion_total"
].max()

mes_menor_precipitacion = mensual.loc[
    mensual["precipitacion_total"].idxmin(),
    "nombre_mes"
]

valor_menor_precipitacion = mensual[
    "precipitacion_total"
].min()

# Mes más cálido y más frío según temperatura media
mes_mas_calido = mensual.loc[
    mensual["temperatura_media"].idxmax(),
    "nombre_mes"
]

mes_mas_frio = mensual.loc[
    mensual["temperatura_media"].idxmin(),
    "nombre_mes"
]

# Mes con mayor y menor humedad superficial
mes_mayor_humedad = mensual.loc[
    mensual["humedad_superficial_media"].idxmax(),
    "nombre_mes"
]

mes_menor_humedad = mensual.loc[
    mensual["humedad_superficial_media"].idxmin(),
    "nombre_mes"
]


indicadores = pd.DataFrame(
    [
        {
            "indicador": "temperatura_media_anual",
            "valor": temperatura_media,
            "unidad": "°C",
        },
        {
            "indicador": "temperatura_maxima_anual",
            "valor": temperatura_maxima,
            "unidad": "°C",
        },
        {
            "indicador": "temperatura_minima_anual",
            "valor": temperatura_minima,
            "unidad": "°C",
        },
        {
            "indicador": "precipitacion_acumulada",
            "valor": precipitacion_total,
            "unidad": "mm",
        },
        {
            "indicador": "precipitacion_media_diaria",
            "valor": precipitacion_media,
            "unidad": "mm/día",
        },
        {
            "indicador": "humedad_relativa_media",
            "valor": humedad_relativa_media,
            "unidad": "%",
        },
        {
            "indicador": "radiacion_media",
            "valor": radiacion_media,
            "unidad": "kWh/m²/día",
        },
        {
            "indicador": "viento_medio",
            "valor": viento_medio,
            "unidad": "m/s",
        },
        {
            "indicador": "humedad_superficial_media",
            "valor": humedad_superficial_media,
            "unidad": "m³/m³",
        },
        {
            "indicador": "humedad_raiz_media",
            "valor": humedad_raiz_media,
            "unidad": "m³/m³",
        },
        {
            "indicador": "temperatura_suelo_media",
            "valor": temperatura_suelo_media,
            "unidad": "°C",
        },
        {
            "indicador": "dias_lluviosos",
            "valor": dias_lluviosos,
            "unidad": "días",
        },
        {
            "indicador": "dias_secos",
            "valor": dias_secos,
            "unidad": "días",
        },
        {
            "indicador": "porcentaje_dias_secos",
            "valor": porcentaje_dias_secos,
            "unidad": "%",
        },
        {
            "indicador": "mes_mayor_precipitacion",
            "valor": mes_mayor_precipitacion,
            "unidad": "mes",
        },
        {
            "indicador": "precipitacion_mes_mayor",
            "valor": valor_mayor_precipitacion,
            "unidad": "mm",
        },
        {
            "indicador": "mes_menor_precipitacion",
            "valor": mes_menor_precipitacion,
            "unidad": "mes",
        },
        {
            "indicador": "precipitacion_mes_menor",
            "valor": valor_menor_precipitacion,
            "unidad": "mm",
        },
        {
            "indicador": "mes_mas_calido",
            "valor": mes_mas_calido,
            "unidad": "mes",
        },
        {
            "indicador": "mes_mas_frio",
            "valor": mes_mas_frio,
            "unidad": "mes",
        },
        {
            "indicador": "mes_mayor_humedad_suelo",
            "valor": mes_mayor_humedad,
            "unidad": "mes",
        },
        {
            "indicador": "mes_menor_humedad_suelo",
            "valor": mes_menor_humedad,
            "unidad": "mes",
        },
        {
            "indicador": "cambio_humedad_superficial",
            "valor": cambio_humedad_superficial,
            "unidad": "m³/m³",
        },
        {
            "indicador": "cambio_humedad_zona_radicular",
            "valor": cambio_humedad_raiz,
            "unidad": "m³/m³",
        },
    ]
)

indicadores.to_csv(
    OUTPUT_INDICADORES,
    index=False
)


# ============================================================
# 6. GRÁFICA: PRECIPITACIÓN MENSUAL
# ============================================================

plt.figure(figsize=(12, 6))

plt.bar(
    mensual["nombre_mes"],
    mensual["precipitacion_total"]
)

plt.title(
    "Precipitación acumulada por mes - 2020"
)

plt.xlabel("Mes")
plt.ylabel("Precipitación (mm)")

plt.xticks(rotation=45)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "precipitacion_mensual_2020.png",
    dpi=300
)

plt.close()


# ============================================================
# 7. GRÁFICA: TEMPERATURA MENSUAL
# ============================================================

plt.figure(figsize=(12, 6))

plt.plot(
    mensual["nombre_mes"],
    mensual["temperatura_media"],
    marker="o"
)

plt.title(
    "Temperatura media mensual - 2020"
)

plt.xlabel("Mes")
plt.ylabel("Temperatura (°C)")

plt.xticks(rotation=45)

plt.grid(True, alpha=0.3)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "temperatura_mensual_2020.png",
    dpi=300
)

plt.close()


# ============================================================
# 8. GRÁFICA: HUMEDAD DEL SUELO
# ============================================================

plt.figure(figsize=(12, 6))

plt.plot(
    df["fecha"],
    df["sm_surface"],
    label="Humedad superficial"
)

plt.plot(
    df["fecha"],
    df["sm_rootzone"],
    label="Humedad zona radicular"
)

plt.title(
    "Humedad del suelo durante 2020"
)

plt.xlabel("Fecha")
plt.ylabel("Humedad (m³/m³)")

plt.legend()

plt.grid(True, alpha=0.3)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "humedad_suelo_2020.png",
    dpi=300
)

plt.close()


# ============================================================
# 9. GRÁFICA: PRECIPITACIÓN VS HUMEDAD DEL SUELO
# ============================================================

plt.figure(figsize=(10, 6))

plt.scatter(
    df["PRECTOTCORR"],
    df["sm_surface"],
    alpha=0.6
)

plt.title(
    "Precipitación vs humedad superficial del suelo - 2020"
)

plt.xlabel("Precipitación diaria (mm)")

plt.ylabel(
    "Humedad superficial del suelo (m³/m³)"
)

plt.grid(True, alpha=0.3)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "precipitacion_vs_humedad_suelo_2020.png",
    dpi=300
)

plt.close()


# ============================================================
# 10. GRÁFICA: TEMPERATURA
# ============================================================

plt.figure(figsize=(12, 6))

plt.plot(
    df["fecha"],
    df["T2M"],
    label="Temperatura media"
)

plt.plot(
    df["fecha"],
    df["T2M_MAX"],
    label="Temperatura máxima",
    alpha=0.6
)

plt.plot(
    df["fecha"],
    df["T2M_MIN"],
    label="Temperatura mínima",
    alpha=0.6
)

plt.title(
    "Comportamiento de la temperatura - 2020"
)

plt.xlabel("Fecha")
plt.ylabel("Temperatura (°C)")

plt.legend()

plt.grid(True, alpha=0.3)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "temperatura_diaria_2020.png",
    dpi=300
)

plt.close()


# ============================================================
# 11. GRÁFICA: PRECIPITACIÓN DIARIA
# ============================================================

plt.figure(figsize=(12, 6))

plt.bar(
    df["fecha"],
    df["PRECTOTCORR"]
)

plt.title(
    "Precipitación diaria - 2020"
)

plt.xlabel("Fecha")
plt.ylabel("Precipitación (mm)")

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "precipitacion_diaria_2020.png",
    dpi=300
)

plt.close()


# ============================================================
# 12. MOSTRAR INDICADORES PRINCIPALES
# ============================================================

print("\n" + "=" * 70)
print("INDICADORES PRINCIPALES")
print("=" * 70)

print(
    f"\nMes con mayor precipitación: "
    f"{mes_mayor_precipitacion} "
    f"({valor_mayor_precipitacion:.2f} mm)"
)

print(
    f"Mes con menor precipitación: "
    f"{mes_menor_precipitacion} "
    f"({valor_menor_precipitacion:.2f} mm)"
)

print(
    f"\nMes más cálido: "
    f"{mes_mas_calido}"
)

print(
    f"Mes más frío: "
    f"{mes_mas_frio}"
)

print(
    f"\nMes con mayor humedad superficial: "
    f"{mes_mayor_humedad}"
)

print(
    f"Mes con menor humedad superficial: "
    f"{mes_menor_humedad}"
)

print(
    f"\nCambio de humedad superficial "
    f"entre primer y último registro: "
    f"{cambio_humedad_superficial:.4f} m³/m³"
)

print(
    f"Cambio de humedad de zona radicular: "
    f"{cambio_humedad_raiz:.4f} m³/m³"
)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("ARCHIVOS GENERADOS")
print("=" * 70)

print(
    f"\n✓ {OUTPUT_INDICADORES.name}"
)

print(
    f"✓ {OUTPUT_MENSUAL.name}"
)

print(
    f"✓ {OUTPUT_CORRELACIONES.name}"
)

print("✓ precipitacion_mensual_2020.png")
print("✓ temperatura_mensual_2020.png")
print("✓ humedad_suelo_2020.png")
print("✓ precipitacion_vs_humedad_suelo_2020.png")
print("✓ temperatura_diaria_2020.png")
print("✓ precipitacion_diaria_2020.png")

print("\n" + "=" * 70)
print("✓ ANÁLISIS AMBIENTAL 2020 COMPLETADO")
print("=" * 70)
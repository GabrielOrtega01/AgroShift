import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# AGROSHIFT
# ANÁLISIS DEL ESTADO HÍDRICO OBSERVADO
#
# NASA POWER + SMAP + ETc
#
# IMPORTANTE:
# Este módulo genera indicadores relativos basados en
# la humedad observada por SMAP.
#
# NO calcula todavía estrés hídrico físico ni Ks.
# ============================================================

print("=" * 70)
print("AGROSHIFT - ANÁLISIS DEL ESTADO HÍDRICO")
print("=" * 70)


# ------------------------------------------------------------
# RUTAS
# ------------------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

ARCHIVO_BALANCE = os.path.join(
    BASE_DIR,
    "data",
    "analysis",
    "balance_hidrico_cultivos_2020.csv"
)

ARCHIVO_SALIDA = os.path.join(
    BASE_DIR,
    "data",
    "analysis",
    "estado_hidrico_cultivos_2020.csv"
)

ARCHIVO_RESUMEN = os.path.join(
    BASE_DIR,
    "data",
    "analysis",
    "estado_hidrico_resumen_2020.csv"
)

ARCHIVO_GRAFICA = os.path.join(
    BASE_DIR,
    "data",
    "analysis",
    "estado_hidrico_2020.png"
)


# ------------------------------------------------------------
# CARGAR DATOS
# ------------------------------------------------------------

print("\nCargando balance hídrico...")

df = pd.read_csv(
    ARCHIVO_BALANCE
)

df["fecha"] = pd.to_datetime(
    df["fecha"],
    errors="coerce"
)

print(
    f"✓ Registros cargados: {len(df)}"
)


# ------------------------------------------------------------
# COLUMNAS NECESARIAS
# ------------------------------------------------------------

columnas_requeridas = [
    "cultivo",
    "fecha",
    "dia_ciclo",
    "ETc",
    "PRECTOTCORR",
    "sm_surface",
    "sm_rootzone",
    "sm_surface_wetness",
    "sm_rootzone_wetness",
    "demanda_no_cubierta"
]

faltantes = [
    columna
    for columna in columnas_requeridas
    if columna not in df.columns
]

if faltantes:

    raise ValueError(
        "Faltan columnas: "
        + ", ".join(faltantes)
    )


# ------------------------------------------------------------
# CONVERSIÓN NUMÉRICA
# ------------------------------------------------------------

columnas_numericas = [
    "ETc",
    "PRECTOTCORR",
    "sm_surface",
    "sm_rootzone",
    "sm_surface_wetness",
    "sm_rootzone_wetness",
    "demanda_no_cubierta"
]

for columna in columnas_numericas:

    df[columna] = pd.to_numeric(
        df[columna],
        errors="coerce"
    )


# ------------------------------------------------------------
# LIMPIEZA
# ------------------------------------------------------------

df = df.dropna(
    subset=[
        "fecha",
        "cultivo",
        "sm_rootzone"
    ]
).copy()


# ------------------------------------------------------------
# PERCENTILES DE HUMEDAD
# ------------------------------------------------------------
#
# Los percentiles se calculan sobre los valores diarios
# observados de SMAP en 2020.
#
# NO representan límites agronómicos universales.
# ------------------------------------------------------------

print("\nCalculando distribución de humedad SMAP...")

p10 = df["sm_rootzone"].quantile(0.10)
p25 = df["sm_rootzone"].quantile(0.25)
p50 = df["sm_rootzone"].quantile(0.50)
p75 = df["sm_rootzone"].quantile(0.75)
p90 = df["sm_rootzone"].quantile(0.90)


print(
    f"P10: {p10:.6f}"
)

print(
    f"P25: {p25:.6f}"
)

print(
    f"P50: {p50:.6f}"
)

print(
    f"P75: {p75:.6f}"
)

print(
    f"P90: {p90:.6f}"
)


# ------------------------------------------------------------
# CLASIFICACIÓN RELATIVA
# ------------------------------------------------------------

def clasificar_humedad(valor):

    if valor <= p10:
        return "Muy baja"

    if valor <= p25:
        return "Baja"

    if valor <= p75:
        return "Media"

    if valor <= p90:
        return "Alta"

    return "Muy alta"


df["estado_humedad_relativo"] = (
    df["sm_rootzone"]
    .apply(clasificar_humedad)
)


# ------------------------------------------------------------
# CAMBIO DIARIO
# ------------------------------------------------------------

df = df.sort_values(
    [
        "cultivo",
        "fecha"
    ]
).copy()


df["cambio_sm_rootzone"] = (
    df
    .groupby("cultivo")["sm_rootzone"]
    .diff()
)


df["cambio_sm_surface"] = (
    df
    .groupby("cultivo")["sm_surface"]
    .diff()
)


# ------------------------------------------------------------
# TENDENCIA DE HUMEDAD
# ------------------------------------------------------------

def clasificar_tendencia(valor):

    if pd.isna(valor):
        return "Sin referencia"

    if valor > 0.005:
        return "Aumento"

    if valor < -0.005:
        return "Disminución"

    return "Estable"


df["tendencia_humedad"] = (
    df["cambio_sm_rootzone"]
    .apply(clasificar_tendencia)
)


# ------------------------------------------------------------
# INDICADOR DE DEMANDA
# ------------------------------------------------------------
#
# Se mantiene separado del estado de humedad.
#
# demanda_no_cubierta = max(ETc - P, 0)
#
# No significa déficit hídrico real.
# ------------------------------------------------------------

df["demanda_no_cubierta"] = (
    pd.to_numeric(
        df["demanda_no_cubierta"],
        errors="coerce"
    )
)


# ------------------------------------------------------------
# RELACIÓN DEMANDA + HUMEDAD
# ------------------------------------------------------------
#
# Este indicador permite identificar situaciones en las que:
#
# 1. existe demanda climática no cubierta por precipitación
# 2. y simultáneamente la humedad radicular está baja
#
# Sigue siendo un indicador relativo, no un Ks.
# ------------------------------------------------------------

def evaluar_condicion(fila):

    humedad = fila[
        "estado_humedad_relativo"
    ]

    demanda = fila[
        "demanda_no_cubierta"
    ]

    if demanda <= 0:

        return "Demanda cubierta"

    if humedad in [
        "Muy baja",
        "Baja"
    ]:

        return "Demanda + humedad baja"

    if humedad == "Media":

        return "Demanda + humedad media"

    return "Demanda + humedad alta"


df["condicion_hidrica_observada"] = (
    df.apply(
        evaluar_condicion,
        axis=1
    )
)


# ------------------------------------------------------------
# RESUMEN POR CULTIVO
# ------------------------------------------------------------

print("\nCalculando resumen por cultivo...")

resumen = (
    df
    .groupby("cultivo")
    .agg(

        dias_simulados=(
            "fecha",
            "count"
        ),

        ETc_acumulada_mm=(
            "ETc",
            "sum"
        ),

        precipitacion_acumulada_mm=(
            "PRECTOTCORR",
            "sum"
        ),

        demanda_no_cubierta_mm=(
            "demanda_no_cubierta",
            "sum"
        ),

        sm_rootzone_media=(
            "sm_rootzone",
            "mean"
        ),

        sm_rootzone_min=(
            "sm_rootzone",
            "min"
        ),

        sm_rootzone_max=(
            "sm_rootzone",
            "max"
        ),

        sm_rootzone_wetness_media=(
            "sm_rootzone_wetness",
            "mean"
        ),

        cambio_sm_rootzone_medio=(
            "cambio_sm_rootzone",
            "mean"
        )
    )
    .reset_index()
)


# ------------------------------------------------------------
# PORCENTAJES DE ESTADO
# ------------------------------------------------------------

total_dias = (
    df
    .groupby("cultivo")
    .size()
    .rename("total")
)


conteo_bajo = (
    df[
        df["estado_humedad_relativo"].isin(
            [
                "Muy baja",
                "Baja"
            ]
        )
    ]
    .groupby("cultivo")
    .size()
    .rename("dias_humedad_baja")
)


conteo_demanda = (
    df[
        df["demanda_no_cubierta"] > 0
    ]
    .groupby("cultivo")
    .size()
    .rename("dias_demanda")
)


conteo_demanda_humedad = (
    df[
        df["condicion_hidrica_observada"]
        == "Demanda + humedad baja"
    ]
    .groupby("cultivo")
    .size()
    .rename(
        "dias_demanda_humedad_baja"
    )
)


resumen = resumen.merge(
    total_dias,
    on="cultivo",
    how="left"
)


resumen = resumen.merge(
    conteo_bajo,
    on="cultivo",
    how="left"
)


resumen = resumen.merge(
    conteo_demanda,
    on="cultivo",
    how="left"
)


resumen = resumen.merge(
    conteo_demanda_humedad,
    on="cultivo",
    how="left"
)


for columna in [
    "dias_humedad_baja",
    "dias_demanda",
    "dias_demanda_humedad_baja"
]:

    resumen[columna] = (
        resumen[columna]
        .fillna(0)
    )


resumen[
    "pct_dias_humedad_baja"
] = (
    resumen["dias_humedad_baja"]
    /
    resumen["total"]
    * 100
)


resumen[
    "pct_dias_demanda"
] = (
    resumen["dias_demanda"]
    /
    resumen["total"]
    * 100
)


resumen[
    "pct_dias_demanda_humedad_baja"
] = (
    resumen["dias_demanda_humedad_baja"]
    /
    resumen["total"]
    * 100
)


# ------------------------------------------------------------
# GUARDAR
# ------------------------------------------------------------

df.to_csv(
    ARCHIVO_SALIDA,
    index=False
)

resumen.to_csv(
    ARCHIVO_RESUMEN,
    index=False
)


# ------------------------------------------------------------
# MOSTRAR RESUMEN
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("ESTADO HÍDRICO OBSERVADO")
print("=" * 70)

columnas_mostrar = [

    "cultivo",

    "dias_simulados",

    "ETc_acumulada_mm",

    "precipitacion_acumulada_mm",

    "demanda_no_cubierta_mm",

    "sm_rootzone_media",

    "sm_rootzone_min",

    "sm_rootzone_max",

    "pct_dias_humedad_baja",

    "pct_dias_demanda",

    "pct_dias_demanda_humedad_baja"
]


print(
    resumen[
        columnas_mostrar
    ].to_string(
        index=False
    )
)


# ------------------------------------------------------------
# GRÁFICA 1
# HUMEDAD RADICULAR
# ------------------------------------------------------------

plt.figure(
    figsize=(12, 6)
)

for cultivo in df["cultivo"].unique():

    datos = df[
        df["cultivo"] == cultivo
    ]

    plt.plot(
        datos["dia_ciclo"],
        datos["sm_rootzone"],
        label=cultivo
    )


plt.axhline(
    p10,
    linestyle="--",
    label="P10"
)

plt.axhline(
    p50,
    linestyle="--",
    label="P50"
)

plt.axhline(
    p90,
    linestyle="--",
    label="P90"
)


plt.title(
    "Humedad radicular SMAP durante los ciclos"
)

plt.xlabel(
    "Día del ciclo"
)

plt.ylabel(
    "Humedad del suelo (m³/m³)"
)

plt.legend(
    fontsize=8
)

plt.grid(
    True,
    alpha=0.3
)

plt.tight_layout()

plt.savefig(
    ARCHIVO_GRAFICA,
    dpi=150
)

plt.close()


# ------------------------------------------------------------
# VALIDACIÓN
# ------------------------------------------------------------

print("\n" + "-" * 70)
print("VALIDACIÓN")
print("-" * 70)

print(
    f"✓ Cultivos: "
    f"{df['cultivo'].nunique()}"
)

print(
    f"✓ Registros: "
    f"{len(df)}"
)

print(
    f"✓ SMAP faltante: "
    f"{df['sm_rootzone'].isna().sum()}"
)

print(
    f"✓ ETc faltante: "
    f"{df['ETc'].isna().sum()}"
)

print(
    f"✓ Clasificaciones generadas: "
    f"{df['estado_humedad_relativo'].notna().sum()}"
)

print(
    f"✓ Archivo diario: "
    f"{ARCHIVO_SALIDA}"
)

print(
    f"✓ Archivo resumen: "
    f"{ARCHIVO_RESUMEN}"
)

print(
    f"✓ Gráfica: "
    f"{ARCHIVO_GRAFICA}"
)

print("\n" + "=" * 70)
print("✓ ANÁLISIS DEL ESTADO HÍDRICO COMPLETADO")
print("=" * 70)
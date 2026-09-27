import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# AGROSHIFT
# BALANCE HÍDRICO PRELIMINAR
#
# NASA POWER + SMAP + ETc
# ============================================================

print("=" * 70)
print("AGROSHIFT - BALANCE HÍDRICO PRELIMINAR")
print("=" * 70)


# ------------------------------------------------------------
# RUTAS
# ------------------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

ARCHIVO_AMBIENTAL = os.path.join(
    BASE_DIR,
    "data",
    "analysis",
    "agroshift_environmental_2020.csv"
)

ARCHIVO_ETC = os.path.join(
    BASE_DIR,
    "data",
    "analysis",
    "etc_cultivos_2020.csv"
)

ARCHIVO_SALIDA = os.path.join(
    BASE_DIR,
    "data",
    "analysis",
    "balance_hidrico_cultivos_2020.csv"
)

ARCHIVO_RESUMEN = os.path.join(
    BASE_DIR,
    "data",
    "analysis",
    "balance_hidrico_resumen_2020.csv"
)

ARCHIVO_GRAFICA = os.path.join(
    BASE_DIR,
    "data",
    "analysis",
    "balance_hidrico_2020.png"
)


# ------------------------------------------------------------
# CARGAR DATOS AMBIENTALES
# ------------------------------------------------------------

print("\nCargando datos ambientales NASA...")

ambiental = pd.read_csv(
    ARCHIVO_AMBIENTAL
)

ambiental["fecha"] = pd.to_datetime(
    ambiental["fecha"],
    errors="coerce"
)

print(
    f"✓ Registros ambientales: "
    f"{len(ambiental)}"
)


# ------------------------------------------------------------
# CARGAR ETc
# ------------------------------------------------------------

print("\nCargando ETc por cultivo...")

etc = pd.read_csv(
    ARCHIVO_ETC
)

etc["fecha"] = pd.to_datetime(
    etc["fecha"],
    errors="coerce"
)

print(
    f"✓ Registros ETc: "
    f"{len(etc)}"
)


# ------------------------------------------------------------
# COLUMNAS NECESARIAS
# ------------------------------------------------------------

columnas_ambientales = [
    "fecha",
    "PRECTOTCORR",
    "sm_surface",
    "sm_rootzone",
    "sm_surface_wetness",
    "sm_rootzone_wetness",
    "soil_temp_layer1_celsius"
]

faltantes = [
    c
    for c in columnas_ambientales
    if c not in ambiental.columns
]

if faltantes:

    raise ValueError(
        "Faltan columnas ambientales: "
        + ", ".join(faltantes)
    )


columnas_etc = [
    "cultivo",
    "fecha",
    "dia_ciclo",
    "etapa",
    "ETo",
    "Kc",
    "ETc"
]

faltantes = [
    c
    for c in columnas_etc
    if c not in etc.columns
]

if faltantes:

    raise ValueError(
        "Faltan columnas de ETc: "
        + ", ".join(faltantes)
    )


# ------------------------------------------------------------
# SELECCIONAR COLUMNAS
# ------------------------------------------------------------

ambiental = ambiental[
    columnas_ambientales
].copy()

etc = etc[
    columnas_etc
].copy()


# ------------------------------------------------------------
# CONVERTIR VARIABLES NUMÉRICAS
# ------------------------------------------------------------

columnas_numericas_ambientales = [
    "PRECTOTCORR",
    "sm_surface",
    "sm_rootzone",
    "sm_surface_wetness",
    "sm_rootzone_wetness",
    "soil_temp_layer1_celsius"
]

for columna in columnas_numericas_ambientales:

    ambiental[columna] = pd.to_numeric(
        ambiental[columna],
        errors="coerce"
    )


for columna in [
    "ETo",
    "Kc",
    "ETc"
]:

    etc[columna] = pd.to_numeric(
        etc[columna],
        errors="coerce"
    )


# ------------------------------------------------------------
# ELIMINAR DATOS INVÁLIDOS
# ------------------------------------------------------------

ambiental = ambiental.dropna(
    subset=["fecha"]
).copy()

etc = etc.dropna(
    subset=["fecha", "cultivo", "ETc"]
).copy()


# ------------------------------------------------------------
# UNIR AMBIENTE + ETC
# ------------------------------------------------------------

print("\nIntegrando datos...")

resultado = etc.merge(
    ambiental,
    on="fecha",
    how="left"
)


print(
    f"✓ Registros integrados: "
    f"{len(resultado)}"
)


# ------------------------------------------------------------
# VALIDAR HUMEDAD
# ------------------------------------------------------------

print("\nValidando datos SMAP...")

print(
    "Valores faltantes sm_surface:",
    resultado["sm_surface"].isna().sum()
)

print(
    "Valores faltantes sm_rootzone:",
    resultado["sm_rootzone"].isna().sum()
)


# ------------------------------------------------------------
# INDICADOR DE DEMANDA NO CUBIERTA
# ------------------------------------------------------------
#
# NO representa todavía un déficit hídrico real.
#
# Simplemente compara:
#
#       ETc - precipitación
#
# Si es positivo:
# la demanda evapotranspirativa supera
# la precipitación del día.
#
# Si es negativo:
# la precipitación supera la ETc del día.
# ------------------------------------------------------------

resultado["balance_precipitacion_etc"] = (
    resultado["PRECTOTCORR"]
    - resultado["ETc"]
)


resultado["demanda_no_cubierta"] = (
    resultado["ETc"]
    - resultado["PRECTOTCORR"]
).clip(
    lower=0
)


resultado["exceso_precipitacion"] = (
    resultado["PRECTOTCORR"]
    - resultado["ETc"]
).clip(
    lower=0
)


# ------------------------------------------------------------
# CLASIFICACIÓN PRELIMINAR
# ------------------------------------------------------------

def clasificar_demanda(valor):

    if valor <= 0:
        return "Cubierta"

    if valor < 2:
        return "Baja"

    if valor < 4:
        return "Moderada"

    if valor < 6:
        return "Alta"

    return "Muy alta"


resultado["nivel_demanda_hidrica"] = (
    resultado["demanda_no_cubierta"]
    .apply(clasificar_demanda)
)


# ------------------------------------------------------------
# CAMBIO DE HUMEDAD DEL SUELO
# ------------------------------------------------------------
#
# Comparamos con el día anterior para cada cultivo.
#
# Como todos los cultivos comparten el mismo SMAP,
# el cambio ambiental será igual para los cultivos
# que estén activos en esa fecha.
# ------------------------------------------------------------

resultado = resultado.sort_values(
    [
        "cultivo",
        "fecha"
    ]
).copy()


resultado["cambio_sm_surface"] = (
    resultado
    .groupby("cultivo")["sm_surface"]
    .diff()
)


resultado["cambio_sm_rootzone"] = (
    resultado
    .groupby("cultivo")["sm_rootzone"]
    .diff()
)


# ------------------------------------------------------------
# INDICADOR SIMPLE DE VARIACIÓN DE HUMEDAD
# ------------------------------------------------------------

resultado["tendencia_humedad_suelo"] = np.select(

    [
        resultado["cambio_sm_rootzone"] > 0.005,
        resultado["cambio_sm_rootzone"] < -0.005
    ],

    [
        "Aumento",
        "Disminución"
    ],

    default="Estable"
)


# ------------------------------------------------------------
# GUARDAR RESULTADO DIARIO
# ------------------------------------------------------------

resultado.to_csv(
    ARCHIVO_SALIDA,
    index=False
)


# ------------------------------------------------------------
# RESUMEN POR CULTIVO
# ------------------------------------------------------------

resumen = (
    resultado
    .groupby("cultivo")
    .agg(
        dias_simulados=(
            "fecha",
            "count"
        ),

        precipitacion_acumulada_mm=(
            "PRECTOTCORR",
            "sum"
        ),

        precipitacion_media_mm_dia=(
            "PRECTOTCORR",
            "mean"
        ),

        ETo_acumulada_mm=(
            "ETo",
            "sum"
        ),

        ETc_acumulada_mm=(
            "ETc",
            "sum"
        ),

        demanda_no_cubierta_mm=(
            "demanda_no_cubierta",
            "sum"
        ),

        exceso_precipitacion_mm=(
            "exceso_precipitacion",
            "sum"
        ),

        sm_surface_media=(
            "sm_surface",
            "mean"
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

        wetness_rootzone_media=(
            "sm_rootzone_wetness",
            "mean"
        )
    )
    .reset_index()
)


# ------------------------------------------------------------
# RELACIÓN PRECIPITACIÓN / ETC
# ------------------------------------------------------------

resumen["precipitacion_menos_etc_mm"] = (
    resumen["precipitacion_acumulada_mm"]
    -
    resumen["ETc_acumulada_mm"]
)


# ------------------------------------------------------------
# PORCENTAJE DE DÍAS CON DEMANDA NO CUBIERTA
# ------------------------------------------------------------

dias_demanda = (
    resultado
    .groupby("cultivo")[
        "demanda_no_cubierta"
    ]
    .apply(
        lambda x:
        (x > 0).mean() * 100
    )
    .reset_index(
        name="dias_con_demanda_no_cubierta_pct"
    )
)


resumen = resumen.merge(
    dias_demanda,
    on="cultivo",
    how="left"
)


# ------------------------------------------------------------
# GUARDAR RESUMEN
# ------------------------------------------------------------

resumen.to_csv(
    ARCHIVO_RESUMEN,
    index=False
)


# ------------------------------------------------------------
# MOSTRAR RESULTADOS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("RESUMEN DEL BALANCE PRELIMINAR")
print("=" * 70)

print(
    resumen.to_string(
        index=False
    )
)


# ------------------------------------------------------------
# GRÁFICA
# ------------------------------------------------------------

plt.figure(
    figsize=(12, 6)
)

for cultivo in resultado["cultivo"].unique():

    datos = resultado[
        resultado["cultivo"] == cultivo
    ]

    plt.plot(
        datos["dia_ciclo"],
        datos["demanda_no_cubierta"],
        label=cultivo
    )


plt.title(
    "Demanda hídrica no cubierta por precipitación"
)

plt.xlabel(
    "Día del ciclo"
)

plt.ylabel(
    "ETc - precipitación (mm/día)"
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
    f"{resultado['cultivo'].nunique()}"
)

print(
    f"✓ Registros: "
    f"{len(resultado)}"
)

print(
    f"✓ Valores faltantes ETc: "
    f"{resultado['ETc'].isna().sum()}"
)

print(
    f"✓ Valores faltantes precipitación: "
    f"{resultado['PRECTOTCORR'].isna().sum()}"
)

print(
    f"✓ Valores faltantes SMAP: "
    f"{resultado['sm_rootzone'].isna().sum()}"
)

print(
    f"✓ Demanda no cubierta negativa: "
    f"{(resultado['demanda_no_cubierta'] < 0).sum()}"
)


print("\n✓ Archivo diario:")

print(
    ARCHIVO_SALIDA
)

print("\n✓ Archivo resumen:")

print(
    ARCHIVO_RESUMEN
)

print("\n✓ Gráfica:")

print(
    ARCHIVO_GRAFICA
)

print("\n" + "=" * 70)
print("✓ BALANCE HÍDRICO PRELIMINAR COMPLETADO")
print("=" * 70)
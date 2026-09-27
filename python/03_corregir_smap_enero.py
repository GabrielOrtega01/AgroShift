from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ANALYSIS_DIR = (
    BASE_DIR /
    "data" /
    "analysis"
)

ARCHIVO_HISTORICO = (
    ANALYSIS_DIR /
    "smap_historico_2020_01.csv"
)

ARCHIVO_DIARIO = (
    ANALYSIS_DIR /
    "smap_diario_2020_01.csv"
)


# ============================================================
# CARGAR HISTÓRICO
# ============================================================

print("=" * 60)
print("CORRECCIÓN SMAP ENERO 2020")
print("=" * 60)

df = pd.read_csv(
    ARCHIVO_HISTORICO
)

df["fecha_hora"] = pd.to_datetime(
    df["fecha_hora"],
    utc=True
)

print(
    f"\nRegistros originales: {len(df)}"
)


# ============================================================
# FILTRAR ENERO 2020
# ============================================================

inicio = pd.Timestamp(
    "2020-01-01",
    tz="UTC"
)

fin = pd.Timestamp(
    "2020-02-01",
    tz="UTC"
)

df = df[
    (df["fecha_hora"] >= inicio) &
    (df["fecha_hora"] < fin)
].copy()

df = df.sort_values(
    "fecha_hora"
).reset_index(drop=True)


# ============================================================
# CREAR FECHA
# ============================================================

df["fecha"] = (
    df["fecha_hora"]
    .dt.date
)


# ============================================================
# GUARDAR HISTÓRICO CORREGIDO
# ============================================================

df.to_csv(
    ARCHIVO_HISTORICO,
    index=False
)


# ============================================================
# GENERAR RESUMEN DIARIO
# ============================================================

columnas_promedio = [
    "sm_surface",
    "sm_rootzone",
    "sm_surface_wetness",
    "sm_rootzone_wetness",
    "soil_temp_layer1_celsius"
]

df_diario = (
    df.groupby("fecha")[columnas_promedio]
    .mean()
    .reset_index()
)

observaciones = (
    df.groupby("fecha")
    .size()
    .reset_index(
        name="observaciones_smap"
    )
)

df_diario = df_diario.merge(
    observaciones,
    on="fecha",
    how="left"
)

df_diario.to_csv(
    ARCHIVO_DIARIO,
    index=False
)


# ============================================================
# RESULTADO
# ============================================================

print("\n" + "=" * 60)
print("RESULTADO")
print("=" * 60)

print(
    f"\nRegistros corregidos: {len(df)}"
)

print(
    f"Días con información: {len(df_diario)}"
)

print(
    f"Periodo: "
    f"{df['fecha'].min()} -> {df['fecha'].max()}"
)

print("\nObservaciones por día:")

print(
    df_diario["observaciones_smap"]
    .value_counts()
    .sort_index()
)

print("\nArchivos actualizados:")

print(ARCHIVO_HISTORICO)
print(ARCHIVO_DIARIO)

print("\nCorrección terminada.")
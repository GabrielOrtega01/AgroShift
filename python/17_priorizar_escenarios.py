import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# AGROSHIFT - ANÁLISIS DE ROTACIONES V9
# Priorización configurable sin puntuación única
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ANALYSIS_DIR = BASE_DIR / "data" / "analysis"

INPUT_FILE = ANALYSIS_DIR / "resumen_rotaciones_2020_v8.csv"

OUTPUT_FILE = ANALYSIS_DIR / "escenarios_priorizados_2020_v9.csv"
OUTPUT_WATER = ANALYSIS_DIR / "escenarios_prioridad_agua_2020_v9.csv"
OUTPUT_HUMIDITY = ANALYSIS_DIR / "escenarios_prioridad_humedad_2020_v9.csv"
OUTPUT_BALANCE = ANALYSIS_DIR / "escenarios_prioridad_balance_2020_v9.csv"
OUTPUT_TEMPORAL = ANALYSIS_DIR / "escenarios_prioridad_temporal_2020_v9.csv"


# ============================================================
# CONFIGURACIÓN
# ============================================================

COBERTURA_MIN_AGUA = 75.0
BALANCE_MIN = 0.0
PERCENTIL_HUMEDAD_MIN = 25.0
COBERTURA_MIN_TEMPORAL = 60.0


# ============================================================
# INICIO
# ============================================================

print("=" * 70)
print("AGROSHIFT - ANÁLISIS DE ROTACIONES V9")
print("=" * 70)

print("\nCargando resultados V8...")

df = pd.read_csv(INPUT_FILE)

print(f"Escenarios V8 cargados: {len(df)}")


# ============================================================
# MOSTRAR COLUMNAS DISPONIBLES
# ============================================================

print("\nColumnas detectadas en V8:")

for columna in df.columns:
    print(f"  - {columna}")


# ============================================================
# VALIDACIÓN
# ============================================================

columnas_requeridas = [
    "rotacion",
    "fecha_inicio_escenario",
    "precipitacion_total_mm",
    "ETc_total_mm",
    "balance_P_ETc_total_mm",
    "cobertura_precipitacion_pct",
    "sm_rootzone_media",
    "percentil_humedad_medio"
]
# Usar el nombre real de V8 dentro del análisis V9
df["balance_P_ETc_mm"] = df["balance_P_ETc_total_mm"]

faltantes = [
    columna
    for columna in columnas_requeridas
    if columna not in df.columns
]

if faltantes:

    raise ValueError(
        "\nFaltan las siguientes columnas en el archivo V8:\n"
        + "\n".join(f"- {col}" for col in faltantes)
        + "\n\nRevisa las columnas mostradas anteriormente."
    )


# ============================================================
# CONVERSIÓN NUMÉRICA
# ============================================================

columnas_numericas = [
    "precipitacion_total_mm",
    "ETc_total_mm",
    "balance_P_ETc_total_mm",
    "cobertura_precipitacion_pct",
    "sm_rootzone_media",
    "percentil_humedad_medio",
    "dias_menor_P10",
    "porcentaje_dias_menor_P10",
    "duracion_total_dias"
]

for columna in columnas_numericas:

    if columna in df.columns:

        df[columna] = pd.to_numeric(
            df[columna],
            errors="coerce"
        )


# ============================================================
# INDICADORES DERIVADOS
# ============================================================

# ------------------------------------------------------------
# Cobertura de demanda limitada a 100 %
# ------------------------------------------------------------

df["cobertura_demanda_pct"] = (
    df["cobertura_precipitacion_pct"]
    .clip(lower=0, upper=100)
)


# ------------------------------------------------------------
# Exceso simplificado de precipitación
# ------------------------------------------------------------

df["exceso_precipitacion_mm"] = (
    df["balance_P_ETc_mm"]
    .clip(lower=0)
)


# ------------------------------------------------------------
# Déficit simplificado
# ------------------------------------------------------------

df["deficit_balance_mm"] = (
    -df["balance_P_ETc_mm"]
).clip(lower=0)


# ============================================================
# PRIORIDAD 1 - AGUA
# ============================================================

print("\nAnalizando prioridad: AGUA...")

df["cumple_prioridad_agua"] = (
    df["cobertura_demanda_pct"]
    >= COBERTURA_MIN_AGUA
)

df["criterio_agua"] = np.where(
    df["cumple_prioridad_agua"],
    f"Cobertura >= {COBERTURA_MIN_AGUA:.0f} %",
    f"Cobertura < {COBERTURA_MIN_AGUA:.0f} %"
)


# ============================================================
# PRIORIDAD 2 - BALANCE
# ============================================================

print("Analizando prioridad: BALANCE HÍDRICO...")

df["cumple_prioridad_balance"] = (
    df["balance_P_ETc_mm"]
    >= BALANCE_MIN
)

df["criterio_balance"] = np.where(
    df["cumple_prioridad_balance"],
    f"Balance >= {BALANCE_MIN:.0f} mm",
    f"Balance < {BALANCE_MIN:.0f} mm"
)


# ============================================================
# PRIORIDAD 3 - HUMEDAD DEL SUELO
# ============================================================

print("Analizando prioridad: HUMEDAD DEL SUELO...")

df["cumple_prioridad_humedad"] = (
    df["percentil_humedad_medio"]
    >= PERCENTIL_HUMEDAD_MIN
)

df["criterio_humedad"] = np.where(
    df["cumple_prioridad_humedad"],
    f"Percentil >= P{PERCENTIL_HUMEDAD_MIN:.0f}",
    f"Percentil < P{PERCENTIL_HUMEDAD_MIN:.0f}"
)


# ============================================================
# PRIORIDAD 4 - ADAPTACIÓN TEMPORAL
# ============================================================

print("Analizando prioridad: ADAPTACIÓN TEMPORAL...")

df["cumple_prioridad_temporal"] = (
    (
        df["cobertura_demanda_pct"]
        >= COBERTURA_MIN_TEMPORAL
    )
    &
    (
        df["percentil_humedad_medio"]
        >= PERCENTIL_HUMEDAD_MIN
    )
)

df["criterio_temporal"] = np.where(
    df["cumple_prioridad_temporal"],
    (
        f"Cobertura >= {COBERTURA_MIN_TEMPORAL:.0f} % "
        f"y humedad >= P{PERCENTIL_HUMEDAD_MIN:.0f}"
    ),
    (
        f"No cumple simultáneamente cobertura >= "
        f"{COBERTURA_MIN_TEMPORAL:.0f} % y humedad >= "
        f"P{PERCENTIL_HUMEDAD_MIN:.0f}"
    )
)


# ============================================================
# CRITERIOS CUMPLIDOS
# ============================================================

criterios = [
    "cumple_prioridad_agua",
    "cumple_prioridad_balance",
    "cumple_prioridad_humedad",
    "cumple_prioridad_temporal"
]

df["numero_criterios_cumplidos"] = (
    df[criterios]
    .sum(axis=1)
)


def obtener_criterios(fila):

    nombres = [
        "Agua",
        "Balance",
        "Humedad",
        "Temporal"
    ]

    resultado = []

    for nombre, valor in zip(nombres, fila):

        if valor:
            resultado.append(nombre)

    if resultado:
        return ", ".join(resultado)

    return "Ninguno"


df["criterios_cumplidos"] = (
    df[criterios]
    .apply(obtener_criterios, axis=1)
)


def describir_criterios(numero):

    if numero == 4:
        return "Cumple los 4 criterios"

    if numero == 3:
        return "Cumple 3 criterios"

    if numero == 2:
        return "Cumple 2 criterios"

    if numero == 1:
        return "Cumple 1 criterio"

    return "No cumple los criterios"


df["descripcion_criterios"] = (
    df["numero_criterios_cumplidos"]
    .apply(describir_criterios)
)


# ============================================================
# ORDENAMIENTO
# ============================================================

df = df.sort_values(
    by=[
        "numero_criterios_cumplidos",
        "cobertura_demanda_pct",
        "percentil_humedad_medio"
    ],
    ascending=[
        False,
        False,
        False
    ]
).reset_index(drop=True)


# ============================================================
# GUARDAR RESULTADOS
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

df[
    df["cumple_prioridad_agua"]
].to_csv(
    OUTPUT_WATER,
    index=False,
    encoding="utf-8-sig"
)

df[
    df["cumple_prioridad_humedad"]
].to_csv(
    OUTPUT_HUMIDITY,
    index=False,
    encoding="utf-8-sig"
)

df[
    df["cumple_prioridad_balance"]
].to_csv(
    OUTPUT_BALANCE,
    index=False,
    encoding="utf-8-sig"
)

df[
    df["cumple_prioridad_temporal"]
].to_csv(
    OUTPUT_TEMPORAL,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# RESULTADOS
# ============================================================

print("\n" + "=" * 70)
print("RESULTADOS V9")
print("=" * 70)

print(f"\nEscenarios analizados: {len(df)}")

print("\nCriterios configurados:")

print(
    f"  Cobertura mínima agua: "
    f"{COBERTURA_MIN_AGUA:.1f} %"
)

print(
    f"  Balance mínimo: "
    f"{BALANCE_MIN:.1f} mm"
)

print(
    f"  Humedad mínima: "
    f"P{PERCENTIL_HUMEDAD_MIN:.0f}"
)

print(
    f"  Cobertura temporal: "
    f"{COBERTURA_MIN_TEMPORAL:.1f} %"
)


# ============================================================
# CUMPLIMIENTO
# ============================================================

print("\nCumplimiento por prioridad:")

print(
    f"  Agua:      "
    f"{df['cumple_prioridad_agua'].sum()} / {len(df)}"
)

print(
    f"  Balance:   "
    f"{df['cumple_prioridad_balance'].sum()} / {len(df)}"
)

print(
    f"  Humedad:   "
    f"{df['cumple_prioridad_humedad'].sum()} / {len(df)}"
)

print(
    f"  Temporal:  "
    f"{df['cumple_prioridad_temporal'].sum()} / {len(df)}"
)


# ============================================================
# DISTRIBUCIÓN
# ============================================================

print("\nCantidad de criterios cumplidos:")

print(
    df["descripcion_criterios"]
    .value_counts()
)


# ============================================================
# ESCENARIOS QUE CUMPLEN LOS 4
# ============================================================

cumplen_todos = df[
    df["numero_criterios_cumplidos"] == 4
]

print("\n" + "-" * 70)
print("ESCENARIOS QUE CUMPLEN LOS 4 CRITERIOS")
print("-" * 70)

if len(cumplen_todos) == 0:

    print(
        "No existen escenarios que cumplan simultáneamente "
        "los cuatro criterios configurados."
    )

else:

    columnas_mostrar = [
        "rotacion",
        "fecha_inicio_escenario",
        "precipitacion_total_mm",
        "ETc_total_mm",
        "balance_P_ETc_total_mm",
        "cobertura_demanda_pct",
        "sm_rootzone_media",
        "percentil_humedad_medio",
        "descripcion_criterios"
    ]

    print(
        cumplen_todos[
            columnas_mostrar
        ].to_string(index=False)
    )


# ============================================================
# EJEMPLO TOMATE → PAPA
# ============================================================

print("\n" + "-" * 70)
print("EJEMPLO: TOMATE → PAPA")
print("-" * 70)

ejemplo = df[
    df["rotacion"].str.contains(
        "Lycopersicon esculentum.*Solanum tuberosum",
        regex=True,
        na=False
    )
]

if len(ejemplo) > 0:

    columnas_ejemplo = [
        "fecha_inicio_escenario",
        "rotacion",
        "balance_P_ETc_total_mm",
        "cobertura_demanda_pct",
        "sm_rootzone_media",
        "percentil_humedad_medio",
        "numero_criterios_cumplidos",
        "criterios_cumplidos"
    ]

    print(
        ejemplo[
            columnas_ejemplo
        ].to_string(index=False)
    )


# ============================================================
# ARCHIVOS
# ============================================================

print("\n" + "=" * 70)
print("ARCHIVOS GENERADOS")
print("=" * 70)

print(f"\n1. {OUTPUT_FILE}")
print(f"2. {OUTPUT_WATER}")
print(f"3. {OUTPUT_HUMIDITY}")
print(f"4. {OUTPUT_BALANCE}")
print(f"5. {OUTPUT_TEMPORAL}")

print("\nProceso terminado.")
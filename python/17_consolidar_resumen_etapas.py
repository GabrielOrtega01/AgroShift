import os
import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agroshift.regions import get_region

REGION_SLUG = get_region(os.environ.get("AGROSHIFT_REGION", "santander")).slug


# ============================================================
# AGROSHIFT - ANÁLISIS DE ROTACIONES V10
# Análisis descriptivo por etapas
# ============================================================

print("=" * 70)
print("AGROSHIFT - ANÁLISIS DE ROTACIONES V10")
print("=" * 70)


# ============================================================
# RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ANALYSIS_DIR = BASE_DIR / "data" / "analysis" / REGION_SLUG

ARCHIVO_ENTRADA = (
    ANALYSIS_DIR / "analisis_etapas_rotacion_2020_v8.csv"
)

ARCHIVO_SALIDA_ETAPAS = (
    ANALYSIS_DIR / "analisis_etapas_rotacion_2020_v10.csv"
)

ARCHIVO_SALIDA_RESUMEN = (
    ANALYSIS_DIR / "resumen_etapas_rotacion_2020_v10.csv"
)


# ============================================================
# CARGAR DATOS
# ============================================================

print("\nCargando resultados V8...")

if not ARCHIVO_ENTRADA.exists():
    raise FileNotFoundError(
        f"No se encontró el archivo:\n{ARCHIVO_ENTRADA}"
    )

df = pd.read_csv(ARCHIVO_ENTRADA)

print(f"Etapas V8 cargadas: {len(df)}")


print("\nColumnas detectadas:")

for columna in df.columns:
    print(f"  - {columna}")


# ============================================================
# COLUMNAS REQUERIDAS
# ============================================================

columnas_requeridas = [
    "fecha_inicio_escenario",
    "rotacion",
    "numero_etapa",
    "cultivo",
    "fecha_inicio",
    "fecha_fin",
    "dias",
    "precipitacion_mm",
    "ETo_mm",
    "ETc_mm",
    "balance_P_ETc_mm",
    "demanda_no_cubierta_mm",
    "cobertura_precipitacion_pct",
    "sm_rootzone_media",
    "percentil_humedad_medio",
    "dias_humedad_menor_P10",
    "porcentaje_dias_menor_P10",
    "condicion_balance",
    "condicion_humedad",
]

faltantes = [
    columna
    for columna in columnas_requeridas
    if columna not in df.columns
]

if faltantes:
    raise ValueError(
        "\nFaltan las siguientes columnas:\n"
        + "\n".join(f"- {c}" for c in faltantes)
    )


# ============================================================
# CONVERSIÓN DE FECHAS
# ============================================================

df["fecha_inicio"] = pd.to_datetime(
    df["fecha_inicio"],
    errors="coerce"
)

df["fecha_fin"] = pd.to_datetime(
    df["fecha_fin"],
    errors="coerce"
)

df["fecha_inicio_escenario"] = pd.to_datetime(
    df["fecha_inicio_escenario"],
    errors="coerce"
)


# ============================================================
# CONVERSIÓN NUMÉRICA
# ============================================================

columnas_numericas = [
    "numero_etapa",
    "dias",
    "precipitacion_mm",
    "ETo_mm",
    "ETc_mm",
    "balance_P_ETc_mm",
    "demanda_no_cubierta_mm",
    "cobertura_precipitacion_pct",
    "sm_rootzone_media",
    "percentil_humedad_medio",
    "dias_humedad_menor_P10",
    "porcentaje_dias_menor_P10",
]

for columna in columnas_numericas:

    df[columna] = pd.to_numeric(
        df[columna],
        errors="coerce"
    )


# ============================================================
# INDICADORES DERIVADOS
# ============================================================

print("\nCalculando indicadores por etapa...")


# ------------------------------------------------------------
# Cobertura de demanda
# ------------------------------------------------------------

df["cobertura_demanda_pct"] = (
    df["cobertura_precipitacion_pct"]
    .clip(lower=0, upper=100)
)


# ------------------------------------------------------------
# Exceso de precipitación
# ------------------------------------------------------------

df["exceso_precipitacion_mm"] = (
    df["balance_P_ETc_mm"]
    .clip(lower=0)
)


# ------------------------------------------------------------
# Déficit según balance P-ETc
# ------------------------------------------------------------

df["deficit_balance_mm"] = (
    -df["balance_P_ETc_mm"]
).clip(lower=0)


# ------------------------------------------------------------
# Relación ETc / ETo
# ------------------------------------------------------------

df["relacion_ETc_ETo_pct"] = (
    df["ETc_mm"]
    / df["ETo_mm"]
    * 100
).replace(
    [float("inf"), -float("inf")],
    pd.NA
)


# ============================================================
# DESCRIPCIÓN DE LA ETAPA
# ============================================================

def describir_etapa(fila):

    condiciones = []

    balance = fila["balance_P_ETc_mm"]
    cobertura = fila["cobertura_demanda_pct"]
    humedad = fila["percentil_humedad_medio"]

    # Balance
    if pd.notna(balance):

        if balance > 0:
            condiciones.append("balance positivo")

        elif balance < 0:
            condiciones.append("balance negativo")

        else:
            condiciones.append("balance cercano a cero")

    # Cobertura
    if pd.notna(cobertura):

        if cobertura >= 100:
            condiciones.append(
                "precipitación cubre la ETc"
            )

        elif cobertura >= 75:
            condiciones.append(
                "cobertura de precipitación alta"
            )

        elif cobertura >= 50:
            condiciones.append(
                "cobertura de precipitación intermedia"
            )

        else:
            condiciones.append(
                "cobertura de precipitación baja"
            )

    # Humedad
    if pd.notna(humedad):

        if humedad < 25:
            condiciones.append(
                "humedad relativamente baja"
            )

        elif humedad < 50:
            condiciones.append(
                "humedad inferior a la mediana"
            )

        elif humedad < 75:
            condiciones.append(
                "humedad superior a la mediana"
            )

        else:
            condiciones.append(
                "humedad relativamente alta"
            )

    return "; ".join(condiciones)


df["descripcion_hidrica_etapa"] = df.apply(
    describir_etapa,
    axis=1
)


# ============================================================
# ALERTAS
# ============================================================

def generar_alertas(fila):

    alertas = []

    balance = fila["balance_P_ETc_mm"]
    cobertura = fila["cobertura_demanda_pct"]
    porcentaje_p10 = fila["porcentaje_dias_menor_P10"]

    if pd.notna(balance) and balance < 0:

        alertas.append(
            "balance P-ETc negativo"
        )

    if pd.notna(cobertura) and cobertura < 75:

        alertas.append(
            "cobertura de precipitación inferior a 75%"
        )

    if (
        pd.notna(porcentaje_p10)
        and porcentaje_p10 >= 10
    ):

        alertas.append(
            "presencia relevante de días bajo P10"
        )

    if not alertas:

        return (
            "Sin alerta según los criterios "
            "descriptivos"
        )

    return "; ".join(alertas)


df["alertas_etapa"] = df.apply(
    generar_alertas,
    axis=1
)


# ============================================================
# ORDEN
# ============================================================

df = df.sort_values(
    by=[
        "fecha_inicio_escenario",
        "rotacion",
        "numero_etapa",
    ]
).reset_index(drop=True)


# ============================================================
# RESUMEN POR CULTIVO / ETAPA
# ============================================================

print("\nGenerando resumen por cultivo...")


resumen = (
    df.groupby(
        [
            "rotacion",
            "numero_etapa",
            "cultivo",
        ],
        as_index=False
    )
    .agg(
        cantidad_registros=("cultivo", "count"),

        duracion_promedio_dias=(
            "dias",
            "mean"
        ),

        precipitacion_promedio_mm=(
            "precipitacion_mm",
            "mean"
        ),

        ETo_promedio_mm=(
            "ETo_mm",
            "mean"
        ),

        ETc_promedio_mm=(
            "ETc_mm",
            "mean"
        ),

        balance_promedio_mm=(
            "balance_P_ETc_mm",
            "mean"
        ),

        demanda_no_cubierta_promedio_mm=(
            "demanda_no_cubierta_mm",
            "mean"
        ),

        cobertura_promedio_pct=(
            "cobertura_demanda_pct",
            "mean"
        ),

        humedad_suelo_promedio=(
            "sm_rootzone_media",
            "mean"
        ),

        percentil_humedad_promedio=(
            "percentil_humedad_medio",
            "mean"
        ),

        dias_P10_promedio=(
            "dias_humedad_menor_P10",
            "mean"
        ),

        porcentaje_P10_promedio=(
            "porcentaje_dias_menor_P10",
            "mean"
        ),
    )
)


# ============================================================
# REDONDEAR
# ============================================================

columnas_redondear = [
    "duracion_promedio_dias",
    "precipitacion_promedio_mm",
    "ETo_promedio_mm",
    "ETc_promedio_mm",
    "balance_promedio_mm",
    "demanda_no_cubierta_promedio_mm",
    "cobertura_promedio_pct",
    "humedad_suelo_promedio",
    "percentil_humedad_promedio",
    "dias_P10_promedio",
    "porcentaje_P10_promedio",
]

for columna in columnas_redondear:

    if columna in resumen.columns:

        resumen[columna] = resumen[
            columna
        ].round(4)


# ============================================================
# GUARDAR
# ============================================================

df.to_csv(
    ARCHIVO_SALIDA_ETAPAS,
    index=False,
    encoding="utf-8-sig"
)

resumen.to_csv(
    ARCHIVO_SALIDA_RESUMEN,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# RESULTADOS
# ============================================================

print("\n" + "=" * 70)
print("RESULTADOS V10")
print("=" * 70)

print(
    f"\nEtapas analizadas: {len(df)}"
)

print(
    f"Rotaciones diferentes: "
    f"{df['rotacion'].nunique()}"
)

print(
    f"Cultivos diferentes: "
    f"{df['cultivo'].nunique()}"
)

escenarios_diferentes = (
    df[
        [
            "fecha_inicio_escenario",
            "rotacion",
        ]
    ]
    .drop_duplicates()
    .shape[0]
)

print(
    f"Escenarios diferentes: {escenarios_diferentes}"
)


# ============================================================
# CONDICIONES DE BALANCE
# ============================================================

print("\nCondiciones de balance:")

print(
    df["condicion_balance"]
    .value_counts()
)


# ============================================================
# CONDICIONES DE HUMEDAD
# ============================================================

print("\nCondiciones de humedad:")

print(
    df["condicion_humedad"]
    .value_counts()
)


# ============================================================
# ALERTAS
# ============================================================

print("\nAlertas:")

print(
    df["alertas_etapa"]
    .value_counts()
)


# ============================================================
# EJEMPLO TOMATE → PAPA
# ============================================================

print("\n" + "-" * 70)
print("EJEMPLO: TOMATE → PAPA")
print("-" * 70)


mascara_tomate_papa = (
    df["rotacion"]
    .str.contains(
        "Lycopersicon esculentum.*Solanum tuberosum",
        regex=True,
        na=False
    )
)


ejemplo = df.loc[
    mascara_tomate_papa,
    [
        "fecha_inicio_escenario",
        "rotacion",
        "numero_etapa",
        "cultivo",
        "fecha_inicio",
        "fecha_fin",
        "dias",
        "precipitacion_mm",
        "ETo_mm",
        "ETc_mm",
        "balance_P_ETc_mm",
        "demanda_no_cubierta_mm",
        "cobertura_demanda_pct",
        "sm_rootzone_media",
        "percentil_humedad_medio",
        "dias_humedad_menor_P10",
        "porcentaje_dias_menor_P10",
        "condicion_balance",
        "condicion_humedad",
        "descripcion_hidrica_etapa",
        "alertas_etapa",
    ]
]


if len(ejemplo) > 0:

    print(
        ejemplo.to_string(index=False)
    )

else:

    print(
        "No se encontró la rotación "
        "Tomate → Papa."
    )


# ============================================================
# ARCHIVOS GENERADOS
# ============================================================

print("\n" + "=" * 70)
print("ARCHIVOS GENERADOS")
print("=" * 70)

print(
    f"\n1. {ARCHIVO_SALIDA_ETAPAS}"
)

print(
    f"2. {ARCHIVO_SALIDA_RESUMEN}"
)

print("\nProceso terminado.")
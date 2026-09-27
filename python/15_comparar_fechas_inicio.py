import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ANALYSIS_DIR = BASE_DIR / "data" / "analysis"

ARCHIVO_ESCENARIOS = (
    ANALYSIS_DIR /
    "escenarios_rotacion_2020_v6.csv"
)

ARCHIVO_ETAPAS = (
    ANALYSIS_DIR /
    "escenarios_rotacion_2020_v6_etapas.csv"
)

SALIDA_COMPARACION = (
    ANALYSIS_DIR /
    "comparacion_rotaciones_fecha_inicio_2020_v7.csv"
)

SALIDA_ETAPAS = (
    ANALYSIS_DIR /
    "comparacion_etapas_fecha_inicio_2020_v7.csv"
)


# ============================================================
# INICIO
# ============================================================

print("=" * 70)
print("AGROSHIFT - COMPARACIÓN DE FECHAS DE INICIO V7")
print("=" * 70)

print("\nCargando resultados V6...")

df_escenarios = pd.read_csv(
    ARCHIVO_ESCENARIOS,
    parse_dates=[
        "fecha_inicio_escenario",
        "fecha_fin_escenario"
    ]
)

df_etapas = pd.read_csv(
    ARCHIVO_ETAPAS,
    parse_dates=[
        "fecha_inicio",
        "fecha_fin",
        "fecha_inicio_escenario"
    ]
)

print(f"Escenarios V6: {len(df_escenarios)}")
print(f"Etapas V6: {len(df_etapas)}")


# ============================================================
# VALIDACIÓN
# ============================================================

if df_escenarios.empty:

    print("\nNo existen escenarios para analizar.")
    raise SystemExit


# ============================================================
# COMPARACIÓN DE UNA MISMA ROTACIÓN
# ============================================================

print("\nAnalizando comportamiento por rotación...")


# Para cada rotación y fecha de inicio calculamos
# nuevamente los indicadores principales.

comparaciones = []

for rotacion, grupo in df_escenarios.groupby("rotacion"):

    grupo = grupo.sort_values(
        "fecha_inicio_escenario"
    )

    for _, fila in grupo.iterrows():

        comparaciones.append({

            "rotacion": rotacion,

            "fecha_inicio": (
                fila["fecha_inicio_escenario"]
            ),

            "fecha_fin": (
                fila["fecha_fin_escenario"]
            ),

            "mes_inicio": (
                fila["fecha_inicio_escenario"].month
            ),

            "duracion_dias": (
                fila["duracion_total_dias"]
            ),

            "numero_etapas": (
                fila["numero_etapas"]
            ),

            "precipitacion_mm": (
                fila["precipitacion_total_mm"]
            ),

            "ETo_mm": (
                fila["ETo_total_mm"]
            ),

            "ETc_mm": (
                fila["ETc_total_mm"]
            ),

            "balance_P_ETc_mm": (
                fila["balance_P_ETc_total_mm"]
            ),

            "demanda_no_cubierta_mm": (
                fila["demanda_no_cubierta_total_mm"]
            ),

            "cobertura_precipitacion_pct": (
                fila["cobertura_precipitacion_pct"]
            ),

            "sm_rootzone_media": (
                fila["sm_rootzone_media"]
            ),

            "percentil_humedad_medio": (
                fila["percentil_humedad_medio"]
            ),

            "dias_humedad_menor_P10": (
                fila["dias_humedad_menor_P10"]
            ),

            "porcentaje_dias_menor_P10": (
                fila["porcentaje_dias_menor_P10"]
            )
        })


df_comparacion = pd.DataFrame(
    comparaciones
)


# ============================================================
# DIFERENCIA RESPECTO AL PRIMER INICIO DISPONIBLE
# ============================================================

print("\nCalculando cambios respecto al primer inicio disponible...")


resultados = []

for rotacion, grupo in df_comparacion.groupby(
    "rotacion"
):

    grupo = grupo.sort_values(
        "fecha_inicio"
    ).copy()

    referencia = grupo.iloc[0]

    for _, fila in grupo.iterrows():

        resultados.append({

            "rotacion": rotacion,

            "fecha_inicio": fila["fecha_inicio"],
            "fecha_fin": fila["fecha_fin"],

            "duracion_dias": fila["duracion_dias"],

            "precipitacion_mm": fila["precipitacion_mm"],
            "ETo_mm": fila["ETo_mm"],
            "ETc_mm": fila["ETc_mm"],

            "balance_P_ETc_mm": fila[
                "balance_P_ETc_mm"
            ],

            "cobertura_precipitacion_pct": fila[
                "cobertura_precipitacion_pct"
            ],

            "sm_rootzone_media": fila[
                "sm_rootzone_media"
            ],

            "percentil_humedad_medio": fila[
                "percentil_humedad_medio"
            ],

            "dias_humedad_menor_P10": fila[
                "dias_humedad_menor_P10"
            ],

            "porcentaje_dias_menor_P10": fila[
                "porcentaje_dias_menor_P10"
            ],

            # Cambios respecto al primer inicio disponible
            "cambio_precipitacion_mm": (
                fila["precipitacion_mm"]
                - referencia["precipitacion_mm"]
            ),

            "cambio_ETc_mm": (
                fila["ETc_mm"]
                - referencia["ETc_mm"]
            ),

            "cambio_balance_mm": (
                fila["balance_P_ETc_mm"]
                - referencia["balance_P_ETc_mm"]
            ),

            "cambio_cobertura_pct": (
                fila["cobertura_precipitacion_pct"]
                - referencia[
                    "cobertura_precipitacion_pct"
                ]
            ),

            "cambio_humedad_smap": (
                fila["sm_rootzone_media"]
                - referencia["sm_rootzone_media"]
            ),

            "cambio_percentil_humedad": (
                fila["percentil_humedad_medio"]
                - referencia[
                    "percentil_humedad_medio"
                ]
            )
        })


df_resultado = pd.DataFrame(
    resultados
)


# ============================================================
# ANÁLISIS POR ETAPA
# ============================================================

print("\nAnalizando comportamiento de cada etapa...")

if not df_etapas.empty:

    columnas_etapas = [
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
        "porcentaje_dias_menor_P10"
    ]

    columnas_disponibles = [
        columna
        for columna in columnas_etapas
        if columna in df_etapas.columns
    ]

    df_etapas_resultado = df_etapas[
        columnas_disponibles
    ].copy()

else:

    df_etapas_resultado = pd.DataFrame()


# ============================================================
# ORDENAMIENTO
# ============================================================

df_resultado = df_resultado.sort_values(
    [
        "rotacion",
        "fecha_inicio"
    ]
)

if not df_etapas_resultado.empty:

    df_etapas_resultado = (
        df_etapas_resultado
        .sort_values(
            [
                "rotacion",
                "fecha_inicio_escenario",
                "numero_etapa"
            ]
        )
    )


# ============================================================
# GUARDAR
# ============================================================

df_resultado.to_csv(
    SALIDA_COMPARACION,
    index=False,
    encoding="utf-8-sig"
)

df_etapas_resultado.to_csv(
    SALIDA_ETAPAS,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# RESUMEN
# ============================================================

print("\n" + "=" * 70)
print("RESULTADOS V7")
print("=" * 70)

print(
    f"\nRotaciones diferentes: "
    f"{df_resultado['rotacion'].nunique()}"
)

print(
    f"Escenarios analizados: "
    f"{len(df_resultado)}"
)

print(
    f"Fechas de inicio utilizadas: "
    f"{df_resultado['fecha_inicio'].nunique()}"
)


# ============================================================
# MOSTRAR ROTACIONES CON MÁS DE UNA FECHA
# ============================================================

conteo = (
    df_resultado
    .groupby("rotacion")
    .size()
    .sort_values(ascending=False)
)

print("\nRotaciones con mayor cantidad de fechas:")

print(
    conteo.head(10).to_string()
)


# ============================================================
# EJEMPLO: TOMATE → PAPA
# ============================================================

rotacion_ejemplo = (
    "Lycopersicon esculentum → Solanum tuberosum"
)

ejemplo = df_resultado[
    df_resultado["rotacion"] == rotacion_ejemplo
].copy()

if not ejemplo.empty:

    print(
        "\nComparación de ejemplo:"
    )

    columnas = [
        "fecha_inicio",
        "fecha_fin",
        "precipitacion_mm",
        "ETc_mm",
        "balance_P_ETc_mm",
        "cobertura_precipitacion_pct",
        "sm_rootzone_media",
        "percentil_humedad_medio"
    ]

    print(
        ejemplo[columnas]
        .to_string(index=False)
    )

else:

    print(
        "\nLa rotación Tomate → Papa "
        "no aparece en los escenarios V6."
    )


# ============================================================
# ARCHIVOS
# ============================================================

print("\nArchivos generados:")

print(
    f"1. {SALIDA_COMPARACION}"
)

print(
    f"2. {SALIDA_ETAPAS}"
)

print("\nProceso terminado.")
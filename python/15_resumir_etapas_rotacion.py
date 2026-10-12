import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agroshift.regions import get_region

REGION_SLUG = get_region(os.environ.get("AGROSHIFT_REGION", "santander")).slug


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ANALYSIS_DIR = BASE_DIR / "data" / "analysis" / REGION_SLUG

ARCHIVO_ETAPAS = (
    ANALYSIS_DIR /
    "comparacion_etapas_fecha_inicio_v7.csv"
)

ARCHIVO_ESCENARIOS = (
    ANALYSIS_DIR /
    "comparacion_rotaciones_fecha_inicio_v7.csv"
)

SALIDA_ETAPAS = (
    ANALYSIS_DIR /
    "analisis_etapas_rotacion_v8.csv"
)

SALIDA_RESUMEN = (
    ANALYSIS_DIR /
    "resumen_rotaciones_v8.csv"
)


# ============================================================
# INICIO
# ============================================================

print("=" * 70)
print("AGROSHIFT - ANÁLISIS DETALLADO DE ROTACIONES V8")
print("=" * 70)

print("\nCargando datos V7...")

df_etapas = pd.read_csv(
    ARCHIVO_ETAPAS,
    parse_dates=[
        "fecha_inicio_escenario",
        "fecha_inicio",
        "fecha_fin"
    ]
)

df_escenarios = pd.read_csv(
    ARCHIVO_ESCENARIOS,
    parse_dates=[
        "fecha_inicio",
        "fecha_fin"
    ]
)

print(f"Etapas cargadas: {len(df_etapas)}")
print(f"Escenarios cargados: {len(df_escenarios)}")


# ============================================================
# VALIDACIÓN
# ============================================================

if df_etapas.empty:
    print("\nNo hay etapas disponibles.")
    raise SystemExit


# ============================================================
# INDICADORES DE ETAPA
# ============================================================

print("\nCalculando indicadores...")


df_etapas["relacion_ETc_ETo_pct"] = np.where(
    df_etapas["ETo_mm"] > 0,
    (
        df_etapas["ETc_mm"] /
        df_etapas["ETo_mm"]
    ) * 100,
    np.nan
)


df_etapas["diferencia_precipitacion_ETc_mm"] = (
    df_etapas["precipitacion_mm"]
    - df_etapas["ETc_mm"]
)


df_etapas["porcentaje_demanda_no_cubierta"] = np.where(
    df_etapas["ETc_mm"] > 0,
    (
        df_etapas["demanda_no_cubierta_mm"] /
        df_etapas["ETc_mm"]
    ) * 100,
    np.nan
)


# ============================================================
# CLASIFICACIÓN DESCRIPTIVA DEL BALANCE
# ============================================================

def clasificar_balance(valor, etc):

    if pd.isna(valor) or pd.isna(etc) or etc == 0:
        return "Sin datos"

    porcentaje = (
        valor / etc
    ) * 100

    if porcentaje >= 5:
        return "Positivo"

    if porcentaje >= -5:
        return "Cercano a equilibrio"

    return "Negativo"


def clasificar_balance_vectorizado(valor, etc):
    """Mismas reglas que clasificar_balance, sobre series completas."""

    sin_datos = valor.isna() | etc.isna() | (etc == 0)

    with np.errstate(divide="ignore", invalid="ignore"):
        porcentaje = valor / etc * 100

    return pd.Series(
        np.select(
            [sin_datos, porcentaje >= 5, porcentaje >= -5],
            ["Sin datos", "Positivo", "Cercano a equilibrio"],
            default="Negativo"
        ),
        index=valor.index
    )


df_etapas["condicion_balance"] = clasificar_balance_vectorizado(
    df_etapas["balance_P_ETc_mm"],
    df_etapas["ETc_mm"]
)


# ============================================================
# CONDICIÓN DESCRIPTIVA DE HUMEDAD
# ============================================================

def clasificar_humedad(percentil):

    if pd.isna(percentil):
        return "Sin datos"

    if percentil < 25:
        return "Relativamente baja"

    if percentil < 50:
        return "Inferior a la mediana"

    if percentil < 75:
        return "Superior a la mediana"

    return "Relativamente alta"


df_etapas["condicion_humedad"] = (
    df_etapas["percentil_humedad_medio"]
    .apply(clasificar_humedad)
)


# ============================================================
# CLASIFICACIÓN TEMPORAL
# ============================================================

def periodo_anio(fecha):

    mes = fecha.month

    if mes in [12, 1, 2]:
        return "Dic-Feb"

    if mes in [3, 4, 5]:
        return "Mar-May"

    if mes in [6, 7, 8]:
        return "Jun-Ago"

    return "Sep-Nov"


df_etapas["periodo_anual"] = (
    df_etapas["fecha_inicio"]
    .apply(periodo_anio)
)


# ============================================================
# ORDENAR
# ============================================================

df_etapas = df_etapas.sort_values(
    [
        "rotacion",
        "fecha_inicio_escenario",
        "numero_etapa"
    ]
)


# ============================================================
# RESUMEN DE CADA ROTACIÓN
# ============================================================

print("\nGenerando resumen de rotaciones...")

claves = ["rotacion", "fecha_inicio_escenario"]

# df_etapas ya está ordenado por (rotacion, fecha_inicio_escenario,
# numero_etapa), así que cada grupo conserva el orden de sus etapas.
grupos = df_etapas.groupby(claves, sort=True)

fecha_inicio_real = grupos["fecha_inicio"].min()
fecha_fin_real = grupos["fecha_fin"].max()
duracion = (fecha_fin_real - fecha_inicio_real).dt.days + 1

precipitacion = grupos["precipitacion_mm"].sum()
eto = grupos["ETo_mm"].sum()
etc = grupos["ETc_mm"].sum()
balance = grupos["balance_P_ETc_mm"].sum()
demanda = grupos["demanda_no_cubierta_mm"].sum()

cobertura = pd.Series(
    np.where(etc > 0, precipitacion / etc * 100, np.nan),
    index=etc.index
)

llaves = [df_etapas[k] for k in claves]
pesos = df_etapas["dias"]
suma_pesos = pesos.groupby(llaves).sum()


def promedio_ponderado(columna):
    """Igual que np.average(grupo[col], weights=grupo['dias']): un NaN
    en el grupo vuelve NaN el promedio."""

    valores = df_etapas[columna]
    numerador = (valores * pesos).groupby(llaves).sum()
    con_nan = valores.isna().groupby(llaves).any()

    return (numerador / suma_pesos).where(~con_nan)


humedad = promedio_ponderado("sm_rootzone_media")
percentil = promedio_ponderado("percentil_humedad_medio")

dias_p10 = grupos["dias_humedad_menor_P10"].sum()
porcentaje_p10 = dias_p10 / duracion * 100

cultivos = grupos["cultivo"].agg(
    lambda serie: " → ".join(serie.astype(str))
)

df_resumen = pd.DataFrame({

    "fecha_inicio_escenario": etc.index.get_level_values(
        "fecha_inicio_escenario"
    ),
    "fecha_fin_escenario": fecha_fin_real.to_numpy(),

    "rotacion": cultivos.to_numpy(),

    "numero_etapas": grupos.size().to_numpy(),
    "duracion_total_dias": duracion.to_numpy(),

    "precipitacion_total_mm": precipitacion.to_numpy(),
    "ETo_total_mm": eto.to_numpy(),
    "ETc_total_mm": etc.to_numpy(),

    "balance_P_ETc_total_mm": balance.to_numpy(),
    "demanda_no_cubierta_total_mm": demanda.to_numpy(),

    "cobertura_precipitacion_pct": cobertura.to_numpy(),

    "sm_rootzone_media": humedad.to_numpy(),
    "percentil_humedad_medio": percentil.to_numpy(),

    "dias_humedad_menor_P10": dias_p10.to_numpy(),
    "porcentaje_dias_menor_P10": porcentaje_p10.to_numpy(),

    "condicion_balance": clasificar_balance_vectorizado(
        balance, etc
    ).to_numpy(),

    "condicion_humedad": percentil.apply(
        clasificar_humedad
    ).to_numpy()
})


# ============================================================
# ORDENAR RESUMEN
# ============================================================

df_resumen = df_resumen.sort_values(
    [
        "fecha_inicio_escenario",
        "rotacion"
    ]
)


# ============================================================
# GUARDAR
# ============================================================

df_etapas.to_csv(
    SALIDA_ETAPAS,
    index=False,
    encoding="utf-8-sig"
)

df_resumen.to_csv(
    SALIDA_RESUMEN,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# MOSTRAR INFORMACIÓN
# ============================================================

print("\n" + "=" * 70)
print("RESULTADOS V8")
print("=" * 70)

print(
    f"\nEtapas analizadas: "
    f"{len(df_etapas)}"
)

print(
    f"Escenarios resumidos: "
    f"{len(df_resumen)}"
)

print(
    f"Rotaciones diferentes: "
    f"{df_resumen['rotacion'].nunique()}"
)


# ============================================================
# DISTRIBUCIÓN DEL BALANCE
# ============================================================

print("\nCondición del balance:")

print(
    df_resumen[
        "condicion_balance"
    ]
    .value_counts()
    .to_string()
)


# ============================================================
# DISTRIBUCIÓN DE HUMEDAD
# ============================================================

print("\nCondición de humedad:")

print(
    df_resumen[
        "condicion_humedad"
    ]
    .value_counts()
    .to_string()
)


# ============================================================
# EJEMPLO: TOMATE → PAPA
# ============================================================

print("\n" + "-" * 70)
print("EJEMPLO: TOMATE → PAPA")
print("-" * 70)

ejemplo = df_etapas[
    df_etapas["rotacion"]
    == "Lycopersicon esculentum → Solanum tuberosum"
]

if not ejemplo.empty:

    columnas = [
        "fecha_inicio_escenario",
        "numero_etapa",
        "cultivo",
        "fecha_inicio",
        "fecha_fin",
        "precipitacion_mm",
        "ETc_mm",
        "balance_P_ETc_mm",
        "cobertura_precipitacion_pct",
        "sm_rootzone_media",
        "percentil_humedad_medio",
        "condicion_balance",
        "condicion_humedad"
    ]

    print(
        ejemplo[columnas]
        .to_string(index=False)
    )

else:

    print(
        "No se encontró la rotación de ejemplo."
    )


# ============================================================
# ARCHIVOS
# ============================================================

print("\nArchivos generados:")

print(
    f"1. {SALIDA_ETAPAS}"
)

print(
    f"2. {SALIDA_RESUMEN}"
)

print("\nProceso terminado.")
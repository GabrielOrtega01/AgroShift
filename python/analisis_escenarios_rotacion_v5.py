import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ANALYSIS_DIR = BASE_DIR / "data" / "analysis"

ARCHIVO_ESCENARIOS = (
    ANALYSIS_DIR / "escenarios_rotacion_2020_v4.csv"
)

ARCHIVO_ETAPAS = (
    ANALYSIS_DIR / "escenarios_rotacion_2020_v4_etapas.csv"
)

ARCHIVO_AMBIENTAL = (
    ANALYSIS_DIR / "agroshift_environmental_2020.csv"
)

SALIDA_ETAPAS = (
    ANALYSIS_DIR / "escenarios_rotacion_2020_v5_etapas.csv"
)

SALIDA_RESUMEN = (
    ANALYSIS_DIR / "escenarios_rotacion_2020_v5.csv"
)

SALIDA_COMPARACION = (
    ANALYSIS_DIR / "comparacion_humedad_etapas_2020_v5.csv"
)


# ============================================================
# INICIO
# ============================================================

print("=" * 75)
print("AGROSHIFT - ANÁLISIS DE ROTACIONES V5")
print("=" * 75)


# ============================================================
# CARGAR DATOS V4
# ============================================================

escenarios = pd.read_csv(
    ARCHIVO_ESCENARIOS
)

etapas = pd.read_csv(
    ARCHIVO_ETAPAS
)

ambiental = pd.read_csv(
    ARCHIVO_AMBIENTAL
)


# ============================================================
# CONVERTIR FECHAS
# ============================================================

etapas["fecha_inicio"] = pd.to_datetime(
    etapas["fecha_inicio"]
)

etapas["fecha_fin"] = pd.to_datetime(
    etapas["fecha_fin"]
)

ambiental["fecha"] = pd.to_datetime(
    ambiental["fecha"]
)


print(f"\nEscenarios V4 cargados: {len(escenarios)}")
print(f"Etapas V4 cargadas: {len(etapas)}")
print(f"Datos ambientales: {len(ambiental)}")


# ============================================================
# DISTRIBUCIÓN ANUAL SMAP
# ============================================================

smap = ambiental[
    "sm_rootzone"
].dropna()

P10 = smap.quantile(0.10)
P25 = smap.quantile(0.25)
P50 = smap.quantile(0.50)
P75 = smap.quantile(0.75)
P90 = smap.quantile(0.90)

print("\nPercentiles SMAP rootzone 2020:")

print(f"  P10 = {P10:.6f}")
print(f"  P25 = {P25:.6f}")
print(f"  P50 = {P50:.6f}")
print(f"  P75 = {P75:.6f}")
print(f"  P90 = {P90:.6f}")


# ============================================================
# FUNCIÓN: PERCENTIL EMPÍRICO
# ============================================================

def percentil_smap(valor):

    if pd.isna(valor):
        return np.nan

    return float(
        (smap <= valor).mean() * 100
    )


# ============================================================
# RECALCULAR INFORMACIÓN SMAP POR ETAPA
# ============================================================

resultados_etapas = []

for _, etapa in etapas.iterrows():

    inicio = etapa["fecha_inicio"]
    fin = etapa["fecha_fin"]

    datos = ambiental[
        (ambiental["fecha"] >= inicio)
        & (ambiental["fecha"] <= fin)
    ].copy()

    if datos.empty:
        continue

    # --------------------------------------------------------
    # Percentil SMAP diario
    # --------------------------------------------------------

    datos["smap_percentil"] = (
        datos["sm_rootzone"]
        .apply(percentil_smap)
    )

    # --------------------------------------------------------
    # Estadísticas SMAP
    # --------------------------------------------------------

    smap_media = datos[
        "sm_rootzone"
    ].mean()

    smap_min = datos[
        "sm_rootzone"
    ].min()

    smap_max = datos[
        "sm_rootzone"
    ].max()

    percentil_medio = datos[
        "smap_percentil"
    ].mean()

    percentil_min = datos[
        "smap_percentil"
    ].min()

    percentil_max = datos[
        "smap_percentil"
    ].max()

    # --------------------------------------------------------
    # Días según percentiles
    # --------------------------------------------------------

    dias_bajo_p10 = (
        datos["sm_rootzone"] < P10
    ).sum()

    dias_p10_p25 = (
        (datos["sm_rootzone"] >= P10)
        &
        (datos["sm_rootzone"] < P25)
    ).sum()

    dias_p25_p50 = (
        (datos["sm_rootzone"] >= P25)
        &
        (datos["sm_rootzone"] < P50)
    ).sum()

    dias_p50_p75 = (
        (datos["sm_rootzone"] >= P50)
        &
        (datos["sm_rootzone"] < P75)
    ).sum()

    dias_p75_p90 = (
        (datos["sm_rootzone"] >= P75)
        &
        (datos["sm_rootzone"] < P90)
    ).sum()

    dias_sobre_p90 = (
        datos["sm_rootzone"] >= P90
    ).sum()

    total_dias = len(datos)

    # --------------------------------------------------------
    # Porcentajes
    # --------------------------------------------------------

    porcentaje_bajo_p10 = (
        dias_bajo_p10 / total_dias * 100
    )

    porcentaje_p10_p25 = (
        dias_p10_p25 / total_dias * 100
    )

    porcentaje_p25_p50 = (
        dias_p25_p50 / total_dias * 100
    )

    porcentaje_p50_p75 = (
        dias_p50_p75 / total_dias * 100
    )

    porcentaje_p75_p90 = (
        dias_p75_p90 / total_dias * 100
    )

    porcentaje_sobre_p90 = (
        dias_sobre_p90 / total_dias * 100
    )

    # --------------------------------------------------------
    # Copiar información V4
    # --------------------------------------------------------

    resultado = etapa.to_dict()

    resultado.update({

        "dias_ambientales_analizados": total_dias,

        "smap_percentil_medio_v5":
            percentil_medio,

        "smap_percentil_min_v5":
            percentil_min,

        "smap_percentil_max_v5":
            percentil_max,

        "sm_rootzone_media_v5":
            smap_media,

        "sm_rootzone_min_v5":
            smap_min,

        "sm_rootzone_max_v5":
            smap_max,

        "dias_smap_bajo_P10":
            dias_bajo_p10,

        "dias_smap_P10_P25":
            dias_p10_p25,

        "dias_smap_P25_P50":
            dias_p25_p50,

        "dias_smap_P50_P75":
            dias_p50_p75,

        "dias_smap_P75_P90":
            dias_p75_p90,

        "dias_smap_sobre_P90":
            dias_sobre_p90,

        "porcentaje_smap_bajo_P10":
            porcentaje_bajo_p10,

        "porcentaje_smap_P10_P25":
            porcentaje_p10_p25,

        "porcentaje_smap_P25_P50":
            porcentaje_p25_p50,

        "porcentaje_smap_P50_P75":
            porcentaje_p50_p75,

        "porcentaje_smap_P75_P90":
            porcentaje_p75_p90,

        "porcentaje_smap_sobre_P90":
            porcentaje_sobre_p90
    })

    resultados_etapas.append(resultado)


# ============================================================
# DATAFRAME DE ETAPAS
# ============================================================

df_etapas = pd.DataFrame(
    resultados_etapas
)

df_etapas = df_etapas.sort_values(
    ["id_escenario", "etapa"]
).reset_index(drop=True)


# ============================================================
# RESUMEN POR ESCENARIO
# ============================================================

resumen = []

for id_escenario, grupo in df_etapas.groupby(
    "id_escenario"
):

    grupo = grupo.sort_values("etapa")

    primera = grupo.iloc[0]

    registro = {
        "id_escenario":
            id_escenario,

        "numero_etapas":
            int(primera["numero_etapas"]),

        "rotacion":
            " → ".join(
                grupo["cultivo"].astype(str)
            ),

        "dias_totales":
            int(grupo["dias"].sum()),

        "precipitacion_total_mm":
            grupo["precipitacion_mm"].sum(),

        "ETo_total_mm":
            grupo["ETo_mm"].sum(),

        "ETc_total_mm":
            grupo["ETc_mm"].sum(),

        "balance_P_ETc_total_mm":
            grupo["balance_P_ETc_mm"].sum(),

        "demanda_no_cubierta_total_mm":
            grupo["demanda_no_cubierta_mm"].sum(),

        "cobertura_precipitacion_pct":
            (
                grupo["precipitacion_mm"].sum()
                /
                grupo["ETc_mm"].sum()
                * 100
            ),

        "temperatura_media_c":
            np.average(
                grupo["temperatura_media_c"],
                weights=grupo["dias"]
            ),

        "indicador_temperatura":
            np.average(
                grupo["indicador_temperatura"],
                weights=grupo["dias"]
            ),

        "sm_rootzone_media":
            np.average(
                grupo["sm_rootzone_media_v5"],
                weights=grupo["dias"]
            ),

        "smap_percentil_medio":
            np.average(
                grupo["smap_percentil_medio_v5"],
                weights=grupo["dias"]
            ),

        "dias_humedad_bajo_P10":
            grupo["dias_smap_bajo_P10"].sum()
    }

    resumen.append(registro)


df_resumen = pd.DataFrame(
    resumen
)


# ============================================================
# COMPARACIÓN DE ETAPAS
# ============================================================

comparacion = df_etapas[
    [
        "id_escenario",
        "numero_etapas",
        "etapa",
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

        "sm_rootzone_media_v5",
        "sm_rootzone_min_v5",
        "sm_rootzone_max_v5",

        "smap_percentil_medio_v5",
        "smap_percentil_min_v5",
        "smap_percentil_max_v5",

        "dias_smap_bajo_P10",
        "porcentaje_smap_bajo_P10",

        "dias_smap_P10_P25",
        "dias_smap_P25_P50",
        "dias_smap_P50_P75",
        "dias_smap_P75_P90",
        "dias_smap_sobre_P90"
    ]
].copy()


# ============================================================
# ORDENAR RESUMEN
# ============================================================

df_resumen = df_resumen.sort_values(
    "cobertura_precipitacion_pct",
    ascending=False
).reset_index(drop=True)


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

comparacion.to_csv(
    SALIDA_COMPARACION,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# MOSTRAR RESULTADOS
# ============================================================

print("\n" + "=" * 75)
print("RESULTADOS V5")
print("=" * 75)

print(
    f"\nEtapas analizadas: {len(df_etapas)}"
)

print(
    f"Escenarios analizados: {len(df_resumen)}"
)


print("\nDetalle de las primeras etapas:\n")

columnas = [
    "id_escenario",
    "etapa",
    "cultivo",
    "fecha_inicio",
    "fecha_fin",
    "dias",

    "precipitacion_mm",
    "ETc_mm",
    "balance_P_ETc_mm",
    "cobertura_precipitacion_pct",

    "sm_rootzone_media_v5",
    "smap_percentil_medio_v5",

    "dias_smap_bajo_P10",
    "porcentaje_smap_bajo_P10"
]

print(
    df_etapas[
        columnas
    ].head(20).to_string(index=False)
)


print("\n" + "-" * 75)

print(
    "Escenarios con mayor cobertura de precipitación:\n"
)

columnas_resumen = [
    "id_escenario",
    "rotacion",
    "dias_totales",
    "precipitacion_total_mm",
    "ETc_total_mm",
    "balance_P_ETc_total_mm",
    "cobertura_precipitacion_pct",
    "sm_rootzone_media",
    "smap_percentil_medio",
    "dias_humedad_bajo_P10"
]

print(
    df_resumen[
        columnas_resumen
    ].head(15).to_string(index=False)
)


# ============================================================
# ARCHIVOS
# ============================================================

print("\n" + "=" * 75)
print("ARCHIVOS GENERADOS")
print("=" * 75)

print(
    f"\n1. {SALIDA_RESUMEN}"
)

print(
    f"2. {SALIDA_ETAPAS}"
)

print(
    f"3. {SALIDA_COMPARACION}"
)

print("\nProceso V5 terminado.")
import os
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agroshift.regions import get_region

REGION = get_region(os.environ.get("AGROSHIFT_REGION", "santander"))
FECHA_INICIO = os.environ.get("AGROSHIFT_FECHA_INICIO", "2020-01-01")
FECHA_FIN = os.environ.get("AGROSHIFT_FECHA_FIN", "2025-12-31")


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ANALYSIS_DIR = BASE_DIR / "data" / "analysis" / REGION.slug
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

POWER_FILE = BASE_DIR / "data" / "power" / f"nasa_power_{REGION.slug}.csv"
SMAP_FILE = ANALYSIS_DIR / "smap_diario_2020.csv"

OUTPUT_FILE = ANALYSIS_DIR / "agroshift_environmental_2020.csv"

SUMMARY_FILE = ANALYSIS_DIR / "agroshift_environmental_2020_resumen.csv"

LATITUD = REGION.latitud
LONGITUD = REGION.longitud


# ============================================================
# 1. CARGAR DATOS
# ============================================================

print("=" * 60)
print("INTEGRACIÓN SMAP + NASA POWER - AGROSHIFT 2020")
print("=" * 60)

print("\nCargando NASA POWER...")
power = pd.read_csv(POWER_FILE)

print(f"Registros NASA POWER cargados: {len(power)}")

print("\nCargando SMAP...")
smap = pd.read_csv(SMAP_FILE)

print(f"Registros SMAP cargados: {len(smap)}")


# ============================================================
# 2. PREPARAR FECHAS
# ============================================================

power["fecha"] = pd.to_datetime(
    power["DATE"],
    errors="coerce"
).dt.date

smap["fecha"] = pd.to_datetime(
    smap["fecha"],
    errors="coerce"
).dt.date


# ============================================================
# 3. FILTRAR AL RANGO SOLICITADO
# ============================================================

fecha_inicio = pd.Timestamp(FECHA_INICIO).date()
fecha_fin = pd.Timestamp(FECHA_FIN).date()

power_2020 = power[
    (power["fecha"] >= fecha_inicio)
    & (power["fecha"] <= fecha_fin)
].copy()

smap_2020 = smap[
    (smap["fecha"] >= fecha_inicio)
    & (smap["fecha"] <= fecha_fin)
].copy()

print("\nDatos después del filtro:")
print(f"NASA POWER: {len(power_2020)} registros")
print(f"SMAP:       {len(smap_2020)} registros")


# ============================================================
# 4. COMPROBAR DUPLICADOS
# ============================================================

duplicados_power = power_2020["fecha"].duplicated().sum()
duplicados_smap = smap_2020["fecha"].duplicated().sum()

print("\nDuplicados:")
print(f"NASA POWER: {duplicados_power}")
print(f"SMAP:       {duplicados_smap}")


# ============================================================
# 5. SELECCIONAR COLUMNAS
# ============================================================

columnas_power = [
    "fecha",
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "PRECTOTCORR",
    "RH2M",
    "WS10M",
    "ALLSKY_SFC_SW_DWN"
]

columnas_power = [
    columna
    for columna in columnas_power
    if columna in power_2020.columns
]

power_2020 = power_2020[columnas_power].copy()


# ============================================================
# 6. INTEGRAR SMAP + NASA POWER
# ============================================================

print("\nIntegrando datasets...")

integrado = pd.merge(
    power_2020,
    smap_2020,
    on="fecha",
    how="outer",
    indicator=True
)


# ============================================================
# 7. VALIDAR INTEGRACIÓN
# ============================================================

solo_power = (integrado["_merge"] == "left_only").sum()
solo_smap = (integrado["_merge"] == "right_only").sum()
coincidentes = (integrado["_merge"] == "both").sum()

print("\nResultado de la integración:")
print(f"Fechas coincidentes: {coincidentes}")
print(f"Solo NASA POWER:     {solo_power}")
print(f"Solo SMAP:           {solo_smap}")

if solo_power > 0 or solo_smap > 0:
    print("\nADVERTENCIA: existen fechas que no coinciden.")

    if solo_power > 0:
        print("\nFechas presentes solo en NASA POWER:")
        print(
            integrado.loc[
                integrado["_merge"] == "left_only",
                "fecha"
            ].tolist()
        )

    if solo_smap > 0:
        print("\nFechas presentes solo en SMAP:")
        print(
            integrado.loc[
                integrado["_merge"] == "right_only",
                "fecha"
            ].tolist()
        )

else:
    print("✓ Todas las fechas coinciden.")


# El indicador ya no es necesario
integrado.drop(columns=["_merge"], inplace=True)


# ============================================================
# 8. AGREGAR UBICACIÓN
# ============================================================

integrado.insert(
    1,
    "latitud",
    LATITUD
)

integrado.insert(
    2,
    "longitud",
    LONGITUD
)


# ============================================================
# 9. ORDENAR
# ============================================================

integrado.sort_values(
    "fecha",
    inplace=True
)

integrado.reset_index(
    drop=True,
    inplace=True
)


# ============================================================
# 10. REVISAR VALORES FALTANTES
# ============================================================

print("\nValores faltantes:")

faltantes = integrado.isna().sum()

faltantes = faltantes[
    faltantes > 0
]

if len(faltantes) == 0:
    print("✓ No hay valores faltantes.")
else:
    print(faltantes)


# ============================================================
# 11. GUARDAR DATASET INTEGRADO
# ============================================================

integrado.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nDataset integrado guardado en:")
print(OUTPUT_FILE)

print(f"\nTotal de registros: {len(integrado)}")
print(f"Total de columnas:  {len(integrado.columns)}")


# ============================================================
# 12. RESUMEN MENSUAL
# ============================================================

print("\nGenerando resumen mensual...")

integrado["mes"] = pd.to_datetime(
    integrado["fecha"]
).dt.to_period("M")


resumen_mensual = (
    integrado
    .groupby("mes")
    .agg(
        temperatura_media=("T2M", "mean"),
        temperatura_maxima=("T2M_MAX", "max"),
        temperatura_minima=("T2M_MIN", "min"),
        precipitacion_total=("PRECTOTCORR", "sum"),
        humedad_relativa_media=("RH2M", "mean"),
        viento_medio=("WS10M", "mean"),
        radiacion_media=("ALLSKY_SFC_SW_DWN", "mean"),
        humedad_suelo_superficial_media=("sm_surface", "mean"),
        humedad_suelo_superficial_min=("sm_surface", "min"),
        humedad_suelo_superficial_max=("sm_surface", "max"),
        humedad_suelo_raiz_media=("sm_rootzone", "mean"),
        humedad_suelo_raiz_min=("sm_rootzone", "min"),
        humedad_suelo_raiz_max=("sm_rootzone", "max"),
        temperatura_suelo_media=("soil_temp_layer1_celsius", "mean"),
        temperatura_suelo_min=("soil_temp_layer1_celsius", "min"),
        temperatura_suelo_max=("soil_temp_layer1_celsius", "max"),
    )
    .reset_index()
)


resumen_mensual["mes"] = resumen_mensual[
    "mes"
].astype(str)


resumen_mensual.to_csv(
    SUMMARY_FILE,
    index=False
)

print("Resumen mensual guardado en:")
print(SUMMARY_FILE)


# ============================================================
# 13. ESTADÍSTICAS GENERALES
# ============================================================

print("\n" + "=" * 60)
print("RESUMEN GENERAL 2020")
print("=" * 60)

print(
    f"\nPeriodo: "
    f"{integrado['fecha'].min()} -> "
    f"{integrado['fecha'].max()}"
)

print(f"Días analizados: {len(integrado)}")

print(
    f"\nTemperatura media: "
    f"{integrado['T2M'].mean():.2f} °C"
)

print(
    f"Temperatura máxima registrada: "
    f"{integrado['T2M_MAX'].max():.2f} °C"
)

print(
    f"Temperatura mínima registrada: "
    f"{integrado['T2M_MIN'].min():.2f} °C"
)

print(
    f"\nPrecipitación acumulada: "
    f"{integrado['PRECTOTCORR'].sum():.2f} mm"
)

print(
    f"Precipitación media diaria: "
    f"{integrado['PRECTOTCORR'].mean():.2f} mm"
)

print(
    f"\nHumedad relativa media: "
    f"{integrado['RH2M'].mean():.2f} %"
)

print(
    f"Humedad superficial del suelo media: "
    f"{integrado['sm_surface'].mean():.4f} m³/m³"
)

print(
    f"Humedad de la zona radicular media: "
    f"{integrado['sm_rootzone'].mean():.4f} m³/m³"
)

print(
    f"Temperatura media del suelo: "
    f"{integrado['soil_temp_layer1_celsius'].mean():.2f} °C"
)


# ============================================================
# 14. MOSTRAR PRIMEROS REGISTROS
# ============================================================

print("\nPrimeros 5 registros:")

print(
    integrado.head().to_string(
        index=False
    )
)

print("\n" + "=" * 60)
print("✓ INTEGRACIÓN COMPLETADA")
print("=" * 60)
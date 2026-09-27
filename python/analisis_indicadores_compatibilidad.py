import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ARCHIVO_AMBIENTAL = (
    BASE_DIR / "data" / "analysis" / "agroshift_environmental_2020.csv"
)

ARCHIVO_ECOCROP = (
    BASE_DIR / "data" / "crops" / "agroshift_cultivos_caracteristicas.csv"
)

ARCHIVO_HIDRICO = (
    BASE_DIR / "data" / "analysis" / "estado_hidrico_cultivos_2020.csv"
)

CARPETA_SALIDA = BASE_DIR / "data" / "analysis"


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def puntuacion_rango(valor, minimo, maximo, absoluto_min=None, absoluto_max=None):
    """
    Calcula una puntuación 0-100 para un valor respecto
    a un rango óptimo y un rango absoluto.

    100 = dentro del rango óptimo
    50-99 = fuera del óptimo pero dentro del absoluto
    0-49 = cerca/fuera del límite absoluto
    0 = fuera del rango absoluto
    """

    if pd.isna(valor) or pd.isna(minimo) or pd.isna(maximo):
        return np.nan

    # Dentro del rango óptimo
    if minimo <= valor <= maximo:
        return 100.0

    # Si no hay límites absolutos, simplemente penalizamos
    if pd.isna(absoluto_min) or pd.isna(absoluto_max):
        if valor < minimo:
            distancia = minimo - valor
            rango = maximo - minimo
        else:
            distancia = valor - maximo
            rango = maximo - minimo

        if rango == 0:
            return 0.0

        return max(0.0, 100.0 - (distancia / rango) * 50.0)

    # Fuera del rango absoluto
    if valor < absoluto_min or valor > absoluto_max:
        return 0.0

    # Entre absoluto mínimo y óptimo mínimo
    if valor < minimo:
        distancia_total = minimo - absoluto_min

        if distancia_total <= 0:
            return 50.0

        distancia = valor - absoluto_min

        return 50.0 + (distancia / distancia_total) * 50.0

    # Entre óptimo máximo y absoluto máximo
    if valor > maximo:
        distancia_total = absoluto_max - maximo

        if distancia_total <= 0:
            return 50.0

        distancia = absoluto_max - valor

        return 50.0 + (distancia / distancia_total) * 50.0

    return 100.0


def clasificar_indice(valor):
    """Clasificación descriptiva del índice."""

    if pd.isna(valor):
        return "Sin datos"

    if valor >= 90:
        return "Muy alta"
    elif valor >= 75:
        return "Alta"
    elif valor >= 60:
        return "Media"
    elif valor >= 40:
        return "Baja"
    else:
        return "Muy baja"


# ============================================================
# INICIO
# ============================================================

print("=" * 70)
print("AGROSHIFT - INDICADORES DE COMPATIBILIDAD AMBIENTAL")
print("=" * 70)


# ============================================================
# 1. CARGAR DATOS AMBIENTALES
# ============================================================

print("\nCargando datos ambientales...")

ambiental = pd.read_csv(ARCHIVO_AMBIENTAL)

ambiental["fecha"] = pd.to_datetime(
    ambiental["fecha"],
    errors="coerce"
)

print(f"✓ Datos ambientales: {len(ambiental)} registros")


# ============================================================
# 2. CARGAR ECOCROP
# ============================================================

print("\nCargando características ECOCROP...")

ecocrop = pd.read_csv(ARCHIVO_ECOCROP)

print(f"✓ Cultivos ECOCROP: {len(ecocrop)} registros")


# ============================================================
# 3. CARGAR ESTADO HÍDRICO
# ============================================================

print("\nCargando estado hídrico...")

hidrico = pd.read_csv(ARCHIVO_HIDRICO)

hidrico["fecha"] = pd.to_datetime(
    hidrico["fecha"],
    errors="coerce"
)

print(f"✓ Registros estado hídrico: {len(hidrico)}")


# ============================================================
# 4. CULTIVOS A ANALIZAR
# ============================================================

cultivos_prueba = [
    "Coffea arabica",
    "Lycopersicon esculentum",
    "Manihot esculenta",
    "Oryza sativa",
    "Phaseolus vulgaris",
    "Saccharum officinarum",
    "Solanum tuberosum",
    "Zea mays"
]

ecocrop = ecocrop[
    ecocrop["nombre"].isin(cultivos_prueba)
].copy()

hidrico = hidrico[
    hidrico["cultivo"].isin(cultivos_prueba)
].copy()

print(f"✓ Cultivos seleccionados: {len(ecocrop)}")


# ============================================================
# 5. INDICADORES AMBIENTALES GENERALES
# ============================================================

print("\nCalculando indicadores ambientales...")


# Temperatura media del periodo
temperatura_media = ambiental["T2M"].mean()

# Temperatura máxima observada
temperatura_maxima = ambiental["T2M_MAX"].max()

# Temperatura mínima observada
temperatura_minima = ambiental["T2M_MIN"].min()

# Precipitación acumulada
precipitacion_total = ambiental["PRECTOTCORR"].sum()

# Precipitación media diaria
precipitacion_media = ambiental["PRECTOTCORR"].mean()

print(f"Temperatura media: {temperatura_media:.2f} °C")
print(f"Temperatura mínima observada: {temperatura_minima:.2f} °C")
print(f"Temperatura máxima observada: {temperatura_maxima:.2f} °C")
print(f"Precipitación acumulada: {precipitacion_total:.2f} mm")
print(f"Precipitación media diaria: {precipitacion_media:.2f} mm/día")


# ============================================================
# 6. CÁLCULO POR CULTIVO
# ============================================================

resultados = []

for _, cultivo in ecocrop.iterrows():

    nombre = cultivo["nombre"]

    print(f"\nAnalizando: {nombre}")

    datos_hidricos = hidrico[
        hidrico["cultivo"] == nombre
    ].copy()

    if datos_hidricos.empty:
        print("  ⚠ No hay datos hídricos")
        continue

    # --------------------------------------------------------
    # TEMPERATURA
    # --------------------------------------------------------

    puntuacion_temperatura = puntuacion_rango(
        temperatura_media,
        cultivo["temperatura_optima_min_c"],
        cultivo["temperatura_optima_max_c"],
        cultivo["temperatura_absoluta_min_c"],
        cultivo["temperatura_absoluta_max_c"]
    )

    # --------------------------------------------------------
    # PRECIPITACIÓN
    # --------------------------------------------------------

    puntuacion_precipitacion = puntuacion_rango(
        precipitacion_total,
        cultivo["precipitacion_optima_min_mm"],
        cultivo["precipitacion_optima_max_mm"],
        cultivo["precipitacion_absoluta_min_mm"],
        cultivo["precipitacion_absoluta_max_mm"]
    )

    # --------------------------------------------------------
    # ESTADO HÍDRICO
    # --------------------------------------------------------

    demanda_media = datos_hidricos[
        "demanda_no_cubierta"
    ].mean()

    demanda_total = datos_hidricos[
        "demanda_no_cubierta"
    ].sum()

    et_c_total = datos_hidricos[
        "ETc"
    ].sum()

    precipitacion_cultivo = datos_hidricos[
        "PRECTOTCORR"
    ].sum()

    humedad_raiz_media = datos_hidricos[
        "sm_rootzone"
    ].mean()

    humedad_raiz_min = datos_hidricos[
        "sm_rootzone"
    ].min()

    humedad_raiz_max = datos_hidricos[
        "sm_rootzone"
    ].max()

    humedad_relativa_media = datos_hidricos[
        "sm_rootzone_wetness"
    ].mean()

    # --------------------------------------------------------
    # DEMANDA HÍDRICA
    # --------------------------------------------------------

    porcentaje_demanda = (
        datos_hidricos["demanda_no_cubierta"] > 0
    ).mean() * 100

    porcentaje_humedad_baja = (
        datos_hidricos["estado_humedad_relativo"] == "Baja"
    ).mean() * 100

    porcentaje_demanda_humedad = (
        datos_hidricos["condicion_hidrica_observada"]
        .astype(str)
        .str.startswith("Demanda +")
    ).mean() * 100

    # --------------------------------------------------------
    # INDICADOR HÍDRICO
    # --------------------------------------------------------

    # Proporción de días sin demanda no cubierta
    cobertura_demanda = max(
        0.0,
        min(
            100.0,
            100.0 - porcentaje_demanda
        )
    )

    # Penalización descriptiva por condiciones
    penalizacion_humedad = min(
        50.0,
        porcentaje_humedad_baja
    )

    indicador_hidrico = max(
        0.0,
        cobertura_demanda - penalizacion_humedad * 0.5
    )

    # --------------------------------------------------------
    # ÍNDICE GLOBAL
    # --------------------------------------------------------

    componentes = [
        puntuacion_temperatura,
        puntuacion_precipitacion,
        indicador_hidrico
    ]

    componentes_validos = [
        valor for valor in componentes
        if not pd.isna(valor)
    ]

    if componentes_validos:
        indice_global = np.mean(componentes_validos)
    else:
        indice_global = np.nan

    # --------------------------------------------------------
    # CLASIFICACIÓN
    # --------------------------------------------------------

    clasificacion = clasificar_indice(
        indice_global
    )

    resultados.append({
        "cultivo": nombre,

        "ecocrop_id": cultivo["ecocrop_id"],

        "temperatura_media_sitio_c": temperatura_media,

        "temperatura_optima_min_c":
            cultivo["temperatura_optima_min_c"],

        "temperatura_optima_max_c":
            cultivo["temperatura_optima_max_c"],

        "indicador_temperatura": puntuacion_temperatura,

        "precipitacion_total_mm": precipitacion_total,

        "precipitacion_optima_min_mm":
            cultivo["precipitacion_optima_min_mm"],

        "precipitacion_optima_max_mm":
            cultivo["precipitacion_optima_max_mm"],

        "indicador_precipitacion":
            puntuacion_precipitacion,

        "ETc_total_mm":
            et_c_total,

        "precipitacion_cultivo_mm":
            precipitacion_cultivo,

        "demanda_no_cubierta_total_mm":
            demanda_total,

        "demanda_no_cubierta_media_mm_dia":
            demanda_media,

        "porcentaje_dias_demanda_no_cubierta":
            porcentaje_demanda,

        "sm_rootzone_media_m3_m3":
            humedad_raiz_media,

        "sm_rootzone_min_m3_m3":
            humedad_raiz_min,

        "sm_rootzone_max_m3_m3":
            humedad_raiz_max,

        "sm_rootzone_wetness_media":
            humedad_relativa_media,

        "porcentaje_dias_humedad_baja":
            porcentaje_humedad_baja,

        "porcentaje_dias_demanda_humedad":
            porcentaje_demanda_humedad,

        "indicador_hidrico":
            indicador_hidrico,

        "indice_compatibilidad_ambiental":
            indice_global,

        "clasificacion":
            clasificacion,

        "ciclo_min_dias":
            cultivo["ciclo_min_dias"],

        "ciclo_max_dias":
            cultivo["ciclo_max_dias"]
    })


# ============================================================
# 7. CREAR DATAFRAME
# ============================================================

resultado = pd.DataFrame(resultados)

resultado = resultado.sort_values(
    "indice_compatibilidad_ambiental",
    ascending=False
)


# ============================================================
# 8. GUARDAR RESULTADOS
# ============================================================

archivo_salida = (
    CARPETA_SALIDA /
    "indicadores_compatibilidad_2020.csv"
)

resultado.to_csv(
    archivo_salida,
    index=False,
    encoding="utf-8-sig"
)

print("\n" + "=" * 70)
print("RESULTADO")
print("=" * 70)

print(
    resultado[
        [
            "cultivo",
            "indicador_temperatura",
            "indicador_precipitacion",
            "indicador_hidrico",
            "indice_compatibilidad_ambiental",
            "clasificacion"
        ]
    ].to_string(index=False)
)

print("\n✓ Archivo generado:")
print(archivo_salida)


# ============================================================
# 9. GRÁFICO
# ============================================================

plt.figure(figsize=(12, 6))

plt.bar(
    resultado["cultivo"],
    resultado["indice_compatibilidad_ambiental"]
)

plt.axhline(
    75,
    linestyle="--",
    linewidth=1
)

plt.axhline(
    60,
    linestyle="--",
    linewidth=1
)

plt.ylim(0, 105)

plt.ylabel("Índice de compatibilidad ambiental (0-100)")
plt.xlabel("Cultivo")
plt.title(
    "AgroShift - Compatibilidad ambiental de cultivos (2020)"
)

plt.xticks(
    rotation=45,
    ha="right"
)

plt.tight_layout()

archivo_grafico = (
    CARPETA_SALIDA /
    "compatibilidad_cultivos_2020.png"
)

plt.savefig(
    archivo_grafico,
    dpi=150
)

plt.close()

print("✓ Gráfico generado:")
print(archivo_grafico)

print("\n" + "=" * 70)
print("✓ PROCESO COMPLETADO")
print("=" * 70)
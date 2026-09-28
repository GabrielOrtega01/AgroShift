import sys
import os
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agroshift.regions import get_region

REGION_SLUG = get_region(os.environ.get("AGROSHIFT_REGION", "santander")).slug


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RUTA_ECOCROP = os.path.join(
    BASE_DIR,
    "data",
    "crops",
    "agroshift_cultivos_caracteristicas.csv"
)

RUTA_AMBIENTAL = os.path.join(
    BASE_DIR,
    "data",
    "analysis",
    REGION_SLUG,
    "agroshift_environmental_2020.csv"
)

RUTA_SALIDA = os.path.join(
    BASE_DIR,
    "data",
    "analysis",
    REGION_SLUG,
    "compatibilidad_cultivos_ecocrop_2020.csv"
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def convertir_numerico(df, columnas):
    """
    Convierte las columnas indicadas a valores numéricos.
    Los valores que no puedan convertirse pasan a NaN.
    """
    for columna in columnas:
        if columna in df.columns:
            df[columna] = pd.to_numeric(
                df[columna],
                errors="coerce"
            )

    return df


def puntaje_rango(valor, opt_min, opt_max, abs_min, abs_max):
    """
    Calcula un puntaje de 0 a 100 para un valor respecto
    a un rango óptimo y un rango absoluto.

    100 = dentro del rango óptimo
    0   = fuera del rango absoluto

    Entre óptimo y absoluto se aplica una reducción gradual.

    IMPORTANTE:
    Este puntaje es un indicador matemático de compatibilidad,
    no una recomendación agronómica.
    """

    valores = [
        valor,
        opt_min,
        opt_max,
        abs_min,
        abs_max
    ]

    if any(pd.isna(v) for v in valores):
        return np.nan

    # Caso ideal
    if opt_min <= valor <= opt_max:
        return 100.0

    # Fuera del rango absoluto
    if valor < abs_min or valor > abs_max:
        return 0.0

    # Entre absoluto mínimo y óptimo mínimo
    if abs_min <= valor < opt_min:
        distancia = opt_min - abs_min

        if distancia == 0:
            return 100.0

        return 100.0 * (valor - abs_min) / distancia

    # Entre óptimo máximo y absoluto máximo
    if opt_max < valor <= abs_max:
        distancia = abs_max - opt_max

        if distancia == 0:
            return 100.0

        return 100.0 * (abs_max - valor) / distancia

    return np.nan


def clasificar_puntaje(puntaje):
    """
    Clasificación descriptiva del indicador.
    No representa una recomendación agronómica.
    """

    if pd.isna(puntaje):
        return "Sin datos"

    if puntaje >= 80:
        return "Alta compatibilidad"

    if puntaje >= 50:
        return "Compatibilidad intermedia"

    if puntaje > 0:
        return "Compatibilidad baja"

    return "Fuera del rango"


# ============================================================
# CARGA DE DATOS
# ============================================================

print("=" * 70)
print("AGROSHIFT - ANÁLISIS PRELIMINAR DE COMPATIBILIDAD")
print("=" * 70)

print("\nCargando ECOCROP...")

ecocrop = pd.read_csv(
    RUTA_ECOCROP,
    encoding="utf-8-sig"
)

print(f"✓ Cultivos cargados: {len(ecocrop)}")


print("\nCargando datos ambientales NASA 2020...")

ambiental = pd.read_csv(
    RUTA_AMBIENTAL,
    encoding="utf-8-sig"
)

print(f"✓ Registros ambientales: {len(ambiental)}")


# ============================================================
# VALIDACIÓN DE COLUMNAS
# ============================================================

columnas_ecocrop_requeridas = [
    "ecocrop_id",
    "nombre",
    "temperatura_optima_min_c",
    "temperatura_optima_max_c",
    "temperatura_absoluta_min_c",
    "temperatura_absoluta_max_c",
    "precipitacion_optima_min_mm",
    "precipitacion_optima_max_mm",
    "precipitacion_absoluta_min_mm",
    "precipitacion_absoluta_max_mm"
]

faltantes = [
    columna
    for columna in columnas_ecocrop_requeridas
    if columna not in ecocrop.columns
]

if faltantes:
    print("\nERROR: faltan columnas en ECOCROP:")
    for columna in faltantes:
        print(f"  - {columna}")

    raise SystemExit(1)


columnas_ambientales_requeridas = [
    "T2M",
    "PRECTOTCORR"
]

faltantes_ambientales = [
    columna
    for columna in columnas_ambientales_requeridas
    if columna not in ambiental.columns
]

if faltantes_ambientales:
    print("\nERROR: faltan columnas en los datos ambientales:")
    for columna in faltantes_ambientales:
        print(f"  - {columna}")

    raise SystemExit(1)


# ============================================================
# CONVERSIÓN NUMÉRICA
# ============================================================

columnas_numericas_ecocrop = [
    "temperatura_optima_min_c",
    "temperatura_optima_max_c",
    "temperatura_absoluta_min_c",
    "temperatura_absoluta_max_c",
    "precipitacion_optima_min_mm",
    "precipitacion_optima_max_mm",
    "precipitacion_absoluta_min_mm",
    "precipitacion_absoluta_max_mm",
    "ph_optimo_min",
    "ph_optimo_max",
    "ph_absoluto_min",
    "ph_absoluto_max",
    "ciclo_min_dias",
    "ciclo_max_dias"
]

ecocrop = convertir_numerico(
    ecocrop,
    columnas_numericas_ecocrop
)


ambiental = convertir_numerico(
    ambiental,
    [
        "T2M",
        "T2M_MAX",
        "T2M_MIN",
        "PRECTOTCORR",
        "RH2M",
        "WS10M",
        "ALLSKY_SFC_SW_DWN",
        "sm_surface",
        "sm_rootzone",
        "soil_temp_layer1_celsius"
    ]
)


# ============================================================
# RESUMEN AMBIENTAL 2020
# ============================================================

temperatura_media = ambiental["T2M"].mean()

temperatura_minima_observada = ambiental["T2M_MIN"].min()

temperatura_maxima_observada = ambiental["T2M_MAX"].max()

precipitacion_anual = ambiental["PRECTOTCORR"].sum()

precipitacion_media_diaria = ambiental["PRECTOTCORR"].mean()

humedad_suelo_media = (
    ambiental["sm_surface"].mean()
    if "sm_surface" in ambiental.columns
    else np.nan
)

humedad_raiz_media = (
    ambiental["sm_rootzone"].mean()
    if "sm_rootzone" in ambiental.columns
    else np.nan
)

temperatura_suelo_media = (
    ambiental["soil_temp_layer1_celsius"].mean()
    if "soil_temp_layer1_celsius" in ambiental.columns
    else np.nan
)


print("\n" + "-" * 70)
print("RESUMEN AMBIENTAL NASA - 2020")
print("-" * 70)

print(f"Temperatura media:       {temperatura_media:.2f} °C")
print(f"Temperatura mínima:      {temperatura_minima_observada:.2f} °C")
print(f"Temperatura máxima:      {temperatura_maxima_observada:.2f} °C")
print(f"Precipitación acumulada: {precipitacion_anual:.2f} mm")
print(f"Precipitación diaria media: {precipitacion_media_diaria:.2f} mm")
print(f"Humedad suelo superficial media: {humedad_suelo_media:.4f}")
print(f"Humedad suelo raíz media:         {humedad_raiz_media:.4f}")
print(f"Temperatura suelo media:          {temperatura_suelo_media:.2f} °C")


# ============================================================
# CÁLCULO POR CULTIVO
# ============================================================

resultados = []

for _, cultivo in ecocrop.iterrows():

    nombre = cultivo["nombre"]

    # --------------------------------------------------------
    # TEMPERATURA
    # --------------------------------------------------------

    puntaje_temperatura_media = puntaje_rango(
        temperatura_media,
        cultivo["temperatura_optima_min_c"],
        cultivo["temperatura_optima_max_c"],
        cultivo["temperatura_absoluta_min_c"],
        cultivo["temperatura_absoluta_max_c"]
    )

    # Porcentaje de días dentro del rango óptimo
    dias_temperatura_optima = (
        (
            ambiental["T2M"]
            >= cultivo["temperatura_optima_min_c"]
        )
        &
        (
            ambiental["T2M"]
            <= cultivo["temperatura_optima_max_c"]
        )
    ).mean() * 100

    # Porcentaje de días dentro del rango absoluto
    dias_temperatura_absoluta = (
        (
            ambiental["T2M"]
            >= cultivo["temperatura_absoluta_min_c"]
        )
        &
        (
            ambiental["T2M"]
            <= cultivo["temperatura_absoluta_max_c"]
        )
    ).mean() * 100

    # --------------------------------------------------------
    # PRECIPITACIÓN
    # --------------------------------------------------------

    puntaje_precipitacion = puntaje_rango(
        precipitacion_anual,
        cultivo["precipitacion_optima_min_mm"],
        cultivo["precipitacion_optima_max_mm"],
        cultivo["precipitacion_absoluta_min_mm"],
        cultivo["precipitacion_absoluta_max_mm"]
    )

    # --------------------------------------------------------
    # COMPATIBILIDAD CLIMÁTICA
    # --------------------------------------------------------
    #
    # 60% temperatura
    # 40% precipitación
    #
    # Este peso es una decisión metodológica del indicador,
    # no un peso proporcionado por ECOCROP.
    # --------------------------------------------------------

    if (
        not pd.isna(puntaje_temperatura_media)
        and not pd.isna(puntaje_precipitacion)
    ):
        compatibilidad_climatica = (
            puntaje_temperatura_media * 0.60
            +
            puntaje_precipitacion * 0.40
        )
    else:
        compatibilidad_climatica = np.nan

    resultados.append({

        "ecocrop_id": cultivo["ecocrop_id"],

        "nombre": nombre,

        # ---------------------------------------------
        # CONDICIONES NASA
        # ---------------------------------------------

        "temperatura_media_2020_c": temperatura_media,

        "temperatura_minima_2020_c": temperatura_minima_observada,

        "temperatura_maxima_2020_c": temperatura_maxima_observada,

        "precipitacion_anual_2020_mm": precipitacion_anual,

        "precipitacion_media_diaria_2020_mm":
            precipitacion_media_diaria,

        "humedad_suelo_superficial_media":
            humedad_suelo_media,

        "humedad_suelo_raiz_media":
            humedad_raiz_media,

        "temperatura_suelo_media_c":
            temperatura_suelo_media,

        # ---------------------------------------------
        # RANGOS ECOCROP
        # ---------------------------------------------

        "temperatura_optima_min_c":
            cultivo["temperatura_optima_min_c"],

        "temperatura_optima_max_c":
            cultivo["temperatura_optima_max_c"],

        "temperatura_absoluta_min_c":
            cultivo["temperatura_absoluta_min_c"],

        "temperatura_absoluta_max_c":
            cultivo["temperatura_absoluta_max_c"],

        "precipitacion_optima_min_mm":
            cultivo["precipitacion_optima_min_mm"],

        "precipitacion_optima_max_mm":
            cultivo["precipitacion_optima_max_mm"],

        "precipitacion_absoluta_min_mm":
            cultivo["precipitacion_absoluta_min_mm"],

        "precipitacion_absoluta_max_mm":
            cultivo["precipitacion_absoluta_max_mm"],

        # ---------------------------------------------
        # INDICADORES
        # ---------------------------------------------

        "puntaje_temperatura_media":
            round(puntaje_temperatura_media, 2),

        "dias_temperatura_optima_pct":
            round(dias_temperatura_optima, 2),

        "dias_temperatura_absoluta_pct":
            round(dias_temperatura_absoluta, 2),

        "puntaje_precipitacion":
            round(puntaje_precipitacion, 2),

        "compatibilidad_climatica":
            round(compatibilidad_climatica, 2),

        # ---------------------------------------------
        # DATOS DEL CULTIVO
        # ---------------------------------------------

        "ph_optimo_min":
            cultivo.get("ph_optimo_min", np.nan),

        "ph_optimo_max":
            cultivo.get("ph_optimo_max", np.nan),

        "ph_absoluto_min":
            cultivo.get("ph_absoluto_min", np.nan),

        "ph_absoluto_max":
            cultivo.get("ph_absoluto_max", np.nan),

        "ciclo_min_dias":
            cultivo.get("ciclo_min_dias", np.nan),

        "ciclo_max_dias":
            cultivo.get("ciclo_max_dias", np.nan),

        "profundidad_suelo_optima":
            cultivo.get("profundidad_suelo_optima", np.nan),

        "profundidad_suelo_absoluta":
            cultivo.get("profundidad_suelo_absoluta", np.nan),

        "fertilidad_suelo_optima":
            cultivo.get("fertilidad_suelo_optima", np.nan),

        "fertilidad_suelo_absoluta":
            cultivo.get("fertilidad_suelo_absoluta", np.nan),

        "salinidad_suelo_optima":
            cultivo.get("salinidad_suelo_optima", np.nan),

        "salinidad_suelo_absoluta":
            cultivo.get("salinidad_suelo_absoluta", np.nan),

        "drenaje_suelo_optimo":
            cultivo.get("drenaje_suelo_optimo", np.nan),

        "drenaje_suelo_absoluto":
            cultivo.get("drenaje_suelo_absoluto", np.nan)
    })


# ============================================================
# DATAFRAME FINAL
# ============================================================

resultado = pd.DataFrame(resultados)

resultado = resultado.sort_values(
    by="compatibilidad_climatica",
    ascending=False
).reset_index(drop=True)


# ============================================================
# GUARDAR
# ============================================================

resultado.to_csv(
    RUTA_SALIDA,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# MOSTRAR RESULTADOS
# ============================================================

print("\n" + "=" * 70)
print("RESULTADO DE COMPATIBILIDAD PRELIMINAR")
print("=" * 70)

columnas_mostrar = [
    "nombre",
    "puntaje_temperatura_media",
    "dias_temperatura_optima_pct",
    "puntaje_precipitacion",
    "compatibilidad_climatica",
    "ciclo_min_dias",
    "ciclo_max_dias"
]

print(
    resultado[columnas_mostrar].to_string(
        index=False
    )
)


# ============================================================
# VALIDACIÓN
# ============================================================

print("\n" + "-" * 70)
print("VALIDACIÓN")
print("-" * 70)

print(f"✓ Cultivos analizados: {len(resultado)}")

print(
    f"✓ Compatibilidad climática calculada: "
    f"{resultado['compatibilidad_climatica'].notna().sum()}"
)

print(
    f"✓ Archivo generado:\n"
    f"{RUTA_SALIDA}"
)

print("\n" + "=" * 70)
print("✓ PROCESO COMPLETADO")
print("=" * 70)
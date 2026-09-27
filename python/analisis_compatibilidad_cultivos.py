from pathlib import Path

import pandas as pd
import numpy as np


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ENVIRONMENTAL_FILE = (
    BASE_DIR
    / "data"
    / "analysis"
    / "agroshift_environmental_2020.csv"
)

CROPS_FILE = (
    BASE_DIR
    / "data"
    / "crops"
    / "agroshift_crops.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "analysis"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "compatibilidad_cultivos_2020.csv"
)

OUTPUT_MONTHLY_FILE = (
    OUTPUT_DIR
    / "compatibilidad_mensual_cultivos_2020.csv"
)


# ============================================================
# FUNCIONES
# ============================================================

def indicador_temperatura(
    temperatura,
    temperatura_min,
    temperatura_optima_min,
    temperatura_optima_max,
    temperatura_max
):
    """
    Calcula un indicador de compatibilidad térmica entre 0 y 1.

    1.0 = temperatura dentro del rango óptimo.
    0.0 = temperatura fuera del rango mínimo/máximo.
    Valores intermedios = transición hacia/desde el rango óptimo.
    """

    if pd.isna(temperatura):
        return np.nan

    if temperatura_min >= temperatura_max:
        return np.nan

    if (
        temperatura_optima_min > temperatura_optima_max
        or temperatura_optima_min < temperatura_min
        or temperatura_optima_max > temperatura_max
    ):
        return np.nan

    # Dentro del rango óptimo
    if (
        temperatura_optima_min
        <= temperatura
        <= temperatura_optima_max
    ):
        return 1.0

    # Por debajo del óptimo
    if temperatura < temperatura_optima_min:

        distancia = (
            temperatura_optima_min
            - temperatura_min
        )

        if distancia <= 0:
            return 0.0

        indicador = (
            temperatura - temperatura_min
        ) / distancia

        return float(
            np.clip(indicador, 0, 1)
        )

    # Por encima del óptimo
    distancia = (
        temperatura_max
        - temperatura_optima_max
    )

    if distancia <= 0:
        return 0.0

    indicador = (
        temperatura_max - temperatura
    ) / distancia

    return float(
        np.clip(indicador, 0, 1)
    )


def indicador_agua(
    precipitacion,
    agua_min,
    agua_max
):
    """
    Indicador simplificado de disponibilidad de agua.

    Compara la precipitación acumulada observada
    durante el periodo con el rango de agua
    documentado para el cultivo.

    Este indicador es exploratorio y NO representa
    un balance hídrico completo.
    """

    if pd.isna(precipitacion):
        return np.nan

    if agua_min <= 0 or agua_max <= agua_min:
        return np.nan

    if agua_min <= precipitacion <= agua_max:
        return 1.0

    if precipitacion < agua_min:

        indicador = (
            precipitacion / agua_min
        )

        return float(
            np.clip(indicador, 0, 1)
        )

    # Si supera el máximo, no penalizamos
    # automáticamente por exceso porque la
    # precipitación no equivale directamente
    # a exceso hídrico en el suelo.

    return 1.0


def calcular_indicador_humedad_suelo(
    humedad,
    humedad_min,
    humedad_max
):
    """
    Indicador relativo de humedad del suelo.

    Esta función se utiliza solamente si el CSV
    de cultivos contiene los parámetros opcionales
    humedad_suelo_min y humedad_suelo_max.
    """

    if pd.isna(humedad):
        return np.nan

    if (
        pd.isna(humedad_min)
        or pd.isna(humedad_max)
    ):
        return np.nan

    if humedad_max <= humedad_min:
        return np.nan

    if humedad_min <= humedad <= humedad_max:
        return 1.0

    if humedad < humedad_min:

        indicador = (
            humedad / humedad_min
        )

        return float(
            np.clip(indicador, 0, 1)
        )

    return 1.0


# ============================================================
# CARGAR DATOS AMBIENTALES
# ============================================================

print("=" * 70)
print("ANÁLISIS DE COMPATIBILIDAD DE CULTIVOS - AGROSHIFT")
print("=" * 70)

print("\nCargando datos ambientales...")

environmental = pd.read_csv(
    ENVIRONMENTAL_FILE
)

environmental["fecha"] = pd.to_datetime(
    environmental["fecha"],
    errors="coerce"
)

print(
    f"Registros ambientales: "
    f"{len(environmental)}"
)


# ============================================================
# CARGAR CULTIVOS
# ============================================================

print("\nCargando catálogo de cultivos...")

crops = pd.read_csv(
    CROPS_FILE
)

print(
    f"Cultivos encontrados: "
    f"{len(crops)}"
)

print("\nCultivos:")

for cultivo in crops["cultivo"]:
    print(f"  - {cultivo}")


# ============================================================
# VALIDAR COLUMNAS
# ============================================================

columnas_obligatorias = [
    "cultivo",
    "nombre_cientifico",
    "temperatura_min_c",
    "temperatura_optima_min_c",
    "temperatura_optima_max_c",
    "temperatura_max_c",
    "agua_min_mm",
    "agua_max_mm",
    "ciclo_min_dias",
    "ciclo_max_dias",
    "sensibilidad_deficit_hidrico",
]

faltantes = [
    columna
    for columna in columnas_obligatorias
    if columna not in crops.columns
]

if faltantes:

    print("\nERROR: faltan columnas en")
    print(CROPS_FILE)

    for columna in faltantes:
        print(f"  - {columna}")

    raise SystemExit(
        "\nCorrige el CSV de cultivos antes de continuar."
    )


# ============================================================
# PREPARAR DATOS NUMÉRICOS
# ============================================================

columnas_numericas = [
    "temperatura_min_c",
    "temperatura_optima_min_c",
    "temperatura_optima_max_c",
    "temperatura_max_c",
    "agua_min_mm",
    "agua_max_mm",
    "ciclo_min_dias",
    "ciclo_max_dias",
]

for columna in columnas_numericas:

    crops[columna] = pd.to_numeric(
        crops[columna],
        errors="coerce"
    )


# ============================================================
# ESTADÍSTICAS AMBIENTALES 2020
# ============================================================

temperatura_media = (
    environmental["T2M"].mean()
)

temperatura_minima = (
    environmental["T2M_MIN"].min()
)

temperatura_maxima = (
    environmental["T2M_MAX"].max()
)

precipitacion_anual = (
    environmental["PRECTOTCORR"].sum()
)

precipitacion_media = (
    environmental["PRECTOTCORR"].mean()
)

humedad_suelo_media = (
    environmental["sm_surface"].mean()
)

humedad_raiz_media = (
    environmental["sm_rootzone"].mean()
)

temperatura_suelo_media = (
    environmental[
        "soil_temp_layer1_celsius"
    ].mean()
)


print("\n" + "=" * 70)
print("CONDICIONES AMBIENTALES UTILIZADAS")
print("=" * 70)

print(
    f"\nTemperatura media: "
    f"{temperatura_media:.2f} °C"
)

print(
    f"Temperatura mínima: "
    f"{temperatura_minima:.2f} °C"
)

print(
    f"Temperatura máxima: "
    f"{temperatura_maxima:.2f} °C"
)

print(
    f"Precipitación acumulada: "
    f"{precipitacion_anual:.2f} mm"
)

print(
    f"Precipitación media diaria: "
    f"{precipitacion_media:.2f} mm"
)

print(
    f"Humedad superficial media: "
    f"{humedad_suelo_media:.4f} m³/m³"
)

print(
    f"Humedad radicular media: "
    f"{humedad_raiz_media:.4f} m³/m³"
)

print(
    f"Temperatura del suelo media: "
    f"{temperatura_suelo_media:.2f} °C"
)


# ============================================================
# ANALIZAR CADA CULTIVO
# ============================================================

resultados = []


for _, crop in crops.iterrows():

    cultivo = crop["cultivo"]

    print(
        f"\nAnalizando: {cultivo}"
    )

    # --------------------------------------------------------
    # TEMPERATURA
    # --------------------------------------------------------

    indicadores_temperatura = []

    for temperatura in environmental["T2M"]:

        indicador = indicador_temperatura(
            temperatura,
            crop["temperatura_min_c"],
            crop["temperatura_optima_min_c"],
            crop["temperatura_optima_max_c"],
            crop["temperatura_max_c"],
        )

        indicadores_temperatura.append(
            indicador
        )

    compatibilidad_termica = np.nanmean(
        indicadores_temperatura
    )

    # --------------------------------------------------------
    # AGUA
    # --------------------------------------------------------

    compatibilidad_agua = indicador_agua(
        precipitacion_anual,
        crop["agua_min_mm"],
        crop["agua_max_mm"],
    )

    # --------------------------------------------------------
    # HUMEDAD DEL SUELO
    # --------------------------------------------------------

    if (
        "humedad_suelo_min_m3_m3"
        in crops.columns
        and
        "humedad_suelo_max_m3_m3"
        in crops.columns
    ):

        compatibilidad_humedad = (
            calcular_indicador_humedad_suelo(
                humedad_suelo_media,
                crop[
                    "humedad_suelo_min_m3_m3"
                ],
                crop[
                    "humedad_suelo_max_m3_m3"
                ],
            )
        )

    else:

        compatibilidad_humedad = np.nan

    # --------------------------------------------------------
    # TEMPERATURA DEL SUELO
    # --------------------------------------------------------

    compatibilidad_suelo_termico = (
        compatibilidad_termica
    )

    # --------------------------------------------------------
    # COMPATIBILIDAD GLOBAL
    # --------------------------------------------------------

    indicadores_validos = [
        compatibilidad_termica,
        compatibilidad_agua,
    ]

    if not pd.isna(
        compatibilidad_humedad
    ):
        indicadores_validos.append(
            compatibilidad_humedad
        )

    indicadores_validos = [
        valor
        for valor in indicadores_validos
        if not pd.isna(valor)
    ]

    if indicadores_validos:

        compatibilidad_global = np.mean(
            indicadores_validos
        )

    else:

        compatibilidad_global = np.nan

    resultados.append(
        {
            "cultivo": cultivo,
            "nombre_cientifico": crop[
                "nombre_cientifico"
            ],
            "temperatura_media_2020": (
                temperatura_media
            ),
            "compatibilidad_termica": (
                compatibilidad_termica
            ),
            "precipitacion_2020_mm": (
                precipitacion_anual
            ),
            "agua_min_mm": (
                crop["agua_min_mm"]
            ),
            "agua_max_mm": (
                crop["agua_max_mm"]
            ),
            "compatibilidad_hidrica": (
                compatibilidad_agua
            ),
            "humedad_suelo_media": (
                humedad_suelo_media
            ),
            "humedad_raiz_media": (
                humedad_raiz_media
            ),
            "compatibilidad_humedad_suelo": (
                compatibilidad_humedad
            ),
            "temperatura_suelo_media": (
                temperatura_suelo_media
            ),
            "ciclo_min_dias": (
                crop["ciclo_min_dias"]
            ),
            "ciclo_max_dias": (
                crop["ciclo_max_dias"]
            ),
            "sensibilidad_deficit_hidrico": (
                crop[
                    "sensibilidad_deficit_hidrico"
                ]
            ),
            "compatibilidad_global": (
                compatibilidad_global
            ),
        }
    )


# ============================================================
# CREAR DATAFRAME DE RESULTADOS
# ============================================================

resultados_df = pd.DataFrame(
    resultados
)


# ============================================================
# CONVERTIR INDICADORES A PORCENTAJE
# ============================================================

columnas_indicadores = [
    "compatibilidad_termica",
    "compatibilidad_hidrica",
    "compatibilidad_humedad_suelo",
    "compatibilidad_global",
]

for columna in columnas_indicadores:

    resultados_df[
        columna + "_porcentaje"
    ] = (
        resultados_df[columna] * 100
    )


# ============================================================
# GUARDAR RESULTADOS
# ============================================================

resultados_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# ANÁLISIS MENSUAL POR CULTIVO
# ============================================================

print("\nGenerando análisis mensual...")

resultados_mensuales = []


for _, crop in crops.iterrows():

    cultivo = crop["cultivo"]

    for mes, grupo in environmental.groupby(
        environmental["fecha"].dt.month
    ):

        indicadores = []

        for temperatura in grupo["T2M"]:

            indicador = indicador_temperatura(
                temperatura,
                crop["temperatura_min_c"],
                crop["temperatura_optima_min_c"],
                crop["temperatura_optima_max_c"],
                crop["temperatura_max_c"],
            )

            indicadores.append(
                indicador
            )

        compatibilidad_termica = (
            np.nanmean(indicadores)
        )

        precipitacion_mes = (
            grupo["PRECTOTCORR"].sum()
        )

        compatibilidad_agua = (
            indicador_agua(
                precipitacion_mes,
                crop["agua_min_mm"],
                crop["agua_max_mm"],
            )
        )

        resultados_mensuales.append(
            {
                "cultivo": cultivo,
                "mes": mes,
                "temperatura_media": (
                    grupo["T2M"].mean()
                ),
                "precipitacion_total_mm": (
                    precipitacion_mes
                ),
                "humedad_suelo_media": (
                    grupo["sm_surface"].mean()
                ),
                "humedad_raiz_media": (
                    grupo["sm_rootzone"].mean()
                ),
                "compatibilidad_termica": (
                    compatibilidad_termica
                ),
                "compatibilidad_hidrica": (
                    compatibilidad_agua
                ),
            }
        )


mensual_df = pd.DataFrame(
    resultados_mensuales
)

mensual_df[
    "compatibilidad_termica_porcentaje"
] = (
    mensual_df["compatibilidad_termica"]
    * 100
)

mensual_df[
    "compatibilidad_hidrica_porcentaje"
] = (
    mensual_df["compatibilidad_hidrica"]
    * 100
)


mensual_df.to_csv(
    OUTPUT_MONTHLY_FILE,
    index=False
)


# ============================================================
# MOSTRAR RESULTADOS
# ============================================================

print("\n" + "=" * 70)
print("RESULTADOS DE COMPATIBILIDAD")
print("=" * 70)

mostrar = resultados_df[
    [
        "cultivo",
        "compatibilidad_termica_porcentaje",
        "compatibilidad_hidrica_porcentaje",
        "compatibilidad_global_porcentaje",
    ]
].copy()

mostrar[
    "compatibilidad_termica_porcentaje"
] = mostrar[
    "compatibilidad_termica_porcentaje"
].round(2)

mostrar[
    "compatibilidad_hidrica_porcentaje"
] = mostrar[
    "compatibilidad_hidrica_porcentaje"
].round(2)

mostrar[
    "compatibilidad_global_porcentaje"
] = mostrar[
    "compatibilidad_global_porcentaje"
].round(2)

print(
    mostrar.to_string(
        index=False
    )
)


# ============================================================
# ARCHIVOS GENERADOS
# ============================================================

print("\n" + "=" * 70)
print("ARCHIVOS GENERADOS")
print("=" * 70)

print(
    f"\n✓ {OUTPUT_FILE.name}"
)

print(
    f"✓ {OUTPUT_MONTHLY_FILE.name}"
)

print("\n" + "=" * 70)
print("✓ ANÁLISIS COMPLETADO")
print("=" * 70)
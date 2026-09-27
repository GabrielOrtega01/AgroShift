import os
import pandas as pd
import numpy as np


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
    "agroshift_environmental_2020.csv"
)

RUTA_SALIDA = os.path.join(
    BASE_DIR,
    "data",
    "analysis",
    "indicadores_cultivos_2020.csv"
)


# ============================================================
# FUNCIONES
# ============================================================

def convertir_numerico(df, columnas):
    """
    Convierte las columnas disponibles a valores numéricos.
    Los valores que no puedan convertirse quedan como NaN.
    """

    for columna in columnas:
        if columna in df.columns:
            df[columna] = pd.to_numeric(
                df[columna],
                errors="coerce"
            )

    return df


def puntaje_rango(
    valor,
    opt_min,
    opt_max,
    abs_min,
    abs_max
):
    """
    Calcula un indicador de 0 a 100 respecto a ECOCROP.

    100:
        valor dentro del rango óptimo.

    0:
        valor fuera del rango absoluto.

    Entre el rango óptimo y absoluto:
        reducción gradual.

    Este indicador describe compatibilidad con el rango
    ambiental de ECOCROP. No constituye una recomendación.
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

    # Dentro del rango óptimo
    if opt_min <= valor <= opt_max:
        return 100.0

    # Fuera del rango absoluto
    if valor < abs_min or valor > abs_max:
        return 0.0

    # Entre absoluto mínimo y óptimo mínimo
    if abs_min <= valor < opt_min:

        diferencia = opt_min - abs_min

        if diferencia == 0:
            return 100.0

        return (
            (valor - abs_min)
            / diferencia
        ) * 100

    # Entre óptimo máximo y absoluto máximo
    if opt_max < valor <= abs_max:

        diferencia = abs_max - opt_max

        if diferencia == 0:
            return 100.0

        return (
            (abs_max - valor)
            / diferencia
        ) * 100

    return np.nan


def clasificar_indicador(valor):
    """
    Clasificación descriptiva.
    No representa recomendación agronómica.
    """

    if pd.isna(valor):
        return "Sin datos"

    if valor >= 80:
        return "Alta compatibilidad"

    if valor >= 50:
        return "Compatibilidad intermedia"

    if valor > 0:
        return "Compatibilidad baja"

    return "Fuera del rango"


# ============================================================
# INICIO
# ============================================================

print("=" * 70)
print("AGROSHIFT - INDICADORES AMBIENTALES POR CULTIVO")
print("=" * 70)


# ============================================================
# CARGAR ECOCROP
# ============================================================

print("\nCargando características ECOCROP...")

ecocrop = pd.read_csv(
    RUTA_ECOCROP,
    encoding="utf-8-sig"
)

print(
    f"✓ Cultivos cargados: {len(ecocrop)}"
)


# ============================================================
# CARGAR NASA
# ============================================================

print("\nCargando datos ambientales NASA 2020...")

ambiental = pd.read_csv(
    RUTA_AMBIENTAL,
    encoding="utf-8-sig"
)

print(
    f"✓ Registros ambientales: {len(ambiental)}"
)


# ============================================================
# VALIDAR COLUMNAS ECOCROP
# ============================================================

columnas_ecocrop = [
    "ecocrop_id",
    "nombre",

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


faltantes_ecocrop = [
    columna
    for columna in columnas_ecocrop
    if columna not in ecocrop.columns
]


if faltantes_ecocrop:

    print("\nERROR: faltan columnas de ECOCROP:")

    for columna in faltantes_ecocrop:
        print(f"  - {columna}")

    raise SystemExit(1)


# ============================================================
# VALIDAR COLUMNAS NASA
# ============================================================

columnas_nasa = [
    "fecha",
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "PRECTOTCORR",
    "RH2M",
    "WS10M",
    "ALLSKY_SFC_SW_DWN",
    "sm_surface",
    "sm_rootzone",
    "sm_surface_wetness",
    "sm_rootzone_wetness",
    "soil_temp_layer1_celsius"
]


faltantes_nasa = [
    columna
    for columna in columnas_nasa
    if columna not in ambiental.columns
]


if faltantes_nasa:

    print("\nERROR: faltan columnas ambientales:")

    for columna in faltantes_nasa:
        print(f"  - {columna}")

    raise SystemExit(1)


# ============================================================
# CONVERSIÓN NUMÉRICA
# ============================================================

ecocrop = convertir_numerico(
    ecocrop,
    [
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
        "sm_surface_wetness",
        "sm_rootzone_wetness",

        "soil_temp_layer1_celsius"
    ]
)


# ============================================================
# RESUMEN AMBIENTAL
# ============================================================

print("\n" + "-" * 70)
print("CONDICIONES AMBIENTALES OBSERVADAS")
print("-" * 70)


temperatura_media = ambiental["T2M"].mean()

temperatura_minima = ambiental["T2M_MIN"].min()

temperatura_maxima = ambiental["T2M_MAX"].max()

precipitacion_total = ambiental[
    "PRECTOTCORR"
].sum()

precipitacion_media = ambiental[
    "PRECTOTCORR"
].mean()


humedad_superficial_media = ambiental[
    "sm_surface"
].mean()

humedad_raiz_media = ambiental[
    "sm_rootzone"
].mean()

saturacion_superficial_media = ambiental[
    "sm_surface_wetness"
].mean()

saturacion_raiz_media = ambiental[
    "sm_rootzone_wetness"
].mean()

temperatura_suelo_media = ambiental[
    "soil_temp_layer1_celsius"
].mean()


dias_lluviosos = (
    ambiental["PRECTOTCORR"] >= 1
).sum()

dias_secos = (
    ambiental["PRECTOTCORR"] < 1
).sum()


print(
    f"Temperatura media:             "
    f"{temperatura_media:.2f} °C"
)

print(
    f"Temperatura mínima:            "
    f"{temperatura_minima:.2f} °C"
)

print(
    f"Temperatura máxima:            "
    f"{temperatura_maxima:.2f} °C"
)

print(
    f"Precipitación acumulada:       "
    f"{precipitacion_total:.2f} mm"
)

print(
    f"Precipitación diaria media:    "
    f"{precipitacion_media:.2f} mm"
)

print(
    f"Humedad superficial media:     "
    f"{humedad_superficial_media:.4f}"
)

print(
    f"Humedad radicular media:       "
    f"{humedad_raiz_media:.4f}"
)

print(
    f"Saturación superficial media:  "
    f"{saturacion_superficial_media:.4f}"
)

print(
    f"Saturación radicular media:    "
    f"{saturacion_raiz_media:.4f}"
)

print(
    f"Temperatura del suelo media:   "
    f"{temperatura_suelo_media:.2f} °C"
)

print(
    f"Días lluviosos (>=1 mm):       "
    f"{dias_lluviosos}"
)

print(
    f"Días secos (<1 mm):            "
    f"{dias_secos}"
)


# ============================================================
# ANÁLISIS DE CADA CULTIVO
# ============================================================

resultados = []


for _, cultivo in ecocrop.iterrows():

    nombre = cultivo["nombre"]


    # ========================================================
    # INDICADOR TÉRMICO
    # ========================================================

    indicador_temperatura = puntaje_rango(

        temperatura_media,

        cultivo[
            "temperatura_optima_min_c"
        ],

        cultivo[
            "temperatura_optima_max_c"
        ],

        cultivo[
            "temperatura_absoluta_min_c"
        ],

        cultivo[
            "temperatura_absoluta_max_c"
        ]
    )


    # --------------------------------------------------------
    # DÍAS DENTRO DEL RANGO ÓPTIMO
    # --------------------------------------------------------

    dias_temp_optima = (
        (
            ambiental["T2M"]
            >= cultivo[
                "temperatura_optima_min_c"
            ]
        )
        &
        (
            ambiental["T2M"]
            <= cultivo[
                "temperatura_optima_max_c"
            ]
        )
    ).mean() * 100


    # --------------------------------------------------------
    # DÍAS DENTRO DEL RANGO ABSOLUTO
    # --------------------------------------------------------

    dias_temp_absoluta = (
        (
            ambiental["T2M"]
            >= cultivo[
                "temperatura_absoluta_min_c"
            ]
        )
        &
        (
            ambiental["T2M"]
            <= cultivo[
                "temperatura_absoluta_max_c"
            ]
        )
    ).mean() * 100


    # --------------------------------------------------------
    # DÍAS FUERA DEL RANGO ABSOLUTO
    # --------------------------------------------------------

    dias_temp_fuera = (
        100
        -
        dias_temp_absoluta
    )


    # ========================================================
    # INDICADOR DE PRECIPITACIÓN
    # ========================================================

    indicador_precipitacion = puntaje_rango(

        precipitacion_total,

        cultivo[
            "precipitacion_optima_min_mm"
        ],

        cultivo[
            "precipitacion_optima_max_mm"
        ],

        cultivo[
            "precipitacion_absoluta_min_mm"
        ],

        cultivo[
            "precipitacion_absoluta_max_mm"
        ]
    )


    # ========================================================
    # DIFERENCIA CON EL RANGO ÓPTIMO DE PRECIPITACIÓN
    # ========================================================

    lluvia_optima_min = cultivo[
        "precipitacion_optima_min_mm"
    ]

    lluvia_optima_max = cultivo[
        "precipitacion_optima_max_mm"
    ]


    if precipitacion_total < lluvia_optima_min:

        diferencia_precipitacion = (
            precipitacion_total
            - lluvia_optima_min
        )

        estado_precipitacion = (
            "Por debajo del rango óptimo"
        )

    elif precipitacion_total > lluvia_optima_max:

        diferencia_precipitacion = (
            precipitacion_total
            - lluvia_optima_max
        )

        estado_precipitacion = (
            "Por encima del rango óptimo"
        )

    else:

        diferencia_precipitacion = 0

        estado_precipitacion = (
            "Dentro del rango óptimo"
        )


    # ========================================================
    # PERFIL TÉRMICO
    # ========================================================

    if dias_temp_optima >= 80:

        perfil_termico = "Favorable"

    elif dias_temp_optima >= 50:

        perfil_termico = "Intermedio"

    else:

        perfil_termico = "Limitado"


    # ========================================================
    # PERFIL DE PRECIPITACIÓN
    # ========================================================

    if indicador_precipitacion >= 80:

        perfil_precipitacion = "Favorable"

    elif indicador_precipitacion >= 50:

        perfil_precipitacion = "Intermedio"

    else:

        perfil_precipitacion = "Limitado"


    # ========================================================
    # INFORMACIÓN DEL CICLO
    # ========================================================

    ciclo_min = cultivo[
        "ciclo_min_dias"
    ]

    ciclo_max = cultivo[
        "ciclo_max_dias"
    ]


    if pd.isna(ciclo_min) or pd.isna(ciclo_max):

        ciclo_medio = np.nan

    else:

        ciclo_medio = (
            ciclo_min + ciclo_max
        ) / 2


    # ========================================================
    # RESULTADO
    # ========================================================

    resultados.append({

        # ----------------------------------------------------
        # IDENTIFICACIÓN
        # ----------------------------------------------------

        "ecocrop_id":
            cultivo["ecocrop_id"],

        "nombre":
            nombre,


        # ----------------------------------------------------
        # CONDICIONES NASA
        # ----------------------------------------------------

        "temperatura_media_2020_c":
            temperatura_media,

        "temperatura_minima_2020_c":
            temperatura_minima,

        "temperatura_maxima_2020_c":
            temperatura_maxima,

        "precipitacion_total_2020_mm":
            precipitacion_total,

        "precipitacion_media_diaria_mm":
            precipitacion_media,

        "dias_lluviosos":
            dias_lluviosos,

        "dias_secos":
            dias_secos,


        # ----------------------------------------------------
        # SMAP
        # ----------------------------------------------------

        "humedad_superficial_media":
            humedad_superficial_media,

        "humedad_raiz_media":
            humedad_raiz_media,

        "saturacion_superficial_media":
            saturacion_superficial_media,

        "saturacion_raiz_media":
            saturacion_raiz_media,

        "temperatura_suelo_media_c":
            temperatura_suelo_media,


        # ----------------------------------------------------
        # RANGOS TÉRMICOS ECOCROP
        # ----------------------------------------------------

        "temperatura_optima_min_c":
            cultivo[
                "temperatura_optima_min_c"
            ],

        "temperatura_optima_max_c":
            cultivo[
                "temperatura_optima_max_c"
            ],

        "temperatura_absoluta_min_c":
            cultivo[
                "temperatura_absoluta_min_c"
            ],

        "temperatura_absoluta_max_c":
            cultivo[
                "temperatura_absoluta_max_c"
            ],


        # ----------------------------------------------------
        # INDICADORES TÉRMICOS
        # ----------------------------------------------------

        "indicador_temperatura":
            round(
                indicador_temperatura,
                2
            ),

        "dias_temperatura_optima_pct":
            round(
                dias_temp_optima,
                2
            ),

        "dias_temperatura_absoluta_pct":
            round(
                dias_temp_absoluta,
                2
            ),

        "dias_temperatura_fuera_absoluto_pct":
            round(
                dias_temp_fuera,
                2
            ),

        "perfil_termico":
            perfil_termico,


        # ----------------------------------------------------
        # RANGOS DE PRECIPITACIÓN
        # ----------------------------------------------------

        "precipitacion_optima_min_mm":
            cultivo[
                "precipitacion_optima_min_mm"
            ],

        "precipitacion_optima_max_mm":
            cultivo[
                "precipitacion_optima_max_mm"
            ],

        "precipitacion_absoluta_min_mm":
            cultivo[
                "precipitacion_absoluta_min_mm"
            ],

        "precipitacion_absoluta_max_mm":
            cultivo[
                "precipitacion_absoluta_max_mm"
            ],


        # ----------------------------------------------------
        # INDICADORES DE PRECIPITACIÓN
        # ----------------------------------------------------

        "indicador_precipitacion":
            round(
                indicador_precipitacion,
                2
            ),

        "diferencia_precipitacion_optima_mm":
            round(
                diferencia_precipitacion,
                2
            ),

        "estado_precipitacion":
            estado_precipitacion,

        "perfil_precipitacion":
            perfil_precipitacion,


        # ----------------------------------------------------
        # DATOS EDÁFICOS ECOCROP
        # ----------------------------------------------------

        "ph_optimo_min":
            cultivo["ph_optimo_min"],

        "ph_optimo_max":
            cultivo["ph_optimo_max"],

        "ph_absoluto_min":
            cultivo["ph_absoluto_min"],

        "ph_absoluto_max":
            cultivo["ph_absoluto_max"],

        "profundidad_suelo_optima":
            cultivo.get(
                "profundidad_suelo_optima",
                np.nan
            ),

        "profundidad_suelo_absoluta":
            cultivo.get(
                "profundidad_suelo_absoluta",
                np.nan
            ),

        "fertilidad_suelo_optima":
            cultivo.get(
                "fertilidad_suelo_optima",
                np.nan
            ),

        "fertilidad_suelo_absoluta":
            cultivo.get(
                "fertilidad_suelo_absoluta",
                np.nan
            ),

        "salinidad_suelo_optima":
            cultivo.get(
                "salinidad_suelo_optima",
                np.nan
            ),

        "salinidad_suelo_absoluta":
            cultivo.get(
                "salinidad_suelo_absoluta",
                np.nan
            ),

        "drenaje_suelo_optimo":
            cultivo.get(
                "drenaje_suelo_optimo",
                np.nan
            ),

        "drenaje_suelo_absoluto":
            cultivo.get(
                "drenaje_suelo_absoluto",
                np.nan
            ),


        # ----------------------------------------------------
        # CICLO
        # ----------------------------------------------------

        "ciclo_min_dias":
            ciclo_min,

        "ciclo_max_dias":
            ciclo_max,

        "ciclo_medio_dias":
            ciclo_medio
    })


# ============================================================
# DATAFRAME
# ============================================================

resultado = pd.DataFrame(
    resultados
)


# ============================================================
# REDONDEAR
# ============================================================

columnas_redondear = [
    "temperatura_media_2020_c",
    "temperatura_minima_2020_c",
    "temperatura_maxima_2020_c",
    "precipitacion_total_2020_mm",
    "precipitacion_media_diaria_mm",

    "humedad_superficial_media",
    "humedad_raiz_media",
    "saturacion_superficial_media",
    "saturacion_raiz_media",
    "temperatura_suelo_media_c",

    "indicador_temperatura",
    "dias_temperatura_optima_pct",
    "dias_temperatura_absoluta_pct",
    "dias_temperatura_fuera_absoluto_pct",

    "indicador_precipitacion",
    "diferencia_precipitacion_optima_mm",

    "ciclo_medio_dias"
]


for columna in columnas_redondear:

    if columna in resultado.columns:

        resultado[columna] = resultado[
            columna
        ].round(2)


# ============================================================
# GUARDAR CSV
# ============================================================

resultado.to_csv(
    RUTA_SALIDA,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# MOSTRAR RESULTADO
# ============================================================

print("\n" + "=" * 70)
print("INDICADORES POR CULTIVO")
print("=" * 70)


columnas_mostrar = [

    "nombre",

    "indicador_temperatura",

    "dias_temperatura_optima_pct",

    "dias_temperatura_absoluta_pct",

    "indicador_precipitacion",

    "perfil_termico",

    "perfil_precipitacion",

    "humedad_superficial_media",

    "humedad_raiz_media",

    "temperatura_suelo_media_c",

    "ciclo_min_dias",

    "ciclo_max_dias"
]


print(
    resultado[
        columnas_mostrar
    ].to_string(
        index=False
    )
)


# ============================================================
# VALIDACIONES
# ============================================================

print("\n" + "-" * 70)
print("VALIDACIÓN")
print("-" * 70)


print(
    f"✓ Cultivos analizados: "
    f"{len(resultado)}"
)


print(
    f"✓ Indicadores térmicos calculados: "
    f"{resultado['indicador_temperatura'].notna().sum()}"
)


print(
    f"✓ Indicadores de precipitación calculados: "
    f"{resultado['indicador_precipitacion'].notna().sum()}"
)


print(
    f"✓ Temperatura del suelo disponible: "
    f"{resultado['temperatura_suelo_media_c'].notna().sum()}"
)


print(
    f"✓ Archivo generado:"
)


print(
    RUTA_SALIDA
)


print("\n" + "=" * 70)
print("✓ PROCESO COMPLETADO")
print("=" * 70)
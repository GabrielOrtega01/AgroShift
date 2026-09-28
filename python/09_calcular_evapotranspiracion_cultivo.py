import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agroshift.regions import get_region

REGION_SLUG = get_region(os.environ.get("AGROSHIFT_REGION", "santander")).slug


# ============================================================
# AGROSHIFT
# EVAPOTRANSPIRACIÓN DEL CULTIVO (ETc)
# ETo FAO-56 + Kc por etapas
# ============================================================

print("=" * 70)
print("AGROSHIFT - CÁLCULO DE ETc POR CULTIVO")
print("=" * 70)


# ------------------------------------------------------------
# RUTAS
# ------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ARCHIVO_ETO = os.path.join(
    BASE_DIR,
    "data",
    "analysis",
    REGION_SLUG,
    "eto_2020.csv"
)

ARCHIVO_CULTIVOS = os.path.join(
    BASE_DIR,
    "data",
    "crops",
    "agroshift_cultivos_caracteristicas.csv"
)

ARCHIVO_SALIDA = os.path.join(
    BASE_DIR,
    "data",
    "analysis",
    REGION_SLUG,
    "etc_cultivos_2020.csv"
)

ARCHIVO_RESUMEN = os.path.join(
    BASE_DIR,
    "data",
    "analysis",
    REGION_SLUG,
    "etc_resumen_cultivos_2020.csv"
)

ARCHIVO_GRAFICA = os.path.join(
    BASE_DIR,
    "data",
    "analysis",
    REGION_SLUG,
    "etc_cultivos_2020.png"
)


# ------------------------------------------------------------
# CONFIGURACIÓN DE Kc
# ------------------------------------------------------------
#
# Valores de referencia para el prototipo.
#
# Kc:
#   inicial -> desarrollo -> medio -> final
#
# Los valores deben ser refinados posteriormente según:
# variedad, clima, manejo, fecha de siembra y fuente técnica.
#
# ------------------------------------------------------------

KC_CULTIVOS = {

    "Zea mays": {
        "kc_inicial": 0.30,
        "kc_medio": 1.20,
        "kc_final": 0.60
    },

    "Phaseolus vulgaris": {
        "kc_inicial": 0.40,
        "kc_medio": 1.15,
        "kc_final": 0.35
    },

    "Solanum tuberosum": {
        "kc_inicial": 0.50,
        "kc_medio": 1.15,
        "kc_final": 0.75
    },

    "Lycopersicon esculentum": {
        "kc_inicial": 0.60,
        "kc_medio": 1.15,
        "kc_final": 0.80
    },

    "Oryza sativa": {
        "kc_inicial": 1.05,
        "kc_medio": 1.20,
        "kc_final": 0.90
    },

    "Manihot esculenta": {
        "kc_inicial": 0.30,
        "kc_medio": 1.10,
        "kc_final": 0.80
    },

    "Saccharum officinarum": {
        "kc_inicial": 0.40,
        "kc_medio": 1.25,
        "kc_final": 0.75
    },

    "Coffea arabica": {
        "kc_inicial": 0.87,
        "kc_medio": 0.98,
        "kc_final": 0.97
    }
}


# ------------------------------------------------------------
# FUNCIÓN PARA CONSTRUIR LAS ETAPAS
# ------------------------------------------------------------

def construir_etapas(ciclo_dias):
    """
    Distribuye el ciclo del cultivo en cuatro etapas:

    1. Inicial
    2. Desarrollo
    3. Media
    4. Final

    Esta distribución es una aproximación inicial para el
    prototipo AgroShift.
    """

    ciclo_dias = max(
        int(round(ciclo_dias)),
        1
    )

    inicial = max(
        int(round(ciclo_dias * 0.10)),
        1
    )

    desarrollo = max(
        int(round(ciclo_dias * 0.20)),
        1
    )

    final = max(
        int(round(ciclo_dias * 0.15)),
        1
    )

    media = (
        ciclo_dias
        - inicial
        - desarrollo
        - final
    )

    media = max(
        media,
        1
    )

    return {
        "inicial": inicial,
        "desarrollo": desarrollo,
        "media": media,
        "final": final
    }


# ------------------------------------------------------------
# FUNCIÓN Kc DIARIO
# ------------------------------------------------------------

def calcular_kc_diario(dia, etapas, kc):
    """
    Obtiene Kc para un día específico del ciclo.

    Durante desarrollo y final se realiza interpolación lineal.
    """

    inicial = etapas["inicial"]
    desarrollo = etapas["desarrollo"]
    media = etapas["media"]
    final = etapas["final"]

    kc_inicial = kc["kc_inicial"]
    kc_medio = kc["kc_medio"]
    kc_final = kc["kc_final"]

    # -------------------------
    # ETAPA INICIAL
    # -------------------------

    if dia <= inicial:
        return kc_inicial, "Inicial"

    # -------------------------
    # DESARROLLO
    # -------------------------

    inicio_desarrollo = inicial + 1

    fin_desarrollo = (
        inicial
        + desarrollo
    )

    if dia <= fin_desarrollo:

        progreso = (
            dia - inicio_desarrollo
        ) / max(
            desarrollo - 1,
            1
        )

        valor = (
            kc_inicial
            +
            progreso
            * (
                kc_medio
                - kc_inicial
            )
        )

        return valor, "Desarrollo"

    # -------------------------
    # MEDIA
    # -------------------------

    fin_media = (
        inicial
        + desarrollo
        + media
    )

    if dia <= fin_media:
        return kc_medio, "Media"

    # -------------------------
    # FINAL
    # -------------------------

    inicio_final = fin_media + 1

    progreso = (
        dia - inicio_final
    ) / max(
        final - 1,
        1
    )

    progreso = min(
        max(progreso, 0),
        1
    )

    valor = (
        kc_medio
        +
        progreso
        * (
            kc_final
            - kc_medio
        )
    )

    return valor, "Final"


# ------------------------------------------------------------
# CARGAR ETo
# ------------------------------------------------------------

print("\nCargando ETo FAO-56...")

eto = pd.read_csv(
    ARCHIVO_ETO
)

eto["fecha"] = pd.to_datetime(
    eto["fecha"],
    errors="coerce"
)

eto["ETo"] = pd.to_numeric(
    eto["ETo"],
    errors="coerce"
)

eto = eto.dropna(
    subset=["fecha", "ETo"]
).copy()

print(
    f"✓ Registros ETo: {len(eto)}"
)


# ------------------------------------------------------------
# CARGAR CULTIVOS
# ------------------------------------------------------------

print("\nCargando características ECOCROP...")

cultivos = pd.read_csv(
    ARCHIVO_CULTIVOS
)

print(
    f"✓ Cultivos ECOCROP: {len(cultivos)}"
)


# ------------------------------------------------------------
# CULTIVOS DISPONIBLES
# ------------------------------------------------------------

cultivos = cultivos[
    cultivos["nombre"].isin(
        KC_CULTIVOS.keys()
    )
].copy()

print(
    f"✓ Cultivos con configuración Kc: "
    f"{len(cultivos)}"
)


# ------------------------------------------------------------
# VALIDACIÓN
# ------------------------------------------------------------

if cultivos.empty:

    raise ValueError(
        "No se encontraron cultivos "
        "compatibles con KC_CULTIVOS."
    )


# ------------------------------------------------------------
# PROCESAR CULTIVOS
# ------------------------------------------------------------

resultados = []

resumen = []


for _, cultivo in cultivos.iterrows():

    nombre = cultivo["nombre"]

    ciclo_min = pd.to_numeric(
        cultivo["ciclo_min_dias"],
        errors="coerce"
    )

    ciclo_max = pd.to_numeric(
        cultivo["ciclo_max_dias"],
        errors="coerce"
    )

    if pd.isna(ciclo_min):
        continue

    if pd.isna(ciclo_max):
        ciclo_max = ciclo_min

    # --------------------------------------------------------
    # CICLO DE REFERENCIA
    # --------------------------------------------------------
    #
    # Utilizamos el punto medio del intervalo ECOCROP.
    #
    # Ejemplo:
    # 65 - 365 -> 215 días
    #
    # Esto NO significa que sea el ciclo real del cultivo.
    # Es una duración de referencia para el prototipo.
    # --------------------------------------------------------

    ciclo_referencia = int(
        round(
            (ciclo_min + ciclo_max) / 2
        )
    )

    etapas = construir_etapas(
        ciclo_referencia
    )

    kc = KC_CULTIVOS[nombre]


    # --------------------------------------------------------
    # ETo DEL PERÍODO
    # --------------------------------------------------------

    datos = eto.copy()

    # Utilizamos como máximo un ciclo completo.
    datos = datos.iloc[
        :min(
            ciclo_referencia,
            len(datos)
        )
    ].copy()

    datos["dia_ciclo"] = (
        np.arange(
            1,
            len(datos) + 1
        )
    )


    # --------------------------------------------------------
    # Kc Y ETc
    # --------------------------------------------------------

    kc_valores = []
    etapas_dia = []

    for dia in datos["dia_ciclo"]:

        valor_kc, etapa = calcular_kc_diario(
            dia,
            etapas,
            kc
        )

        kc_valores.append(
            valor_kc
        )

        etapas_dia.append(
            etapa
        )


    datos["Kc"] = kc_valores

    datos["etapa"] = etapas_dia


    # --------------------------------------------------------
    # ETc
    # --------------------------------------------------------

    datos["ETc"] = (
        datos["ETo"]
        * datos["Kc"]
    )


    datos["cultivo"] = nombre

    datos["ciclo_referencia_dias"] = (
        ciclo_referencia
    )

    datos["ciclo_min_dias"] = (
        ciclo_min
    )

    datos["ciclo_max_dias"] = (
        ciclo_max
    )


    resultados.append(
        datos[
            [
                "cultivo",
                "fecha",
                "dia_ciclo",
                "etapa",
                "ETo",
                "Kc",
                "ETc",
                "ciclo_referencia_dias",
                "ciclo_min_dias",
                "ciclo_max_dias"
            ]
        ]
    )


    # --------------------------------------------------------
    # RESUMEN
    # --------------------------------------------------------

    resumen.append({

        "cultivo": nombre,

        "ciclo_min_dias":
            ciclo_min,

        "ciclo_max_dias":
            ciclo_max,

        "ciclo_referencia_dias":
            ciclo_referencia,

        "dias_simulados":
            len(datos),

        "kc_inicial":
            kc["kc_inicial"],

        "kc_medio":
            kc["kc_medio"],

        "kc_final":
            kc["kc_final"],

        "ETo_acumulada_mm":
            datos["ETo"].sum(),

        "ETc_acumulada_mm":
            datos["ETc"].sum(),

        "ETc_media_mm_dia":
            datos["ETc"].mean(),

        "ETc_max_mm_dia":
            datos["ETc"].max()
    })


# ------------------------------------------------------------
# UNIR RESULTADOS
# ------------------------------------------------------------

resultado = pd.concat(
    resultados,
    ignore_index=True
)

resumen_df = pd.DataFrame(
    resumen
)


# ------------------------------------------------------------
# GUARDAR
# ------------------------------------------------------------

resultado.to_csv(
    ARCHIVO_SALIDA,
    index=False
)

resumen_df.to_csv(
    ARCHIVO_RESUMEN,
    index=False
)


# ------------------------------------------------------------
# MOSTRAR RESULTADOS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("ETc POR CULTIVO")
print("=" * 70)

columnas_mostrar = [
    "cultivo",
    "ciclo_referencia_dias",
    "kc_inicial",
    "kc_medio",
    "kc_final",
    "ETo_acumulada_mm",
    "ETc_acumulada_mm",
    "ETc_media_mm_dia"
]

print(
    resumen_df[
        columnas_mostrar
    ].to_string(
        index=False
    )
)


# ------------------------------------------------------------
# GRÁFICA
# ------------------------------------------------------------

plt.figure(
    figsize=(12, 6)
)

for cultivo in resultado["cultivo"].unique():

    datos_cultivo = resultado[
        resultado["cultivo"] == cultivo
    ]

    plt.plot(
        datos_cultivo["dia_ciclo"],
        datos_cultivo["ETc"],
        label=cultivo
    )


plt.title(
    "ETc diaria por cultivo - AgroShift"
)

plt.xlabel(
    "Día del ciclo"
)

plt.ylabel(
    "ETc (mm/día)"
)

plt.legend(
    fontsize=8
)

plt.grid(
    True,
    alpha=0.3
)

plt.tight_layout()

plt.savefig(
    ARCHIVO_GRAFICA,
    dpi=150
)

plt.close()


# ------------------------------------------------------------
# VALIDACIÓN
# ------------------------------------------------------------

print("\n" + "-" * 70)
print("VALIDACIÓN")
print("-" * 70)

print(
    f"✓ Cultivos procesados: "
    f"{resultado['cultivo'].nunique()}"
)

print(
    f"✓ Registros ETc: "
    f"{len(resultado)}"
)

print(
    f"✓ Valores Kc faltantes: "
    f"{resultado['Kc'].isna().sum()}"
)

print(
    f"✓ Valores ETc faltantes: "
    f"{resultado['ETc'].isna().sum()}"
)

print(
    f"✓ Valores ETc negativos: "
    f"{(resultado['ETc'] < 0).sum()}"
)

print("\n✓ Archivo diario:")

print(
    ARCHIVO_SALIDA
)

print("\n✓ Archivo resumen:")

print(
    ARCHIVO_RESUMEN
)

print("\n✓ Gráfica:")

print(
    ARCHIVO_GRAFICA
)

print("\n" + "=" * 70)
print("✓ MÓDULO ETc COMPLETADO")
print("=" * 70)
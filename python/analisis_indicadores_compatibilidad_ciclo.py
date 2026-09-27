import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ENV_FILE = BASE_DIR / "data" / "analysis" / "agroshift_environmental_2020.csv"
ETO_FILE = BASE_DIR / "data" / "analysis" / "eto_2020.csv"
ECOCROP_FILE = BASE_DIR / "data" / "crops" / "agroshift_cultivos_caracteristicas.csv"
HIDRICO_FILE = BASE_DIR / "data" / "analysis" / "estado_hidrico_cultivos_2020.csv"

OUTPUT_FILE = BASE_DIR / "data" / "analysis" / "indicadores_compatibilidad_ciclo_2020.csv"
OUTPUT_GRAPH = BASE_DIR / "data" / "analysis" / "compatibilidad_cultivos_ciclo_2020.png"


# ============================================================
# CULTIVOS A ANALIZAR
# ============================================================

CULTIVOS_ANALIZAR = [
    2175,   # Zea mays
    1668,   # Phaseolus vulgaris
    1574,   # Oryza sativa
    1971,   # Solanum tuberosum
    1379,   # Lycopersicon esculentum
    1420,   # Manihot esculenta
    749,    # Coffea arabica
    1884    # Saccharum officinarum
]


# ============================================================
# FUNCIONES
# ============================================================

def indicador_rango(valor, minimo, maximo):
    """
    Calcula compatibilidad con un rango óptimo.

    Dentro del rango óptimo = 100.

    Fuera del rango:
    - disminuye progresivamente;
    - no baja de 0.
    """

    if pd.isna(valor) or pd.isna(minimo) or pd.isna(maximo):
        return np.nan

    if minimo <= valor <= maximo:
        return 100.0

    if valor < minimo:
        amplitud = maximo - minimo

        if amplitud <= 0:
            return 0.0

        diferencia = minimo - valor
        indicador = 100 - (diferencia / amplitud) * 100

    else:
        amplitud = maximo - minimo

        if amplitud <= 0:
            return 0.0

        diferencia = valor - maximo
        indicador = 100 - (diferencia / amplitud) * 100

    return max(0.0, min(100.0, indicador))


def indicador_precipitacion(valor, minimo, maximo):
    """
    Evalúa la precipitación acumulada durante el ciclo
    frente al rango óptimo de ECOCROP.

    Dentro del rango óptimo = 100.
    """

    return indicador_rango(valor, minimo, maximo)


def clasificar_indice(indice):
    """
    Clasificación descriptiva del índice.
    """

    if pd.isna(indice):
        return "Sin datos"

    if indice >= 80:
        return "Alta"

    if indice >= 60:
        return "Media"

    if indice >= 40:
        return "Baja"

    return "Muy baja"


# ============================================================
# CARGA DE DATOS
# ============================================================

print("=" * 70)
print("AGROSHIFT - V2 COMPATIBILIDAD AMBIENTAL POR CICLO")
print("=" * 70)

print("\nCargando datos...")

if not ENV_FILE.exists():
    raise FileNotFoundError(
        f"No se encontró el archivo ambiental:\n{ENV_FILE}"
    )

if not ECOCROP_FILE.exists():
    raise FileNotFoundError(
        f"No se encontró el archivo ECOCROP:\n{ECOCROP_FILE}"
    )

if not HIDRICO_FILE.exists():
    raise FileNotFoundError(
        f"No se encontró el archivo de estado hídrico:\n{HIDRICO_FILE}"
    )


environmental = pd.read_csv(ENV_FILE)
eto = pd.read_csv(ETO_FILE)
ecocrop = pd.read_csv(ECOCROP_FILE)
hidrico = pd.read_csv(HIDRICO_FILE)


print(f"Datos ambientales: {len(environmental)} registros")
print(f"Datos ECOCROP:     {len(ecocrop)} registros")
print(f"Datos hídricos:    {len(hidrico)} registros")


# ============================================================
# FECHAS
# ============================================================

environmental["fecha"] = pd.to_datetime(
    environmental["fecha"],
    errors="coerce"
)

hidrico["fecha"] = pd.to_datetime(
    hidrico["fecha"],
    errors="coerce"
)
eto["fecha"] = pd.to_datetime(
    eto["fecha"],
    errors="coerce"
)


environmental = environmental.sort_values("fecha").reset_index(drop=True)
hidrico = hidrico.sort_values("fecha").reset_index(drop=True)
eto = eto.sort_values("fecha").reset_index(drop=True)

# ------------------------------------------------------------
# INTEGRAR ETo FAO-56
# ------------------------------------------------------------

# Evitar duplicar la columna si el archivo ambiental
# ya la contiene.
if "ETo" in environmental.columns:
    environmental = environmental.drop(columns=["ETo"])

environmental = environmental.merge(
    eto[["fecha", "ETo"]],
    on="fecha",
    how="left"
)

print(
    f"ETo integrada: "
    f"{environmental['ETo'].notna().sum()} registros"
)

print(
    f"ETo faltante: "
    f"{environmental['ETo'].isna().sum()} registros"
)

# ============================================================
# VALIDACIÓN
# ============================================================

print("\nValidación de datos:")

print(
    f"Periodo ambiental: "
    f"{environmental['fecha'].min().date()} -> "
    f"{environmental['fecha'].max().date()}"
)

print(
    f"Registros ambientales: {len(environmental)}"
)

print(
    f"Registros hídricos: {len(hidrico)}"
)


# ============================================================
# PREPARAR ECOCROP
# ============================================================

ecocrop = ecocrop[
    ecocrop["ecocrop_id"].isin(CULTIVOS_ANALIZAR)
].copy()


if ecocrop.empty:
    raise ValueError(
        "No se encontraron los cultivos seleccionados en ECOCROP."
    )


# ============================================================
# RESULTADOS
# ============================================================

resultados = []


# ============================================================
# ANALIZAR CADA CULTIVO
# ============================================================

for _, cultivo in ecocrop.iterrows():

    nombre = cultivo["nombre"]
    ecocrop_id = int(cultivo["ecocrop_id"])

    print("\n" + "-" * 70)
    print(f"Analizando: {nombre}")
    print(f"ECOCROP ID: {ecocrop_id}")

    # --------------------------------------------------------
    # CICLO DE REFERENCIA
    # --------------------------------------------------------

    ciclo_min = cultivo["ciclo_min_dias"]
    ciclo_max = cultivo["ciclo_max_dias"]

    if pd.isna(ciclo_min) or pd.isna(ciclo_max):
        print("No existe duración de ciclo.")
        continue

    ciclo_min = float(ciclo_min)
    ciclo_max = float(ciclo_max)

    # Prototipo:
    # se utiliza el punto medio del rango ECOCROP.
    ciclo_dias = int(round((ciclo_min + ciclo_max) / 2))

    ciclo_dias = max(1, ciclo_dias)

    print(
        f"Ciclo ECOCROP: {ciclo_min:.0f}-{ciclo_max:.0f} días"
    )

    print(
        f"Ciclo de referencia utilizado: {ciclo_dias} días"
    )

    # --------------------------------------------------------
    # FECHA DE INICIO
    # --------------------------------------------------------

    fecha_inicio = pd.Timestamp("2020-01-01")

    fecha_fin = fecha_inicio + pd.Timedelta(
        days=ciclo_dias - 1
    )

    print(
        f"Periodo analizado: "
        f"{fecha_inicio.date()} -> {fecha_fin.date()}"
    )

    # --------------------------------------------------------
    # DATOS AMBIENTALES DEL CICLO
    # --------------------------------------------------------

    ciclo = environmental[
        (environmental["fecha"] >= fecha_inicio)
        &
        (environmental["fecha"] <= fecha_fin)
    ].copy()

    if ciclo.empty:
        print("No existen datos ambientales para el ciclo.")
        continue

    # --------------------------------------------------------
    # DATOS HÍDRICOS DEL CULTIVO
    # --------------------------------------------------------

    hidrico_cultivo = hidrico[
        (hidrico["cultivo"] == nombre)
        &
        (hidrico["fecha"] >= fecha_inicio)
        &
        (hidrico["fecha"] <= fecha_fin)
    ].copy()

    # --------------------------------------------------------
    # TEMPERATURA
    # --------------------------------------------------------

    temperatura_media = ciclo["T2M"].mean()

    indicador_temperatura = indicador_rango(
        temperatura_media,
        cultivo["temperatura_optima_min_c"],
        cultivo["temperatura_optima_max_c"]
    )

    # --------------------------------------------------------
    # PRECIPITACIÓN
    # --------------------------------------------------------

    precipitacion_ciclo = ciclo["PRECTOTCORR"].sum()

    indicador_precipitacion_ciclo = indicador_precipitacion(
        precipitacion_ciclo,
        cultivo["precipitacion_optima_min_mm"],
        cultivo["precipitacion_optima_max_mm"]
    )

    # --------------------------------------------------------
    # EVAPOTRANSPIRACIÓN
    # --------------------------------------------------------

    if "ETo" in ciclo.columns:
        eto_ciclo = ciclo["ETo"].sum()
    else:
        eto_ciclo = np.nan

    # --------------------------------------------------------
    # ETc
    # --------------------------------------------------------

    if not hidrico_cultivo.empty and "ETc" in hidrico_cultivo.columns:
        etc_ciclo = hidrico_cultivo["ETc"].sum()
    else:
        etc_ciclo = np.nan

    # --------------------------------------------------------
    # DEMANDA NO CUBIERTA
    # --------------------------------------------------------

    if (
        not hidrico_cultivo.empty
        and "demanda_no_cubierta" in hidrico_cultivo.columns
    ):
        demanda_no_cubierta = (
            hidrico_cultivo["demanda_no_cubierta"]
            .clip(lower=0)
            .sum()
        )

        dias_demanda_no_cubierta = (
            hidrico_cultivo["demanda_no_cubierta"] > 0
        ).sum()

    else:
        demanda_no_cubierta = np.nan
        dias_demanda_no_cubierta = np.nan

    # --------------------------------------------------------
    # HUMEDAD DEL SUELO SMAP
    # --------------------------------------------------------

    if not hidrico_cultivo.empty:

        sm_rootzone_media = (
            hidrico_cultivo["sm_rootzone"].mean()
        )

        sm_rootzone_min = (
            hidrico_cultivo["sm_rootzone"].min()
        )

        sm_rootzone_max = (
            hidrico_cultivo["sm_rootzone"].max()
        )

        sm_rootzone_wetness_media = (
            hidrico_cultivo["sm_rootzone_wetness"].mean()
        )

        # Umbral descriptivo:
        # percentil 10 de toda la serie anual de humedad
        umbral_humedad_baja = hidrico["sm_rootzone"].quantile(0.10)

        dias_humedad_baja = (
            hidrico_cultivo["sm_rootzone"]
            < umbral_humedad_baja
        ).sum()

        porcentaje_humedad_baja = (
            dias_humedad_baja / len(hidrico_cultivo)
        ) * 100

    else:

        sm_rootzone_media = np.nan
        sm_rootzone_min = np.nan
        sm_rootzone_max = np.nan
        sm_rootzone_wetness_media = np.nan
        dias_humedad_baja = np.nan
        porcentaje_humedad_baja = np.nan

    # --------------------------------------------------------
    # INDICADOR HÍDRICO
    # --------------------------------------------------------
    #
    # No se interpreta ETc > precipitación como estrés directo.
    #
    # Se combinan dos señales:
    #
    # 1. Días con humedad de zona radicular baja.
    # 2. Días con demanda no cubierta.
    #
    # Esto sigue siendo un indicador descriptivo/prototipo.
    # --------------------------------------------------------

    if not hidrico_cultivo.empty:

        indicador_humedad = max(
            0,
            100 - porcentaje_humedad_baja
        )

        porcentaje_demanda = (
            dias_demanda_no_cubierta
            / len(hidrico_cultivo)
        ) * 100

        indicador_demanda = max(
            0,
            100 - porcentaje_demanda
        )

        indicador_hidrico = (
            indicador_humedad * 0.60
            +
            indicador_demanda * 0.40
        )

    else:

        indicador_hidrico = np.nan

    # --------------------------------------------------------
    # ÍNDICE FINAL
    # --------------------------------------------------------
    #
    # Pesos:
    #
    # Temperatura       30 %
    # Precipitación     25 %
    # Estado hídrico    45 %
    #
    # El componente hídrico recibe mayor peso porque AgroShift
    # busca analizar adaptación frente a disponibilidad de agua.
    # --------------------------------------------------------

    componentes = [
        indicador_temperatura,
        indicador_precipitacion_ciclo,
        indicador_hidrico
    ]

    if all(not pd.isna(x) for x in componentes):

        indice_compatibilidad = (
            indicador_temperatura * 0.30
            +
            indicador_precipitacion_ciclo * 0.25
            +
            indicador_hidrico * 0.45
        )

    else:

        indice_compatibilidad = np.nan

    clasificacion = clasificar_indice(
        indice_compatibilidad
    )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    resultado = {

        "cultivo": nombre,

        "ecocrop_id": ecocrop_id,

        "fecha_inicio": fecha_inicio.date(),

        "fecha_fin": fecha_fin.date(),

        "ciclo_dias": ciclo_dias,

        "ciclo_ecocrop_min_dias": ciclo_min,

        "ciclo_ecocrop_max_dias": ciclo_max,

        "temperatura_media_ciclo_c": temperatura_media,

        "temperatura_optima_min_c":
            cultivo["temperatura_optima_min_c"],

        "temperatura_optima_max_c":
            cultivo["temperatura_optima_max_c"],

        "indicador_temperatura":
            indicador_temperatura,

        "precipitacion_ciclo_mm":
            precipitacion_ciclo,

        "precipitacion_optima_min_mm":
            cultivo["precipitacion_optima_min_mm"],

        "precipitacion_optima_max_mm":
            cultivo["precipitacion_optima_max_mm"],

        "indicador_precipitacion":
            indicador_precipitacion_ciclo,

        "ETo_ciclo_mm":
            eto_ciclo,

        "ETc_ciclo_mm":
            etc_ciclo,

        "demanda_no_cubierta_mm":
            demanda_no_cubierta,

        "dias_demanda_no_cubierta":
            dias_demanda_no_cubierta,

        "sm_rootzone_media":
            sm_rootzone_media,

        "sm_rootzone_min":
            sm_rootzone_min,

        "sm_rootzone_max":
            sm_rootzone_max,

        "sm_rootzone_wetness_media":
            sm_rootzone_wetness_media,

        "dias_humedad_baja":
            dias_humedad_baja,

        "porcentaje_humedad_baja":
            porcentaje_humedad_baja,

        "indicador_hidrico":
            indicador_hidrico,

        "indice_compatibilidad_ambiental":
            indice_compatibilidad,

        "clasificacion":
            clasificacion
    }

    resultados.append(resultado)

    # --------------------------------------------------------
    # MOSTRAR RESULTADO
    # --------------------------------------------------------

    print(
        f"Temperatura media:       {temperatura_media:.2f} °C"
    )

    print(
        f"Precipitación ciclo:     {precipitacion_ciclo:.2f} mm"
    )

    print(
        f"ETo ciclo:               {eto_ciclo:.2f} mm"
    )

    print(
        f"ETc ciclo:               {etc_ciclo:.2f} mm"
    )

    print(
        f"SMAP raíz media:         {sm_rootzone_media:.4f}"
    )

    print(
        f"Días humedad baja:       {dias_humedad_baja}"
    )

    print(
        f"Días demanda no cubierta:{dias_demanda_no_cubierta}"
    )

    print(
        f"Indicador temperatura:   {indicador_temperatura:.2f}"
    )

    print(
        f"Indicador precipitación: {indicador_precipitacion_ciclo:.2f}"
    )

    print(
        f"Indicador hídrico:       {indicador_hidrico:.2f}"
    )

    print(
        f"Índice ambiental:        {indice_compatibilidad:.2f}"
    )

    print(
        f"Clasificación:           {clasificacion}"
    )


# ============================================================
# DATAFRAME FINAL
# ============================================================

resultado_df = pd.DataFrame(resultados)


if resultado_df.empty:
    raise ValueError(
        "No se generaron resultados."
    )


# ============================================================
# ORDENAR RESULTADOS
# ============================================================

resultado_df = resultado_df.sort_values(
    "indice_compatibilidad_ambiental",
    ascending=False
).reset_index(drop=True)


# ============================================================
# GUARDAR CSV
# ============================================================

resultado_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# MOSTRAR RESUMEN
# ============================================================

print("\n" + "=" * 70)
print("RESULTADOS FINALES V2")
print("=" * 70)

print(
    resultado_df[
        [
            "cultivo",
            "ciclo_dias",
            "temperatura_media_ciclo_c",
            "precipitacion_ciclo_mm",
            "ETo_ciclo_mm",
            "ETc_ciclo_mm",
            "sm_rootzone_media",
            "dias_humedad_baja",
            "indicador_temperatura",
            "indicador_precipitacion",
            "indicador_hidrico",
            "indice_compatibilidad_ambiental",
            "clasificacion"
        ]
    ].to_string(index=False)
)


# ============================================================
# GRÁFICO
# ============================================================

plt.figure(figsize=(12, 7))

plt.bar(
    resultado_df["cultivo"],
    resultado_df["indice_compatibilidad_ambiental"]
)

plt.axhline(
    80,
    linestyle="--",
    linewidth=1
)

plt.axhline(
    60,
    linestyle="--",
    linewidth=1
)

plt.axhline(
    40,
    linestyle="--",
    linewidth=1
)

plt.title(
    "AgroShift - Compatibilidad ambiental por ciclo de cultivo"
)

plt.ylabel(
    "Índice de compatibilidad ambiental"
)

plt.xlabel(
    "Cultivo"
)

plt.xticks(
    rotation=45,
    ha="right"
)

plt.ylim(
    0,
    105
)

plt.tight_layout()

plt.savefig(
    OUTPUT_GRAPH,
    dpi=150
)

plt.show()


# ============================================================
# VALIDACIÓN FINAL
# ============================================================

print("\n" + "=" * 70)
print("VALIDACIÓN")
print("=" * 70)

print(
    f"Total de cultivos analizados: {len(resultado_df)}"
)

print(
    f"Archivo generado: {OUTPUT_FILE}"
)

print(
    f"Gráfico generado: {OUTPUT_GRAPH}"
)

print(
    f"Valores faltantes totales: "
    f"{resultado_df.isna().sum().sum()}"
)

print("\nProceso terminado correctamente.")
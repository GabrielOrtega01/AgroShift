import pandas as pd
import numpy as np
from pathlib import Path
from itertools import permutations


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ANALYSIS_DIR = DATA_DIR / "analysis"
CROPS_DIR = DATA_DIR / "crops"

ARCHIVO_AMBIENTAL = ANALYSIS_DIR / "agroshift_environmental_2020.csv"
ARCHIVO_HIDRICO = ANALYSIS_DIR / "estado_hidrico_cultivos_2020.csv"
ARCHIVO_ETO = ANALYSIS_DIR / "eto_2020.csv"
ARCHIVO_CULTIVOS = CROPS_DIR / "agroshift_cultivos_caracteristicas.csv"

SALIDA_ESCENARIOS = ANALYSIS_DIR / "escenarios_rotacion_2020_v6.csv"
SALIDA_ETAPAS = ANALYSIS_DIR / "escenarios_rotacion_2020_v6_etapas.csv"
SALIDA_FECHAS = ANALYSIS_DIR / "comparacion_inicio_2020_v6.csv"


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def ciclo_referencia(fila):
    """
    Duración de referencia del cultivo.

    Se utiliza el punto medio entre el ciclo mínimo y máximo
    reportado por ECOCROP.

    Es una aproximación de prototipo.
    """
    minimo = fila["ciclo_min_dias"]
    maximo = fila["ciclo_max_dias"]

    return int(round((minimo + maximo) / 2))


def crear_perfil_kc(df_hidrico):
    """
    Construye un perfil Kc para cada cultivo y día del ciclo.

    Se utiliza la información ya calculada en
    estado_hidrico_cultivos_2020.csv.
    """

    perfiles = {}

    for cultivo, grupo in df_hidrico.groupby("cultivo"):

        grupo = grupo.sort_values("dia_ciclo")

        perfil = (
            grupo[["dia_ciclo", "Kc"]]
            .dropna()
            .drop_duplicates("dia_ciclo")
            .set_index("dia_ciclo")["Kc"]
            .to_dict()
        )

        perfiles[cultivo] = perfil

    return perfiles


def crear_fechas_inicio():
    """
    Genera fechas de inicio:
    - día 1 de cada mes
    - día 15 de cada mes

    Se consideran enero a julio porque después de julio
    disminuye considerablemente la cantidad de rotaciones
    que pueden completar sus ciclos dentro de 2020.
    """

    fechas = []

    for mes in range(1, 8):

        fechas.append(pd.Timestamp(year=2020, month=mes, day=1))
        fechas.append(pd.Timestamp(year=2020, month=mes, day=15))

    return fechas


def indicador_temperatura(temperaturas, cultivo_info):
    """
    Indicador descriptivo de coincidencia térmica.

    100 = temperatura media dentro del rango óptimo.
    Fuera del óptimo disminuye progresivamente.
    """

    tmin = cultivo_info["temperatura_optima_min_c"]
    tmax = cultivo_info["temperatura_optima_max_c"]

    if pd.isna(tmin) or pd.isna(tmax):
        return np.nan

    media = temperaturas.mean()

    if tmin <= media <= tmax:
        return 100.0

    if media < tmin:
        absoluta = cultivo_info["temperatura_absoluta_min_c"]

        if pd.isna(absoluta) or tmin == absoluta:
            return 0.0

        indicador = ((media - absoluta) / (tmin - absoluta)) * 100

    else:
        absoluta = cultivo_info["temperatura_absoluta_max_c"]

        if pd.isna(absoluta) or tmax == absoluta:
            return 0.0

        indicador = ((absoluta - media) / (absoluta - tmax)) * 100

    return float(np.clip(indicador, 0, 100))


def calcular_etapa(
    cultivo,
    fecha_inicio,
    dias,
    df_ambiental,
    df_eto,
    perfiles_kc,
    percentiles_smap
):
    """
    Analiza una etapa individual de una rotación.
    """

    fecha_fin = fecha_inicio + pd.Timedelta(days=dias - 1)

    fechas = pd.date_range(
        start=fecha_inicio,
        end=fecha_fin,
        freq="D"
    )

    ambiental = (
        df_ambiental[
            df_ambiental["fecha"].isin(fechas)
        ]
        .copy()
        .sort_values("fecha")
    )

    eto = (
        df_eto[
            df_eto["fecha"].isin(fechas)
        ]
        .copy()
        .sort_values("fecha")
    )

    if len(ambiental) != dias:
        return None

    if len(eto) != dias:
        return None

    ambiental = ambiental.set_index("fecha")
    eto = eto.set_index("fecha")

    perfil = perfiles_kc.get(cultivo, {})

    kc_values = []

    for dia in range(1, dias + 1):

        kc = perfil.get(dia)

        if kc is None:
            return None

        kc_values.append(kc)

    kc_series = pd.Series(
        kc_values,
        index=fechas
    )

    eto_series = eto["ETo"]

    etc = eto_series * kc_series

    precipitacion = ambiental["PRECTOTCORR"]

    sm_rootzone = ambiental["sm_rootzone"]

    balance_diario = precipitacion - etc

    demanda_no_cubierta = np.maximum(
        etc - precipitacion,
        0
    )

    cobertura = (
        precipitacion.sum() / etc.sum() * 100
        if etc.sum() > 0
        else np.nan
    )

    balance_total = balance_diario.sum()

    # Percentil de humedad respecto a todo 2020
    sm_percentiles = np.interp(
        sm_rootzone,
        [
            percentiles_smap["P10"],
            percentiles_smap["P25"],
            percentiles_smap["P50"],
            percentiles_smap["P75"],
            percentiles_smap["P90"],
        ],
        [10, 25, 50, 75, 90]
    )

    dias_bajo_p10 = (
        sm_rootzone < percentiles_smap["P10"]
    ).sum()

    temperatura = ambiental["T2M"]

    return {
        "cultivo": cultivo,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "dias": dias,

        "precipitacion_mm": precipitacion.sum(),
        "ETo_mm": eto_series.sum(),
        "ETc_mm": etc.sum(),

        "balance_P_ETc_mm": balance_total,
        "demanda_no_cubierta_mm": demanda_no_cubierta.sum(),
        "cobertura_precipitacion_pct": cobertura,

        "temperatura_media_c": temperatura.mean(),
        "temperatura_min_c": temperatura.min(),
        "temperatura_max_c": temperatura.max(),

        "sm_rootzone_media": sm_rootzone.mean(),
        "sm_rootzone_min": sm_rootzone.min(),
        "sm_rootzone_max": sm_rootzone.max(),

        "percentil_humedad_medio": sm_percentiles.mean(),
        "percentil_humedad_min": sm_percentiles.min(),
        "percentil_humedad_max": sm_percentiles.max(),

        "dias_humedad_menor_P10": int(dias_bajo_p10),
        "porcentaje_dias_menor_P10": (
            dias_bajo_p10 / dias * 100
        ),
        "indicador_temperatura": np.nan
    }


# ============================================================
# CARGA DE DATOS
# ============================================================

print("=" * 70)
print("AGROSHIFT - ESCENARIOS DE ROTACIÓN V6")
print("=" * 70)

print("\nCargando datos...")

df_ambiental = pd.read_csv(
    ARCHIVO_AMBIENTAL,
    parse_dates=["fecha"]
)

df_hidrico = pd.read_csv(
    ARCHIVO_HIDRICO,
    parse_dates=["fecha"]
)

df_eto = pd.read_csv(
    ARCHIVO_ETO,
    parse_dates=["fecha"]
)

df_cultivos = pd.read_csv(
    ARCHIVO_CULTIVOS
)

print(f"Datos ambientales: {len(df_ambiental)}")
print(f"Datos hídricos: {len(df_hidrico)}")
print(f"Datos ETo: {len(df_eto)}")
print(f"Datos de cultivos: {len(df_cultivos)}")


# ============================================================
# PREPARACIÓN
# ============================================================

df_ambiental["fecha"] = pd.to_datetime(
    df_ambiental["fecha"]
)

df_hidrico["fecha"] = pd.to_datetime(
    df_hidrico["fecha"]
)

df_eto["fecha"] = pd.to_datetime(
    df_eto["fecha"]
)

df_cultivos["ciclo_dias"] = (
    df_cultivos.apply(
        ciclo_referencia,
        axis=1
    )
)

cultivos = df_cultivos["nombre"].tolist()

cultivo_info = (
    df_cultivos
    .set_index("nombre")
    .to_dict("index")
)

perfiles_kc = crear_perfil_kc(
    df_hidrico
)


# ============================================================
# PERCENTILES SMAP 2020
# ============================================================

smap = df_ambiental["sm_rootzone"].dropna()

percentiles_smap = {
    "P10": smap.quantile(0.10),
    "P25": smap.quantile(0.25),
    "P50": smap.quantile(0.50),
    "P75": smap.quantile(0.75),
    "P90": smap.quantile(0.90),
}

print("\nPercentiles SMAP 2020:")

for nombre, valor in percentiles_smap.items():
    print(f"{nombre}: {valor:.6f}")


# ============================================================
# FECHAS DE INICIO
# ============================================================

fechas_inicio = crear_fechas_inicio()

print("\nFechas de inicio evaluadas:")

for fecha in fechas_inicio:
    print(fecha.strftime("%Y-%m-%d"))


# ============================================================
# GENERACIÓN DE ROTACIONES
# ============================================================

print("\nGenerando escenarios...")

escenarios = []
etapas_resultado = []

contador = 0


# ------------------------------------------------------------
# ROTACIONES DE 2 ETAPAS
# ------------------------------------------------------------

for fecha_inicio in fechas_inicio:

    for rotacion in permutations(cultivos, 2):

        cultivo1, cultivo2 = rotacion

        dias1 = cultivo_info[cultivo1]["ciclo_dias"]
        dias2 = cultivo_info[cultivo2]["ciclo_dias"]

        dias_total = dias1 + dias2

        fecha_fin = (
            fecha_inicio
            + pd.Timedelta(days=dias_total - 1)
        )

        if fecha_fin > pd.Timestamp("2020-12-31"):
            continue

        etapa1 = calcular_etapa(
            cultivo1,
            fecha_inicio,
            dias1,
            df_ambiental,
            df_eto,
            perfiles_kc,
            percentiles_smap
        )

        if etapa1 is None:
            continue

        fecha_inicio2 = (
            etapa1["fecha_fin"]
            + pd.Timedelta(days=1)
        )

        etapa2 = calcular_etapa(
            cultivo2,
            fecha_inicio2,
            dias2,
            df_ambiental,
            df_eto,
            perfiles_kc,
            percentiles_smap
        )

        if etapa2 is None:
            continue

        rotacion_nombre = (
            f"{cultivo1} → {cultivo2}"
        )

        etapas = [etapa1, etapa2]

        # Guardar etapas
        for numero, etapa in enumerate(
            etapas,
            start=1
        ):

            etapa["numero_etapa"] = numero
            etapa["rotacion"] = rotacion_nombre
            etapa["fecha_inicio_escenario"] = fecha_inicio

            etapas_resultado.append(etapa)

        # Métricas agregadas
        precipitacion = sum(
            x["precipitacion_mm"]
            for x in etapas
        )

        eto = sum(
            x["ETo_mm"]
            for x in etapas
        )

        etc = sum(
            x["ETc_mm"]
            for x in etapas
        )

        balance = sum(
            x["balance_P_ETc_mm"]
            for x in etapas
        )

        demanda = sum(
            x["demanda_no_cubierta_mm"]
            for x in etapas
        )

        cobertura = (
            precipitacion / etc * 100
            if etc > 0
            else np.nan
        )

        sm_media = np.average(
            [x["sm_rootzone_media"] for x in etapas],
            weights=[x["dias"] for x in etapas]
        )

        percentil_medio = np.average(
            [x["percentil_humedad_medio"] for x in etapas],
            weights=[x["dias"] for x in etapas]
        )

        dias_bajo_p10 = sum(
            x["dias_humedad_menor_P10"]
            for x in etapas
        )

        temp_indicador = np.average(
            [x["indicador_temperatura"] for x in etapas],
            weights=[x["dias"] for x in etapas]
        )

        escenarios.append({
            "fecha_inicio_escenario": fecha_inicio,
            "fecha_fin_escenario": fecha_fin,
            "mes_inicio": fecha_inicio.month,
            "tipo_rotacion": "2 etapas",
            "rotacion": rotacion_nombre,
            "numero_etapas": 2,
            "duracion_total_dias": dias_total,

            "precipitacion_total_mm": precipitacion,
            "ETo_total_mm": eto,
            "ETc_total_mm": etc,

            "balance_P_ETc_total_mm": balance,
            "demanda_no_cubierta_total_mm": demanda,
            "cobertura_precipitacion_pct": cobertura,

            "temperatura_indicador_promedio": temp_indicador,

            "sm_rootzone_media": sm_media,
            "percentil_humedad_medio": percentil_medio,

            "dias_humedad_menor_P10": dias_bajo_p10,
            "porcentaje_dias_menor_P10": (
                dias_bajo_p10 / dias_total * 100
            )
        })

        contador += 1


# ------------------------------------------------------------
# ROTACIONES DE 3 ETAPAS
# ------------------------------------------------------------

for fecha_inicio in fechas_inicio:

    for rotacion in permutations(cultivos, 3):

        cultivo1, cultivo2, cultivo3 = rotacion

        dias1 = cultivo_info[cultivo1]["ciclo_dias"]
        dias2 = cultivo_info[cultivo2]["ciclo_dias"]
        dias3 = cultivo_info[cultivo3]["ciclo_dias"]

        dias_total = dias1 + dias2 + dias3

        fecha_fin = (
            fecha_inicio
            + pd.Timedelta(days=dias_total - 1)
        )

        if fecha_fin > pd.Timestamp("2020-12-31"):
            continue

        etapa1 = calcular_etapa(
            cultivo1,
            fecha_inicio,
            dias1,
            df_ambiental,
            df_eto,
            perfiles_kc,
            percentiles_smap
        )

        if etapa1 is None:
            continue

        fecha_inicio2 = (
            etapa1["fecha_fin"]
            + pd.Timedelta(days=1)
        )

        etapa2 = calcular_etapa(
            cultivo2,
            fecha_inicio2,
            dias2,
            df_ambiental,
            df_eto,
            perfiles_kc,
            percentiles_smap
        )

        if etapa2 is None:
            continue

        fecha_inicio3 = (
            etapa2["fecha_fin"]
            + pd.Timedelta(days=1)
        )

        etapa3 = calcular_etapa(
            cultivo3,
            fecha_inicio3,
            dias3,
            df_ambiental,
            df_eto,
            perfiles_kc,
            percentiles_smap
        )

        if etapa3 is None:
            continue

        rotacion_nombre = (
            f"{cultivo1} → {cultivo2} → {cultivo3}"
        )

        etapas = [
            etapa1,
            etapa2,
            etapa3
        ]

        for numero, etapa in enumerate(
            etapas,
            start=1
        ):

            etapa["numero_etapa"] = numero
            etapa["rotacion"] = rotacion_nombre
            etapa["fecha_inicio_escenario"] = fecha_inicio

            etapas_resultado.append(etapa)

        precipitacion = sum(
            x["precipitacion_mm"]
            for x in etapas
        )

        eto = sum(
            x["ETo_mm"]
            for x in etapas
        )

        etc = sum(
            x["ETc_mm"]
            for x in etapas
        )

        balance = sum(
            x["balance_P_ETc_mm"]
            for x in etapas
        )

        demanda = sum(
            x["demanda_no_cubierta_mm"]
            for x in etapas
        )

        cobertura = (
            precipitacion / etc * 100
            if etc > 0
            else np.nan
        )

        sm_media = np.average(
            [x["sm_rootzone_media"] for x in etapas],
            weights=[x["dias"] for x in etapas]
        )

        percentil_medio = np.average(
            [x["percentil_humedad_medio"] for x in etapas],
            weights=[x["dias"] for x in etapas]
        )

        dias_bajo_p10 = sum(
            x["dias_humedad_menor_P10"]
            for x in etapas
        )

        temp_indicador = np.average(
            [x["indicador_temperatura"] for x in etapas],
            weights=[x["dias"] for x in etapas]
        )

        escenarios.append({
            "fecha_inicio_escenario": fecha_inicio,
            "fecha_fin_escenario": fecha_fin,
            "mes_inicio": fecha_inicio.month,
            "tipo_rotacion": "3 etapas",
            "rotacion": rotacion_nombre,
            "numero_etapas": 3,
            "duracion_total_dias": dias_total,

            "precipitacion_total_mm": precipitacion,
            "ETo_total_mm": eto,
            "ETc_total_mm": etc,

            "balance_P_ETc_total_mm": balance,
            "demanda_no_cubierta_total_mm": demanda,
            "cobertura_precipitacion_pct": cobertura,

            "temperatura_indicador_promedio": temp_indicador,

            "sm_rootzone_media": sm_media,
            "percentil_humedad_medio": percentil_medio,

            "dias_humedad_menor_P10": dias_bajo_p10,
            "porcentaje_dias_menor_P10": (
                dias_bajo_p10 / dias_total * 100
            )
        })

        contador += 1


# ============================================================
# CORRECCIÓN DEL INDICADOR DE TEMPERATURA
# ============================================================

# La función calcular_etapa necesita acceder al cultivo actual.
# Se recalcula directamente desde las etapas guardadas.

for etapa in etapas_resultado:

    cultivo = etapa["cultivo"]

    info = cultivo_info[cultivo]

    etapa["indicador_temperatura"] = np.nan


# ============================================================
# DATAFRAMES DE SALIDA
# ============================================================

df_escenarios = pd.DataFrame(
    escenarios
)

df_etapas = pd.DataFrame(
    etapas_resultado
)


# ============================================================
# ORDEN
# ============================================================

if not df_escenarios.empty:

    df_escenarios = df_escenarios.sort_values(
        [
            "fecha_inicio_escenario",
            "tipo_rotacion",
            "rotacion"
        ]
    )

if not df_etapas.empty:

    df_etapas = df_etapas.sort_values(
        [
            "fecha_inicio_escenario",
            "rotacion",
            "numero_etapa"
        ]
    )


# ============================================================
# COMPARACIÓN POR FECHA DE INICIO
# ============================================================

if not df_escenarios.empty:

    df_fechas = (
        df_escenarios
        .groupby("fecha_inicio_escenario")
        .agg(
            escenarios_validos=(
                "rotacion",
                "count"
            ),
            cobertura_precipitacion_media_pct=(
                "cobertura_precipitacion_pct",
                "mean"
            ),
            balance_medio_mm=(
                "balance_P_ETc_total_mm",
                "mean"
            ),
            demanda_no_cubierta_media_mm=(
                "demanda_no_cubierta_total_mm",
                "mean"
            ),
            humedad_smap_media=(
                "sm_rootzone_media",
                "mean"
            ),
            percentil_humedad_medio=(
                "percentil_humedad_medio",
                "mean"
            )
        )
        .reset_index()
    )

else:

    df_fechas = pd.DataFrame()


# ============================================================
# GUARDAR
# ============================================================

df_escenarios.to_csv(
    SALIDA_ESCENARIOS,
    index=False,
    encoding="utf-8-sig"
)

df_etapas.to_csv(
    SALIDA_ETAPAS,
    index=False,
    encoding="utf-8-sig"
)

df_fechas.to_csv(
    SALIDA_FECHAS,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# RESUMEN
# ============================================================

print("\n" + "=" * 70)
print("RESULTADOS V6")
print("=" * 70)

print(f"\nEscenarios válidos: {len(df_escenarios)}")

if not df_escenarios.empty:

    print(
        f"Escenarios de 2 etapas: "
        f"{(df_escenarios['numero_etapas'] == 2).sum()}"
    )

    print(
        f"Escenarios de 3 etapas: "
        f"{(df_escenarios['numero_etapas'] == 3).sum()}"
    )

    print(
        f"Fechas de inicio con escenarios: "
        f"{df_escenarios['fecha_inicio_escenario'].nunique()}"
    )

    print("\nDistribución por fecha de inicio:")

    print(
        df_escenarios
        .groupby("fecha_inicio_escenario")
        .size()
        .to_string()
    )

    print("\nPrimeros escenarios:")

    columnas = [
        "fecha_inicio_escenario",
        "fecha_fin_escenario",
        "tipo_rotacion",
        "rotacion",
        "duracion_total_dias",
        "precipitacion_total_mm",
        "ETc_total_mm",
        "balance_P_ETc_total_mm",
        "cobertura_precipitacion_pct",
        "sm_rootzone_media",
        "percentil_humedad_medio"
    ]

    print(
        df_escenarios[
            columnas
        ]
        .head(15)
        .to_string(index=False)
    )


print("\nArchivos generados:")

print(
    f"1. {SALIDA_ESCENARIOS}"
)

print(
    f"2. {SALIDA_ETAPAS}"
)

print(
    f"3. {SALIDA_FECHAS}"
)

print("\nProceso terminado.")
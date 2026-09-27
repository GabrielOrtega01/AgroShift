import pandas as pd
import numpy as np
from itertools import permutations
from pathlib import Path

# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ANALYSIS_DIR = DATA_DIR / "analysis"
CROPS_DIR = DATA_DIR / "crops"

AMBIENTAL_FILE = ANALYSIS_DIR / "agroshift_environmental_2020.csv"
CULTIVOS_FILE = CROPS_DIR / "agroshift_cultivos_caracteristicas.csv"
HIDRICO_FILE = ANALYSIS_DIR / "estado_hidrico_cultivos_2020.csv"
ETO_FILE = ANALYSIS_DIR / "eto_2020.csv"

SALIDA_RESUMEN = ANALYSIS_DIR / "escenarios_rotacion_2020_v4.csv"
SALIDA_ETAPAS = ANALYSIS_DIR / "escenarios_rotacion_2020_v4_etapas.csv"


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def ciclo_referencia(fila):
    """
    Calcula el ciclo de referencia como punto medio
    entre el ciclo mínimo y máximo registrado en ECOCROP.
    """
    minimo = fila["ciclo_min_dias"]
    maximo = fila["ciclo_max_dias"]

    if pd.isna(minimo) or pd.isna(maximo):
        return np.nan

    return int(round((minimo + maximo) / 2))


def indicador_temperatura(temp, minimo, maximo):
    """
    Indicador de compatibilidad térmica.

    100 = temperatura dentro del rango óptimo.
    Fuera del rango se reduce progresivamente.
    """

    if pd.isna(temp) or pd.isna(minimo) or pd.isna(maximo):
        return np.nan

    if minimo <= temp <= maximo:
        return 100.0

    # Distancia respecto al rango óptimo
    if temp < minimo:
        distancia = minimo - temp
    else:
        distancia = temp - maximo

    # Penalización progresiva.
    # 5 °C o más fuera del rango -> 0.
    indicador = 100 - (distancia / 5) * 100

    return float(np.clip(indicador, 0, 100))


def cobertura_precipitacion(precipitacion, etc):
    """
    Porcentaje de ETc que puede cubrir la precipitación.

    Se limita a 100%.
    """
    if etc <= 0:
        return np.nan

    return float(np.clip((precipitacion / etc) * 100, 0, 100))


def indicador_balance(balance, etc):
    """
    Indicador descriptivo basado en el balance P - ETc.

    No representa el déficit hídrico real del cultivo,
    porque no incorpora almacenamiento de agua en el suelo.
    """

    if etc <= 0:
        return np.nan

    proporcion = balance / etc

    indicador = (1 + proporcion) * 100

    return float(np.clip(indicador, 0, 100))


def calcular_percentil(valor, serie):
    """
    Calcula el percentil empírico aproximado de un valor
    dentro de la distribución anual de humedad SMAP.
    """

    serie = serie.dropna()

    if len(serie) == 0 or pd.isna(valor):
        return np.nan

    return float((serie <= valor).mean() * 100)


# ============================================================
# CARGA DE DATOS
# ============================================================

print("=" * 70)
print("AGROSHIFT - ESCENARIOS DE ROTACIÓN V4")
print("=" * 70)

ambiental = pd.read_csv(AMBIENTAL_FILE)
cultivos = pd.read_csv(CULTIVOS_FILE)
hidrico = pd.read_csv(HIDRICO_FILE)
eto = pd.read_csv(ETO_FILE)

# Fechas
ambiental["fecha"] = pd.to_datetime(ambiental["fecha"])
hidrico["fecha"] = pd.to_datetime(hidrico["fecha"])
eto["fecha"] = pd.to_datetime(eto["fecha"])

# Orden temporal
ambiental = ambiental.sort_values("fecha").reset_index(drop=True)
eto = eto.sort_values("fecha").reset_index(drop=True)
hidrico = hidrico.sort_values(["cultivo", "dia_ciclo"]).reset_index(drop=True)

print(f"\nDatos ambientales: {len(ambiental)}")
print(f"Datos de cultivos: {len(cultivos)}")
print(f"Datos hídricos: {len(hidrico)}")
print(f"Datos ETo: {len(eto)}")


# ============================================================
# CICLOS DE CULTIVO
# ============================================================

cultivos["ciclo_referencia_dias"] = cultivos.apply(
    ciclo_referencia,
    axis=1
)

print("\nCiclos de referencia:")

for _, fila in cultivos.iterrows():
    print(
        f"  {fila['nombre']}: "
        f"{fila['ciclo_referencia_dias']} días"
    )


# ============================================================
# PERFIL Kc POR CULTIVO Y DÍA DEL CICLO
# ============================================================

kc_profiles = {}

for cultivo in hidrico["cultivo"].unique():

    datos = hidrico[
        hidrico["cultivo"] == cultivo
    ].copy()

    datos = datos.sort_values("dia_ciclo")

    perfil = (
        datos
        .set_index("dia_ciclo")["Kc"]
        .to_dict()
    )

    kc_profiles[cultivo] = perfil


# ============================================================
# DISTRIBUCIÓN ANUAL DE HUMEDAD SMAP
# ============================================================

serie_smap = ambiental["sm_rootzone"].dropna()

P10 = serie_smap.quantile(0.10)
P25 = serie_smap.quantile(0.25)
P50 = serie_smap.quantile(0.50)
P75 = serie_smap.quantile(0.75)
P90 = serie_smap.quantile(0.90)

print("\nDistribución SMAP rootzone 2020:")
print(f"  P10: {P10:.6f}")
print(f"  P25: {P25:.6f}")
print(f"  P50: {P50:.6f}")
print(f"  P75: {P75:.6f}")
print(f"  P90: {P90:.6f}")


# ============================================================
# PERCENTIL SMAP PARA CADA FECHA
# ============================================================

ambiental["smap_percentil"] = ambiental["sm_rootzone"].apply(
    lambda x: calcular_percentil(x, serie_smap)
)


# ============================================================
# DICCIONARIO DE CULTIVOS
# ============================================================

cultivo_info = {}

for _, fila in cultivos.iterrows():

    nombre = fila["nombre"]

    cultivo_info[nombre] = {
        "ciclo": int(fila["ciclo_referencia_dias"]),
        "temp_min": fila["temperatura_optima_min_c"],
        "temp_max": fila["temperatura_optima_max_c"]
    }


# ============================================================
# FUNCIÓN PARA ANALIZAR UNA ETAPA
# ============================================================

def analizar_etapa(
    cultivo,
    fecha_inicio,
    fecha_fin,
    numero_etapa
):

    ciclo = cultivo_info[cultivo]["ciclo"]

    fechas = pd.date_range(
        start=fecha_inicio,
        end=fecha_fin,
        freq="D"
    )

    if len(fechas) == 0:
        return None

    # --------------------------------------------------------
    # Datos ambientales
    # --------------------------------------------------------

    datos = ambiental[
        ambiental["fecha"].isin(fechas)
    ].copy()

    datos = datos.sort_values("fecha")

    if len(datos) != len(fechas):
        return None

    # --------------------------------------------------------
    # Perfil Kc
    # --------------------------------------------------------

    perfil = kc_profiles.get(cultivo)

    if not perfil:
        return None

    kc_values = []

    for dia_ciclo in range(1, len(fechas) + 1):

        # Si la etapa utiliza solamente una parte del ciclo,
        # se inicia el perfil del cultivo desde día 1.
        kc = perfil.get(dia_ciclo)

        if kc is None:
            return None

        kc_values.append(kc)

    datos["Kc"] = kc_values

    # --------------------------------------------------------
    # ETo
    # --------------------------------------------------------

    datos_eto = eto[
        eto["fecha"].isin(fechas)
    ][["fecha", "ETo"]].copy()

    datos = datos.merge(
        datos_eto,
        on="fecha",
        how="left"
    )

    if datos["ETo"].isna().any():
        return None

    # --------------------------------------------------------
    # ETc
    # --------------------------------------------------------

    datos["ETc"] = datos["ETo"] * datos["Kc"]

    # --------------------------------------------------------
    # Balance hídrico simple
    # --------------------------------------------------------

    datos["balance_P_ETc"] = (
        datos["PRECTOTCORR"] - datos["ETc"]
    )

    datos["demanda_no_cubierta"] = (
        datos["ETc"] - datos["PRECTOTCORR"]
    ).clip(lower=0)

    # --------------------------------------------------------
    # Indicadores
    # --------------------------------------------------------

    precipitacion = datos["PRECTOTCORR"].sum()
    eto_total = datos["ETo"].sum()
    etc_total = datos["ETc"].sum()

    balance_total = datos["balance_P_ETc"].sum()

    demanda_total = datos["demanda_no_cubierta"].sum()

    cobertura = cobertura_precipitacion(
        precipitacion,
        etc_total
    )

    indicador_balance_val = indicador_balance(
        balance_total,
        etc_total
    )

    # --------------------------------------------------------
    # Temperatura
    # --------------------------------------------------------

    temperatura_media = datos["T2M"].mean()

    temp_indicador = indicador_temperatura(
        temperatura_media,
        cultivo_info[cultivo]["temp_min"],
        cultivo_info[cultivo]["temp_max"]
    )

    # --------------------------------------------------------
    # SMAP
    # --------------------------------------------------------

    smap_media = datos["sm_rootzone"].mean()
    smap_min = datos["sm_rootzone"].min()
    smap_max = datos["sm_rootzone"].max()

    smap_percentil_medio = datos["smap_percentil"].mean()
    smap_percentil_min = datos["smap_percentil"].min()
    smap_percentil_max = datos["smap_percentil"].max()

    dias_bajo_p10 = (
        datos["sm_rootzone"] < P10
    ).sum()

    porcentaje_bajo_p10 = (
        dias_bajo_p10 / len(datos)
    ) * 100

    # --------------------------------------------------------
    # Resultado de la etapa
    # --------------------------------------------------------

    resultado = {
        "etapa": numero_etapa,
        "cultivo": cultivo,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "dias": len(datos),

        "temperatura_media_c": temperatura_media,
        "indicador_temperatura": temp_indicador,

        "precipitacion_mm": precipitacion,
        "ETo_mm": eto_total,
        "ETc_mm": etc_total,

        "balance_P_ETc_mm": balance_total,
        "demanda_no_cubierta_mm": demanda_total,

        "cobertura_precipitacion_pct": cobertura,
        "indicador_balance": indicador_balance_val,

        "sm_rootzone_media": smap_media,
        "sm_rootzone_min": smap_min,
        "sm_rootzone_max": smap_max,

        "smap_percentil_medio": smap_percentil_medio,
        "smap_percentil_min": smap_percentil_min,
        "smap_percentil_max": smap_percentil_max,

        "dias_humedad_bajo_P10": dias_bajo_p10,
        "porcentaje_humedad_bajo_P10": porcentaje_bajo_p10
    }

    return resultado

def construir_resumen_escenario(
    id_escenario,
    numero_etapas,
    etapas
):

    precipitacion = sum(
        e["precipitacion_mm"]
        for e in etapas
    )

    eto_total = sum(
        e["ETo_mm"]
        for e in etapas
    )

    etc_total = sum(
        e["ETc_mm"]
        for e in etapas
    )

    balance_total = sum(
        e["balance_P_ETc_mm"]
        for e in etapas
    )

    demanda_total = sum(
        e["demanda_no_cubierta_mm"]
        for e in etapas
    )

    dias_total = sum(
        e["dias"]
        for e in etapas
    )

    cobertura = cobertura_precipitacion(
        precipitacion,
        etc_total
    )

    indicador_balance_total = indicador_balance(
        balance_total,
        etc_total
    )

    temperatura_media = np.average(
        [e["temperatura_media_c"] for e in etapas],
        weights=[e["dias"] for e in etapas]
    )

    indicador_temperatura_total = np.average(
        [e["indicador_temperatura"] for e in etapas],
        weights=[e["dias"] for e in etapas]
    )

    smap_media = np.average(
        [e["sm_rootzone_media"] for e in etapas],
        weights=[e["dias"] for e in etapas]
    )

    smap_percentil = np.average(
        [e["smap_percentil_medio"] for e in etapas],
        weights=[e["dias"] for e in etapas]
    )

    dias_bajo_p10 = sum(
        e["dias_humedad_bajo_P10"]
        for e in etapas
    )

    nombres = " → ".join(
        e["cultivo"]
        for e in etapas
    )

    return {
        "id_escenario": id_escenario,
        "numero_etapas": numero_etapas,
        "rotacion": nombres,
        "dias_totales": dias_total,

        "temperatura_media_c": temperatura_media,
        "indicador_temperatura": indicador_temperatura_total,

        "precipitacion_total_mm": precipitacion,
        "ETo_total_mm": eto_total,
        "ETc_total_mm": etc_total,

        "balance_P_ETc_total_mm": balance_total,
        "demanda_no_cubierta_total_mm": demanda_total,

        "cobertura_precipitacion_pct": cobertura,
        "indicador_balance": indicador_balance_total,

        "sm_rootzone_media": smap_media,
        "smap_percentil_medio": smap_percentil,

        "dias_humedad_bajo_P10": dias_bajo_p10
    }

# ============================================================
# GENERACIÓN DE ESCENARIOS
# ============================================================

nombres_cultivos = list(cultivo_info.keys())

escenarios = []
etapas_resultado = []

fecha_inicio_global = ambiental["fecha"].min()
fecha_fin_global = ambiental["fecha"].max()

contador = 1

print("\nPeriodo disponible:")
print(f"  {fecha_inicio_global.date()} -> {fecha_fin_global.date()}")


# ============================================================
# ESCENARIOS DE 2 ETAPAS
# ============================================================

for cultivo_a, cultivo_b in permutations(nombres_cultivos, 2):

    ciclo_a = cultivo_info[cultivo_a]["ciclo"]
    ciclo_b = cultivo_info[cultivo_b]["ciclo"]

    duracion_total = ciclo_a + ciclo_b

    fecha_inicio = fecha_inicio_global

    fecha_fin = (
        fecha_inicio
        + pd.Timedelta(days=duracion_total - 1)
    )

    # Debe caber completamente dentro de 2020
    if fecha_fin > fecha_fin_global:
        continue

    fecha_fin_a = (
        fecha_inicio
        + pd.Timedelta(days=ciclo_a - 1)
    )

    fecha_inicio_b = fecha_fin_a + pd.Timedelta(days=1)

    fecha_fin_b = fecha_fin

    etapa_a = analizar_etapa(
        cultivo_a,
        fecha_inicio,
        fecha_fin_a,
        1
    )

    etapa_b = analizar_etapa(
        cultivo_b,
        fecha_inicio_b,
        fecha_fin_b,
        2
    )

    if etapa_a is None or etapa_b is None:
        continue

    etapas = [etapa_a, etapa_b]

    for etapa in etapas:
        etapa["id_escenario"] = contador
        etapa["numero_etapas"] = 2
        etapas_resultado.append(etapa)

    # --------------------------------------------------------
    # Resumen del escenario
    # --------------------------------------------------------

    escenario = construir_resumen_escenario(
        contador,
        2,
        [etapa_a, etapa_b]
    )

    escenarios.append(escenario)

    contador += 1


# ============================================================
# ESCENARIOS DE 3 ETAPAS
# ============================================================

for cultivo_a, cultivo_b, cultivo_c in permutations(
    nombres_cultivos,
    3
):

    ciclo_a = cultivo_info[cultivo_a]["ciclo"]
    ciclo_b = cultivo_info[cultivo_b]["ciclo"]
    ciclo_c = cultivo_info[cultivo_c]["ciclo"]

    duracion_total = ciclo_a + ciclo_b + ciclo_c

    fecha_inicio = fecha_inicio_global

    fecha_fin = (
        fecha_inicio
        + pd.Timedelta(days=duracion_total - 1)
    )

    if fecha_fin > fecha_fin_global:
        continue

    # Etapa 1
    fecha_fin_a = (
        fecha_inicio
        + pd.Timedelta(days=ciclo_a - 1)
    )

    # Etapa 2
    fecha_inicio_b = fecha_fin_a + pd.Timedelta(days=1)

    fecha_fin_b = (
        fecha_inicio_b
        + pd.Timedelta(days=ciclo_b - 1)
    )

    # Etapa 3
    fecha_inicio_c = fecha_fin_b + pd.Timedelta(days=1)

    fecha_fin_c = fecha_fin

    etapa_a = analizar_etapa(
        cultivo_a,
        fecha_inicio,
        fecha_fin_a,
        1
    )

    etapa_b = analizar_etapa(
        cultivo_b,
        fecha_inicio_b,
        fecha_fin_b,
        2
    )

    etapa_c = analizar_etapa(
        cultivo_c,
        fecha_inicio_c,
        fecha_fin_c,
        3
    )

    if (
        etapa_a is None
        or etapa_b is None
        or etapa_c is None
    ):
        continue

    etapas = [
        etapa_a,
        etapa_b,
        etapa_c
    ]

    for etapa in etapas:
        etapa["id_escenario"] = contador
        etapa["numero_etapas"] = 3
        etapas_resultado.append(etapa)

    escenario = construir_resumen_escenario(
        contador,
        3,
        etapas
    )

    escenarios.append(escenario)

    contador += 1


# ============================================================
# FUNCIÓN PARA CONSTRUIR RESUMEN
# ============================================================



# ============================================================
# GUARDAR RESULTADOS
# ============================================================

df_escenarios = pd.DataFrame(escenarios)
df_etapas = pd.DataFrame(etapas_resultado)

# Ordenar escenarios por cobertura de precipitación
df_escenarios = df_escenarios.sort_values(
    "cobertura_precipitacion_pct",
    ascending=False
).reset_index(drop=True)

df_etapas = df_etapas.sort_values(
    ["id_escenario", "etapa"]
).reset_index(drop=True)

df_escenarios.to_csv(
    SALIDA_RESUMEN,
    index=False,
    encoding="utf-8-sig"
)

df_etapas.to_csv(
    SALIDA_ETAPAS,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# RESULTADOS
# ============================================================

print("\n" + "=" * 70)
print("RESULTADOS V4")
print("=" * 70)

print(f"\nEscenarios válidos: {len(df_escenarios)}")

print(
    f"  Escenarios de 2 etapas: "
    f"{(df_escenarios['numero_etapas'] == 2).sum()}"
)

print(
    f"  Escenarios de 3 etapas: "
    f"{(df_escenarios['numero_etapas'] == 3).sum()}"
)

print("\nPrimeros escenarios por cobertura de precipitación:\n")

columnas_mostrar = [
    "id_escenario",
    "rotacion",
    "dias_totales",
    "precipitacion_total_mm",
    "ETo_total_mm",
    "ETc_total_mm",
    "balance_P_ETc_total_mm",
    "cobertura_precipitacion_pct",
    "sm_rootzone_media",
    "smap_percentil_medio",
    "dias_humedad_bajo_P10"
]

print(
    df_escenarios[
        columnas_mostrar
    ].head(15).to_string(index=False)
)

print("\nArchivos generados:")

print(
    f"  {SALIDA_RESUMEN}"
)

print(
    f"  {SALIDA_ETAPAS}"
)

print("\nProceso terminado.")
import os
import sys
from pathlib import Path

import earthaccess
import h5py
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agroshift.regions import get_region
from agroshift.retry import con_reintentos
from agroshift.smap_sampling import un_granulo_por_dia

REGION = get_region(os.environ.get("AGROSHIFT_REGION", "santander"))
FECHA_INICIO = os.environ.get("AGROSHIFT_FECHA_INICIO", "2020-01-01")
FECHA_FIN = os.environ.get("AGROSHIFT_FECHA_FIN", "2025-12-31")


# ============================================================
# CONFIGURACIÓN
# ============================================================

LATITUD_OBJETIVO = REGION.latitud
LONGITUD_OBJETIVO = REGION.longitud

FILA_SMAP = REGION.fila_smap
COLUMNA_SMAP = REGION.columna_smap

BASE_DIR = Path(__file__).resolve().parent

SMAP_DIR = BASE_DIR / "data" / "smap"
ANALYSIS_DIR = BASE_DIR / "data" / "analysis" / REGION.slug

SMAP_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)


# Archivo histórico actual
ARCHIVO_HISTORICO = (
    ANALYSIS_DIR / "smap_historico_2020.csv"
)

# Archivo diario actual
ARCHIVO_DIARIO = (
    ANALYSIS_DIR / "smap_diario_2020.csv"
)


# ============================================================
# DÍAS CON DATOS FALTANTES
#
# Se detectan automáticamente: cualquier día del rango pedido
# que no llegue a las 8 observaciones esperadas (una cada 3h),
# incluyendo días que no aparecen en absoluto en el diario.
# ============================================================

rango_completo = pd.date_range(
    FECHA_INICIO, FECHA_FIN, freq="D"
).strftime("%Y-%m-%d").tolist()

if ARCHIVO_DIARIO.exists():

    df_diario_actual = pd.read_csv(ARCHIVO_DIARIO)

    observaciones_por_dia = (
        df_diario_actual
        .set_index("fecha")["observaciones_smap"]
        .to_dict()
    )

else:

    observaciones_por_dia = {}

DIAS_INCOMPLETOS = [
    dia for dia in rango_completo
    if observaciones_por_dia.get(dia, 0) < 1
]


# ============================================================
# FUNCIONES
# ============================================================

def convertir_tiempo(valor):
    """
    Convierte el tiempo SMAP a fecha UTC.
    """

    return pd.to_datetime(
        valor,
        unit="s",
        origin="2000-01-01 11:58:55.816",
        utc=True
    )


def extraer_datos_archivo(archivo):
    """
    Extrae los datos de la celda SMAP correspondiente
    a la ubicación objetivo.
    """

    try:

        with h5py.File(archivo, "r") as h5:

            geophysical = h5["Geophysical_Data"]

            datos = {}

            datasets = [
                "sm_surface",
                "sm_rootzone",
                "sm_surface_wetness",
                "sm_rootzone_wetness",
                "soil_temp_layer1"
            ]

            for nombre in datasets:

                dataset = geophysical[nombre]

                valor = dataset[
                    FILA_SMAP,
                    COLUMNA_SMAP
                ]

                if not np.isfinite(valor):
                    valor = np.nan

                datos[nombre] = float(valor)

            tiempo = h5["time"][0]

            datos["fecha_hora"] = convertir_tiempo(
                tiempo
            )

            datos["archivo_smap"] = archivo.name

            datos["soil_temp_layer1_celsius"] = (
                datos["soil_temp_layer1"] - 273.15
            )

            datos["latitud"] = LATITUD_OBJETIVO
            datos["longitud"] = LONGITUD_OBJETIVO

            return datos

    except Exception as error:

        print(
            f"\nERROR procesando {archivo.name}:"
        )

        print(error)

        return None


# ============================================================
# INICIO
# ============================================================

print("=" * 70)
print("RECUPERACIÓN DE SMAP FALTANTE - AGROSHIFT")
print(f"Región: {REGION.nombre}")
print("=" * 70)

print(f"\nDías incompletos detectados: {len(DIAS_INCOMPLETOS)}")

for dia in DIAS_INCOMPLETOS:
    print(f"  - {dia}")

if not DIAS_INCOMPLETOS:

    print("\nNo hay días por recuperar. Nada que hacer.")

    raise SystemExit(0)


# ============================================================
# COMPROBAR HISTÓRICO
# ============================================================

print("\n" + "=" * 70)
print("CARGANDO HISTÓRICO ACTUAL")
print("=" * 70)

if not ARCHIVO_HISTORICO.exists():

    raise FileNotFoundError(
        f"No existe:\n{ARCHIVO_HISTORICO}"
    )


df = pd.read_csv(
    ARCHIVO_HISTORICO
)

df["fecha_hora"] = pd.to_datetime(
    df["fecha_hora"],
    utc=True
)

print(
    f"\nRegistros actuales: {len(df)}"
)


# ============================================================
# AUTENTICACIÓN
# ============================================================

print("\n" + "=" * 70)
print("AUTENTICACIÓN NASA EARTHDATA")
print("=" * 70)

earthaccess.login()

print("\nAutenticación completada.")


# ============================================================
# RECUPERAR DATOS (búsqueda con reintentos + descarga en lotes)
#
# Esta etapa falló una vez corriendo ~8h: se caía por completo con
# el primer corte de red porque buscaba y descargaba un día a la vez,
# sin reintentos. Ahora reintenta cada llamada de red y descarga en
# lotes paralelos como el script 02.
# ============================================================

print("\nBuscando gránulos de los días incompletos...")

candidatos = []

for dia in DIAS_INCOMPLETOS:

    fecha_inicio_dia = pd.Timestamp(dia, tz="UTC")
    fecha_fin_dia = fecha_inicio_dia + pd.Timedelta(days=1)

    try:
        resultados = con_reintentos(
            lambda: earthaccess.search_data(
                short_name="SPL4SMGP",
                temporal=(dia, dia),
                bounding_box=(
                    LONGITUD_OBJETIVO,
                    LATITUD_OBJETIVO,
                    LONGITUD_OBJETIVO,
                    LATITUD_OBJETIVO,
                ),
            )
        )
    except Exception as error:
        print(f"  {dia}: búsqueda falló tras varios intentos ({error}).")
        continue

    for granulo in un_granulo_por_dia(resultados):
        candidatos.append((fecha_inicio_dia, fecha_fin_dia, granulo))

print(f"Gránulos candidatos a descargar: {len(candidatos)}")

registros_nuevos = []
errores = 0

TAMANO_LOTE = 40

for inicio_lote in range(0, len(candidatos), TAMANO_LOTE):

    lote = candidatos[inicio_lote:inicio_lote + TAMANO_LOTE]
    granulos_lote = [g for _, _, g in lote]

    print(
        f"\n--- Lote {inicio_lote // TAMANO_LOTE + 1} "
        f"({inicio_lote + 1}-{inicio_lote + len(lote)} de {len(candidatos)}) ---"
    )

    try:
        archivos_descargados = con_reintentos(
            lambda: earthaccess.download(granulos_lote, local_path=SMAP_DIR)
        )
    except Exception as error:
        print(f"  ERROR descargando el lote tras varios intentos: {error}")
        errores += len(lote)
        continue

    for (fecha_inicio_dia, fecha_fin_dia, _), ruta_descargada in zip(
        lote, archivos_descargados
    ):

        archivo_local = Path(ruta_descargada)

        try:
            if not archivo_local.exists():
                errores += 1
                continue

            datos = extraer_datos_archivo(archivo_local)

            if datos is None:
                errores += 1
                continue

            fecha_hora = datos["fecha_hora"]

            existentes = df[
                (df["fecha_hora"] >= fecha_inicio_dia)
                & (df["fecha_hora"] < fecha_fin_dia)
            ]
            horas_existentes = set(existentes["fecha_hora"])

            if not (fecha_inicio_dia <= fecha_hora < fecha_fin_dia):
                continue

            if fecha_hora in horas_existentes:
                continue

            registros_nuevos.append(datos)
            print(f"  {fecha_hora}: registro recuperado "
                  f"(sm_surface={datos['sm_surface']:.4f})")

        except Exception as error:
            print(f"  ERROR procesando {archivo_local.name}: {error}")
            errores += 1

        finally:
            if archivo_local.exists():
                archivo_local.unlink()


# ============================================================
# RESULTADO DE LA RECUPERACIÓN
# ============================================================

print("\n" + "=" * 70)
print("RESULTADO DE LA RECUPERACIÓN")
print("=" * 70)

print(
    f"\nNuevos registros recuperados: "
    f"{len(registros_nuevos)}"
)

print(
    f"Errores: {errores}"
)


# ============================================================
# AGREGAR NUEVOS REGISTROS
# ============================================================

if registros_nuevos:

    df_nuevos = pd.DataFrame(
        registros_nuevos
    )

    df = pd.concat(
        [
            df,
            df_nuevos
        ],
        ignore_index=True
    )

    # Eliminar duplicados por fecha/hora
    df = df.drop_duplicates(
        subset=["fecha_hora"],
        keep="first"
    )

    # Ordenar
    df = df.sort_values(
        "fecha_hora"
    ).reset_index(drop=True)


# ============================================================
# FILTRAR AL RANGO SOLICITADO
# ============================================================

fecha_inicio_rango = pd.Timestamp(
    FECHA_INICIO,
    tz="UTC"
)

fecha_fin_rango = (
    pd.Timestamp(FECHA_FIN, tz="UTC")
    + pd.Timedelta(days=1)
)

df = df[
    (df["fecha_hora"] >= fecha_inicio_rango)
    &
    (df["fecha_hora"] < fecha_fin_rango)
].copy()


# ============================================================
# CREAR FECHA
# ============================================================

df["fecha"] = (
    df["fecha_hora"]
    .dt.date
)


# ============================================================
# ORDEN DE COLUMNAS
# ============================================================

columnas = [
    "fecha",
    "fecha_hora",
    "latitud",
    "longitud",
    "sm_surface",
    "sm_rootzone",
    "sm_surface_wetness",
    "sm_rootzone_wetness",
    "soil_temp_layer1",
    "soil_temp_layer1_celsius",
    "archivo_smap"
]

df = df[columnas]


# ============================================================
# GUARDAR HISTÓRICO ACTUALIZADO
# ============================================================

df.to_csv(
    ARCHIVO_HISTORICO,
    index=False
)

print(
    "\nHistórico actualizado:"
)

print(
    ARCHIVO_HISTORICO
)


# ============================================================
# GENERAR RESUMEN DIARIO
# ============================================================

columnas_promedio = [
    "sm_surface",
    "sm_rootzone",
    "sm_surface_wetness",
    "sm_rootzone_wetness",
    "soil_temp_layer1_celsius"
]

df_diario = (
    df.groupby("fecha")
    [columnas_promedio]
    .mean()
    .reset_index()
)

observaciones = (
    df.groupby("fecha")
    .size()
    .reset_index(
        name="observaciones_smap"
    )
)

df_diario = df_diario.merge(
    observaciones,
    on="fecha",
    how="left"
)

df_diario.to_csv(
    ARCHIVO_DIARIO,
    index=False
)

print(
    "\nResumen diario actualizado:"
)

print(
    ARCHIVO_DIARIO
)


# ============================================================
# VERIFICACIÓN FINAL
# ============================================================

print("\n" + "=" * 70)
print("VERIFICACIÓN FINAL")
print("=" * 70)

print(
    f"\nRegistros SMAP: {len(df)}"
)

print(
    f"Días con información: "
    f"{df['fecha'].nunique()}"
)

print(
    "\nObservaciones por día:"
)

print(
    df_diario[
        "observaciones_smap"
    ]
    .value_counts()
    .sort_index()
)


# ============================================================
# REVISAR DÍAS INCOMPLETOS
# ============================================================

dias_incompletos_final = (
    df_diario[
        df_diario["observaciones_smap"] < 1
    ]
)

if dias_incompletos_final.empty:

    print(
        "\n✓ TODOS LOS DÍAS TIENEN AL MENOS 1 OBSERVACIÓN."
    )

else:

    print(
        "\nDías que todavía tienen menos de "
        "8 observaciones:"
    )

    print(
        dias_incompletos_final[
            [
                "fecha",
                "observaciones_smap"
            ]
        ].to_string(index=False)
    )


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("RECUPERACIÓN TERMINADA")
print("=" * 70)
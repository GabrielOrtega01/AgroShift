from pathlib import Path

import earthaccess
import h5py
import numpy as np
import pandas as pd


# ============================================================
# CONFIGURACIÓN
# ============================================================

LATITUD_OBJETIVO = 7.119
LONGITUD_OBJETIVO = -73.122

FECHA_INICIO = "2020-01-01"
FECHA_FIN = "2020-12-31"

BASE_DIR = Path(__file__).resolve().parent

SMAP_DIR = BASE_DIR / "data" / "smap"
ANALYSIS_DIR = BASE_DIR / "data" / "analysis"

SMAP_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)


# Archivo donde se irá guardando el progreso
ARCHIVO_PROGRESO = ANALYSIS_DIR / "smap_historico_2020_progreso.csv"

# Archivos finales
ARCHIVO_HISTORICO = ANALYSIS_DIR / "smap_historico_2020.csv"
ARCHIVO_DIARIO = ANALYSIS_DIR / "smap_diario_2020.csv"


# Celda SMAP identificada anteriormente
FILA_SMAP = 711
COLUMNA_SMAP = 1144


# ============================================================
# FUNCIONES
# ============================================================

def convertir_tiempo(valor):
    """
    Convierte el tiempo utilizado por SMAP.
    """

    return pd.to_datetime(
        valor,
        unit="s",
        origin="2000-01-01 11:58:55.816",
        utc=True
    )


def extraer_datos_archivo(archivo):
    """
    Extrae únicamente los datos de la celda SMAP
    correspondiente a la ubicación objetivo.
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

            return datos

    except Exception as error:

        print(
            f"\nERROR leyendo {archivo.name}:"
        )

        print(error)

        return None


def cargar_progreso():

    if not ARCHIVO_PROGRESO.exists():

        return pd.DataFrame()

    try:

        df = pd.read_csv(
            ARCHIVO_PROGRESO
        )

        if "fecha_hora" in df.columns:

            df["fecha_hora"] = pd.to_datetime(
                df["fecha_hora"],
                utc=True
            )

        return df

    except Exception as error:

        print(
            "\nNo se pudo leer el archivo de progreso."
        )

        print(error)

        return pd.DataFrame()


def guardar_progreso(df):

    df.to_csv(
        ARCHIVO_PROGRESO,
        index=False
    )


# ============================================================
# INICIO
# ============================================================

print("=" * 70)
print("SMAP HISTÓRICO 2020 - AGROSHIFT")
print("=" * 70)

print(
    f"\nPeriodo: {FECHA_INICIO} -> {FECHA_FIN}"
)

print(
    f"Coordenadas: "
    f"{LATITUD_OBJETIVO}, {LONGITUD_OBJETIVO}"
)

print(
    f"Celda SMAP: fila {FILA_SMAP}, "
    f"columna {COLUMNA_SMAP}"
)


# ============================================================
# CARGAR PROGRESO EXISTENTE
# ============================================================

print("\n" + "=" * 70)
print("REVISANDO PROGRESO")
print("=" * 70)

df_progreso = cargar_progreso()

archivos_procesados = set()

if not df_progreso.empty:

    archivos_procesados = set(
        df_progreso["archivo_smap"]
        .dropna()
        .astype(str)
    )

    print(
        f"\nRegistros encontrados en progreso: "
        f"{len(df_progreso)}"
    )

    print(
        f"Archivos ya procesados: "
        f"{len(archivos_procesados)}"
    )

else:

    print("\nNo existe progreso anterior.")

    print(
        "El procesamiento comenzará desde el inicio."
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
# BÚSQUEDA
# ============================================================

print("\n" + "=" * 70)
print("BÚSQUEDA DE GRANULOS SMAP")
print("=" * 70)

print("\nBuscando datos...")

resultados = earthaccess.search_data(
    short_name="SPL4SMGP",
    temporal=(
        FECHA_INICIO,
        FECHA_FIN
    ),
    bounding_box=(
        LONGITUD_OBJETIVO,
        LATITUD_OBJETIVO,
        LONGITUD_OBJETIVO,
        LATITUD_OBJETIVO
    )
)

print(
    f"\nGranulos encontrados: "
    f"{len(resultados)}"
)

if len(resultados) == 0:

    raise RuntimeError(
        "No se encontraron datos SMAP."
    )


# ============================================================
# PROCESAMIENTO
# ============================================================

print("\n" + "=" * 70)
print("PROCESAMIENTO")
print("=" * 70)

registros_nuevos = []

errores = 0
omitidos = 0


for numero, granulo in enumerate(
    resultados,
    start=1
):

    try:

        # ----------------------------------------------------
        # OBTENER NOMBRE
        # ----------------------------------------------------

        data_links = granulo.data_links()

        if not data_links:

            print(
                f"\n[{numero}/{len(resultados)}] "
                "Sin enlace de descarga."
            )

            errores += 1
            continue

        url = data_links[0]

        nombre_archivo = Path(url).name

        # ----------------------------------------------------
        # COMPROBAR SI YA FUE PROCESADO
        # ----------------------------------------------------

        if nombre_archivo in archivos_procesados:

            omitidos += 1

            if numero % 100 == 0:

                print(
                    f"\n[{numero}/{len(resultados)}] "
                    f"Ya procesado: {nombre_archivo}"
                )

            continue

        print(
            f"\n[{numero}/{len(resultados)}] "
            f"{nombre_archivo}"
        )

        # ----------------------------------------------------
        # DESCARGAR
        # ----------------------------------------------------

        archivo_local = SMAP_DIR / nombre_archivo

        if archivo_local.exists():

            print(
                "  Archivo temporal encontrado."
            )

        else:

            print(
                "  Descargando archivo..."
            )

            archivos_descargados = (
                earthaccess.download(
                    granulo,
                    local_path=SMAP_DIR
                )
            )

            if not archivos_descargados:

                print(
                    "  No fue posible descargar."
                )

                errores += 1

                continue

            archivo_local = Path(
                archivos_descargados[0]
            )

        # ----------------------------------------------------
        # EXTRAER DATOS
        # ----------------------------------------------------

        datos = extraer_datos_archivo(
            archivo_local
        )

        if datos is None:

            errores += 1

            if archivo_local.exists():

                archivo_local.unlink()

            continue

        # ----------------------------------------------------
        # FILTRAR FECHA
        # ----------------------------------------------------

        fecha_inicio = pd.Timestamp(
            FECHA_INICIO,
            tz="UTC"
        )

        fecha_fin = (
            pd.Timestamp(
                FECHA_FIN,
                tz="UTC"
            )
            + pd.Timedelta(days=1)
        )

        if not (
            fecha_inicio
            <= datos["fecha_hora"]
            < fecha_fin
        ):

            print(
                "  Granulo fuera del periodo exacto."
            )

            if archivo_local.exists():

                archivo_local.unlink()

            archivos_procesados.add(
                nombre_archivo
            )

            continue

        # ----------------------------------------------------
        # TEMPERATURA DEL SUELO
        # ----------------------------------------------------

        datos[
            "soil_temp_layer1_celsius"
        ] = (
            datos["soil_temp_layer1"]
            - 273.15
        )

        # ----------------------------------------------------
        # COORDENADAS
        # ----------------------------------------------------

        datos["latitud"] = LATITUD_OBJETIVO
        datos["longitud"] = LONGITUD_OBJETIVO

        # ----------------------------------------------------
        # AGREGAR REGISTRO
        # ----------------------------------------------------

        registros_nuevos.append(
            datos
        )

        archivos_procesados.add(
            nombre_archivo
        )

        print(
            "  Datos extraídos correctamente."
        )

        print(
            f"  Humedad superficial: "
            f"{datos['sm_surface']:.4f}"
        )

        print(
            f"  Humedad raíz: "
            f"{datos['sm_rootzone']:.4f}"
        )

        # ----------------------------------------------------
        # GUARDAR PROGRESO
        # ----------------------------------------------------

        df_nuevos = pd.DataFrame(
            registros_nuevos
        )

        df_actualizado = pd.concat(
            [
                df_progreso,
                df_nuevos
            ],
            ignore_index=True
        )

        guardar_progreso(
            df_actualizado
        )

        # Actualizar dataframe en memoria
        df_progreso = df_actualizado

        registros_nuevos = []

        print(
            "  Progreso guardado."
        )

        # ----------------------------------------------------
        # ELIMINAR HDF5
        # ----------------------------------------------------

        if archivo_local.exists():

            archivo_local.unlink()

            print(
                "  Archivo .h5 eliminado."
            )

    except Exception as error:

        print(
            f"\n  ERROR: {error}"
        )

        errores += 1


# ============================================================
# DATASET FINAL
# ============================================================

print("\n" + "=" * 70)
print("GENERANDO DATASET FINAL")
print("=" * 70)

df = cargar_progreso()

if df.empty:

    raise RuntimeError(
        "No existen registros procesados."
    )


# ============================================================
# CONVERTIR FECHA
# ============================================================

df["fecha_hora"] = pd.to_datetime(
    df["fecha_hora"],
    utc=True
)


# ============================================================
# FILTRO EXACTO
# ============================================================

fecha_inicio = pd.Timestamp(
    FECHA_INICIO,
    tz="UTC"
)

fecha_fin = (
    pd.Timestamp(
        FECHA_FIN,
        tz="UTC"
    )
    + pd.Timedelta(days=1)
)

df = df[
    (df["fecha_hora"] >= fecha_inicio)
    &
    (df["fecha_hora"] < fecha_fin)
].copy()


# ============================================================
# ELIMINAR DUPLICADOS
# ============================================================

df = df.drop_duplicates(
    subset=["fecha_hora"],
    keep="last"
)


# ============================================================
# ORDENAR
# ============================================================

df = df.sort_values(
    "fecha_hora"
).reset_index(drop=True)


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
# GUARDAR HISTÓRICO
# ============================================================

df.to_csv(
    ARCHIVO_HISTORICO,
    index=False
)

print(
    f"\nDataset histórico:"
)

print(
    ARCHIVO_HISTORICO
)


# ============================================================
# RESUMEN DIARIO
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


# ============================================================
# ESTADÍSTICAS
# ============================================================

print("\n" + "=" * 70)
print("ESTADÍSTICAS")
print("=" * 70)

print(
    f"\nRegistros SMAP: {len(df)}"
)

print(
    f"Días con información: "
    f"{df['fecha'].nunique()}"
)

print(
    f"Errores durante esta ejecución: "
    f"{errores}"
)

print(
    f"Granulos omitidos por estar procesados: "
    f"{omitidos}"
)

print(
    f"\nHumedad superficial:"
)

print(
    f"  Media: {df['sm_surface'].mean():.4f}"
)

print(
    f"  Mínima: {df['sm_surface'].min():.4f}"
)

print(
    f"  Máxima: {df['sm_surface'].max():.4f}"
)

print(
    f"\nHumedad zona radicular:"
)

print(
    f"  Media: {df['sm_rootzone'].mean():.4f}"
)

print(
    f"  Mínima: {df['sm_rootzone'].min():.4f}"
)

print(
    f"  Máxima: {df['sm_rootzone'].max():.4f}"
)

print(
    f"\nTemperatura del suelo:"
)

print(
    f"  Media: "
    f"{df['soil_temp_layer1_celsius'].mean():.2f} °C"
)

print(
    f"  Mínima: "
    f"{df['soil_temp_layer1_celsius'].min():.2f} °C"
)

print(
    f"  Máxima: "
    f"{df['soil_temp_layer1_celsius'].max():.2f} °C"
)


# ============================================================
# OBSERVACIONES POR DÍA
# ============================================================

print("\n" + "=" * 70)
print("OBSERVACIONES POR DÍA")
print("=" * 70)

print(
    df_diario["observaciones_smap"]
    .value_counts()
    .sort_index()
)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("PROCESO COMPLETADO")
print("=" * 70)

print(
    "\nArchivos generados:"
)

print(
    f"  - {ARCHIVO_HISTORICO}"
)

print(
    f"  - {ARCHIVO_DIARIO}"
)

print(
    f"  - {ARCHIVO_PROGRESO}"
)

print(
    "\nLos archivos .h5 se eliminan después "
    "de extraer sus datos."
)

print(
    "\nSMAP histórico 2020 listo."
)
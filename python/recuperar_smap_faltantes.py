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

FILA_SMAP = 711
COLUMNA_SMAP = 1144

BASE_DIR = Path(__file__).resolve().parent

SMAP_DIR = BASE_DIR / "data" / "smap"
ANALYSIS_DIR = BASE_DIR / "data" / "analysis"

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
# ============================================================

DIAS_INCOMPLETOS = [
    "2020-10-25",
    "2020-10-26",
    "2020-11-04",
    "2020-11-05"
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
print("=" * 70)

print("\nDías que serán revisados:")

for dia in DIAS_INCOMPLETOS:
    print(f"  - {dia}")


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
# RECUPERAR DATOS
# ============================================================

registros_nuevos = []

errores = 0


for dia in DIAS_INCOMPLETOS:

    print("\n" + "=" * 70)
    print(f"REVISANDO {dia}")
    print("=" * 70)

    fecha_inicio = pd.Timestamp(
        dia,
        tz="UTC"
    )

    fecha_fin = (
        fecha_inicio
        + pd.Timedelta(days=1)
    )

    # --------------------------------------------------------
    # HORAS QUE YA TENEMOS
    # --------------------------------------------------------

    existentes = df[
        (df["fecha_hora"] >= fecha_inicio)
        &
        (df["fecha_hora"] < fecha_fin)
    ]

    horas_existentes = set(
        existentes["fecha_hora"]
    )

    print(
        f"\nObservaciones existentes: "
        f"{len(existentes)}"
    )

    # --------------------------------------------------------
    # BUSCAR GRANULOS DEL DÍA
    # --------------------------------------------------------

    print(
        "\nBuscando granulos NASA..."
    )

    resultados = earthaccess.search_data(
        short_name="SPL4SMGP",
        temporal=(
            dia,
            dia
        ),
        bounding_box=(
            LONGITUD_OBJETIVO,
            LATITUD_OBJETIVO,
            LONGITUD_OBJETIVO,
            LATITUD_OBJETIVO
        )
    )

    print(
        f"Granulos encontrados: "
        f"{len(resultados)}"
    )

    if not resultados:

        print(
            "No se encontraron granulos."
        )

        continue

    # --------------------------------------------------------
    # PROCESAR GRANULOS
    # --------------------------------------------------------

    for numero, granulo in enumerate(
        resultados,
        start=1
    ):

        try:

            enlaces = granulo.data_links()

            if not enlaces:

                print(
                    "  Granulo sin enlace."
                )

                errores += 1
                continue

            url = enlaces[0]

            nombre_archivo = Path(url).name

            print(
                f"\n  [{numero}/{len(resultados)}] "
                f"{nombre_archivo}"
            )

            archivo_local = (
                SMAP_DIR / nombre_archivo
            )

            # ------------------------------------------------
            # DESCARGAR
            # ------------------------------------------------

            if archivo_local.exists():

                print(
                    "  Archivo local encontrado."
                )

            else:

                print(
                    "  Descargando..."
                )

                archivos = earthaccess.download(
                    granulo,
                    local_path=SMAP_DIR
                )

                if not archivos:

                    print(
                        "  No se pudo descargar."
                    )

                    errores += 1
                    continue

                archivo_local = Path(
                    archivos[0]
                )

            # ------------------------------------------------
            # EXTRAER
            # ------------------------------------------------

            datos = extraer_datos_archivo(
                archivo_local
            )

            if datos is None:

                errores += 1

                if archivo_local.exists():
                    archivo_local.unlink()

                continue

            fecha_hora = datos["fecha_hora"]

            # ------------------------------------------------
            # VERIFICAR QUE PERTENEZCA AL DÍA
            # ------------------------------------------------

            if not (
                fecha_inicio
                <= fecha_hora
                < fecha_fin
            ):

                print(
                    "  Fuera del día solicitado."
                )

                if archivo_local.exists():
                    archivo_local.unlink()

                continue

            # ------------------------------------------------
            # VERIFICAR SI YA EXISTE
            # ------------------------------------------------

            if fecha_hora in horas_existentes:

                print(
                    "  Esta observación ya existe."
                )

                if archivo_local.exists():
                    archivo_local.unlink()

                continue

            # ------------------------------------------------
            # NUEVO REGISTRO
            # ------------------------------------------------

            registros_nuevos.append(
                datos
            )

            horas_existentes.add(
                fecha_hora
            )

            print(
                "  NUEVO registro recuperado."
            )

            print(
                f"  Fecha: {fecha_hora}"
            )

            print(
                f"  Humedad superficial: "
                f"{datos['sm_surface']:.4f}"
            )

            print(
                f"  Humedad raíz: "
                f"{datos['sm_rootzone']:.4f}"
            )

            # ------------------------------------------------
            # ELIMINAR H5
            # ------------------------------------------------

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
# FILTRAR TODO 2020
# ============================================================

fecha_inicio_2020 = pd.Timestamp(
    "2020-01-01",
    tz="UTC"
)

fecha_fin_2020 = pd.Timestamp(
    "2021-01-01",
    tz="UTC"
)

df = df[
    (df["fecha_hora"] >= fecha_inicio_2020)
    &
    (df["fecha_hora"] < fecha_fin_2020)
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
        df_diario["observaciones_smap"] < 8
    ]
)

if dias_incompletos_final.empty:

    print(
        "\n✓ TODOS LOS DÍAS TIENEN 8 OBSERVACIONES."
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
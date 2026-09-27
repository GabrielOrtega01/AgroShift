from pathlib import Path
import numpy as np
import pandas as pd
import h5py
import earthaccess


# ============================================================
# CONFIGURACIÓN
# ============================================================

LATITUD = 7.119
LONGITUD = -73.122

FECHA_INICIO = "2020-01-01"
FECHA_FIN = "2020-01-07"

# Celda SMAP encontrada anteriormente
FILA = 711
COLUMNA = 1144

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "smap"
OUTPUT_DIR = BASE_DIR / "data" / "analysis"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# AUTENTICACIÓN NASA EARTHDATA
# ============================================================

print("Autenticando con NASA Earthdata...")

earthaccess.login()

print("Autenticación correcta.")


# ============================================================
# BÚSQUEDA DE GRANULOS SMAP
# ============================================================

print()
print("Buscando datos SMAP...")
print(f"Periodo: {FECHA_INICIO} -> {FECHA_FIN}")

resultados = earthaccess.search_data(
    short_name="SPL4SMGP",
    temporal=(FECHA_INICIO, FECHA_FIN),
    bounding_box=(
        LONGITUD,
        LATITUD,
        LONGITUD,
        LATITUD
    )
)

print(f"Granulos encontrados: {len(resultados)}")


if not resultados:
    raise RuntimeError("No se encontraron datos SMAP para el periodo indicado.")


# ============================================================
# DESCARGA
# ============================================================

print()
print("Descargando archivos SMAP...")

archivos = earthaccess.download(
    resultados,
    local_path=str(DATA_DIR)
)

print(f"Archivos descargados: {len(archivos)}")


# ============================================================
# VARIABLES QUE VAMOS A EXTRAER
# ============================================================

VARIABLES = [
    "sm_surface",
    "sm_rootzone",
    "sm_surface_wetness",
    "sm_rootzone_wetness",
    "soil_temp_layer1"
]


# ============================================================
# FUNCIÓN PARA LEER ATRIBUTOS
# ============================================================

def mostrar_atributos(dataset, nombre):
    print()
    print(f"--- Atributos de {nombre} ---")

    for atributo in dataset.attrs:
        valor = dataset.attrs[atributo]

        if isinstance(valor, bytes):
            valor = valor.decode("utf-8", errors="ignore")

        print(f"{atributo}: {valor}")


# ============================================================
# PROCESAR CADA ARCHIVO
# ============================================================

registros = []

print()
print("Procesando archivos...")


for archivo in archivos:

    archivo = Path(archivo)

    print()
    print(f"Procesando: {archivo.name}")

    with h5py.File(archivo, "r") as hdf:

        geophysical = hdf["Geophysical_Data"]

        datos = {}

        # ----------------------------------------------------
        # Extraer variables
        # ----------------------------------------------------

        for variable in VARIABLES:

            if variable not in geophysical:
                print(f"ADVERTENCIA: no existe {variable}")
                datos[variable] = np.nan
                continue

            dataset = geophysical[variable]

            # Mostrar atributos únicamente para el primer archivo
            if len(registros) == 0:
                mostrar_atributos(dataset, variable)

            valor = dataset[FILA, COLUMNA]

            # Convertir valores escalares NumPy
            valor = float(valor)

            # Buscar valor de relleno
            fill_value = dataset.attrs.get("_FillValue")

            if fill_value is not None:

                if isinstance(fill_value, np.ndarray):
                    fill_value = fill_value.item()

                if np.isclose(valor, float(fill_value)):
                    valor = np.nan

            datos[variable] = valor

        # ----------------------------------------------------
        # Tiempo del archivo
        # ----------------------------------------------------

        tiempo = None

        if "time" in hdf:

            dataset_time = hdf["time"]

            try:
                tiempo = dataset_time[()]

                # SMAP devuelve el tiempo como un arreglo de un elemento
                tiempo = float(np.asarray(tiempo).reshape(-1)[0])

            except Exception:
                tiempo = None

        # ----------------------------------------------------
        # Información del archivo
        # ----------------------------------------------------

        registros.append({
            "archivo": archivo.name,
            "tiempo": tiempo,
            "latitud": LATITUD,
            "longitud": LONGITUD,
            "fila_smap": FILA,
            "columna_smap": COLUMNA,
            **datos
        })


# ============================================================
# CREAR DATAFRAME
# ============================================================

df = pd.DataFrame(registros)

# ============================================================
# CONVERTIR TIEMPO SMAP
# ============================================================

# El tiempo de SMAP está expresado como segundos desde
# el origen indicado por los metadatos del producto:
# 2000-01-01 11:58:55.816 UTC.

df["fecha_hora"] = pd.to_datetime(
    df["tiempo"],
    unit="s",
    origin="2000-01-01 11:58:55.816",
    utc=True
)

# Filtrar exactamente el periodo solicitado
fecha_inicio = pd.Timestamp(FECHA_INICIO, tz="UTC")
fecha_fin = pd.Timestamp(FECHA_FIN, tz="UTC") + pd.Timedelta(days=1)

df = df[
    (df["fecha_hora"] >= fecha_inicio) &
    (df["fecha_hora"] < fecha_fin)
].copy()

df = df.sort_values("fecha_hora")

# ============================================================
# CONVERSIÓN DE TEMPERATURA
# ============================================================

# La conversión se hace después de revisar los atributos.
# Si la temperatura está en Kelvin, se agrega una columna
# adicional en Celsius.

df["soil_temp_layer1_celsius"] = df["soil_temp_layer1"] - 273.15


# ============================================================
# ORDENAR
# ============================================================

df = df.sort_values("tiempo")


# ============================================================
# MOSTRAR RESULTADOS
# ============================================================

print()
print("=" * 70)
print("SERIE TEMPORAL SMAP")
print("=" * 70)

print()
print(df.to_string(index=False))


# ============================================================
# ESTADÍSTICAS
# ============================================================

print()
print("=" * 70)
print("ESTADÍSTICAS")
print("=" * 70)

columnas_estadisticas = [
    "sm_surface",
    "sm_rootzone",
    "sm_surface_wetness",
    "sm_rootzone_wetness",
    "soil_temp_layer1",
    "soil_temp_layer1_celsius"
]

print(
    df[columnas_estadisticas].describe()
)


# ============================================================
# GUARDAR CSV
# ============================================================

archivo_salida = OUTPUT_DIR / "smap_timeseries_santander.csv"

df.to_csv(
    archivo_salida,
    index=False,
    encoding="utf-8-sig"
)

print()
print(f"CSV guardado en:")
print(archivo_salida)


# ============================================================
# GRÁFICA
# ============================================================

import matplotlib.pyplot as plt


# Verificar que existan datos para graficar
if df.empty:
    raise RuntimeError(
        "No hay datos disponibles para generar la gráfica."
    )


print()
print("Generando gráfica de humedad del suelo...")


fig, ax = plt.subplots(figsize=(12, 6))


ax.plot(
    df["fecha_hora"],
    df["sm_surface"],
    marker="o",
    linewidth=1.5,
    label="Humedad superficial (0-5 cm)"
)

ax.plot(
    df["fecha_hora"],
    df["sm_rootzone"],
    marker="o",
    linewidth=1.5,
    label="Humedad zona radicular (0-100 cm)"
)


ax.set_title("Humedad del suelo - SMAP")
ax.set_xlabel("Fecha y hora")
ax.set_ylabel("Humedad (m³/m³)")


ax.grid(True, alpha=0.3)
ax.legend()


fig.autofmt_xdate()
fig.tight_layout()


grafica_salida = (
    OUTPUT_DIR
    / "smap_humedad_suelo.png"
)


fig.savefig(
    grafica_salida,
    dpi=150,
    bbox_inches="tight"
)

plt.close(fig)


print()
print("Gráfica guardada en:")
print(grafica_salida)

print()
print("Proceso terminado correctamente.")
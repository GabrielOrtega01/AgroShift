from pathlib import Path
import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

CROPS_FILE = (
    BASE_DIR
    / "data"
    / "crops"
    / "agroshift_cultivos_ecocrop.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "crops"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "agroshift_cultivos_caracteristicas.csv"
)


# ============================================================
# CULTIVOS DE PRUEBA
# ============================================================

CULTIVOS_PRUEBA = [
    2175,   # Zea mays
    1668,   # Phaseolus vulgaris
    1574,   # Oryza sativa
    1971,   # Solanum tuberosum
    1379,   # Lycopersicon esculentum
    1420,   # Manihot esculenta
    749,    # Coffea arabica
    1884,   # Saccharum officinarum
]


# ============================================================
# SESIÓN HTTP
# ============================================================

session = requests.Session()

session.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/153.0 Safari/537.36"
        )
    }
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def limpiar_texto(texto):
    """
    Limpia espacios y caracteres especiales.
    """

    if texto is None:
        return ""

    return " ".join(
        str(texto)
        .replace("\xa0", " ")
        .split()
    )


def extraer_numeros(texto):
    """
    Extrae todos los números de un texto.

    Ejemplos:

        '18 33 10 47'
        -> [18.0, 33.0, 10.0, 47.0]

        '5 7 4.5 8.5'
        -> [5.0, 7.0, 4.5, 8.5]
    """

    if not texto:
        return []

    encontrados = re.findall(
        r"-?\d+(?:[.,]\d+)?",
        texto
    )

    valores = []

    for valor in encontrados:

        try:
            valores.append(
                float(
                    valor.replace(",", ".")
                )
            )
        except ValueError:
            pass

    return valores


def obtener_celdas_fila(fila):
    """
    Devuelve el texto limpio de todas las celdas de una fila.
    """

    celdas = fila.find_all(
        ["td", "th"]
    )

    return [
        limpiar_texto(
            celda.get_text(
                " ",
                strip=True
            )
        )
        for celda in celdas
    ]


# ============================================================
# EXTRAER ECOLOGÍA
# ============================================================

def extraer_datos_ecologia(soup):

    datos = {}

    # --------------------------------------------------------
    # IMPORTANTE
    # --------------------------------------------------------
    #
    # No buscamos una tabla específica.
    #
    # ECOCROP puede modificar la estructura HTML de la página.
    # En lugar de depender de una tabla concreta, recorremos
    # todas las filas y buscamos los nombres de los campos.
    #

    filas = soup.find_all("tr")

    for fila in filas:

        textos = obtener_celdas_fila(
            fila
        )

        if not textos:
            continue

        # ====================================================
        # TEMPERATURA
        # ====================================================

        if "Temperat. requir." in textos:

            i = textos.index(
                "Temperat. requir."
            )

            valores = []

            # Tomamos las celdas posteriores.
            for texto in textos[i + 1:]:

                valores.extend(
                    extraer_numeros(texto)
                )

            if len(valores) >= 4:

                datos[
                    "temperatura_optima_min_c"
                ] = valores[0]

                datos[
                    "temperatura_optima_max_c"
                ] = valores[1]

                datos[
                    "temperatura_absoluta_min_c"
                ] = valores[2]

                datos[
                    "temperatura_absoluta_max_c"
                ] = valores[3]

        # ====================================================
        # PRECIPITACIÓN
        # ====================================================

        if "Rainfall (annual)" in textos:

            i = textos.index(
                "Rainfall (annual)"
            )

            valores = []

            for texto in textos[i + 1:]:

                valores.extend(
                    extraer_numeros(texto)
                )

            if len(valores) >= 4:

                datos[
                    "precipitacion_optima_min_mm"
                ] = valores[0]

                datos[
                    "precipitacion_optima_max_mm"
                ] = valores[1]

                datos[
                    "precipitacion_absoluta_min_mm"
                ] = valores[2]

                datos[
                    "precipitacion_absoluta_max_mm"
                ] = valores[3]

        # ====================================================
        # pH
        # ====================================================

        if "Soil PH" in textos:

            i = textos.index(
                "Soil PH"
            )

            valores = []

            for texto in textos[i + 1:]:

                valores.extend(
                    extraer_numeros(texto)
                )

            if len(valores) >= 4:

                datos[
                    "ph_optimo_min"
                ] = valores[0]

                datos[
                    "ph_optimo_max"
                ] = valores[1]

                datos[
                    "ph_absoluto_min"
                ] = valores[2]

                datos[
                    "ph_absoluto_max"
                ] = valores[3]

        # ====================================================
        # PROFUNDIDAD DEL SUELO
        # ====================================================

        if "Soil depth" in textos:

            i = textos.index(
                "Soil depth"
            )

            if len(textos) > i + 1:

                datos[
                    "profundidad_suelo_optima"
                ] = textos[i + 1]

            if len(textos) > i + 2:

                datos[
                    "profundidad_suelo_absoluta"
                ] = textos[i + 2]

        # ====================================================
        # FERTILIDAD
        # ====================================================

        if "Soil fertility" in textos:

            i = textos.index(
                "Soil fertility"
            )

            if len(textos) > i + 1:

                datos[
                    "fertilidad_suelo_optima"
                ] = textos[i + 1]

            if len(textos) > i + 2:

                datos[
                    "fertilidad_suelo_absoluta"
                ] = textos[i + 2]

        # ====================================================
        # SALINIDAD
        # ====================================================

        if "Soil salinity" in textos:

            i = textos.index(
                "Soil salinity"
            )

            if len(textos) > i + 1:

                datos[
                    "salinidad_suelo_optima"
                ] = textos[i + 1]

            if len(textos) > i + 2:

                datos[
                    "salinidad_suelo_absoluta"
                ] = textos[i + 2]

        # ====================================================
        # DRENAJE
        # ====================================================

        if "Soil drainage" in textos:

            i = textos.index(
                "Soil drainage"
            )

            if len(textos) > i + 1:

                if textos[i + 1]:

                    datos[
                        "drenaje_suelo_optimo"
                    ] = textos[i + 1]

            if len(textos) > i + 2:

                if textos[i + 2]:

                    datos[
                        "drenaje_suelo_absoluto"
                    ] = textos[i + 2]

    return datos


# ============================================================
# EXTRAER CICLO DEL CULTIVO
# ============================================================

def extraer_ciclo(soup):

    """
    Extrae el rango Crop cycle.
    """

    filas = soup.find_all("tr")

    for fila in filas:

        textos = obtener_celdas_fila(
            fila
        )

        if not textos:
            continue

        if "Crop cycle" in textos:

            i = textos.index(
                "Crop cycle"
            )

            valores = []

            for texto in textos[i + 1:]:

                valores.extend(
                    extraer_numeros(texto)
                )

            if len(valores) >= 2:

                return (
                    valores[0],
                    valores[1]
                )

    # Segundo intento:
    # buscar directamente en todo el texto.

    texto = limpiar_texto(
        soup.get_text(
            " ",
            strip=True
        )
    )

    coincidencia = re.search(
        r"Crop cycle\s+"
        r"(\d+(?:[.,]\d+)?)\s+"
        r"(\d+(?:[.,]\d+)?)",
        texto,
        re.IGNORECASE
    )

    if coincidencia:

        return (
            float(
                coincidencia.group(1)
                .replace(",", ".")
            ),
            float(
                coincidencia.group(2)
                .replace(",", ".")
            )
        )

    return None, None


# ============================================================
# EXTRAER UNA FICHA
# ============================================================

def extraer_ficha(
    ecocrop_id,
    nombre,
    url_crop
):

    print(
        f"\nConsultando: {nombre}"
    )

    print(
        f"ID ECOCROP: {ecocrop_id}"
    )

    # --------------------------------------------------------
    # URL DATA SHEET
    # --------------------------------------------------------

    url_datasheet = (
        "https://ecocrop.apps.fao.org"
        f"/ecocrop/srv/en/dataSheet?id={ecocrop_id}"
    )

    print(
        f"Data sheet: {url_datasheet}"
    )

    respuesta = session.get(
        url_datasheet,
        timeout=60
    )

    respuesta.raise_for_status()

    soup = BeautifulSoup(
        respuesta.text,
        "html.parser"
    )

    # --------------------------------------------------------
    # REGISTRO BASE
    # --------------------------------------------------------

    registro = {

        "ecocrop_id":
            ecocrop_id,

        "nombre":
            nombre,

        "url_ecocrop":
            url_crop,

        "url_datasheet":
            url_datasheet,
    }

    # --------------------------------------------------------
    # ECOLOGÍA
    # --------------------------------------------------------

    datos_ecologia = (
        extraer_datos_ecologia(
            soup
        )
    )

    registro.update(
        datos_ecologia
    )

    # --------------------------------------------------------
    # CICLO
    # --------------------------------------------------------

    ciclo_min, ciclo_max = (
        extraer_ciclo(
            soup
        )
    )

    registro[
        "ciclo_min_dias"
    ] = ciclo_min

    registro[
        "ciclo_max_dias"
    ] = ciclo_max

    # --------------------------------------------------------
    # TEXTO COMPLETO
    # --------------------------------------------------------

    texto = limpiar_texto(
        soup.get_text(
            " ",
            strip=True
        )
    )

    registro[
        "longitud_texto_ficha"
    ] = len(texto)

    return registro


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    print("=" * 70)

    print(
        "AGROSHIFT - CARACTERÍSTICAS ECOCROP"
    )

    print("=" * 70)

    # --------------------------------------------------------
    # CARGAR CATÁLOGO
    # --------------------------------------------------------

    crops = pd.read_csv(
        CROPS_FILE,
        encoding="utf-8-sig"
    )

    print(
        f"\n✓ Catálogo cargado: "
        f"{len(crops)} cultivos"
    )

    # --------------------------------------------------------
    # CULTIVOS DE PRUEBA
    # --------------------------------------------------------

    seleccion = crops[
        crops["ecocrop_id"].isin(
            CULTIVOS_PRUEBA
        )
    ].copy()

    print(
        f"✓ Cultivos de prueba: "
        f"{len(seleccion)}"
    )

    # --------------------------------------------------------
    # PROCESAR
    # --------------------------------------------------------

    resultados = []

    for _, fila in seleccion.iterrows():

        try:

            resultado = extraer_ficha(

                int(
                    fila["ecocrop_id"]
                ),

                fila["nombre"],

                fila["url_ecocrop"]
            )

            resultados.append(
                resultado
            )

            print(
                "✓ Ficha procesada"
            )

        except Exception as error:

            print(
                f"✗ Error: {error}"
            )

        time.sleep(1)

    # --------------------------------------------------------
    # VALIDAR
    # --------------------------------------------------------

    if not resultados:

        print(
            "\nNo se obtuvieron resultados."
        )

        return

    # --------------------------------------------------------
    # DATAFRAME
    # --------------------------------------------------------

    df = pd.DataFrame(
        resultados
    )

    # --------------------------------------------------------
    # DIRECTORIO
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "RESULTADO"
    )

    print(
        "=" * 70
    )

    print(
        f"\nFichas procesadas: "
        f"{len(df)}"
    )

    columnas = [

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
        "ciclo_max_dias",

        "profundidad_suelo_optima",
        "profundidad_suelo_absoluta",

        "fertilidad_suelo_optima",
        "fertilidad_suelo_absoluta",

        "salinidad_suelo_optima",
        "salinidad_suelo_absoluta",

        "drenaje_suelo_optimo",
        "drenaje_suelo_absoluto",
    ]

    columnas = [
        columna
        for columna in columnas
        if columna in df.columns
    ]

    print(
        df[columnas]
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # VALIDACIÓN PH
    # --------------------------------------------------------

    print(
        "\n" + "-" * 70
    )

    print(
        "VALIDACIÓN DE pH"
    )

    print(
        "-" * 70
    )

    columnas_ph = [

        "nombre",
        "ph_optimo_min",
        "ph_optimo_max",
        "ph_absoluto_min",
        "ph_absoluto_max",
    ]

    columnas_ph = [
        columna
        for columna in columnas_ph
        if columna in df.columns
    ]

    print(
        df[columnas_ph]
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # VALIDACIÓN CICLO
    # --------------------------------------------------------

    print(
        "\n" + "-" * 70
    )

    print(
        "VALIDACIÓN DEL CICLO"
    )

    print(
        "-" * 70
    )

    columnas_ciclo = [

        "nombre",
        "ciclo_min_dias",
        "ciclo_max_dias",
    ]

    print(
        df[columnas_ciclo]
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # ARCHIVO
    # --------------------------------------------------------

    print(
        "\n✓ Archivo generado:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "✓ PROCESO COMPLETADO"
    )

    print(
        "=" * 70
    )


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    main()
from pathlib import Path
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "data" / "crops"
OUTPUT_FILE = OUTPUT_DIR / "agroshift_cultivos_ecocrop.csv"

URL = "https://ecocrop.apps.fao.org/ecocrop/srv/en/cropListDetails"

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


def limpiar_texto(texto):
    if texto is None:
        return ""

    return " ".join(
        texto.replace("\xa0", " ").split()
    )


def extraer_codigo(texto):
    """
    Extrae el ID real de ECOCROP desde enlaces
    con formato cropView?id=XXXX.
    """

    if texto is None:
        return None

    texto = str(texto)

    # Formato normal:
    # cropView?id=289
    coincidencia = re.search(
        r"cropView\?id=(\d+)",
        texto,
        re.IGNORECASE
    )

    if coincidencia:
        return int(coincidencia.group(1))

    return None


def obtener_catalogo():
    print("=" * 70)
    print("AGROSHIFT - CATÁLOGO ECOCROP")
    print("=" * 70)

    print("\nConsultando ECOCROP...")

    respuesta = session.get(
        URL,
        timeout=60
    )

    respuesta.raise_for_status()

    print(f"✓ Respuesta recibida: {respuesta.status_code}")
    print(f"Tamaño HTML: {len(respuesta.text):,} caracteres")

    soup = BeautifulSoup(
        respuesta.text,
        "html.parser"
    )

    tablas = soup.find_all("table")

    print(f"Tablas encontradas: {len(tablas)}")

    registros = []

    for numero_tabla, tabla in enumerate(tablas, start=1):

        filas = tabla.find_all("tr")

        print(
            f"  Tabla {numero_tabla}: "
            f"{len(filas)} filas"
        )

        for fila in filas:

            texto_fila = limpiar_texto(
                fila.get_text(" ", strip=True)
            )

            if not texto_fila:
                continue

            enlaces = fila.find_all("a")

            for enlace in enlaces:

                nombre = limpiar_texto(
                    enlace.get_text(" ", strip=True)
                )

                href = enlace.get("href")

                if not nombre:
                    continue

                if not href:
                    continue

                # Buscamos enlaces relacionados
                # con la ficha del cultivo.
                if (
                    "cropView" not in href
                    and "crop" not in href.lower()
                ):
                    continue

                codigo = extraer_codigo(
                    href
                )

                if codigo is None:
                    codigo = extraer_codigo(
                        texto_fila
                    )


                    # Extraer el ID real antes de construir la URL
                codigo = extraer_codigo(href)

                if codigo is None:
                    continue

                url_crop = (
                    "https://ecocrop.apps.fao.org"
                   f"/ecocrop/srv/en/cropView?id={codigo}"
                    )

                registros.append(
                    {
                        "ecocrop_id": codigo,
                        "nombre": nombre,
                        "url_ecocrop": url_crop,
                    }
                )

    return registros


def limpiar_catalogo(registros):

    if not registros:
        return pd.DataFrame()

    df = pd.DataFrame(registros)

    # Eliminar posibles duplicados
    df = df.drop_duplicates(
        subset=["ecocrop_id"]
    )

    df = df.sort_values(
        by="nombre"
    )

    df = df.reset_index(
        drop=True
    )

    return df


def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    try:

        registros = obtener_catalogo()

    except requests.RequestException as error:

        print("\nERROR al consultar ECOCROP:")
        print(error)

        return

    print(
        f"\nRegistros detectados: "
        f"{len(registros)}"
    )

    if not registros:

        print("\nNo se encontraron cultivos.")

        print(
            "\nVamos a guardar una copia del HTML "
            "para poder revisar la estructura."
        )

        html_file = OUTPUT_DIR / "ecocrop_respuesta.html"

        respuesta = session.get(
            URL,
            timeout=60
        )

        html_file.write_text(
            respuesta.text,
            encoding="utf-8"
        )

        print(
            f"\nHTML guardado en:\n{html_file}"
        )

        return

    df = limpiar_catalogo(
        registros
    )

    df.insert(
        0,
        "fuente",
        "FAO ECOCROP"
    )

    df.insert(
        1,
        "fecha_consulta",
        pd.Timestamp.now().strftime(
            "%Y-%m-%d"
        )
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n" + "=" * 70)
    print("CATÁLOGO GENERADO")
    print("=" * 70)

    print(
        f"\nArchivo:\n{OUTPUT_FILE}"
    )

    print(
        f"\nTotal de cultivos: {len(df)}"
    )

    print("\nPrimeros registros:")

    print(
        df.head(20).to_string(
            index=False
        )
    )

    print("\nÚltimos registros:")

    print(
        df.tail(10).to_string(
            index=False
        )
    )

    print("\n" + "=" * 70)
    print("✓ PROCESO COMPLETADO")
    print("=" * 70)


if __name__ == "__main__":
    main()
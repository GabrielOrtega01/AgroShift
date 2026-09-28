# 🌱 AgroShift

Herramienta de apoyo a la decisión para **rotación de cultivos**, construida con datos de observación de la Tierra de la NASA y de la FAO.

Proyecto para el **NASA Space Apps Challenge 2026** — reto [*"Cambio de rumbo: adaptando las granjas con datos de la NASA"*](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/).

El agricultor elige su región y la app le muestra las rotaciones de cultivo más adecuadas para **su** clima e historial hídrico — no un solo punto fijo.

Regiones soportadas (ver [`python/agroshift/regions.py`](python/agroshift/regions.py)): Santander, Quindío, Córdoba y Boyacá, Colombia. Historial: **2020–2025**.

## ¿Qué hace?

Cruza clima, humedad del suelo y requerimientos agronómicos para recomendar **secuencias de rotación de cultivos** que:

- Aprovechen mejor la precipitación disponible (cobertura de la demanda hídrica).
- Mantengan un balance hídrico favorable (precipitación vs. evapotranspiración del cultivo, ETc).
- Se ajusten a los rangos de humedad del suelo históricos.
- Encajen temporalmente con las ventanas de siembra.

Agregar una región nueva es cuestión de datos, no de código: solo hay que sumar sus coordenadas a `regions.py` (ver más abajo) y correr el pipeline para ese `--region`.

## Fuentes de datos

| Fuente | Variable | Uso |
|---|---|---|
| [NASA POWER](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) | Temperatura, precipitación, humedad, viento, radiación (diario) | Clima base y cálculo de ETo/ETc |
| [NASA SMAP L4](https://nsidc.org/data/spl4smgp/versions/8) | Humedad del suelo superficial y de zona radicular | Estado hídrico del suelo |
| [FAO ECOCROP](https://www.fao.org/geospatial/data-and-tools/data-portals/ecocrop/) | Requerimientos de temperatura, lluvia, pH, ciclo por cultivo | Compatibilidad climática de cultivos |

## Estructura del proyecto

```
AgroShift/
├── app.py                          # App web (Streamlit) — selector de región + MVP
├── requirements.txt                # Dependencias de la app (Streamlit Cloud las usa)
├── python/
│   ├── requirements.txt            # Dependencias del pipeline de análisis
│   ├── run_pipeline.py             # Orquestador: --region, --fecha-inicio, --fecha-fin
│   ├── agroshift/                  # Paquete de soporte (arquitectura, ver abajo)
│   ├── 01_descargar_nasa_power.py  # ── Adquisición de datos ──
│   ├── 02_descargar_nasa_smap.py
│   ├── 03_recuperar_smap_faltantes.py
│   ├── 04_descargar_catalogo_ecocrop.py
│   ├── 05_extraer_caracteristicas_ecocrop.py
│   ├── 06_integrar_datos_ambientales.py   # ── Análisis ──
│   ├── 07_analizar_clima_2020.py
│   ├── 08_calcular_evapotranspiracion_referencia.py
│   ├── 09_calcular_evapotranspiracion_cultivo.py
│   ├── 10_calcular_balance_hidrico.py
│   ├── 11_analizar_estado_hidrico.py
│   ├── 12_analizar_compatibilidad_cultivos.py
│   ├── 13_generar_escenarios_rotacion.py  # ── Motor de rotación ──
│   ├── 14_comparar_fechas_inicio.py
│   ├── 15_resumir_etapas_rotacion.py
│   ├── 16_priorizar_escenarios.py
│   ├── 17_consolidar_resumen_etapas.py
│   └── data/
│       ├── power/                   # Crudo NASA POWER, por región
│       ├── analysis/<region>/       # CSVs y gráficas generadas, por región
│       └── crops/                   # Catálogo de cultivos y compatibilidad ECOCROP (global)
└── docs/
```

Los scripts están numerados en el **orden real en que se ejecutan** — cada uno lee la salida del anterior y escribe la suya en `python/data/analysis/<región>/`. Cada uno sigue siendo ejecutable de forma independiente (`python 07_analizar_clima_2020.py`) porque solo depende de archivos en disco, no de imports entre ellos; la región activa se pasa por la variable de entorno `AGROSHIFT_REGION` (`run_pipeline.py` la fija por ti).

> El proyecto tenía originalmente ~30 scripts, muchos de ellos iteraciones descartadas (`_v2`...`_v9`), utilidades de depuración de una sola vez, o análisis que ningún otro paso consumía. Se depuraron a los que realmente alimentan la app, trazando qué CSV lee y escribe cada uno.

### Arquitectura (`python/agroshift/`)

La lógica científica de cada script (cálculos FAO-56, balance hídrico, clasificación de escenarios) **no se tocó** — es la parte más valiosa y ya validada del proyecto. Lo que se agregó es una capa delgada de organización alrededor, con patrones de diseño estándar:

| Módulo | Patrón | Qué resuelve |
|---|---|---|
| `agroshift/config.py` | **Singleton / Config centralizado** | Un único `Settings` con rutas base, en vez de repetir `BASE_DIR = Path(__file__)...` en cada script |
| `agroshift/regions.py` | **Registro / Value Object** | `Region` (coordenadas, altitud, celda de grilla SMAP) por cada punto soportado — agregar una región nueva es agregar una entrada aquí |
| `agroshift/repository.py` | **Repository** | `DataRepository(region=...)` para leer los CSV de resultados de una región por nombre lógico (lo usa `app.py`), sin que el consumidor conozca la ruta física |
| `agroshift/sources/` | **Strategy** | `DataSource` (interfaz común `fetch()`) con `PowerDataSource`, `SmapDataSource`, `EcocropDataSource` — cada origen externo se puede invocar de forma intercambiable |
| `agroshift/pipeline/` | **Pipeline / Chain of Responsibility** | `Pipeline` ejecuta una lista ordenada de `PipelineStep`, mide tiempos, se detiene en el primer error y reporta un resumen — reemplaza correr cada script a mano |

### Nota sobre el muestreo de SMAP

SMAP L4 publica una imagen cada 3 horas. Descargar las 8 lecturas diarias para 6 años en varias regiones no es viable en la práctica (~7s por archivo en los servidores de NASA — 8/día × 365 × 6 años ya son ~34h *por región* solo en esa etapa). `agroshift/smap_sampling.py` se queda con **1 lectura por día** (la más cercana a las 13:30 UTC), suficiente para la señal diaria de humedad que usa el resto del pipeline. La descarga además usa lotes en paralelo (`earthaccess` con 8 hilos) en vez de un archivo a la vez.

## Cómo correr la app localmente

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
streamlit run app.py
```

Abre `http://localhost:8501`.

## Cómo regenerar los datos de análisis (opcional)

```bash
cd python
pip install -r requirements.txt

# Pipeline completo para una región (descarga + análisis; requiere credenciales NASA Earthdata)
python run_pipeline.py --region quindio --fecha-inicio 2020-01-01 --fecha-fin 2025-12-31

# Solo reprocesar el análisis con los datos crudos que ya están en data/
python run_pipeline.py --region quindio --analysis-only
```

Las credenciales de NASA Earthdata se configuran una vez con `python -c "import earthaccess; earthaccess.login(persist=True)"` (pide usuario/contraseña por consola y los guarda en `~/.netrc`).

## Despliegue

La app está pensada para desplegarse gratis en [Streamlit Community Cloud](https://streamlit.io/cloud):

1. Conecta este repositorio de GitHub.
2. Archivo principal: `app.py`.
3. Streamlit Cloud instala automáticamente `requirements.txt` de la raíz.

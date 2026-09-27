# 🌱 AgroShift

Herramienta de apoyo a la decisión para **rotación de cultivos**, construida con datos de observación de la Tierra de la NASA y de la FAO.

Proyecto para el **NASA Space Apps Challenge 2026** — reto [*"Cambio de rumbo: adaptando las granjas con datos de la NASA"*](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/).

Región de análisis: **Santander, Colombia** (año de referencia 2020).

## ¿Qué hace?

Cruza clima, humedad del suelo y requerimientos agronómicos para recomendar **secuencias de rotación de cultivos** que:

- Aprovechen mejor la precipitación disponible (cobertura de la demanda hídrica).
- Mantengan un balance hídrico favorable (precipitación vs. evapotranspiración del cultivo, ETc).
- Se ajusten a los rangos de humedad del suelo históricos.
- Encajen temporalmente con las ventanas de siembra.

## Fuentes de datos

| Fuente | Variable | Uso |
|---|---|---|
| [NASA POWER](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) | Temperatura, precipitación, humedad, viento, radiación (diario) | Clima base y cálculo de ETo/ETc |
| [NASA SMAP L4](https://nsidc.org/data/spl4smgp/versions/8) | Humedad del suelo superficial y de zona radicular | Estado hídrico del suelo |
| [FAO ECOCROP](https://www.fao.org/geospatial/data-and-tools/data-portals/ecocrop/) | Requerimientos de temperatura, lluvia, pH, ciclo por cultivo | Compatibilidad climática de cultivos |

## Estructura del proyecto

```
AgroShift/
├── app.py                          # App web (Streamlit) — MVP de presentación
├── requirements.txt                # Dependencias de la app (Streamlit Cloud las usa)
├── python/
│   ├── requirements.txt            # Dependencias del pipeline de análisis
│   ├── run_pipeline.py             # Orquestador: corre las 18 etapas en orden
│   ├── agroshift/                  # Paquete de soporte (arquitectura, ver abajo)
│   ├── 01_descargar_nasa_power.py  # ── Adquisición de datos ──
│   ├── 02_descargar_nasa_smap.py
│   ├── 03_corregir_smap_enero.py
│   ├── 04_recuperar_smap_faltantes.py
│   ├── 05_descargar_catalogo_ecocrop.py
│   ├── 06_extraer_caracteristicas_ecocrop.py
│   ├── 07_integrar_datos_ambientales.py   # ── Análisis ──
│   ├── 08_analizar_clima_2020.py
│   ├── 09_calcular_evapotranspiracion_referencia.py
│   ├── 10_calcular_evapotranspiracion_cultivo.py
│   ├── 11_calcular_balance_hidrico.py
│   ├── 12_analizar_estado_hidrico.py
│   ├── 13_analizar_compatibilidad_cultivos.py
│   ├── 14_generar_escenarios_rotacion.py  # ── Motor de rotación ──
│   ├── 15_comparar_fechas_inicio.py
│   ├── 16_resumir_etapas_rotacion.py
│   ├── 17_priorizar_escenarios.py
│   ├── 18_consolidar_resumen_etapas.py
│   └── data/
│       ├── analysis/                # CSVs y gráficas generadas (resultados)
│       └── crops/                   # Catálogo de cultivos y compatibilidad ECOCROP
└── docs/
```

Los scripts están numerados en el **orden real en que se ejecutan** — cada uno lee la salida del anterior y escribe la suya en `python/data/analysis/`. Cada uno sigue siendo ejecutable de forma independiente (`python 08_analizar_clima_2020.py`) porque solo depende de archivos en disco, no de imports entre ellos.

> El proyecto tenía originalmente ~30 scripts, muchos de ellos iteraciones descartadas (`_v2`...`_v9`), utilidades de depuración de una sola vez, o análisis que ningún otro paso consumía. Se depuraron a los 18 que realmente alimentan la app, trazando qué CSV lee y escribe cada uno.

### Arquitectura (`python/agroshift/`)

La lógica científica de cada script (cálculos FAO-56, balance hídrico, clasificación de escenarios) **no se tocó** — es la parte más valiosa y ya validada del proyecto. Lo que se agregó es una capa delgada de organización alrededor, con patrones de diseño estándar:

| Módulo | Patrón | Qué resuelve |
|---|---|---|
| `agroshift/config.py` | **Singleton / Config centralizado** | Un único `Settings` con rutas y coordenadas, en vez de repetir `BASE_DIR = Path(__file__)...` y lat/lon en cada script |
| `agroshift/repository.py` | **Repository** | `DataRepository` para leer los CSV de resultados por nombre lógico (lo usa `app.py`), sin que el consumidor conozca la ruta física |
| `agroshift/sources/` | **Strategy** | `DataSource` (interfaz común `fetch()`) con `PowerDataSource`, `SmapDataSource`, `EcocropDataSource` — cada origen externo se puede invocar de forma intercambiable |
| `agroshift/pipeline/` | **Pipeline / Chain of Responsibility** | `Pipeline` ejecuta una lista ordenada de `PipelineStep`, mide tiempos, se detiene en el primer error y reporta un resumen — reemplaza correr cada script a mano |

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

# Pipeline completo (descarga + análisis; requiere credenciales NASA Earthdata)
python run_pipeline.py

# Solo reprocesar el análisis con los datos crudos que ya están en data/
python run_pipeline.py --analysis-only
```

## Despliegue

La app está pensada para desplegarse gratis en [Streamlit Community Cloud](https://streamlit.io/cloud):

1. Conecta este repositorio de GitHub.
2. Archivo principal: `app.py`.
3. Streamlit Cloud instala automáticamente `requirements.txt` de la raíz.

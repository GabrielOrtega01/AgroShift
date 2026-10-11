# 🌱 AgroShift

🇬🇧 [Read this in English](README.en.md)

Herramienta de apoyo a la decisión para **rotación de cultivos**, construida con datos de observación de la Tierra de la NASA y de la FAO.

Proyecto para el **NASA Space Apps Challenge 2026** — reto [*"Cambio de rumbo: adaptando las granjas con datos de la NASA"*](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/).

🌐 **App en vivo:** https://agroshift.streamlit.app

El agricultor elige su región y la app le muestra las rotaciones de cultivo más adecuadas para **su** clima, su suelo y su historial hídrico — no un solo punto fijo. La interfaz está en **español e inglés**.

## ¿Qué hace?

Cruza clima, humedad del suelo, suelo y requerimientos agronómicos para recomendar **secuencias de rotación de cultivos** que:

- Aprovechen mejor la precipitación disponible (cobertura de la demanda hídrica).
- Mantengan un balance hídrico favorable (precipitación vs. evapotranspiración del cultivo, ETc).
- Se ajusten a los rangos de humedad del suelo históricos.
- Encajen temporalmente con las ventanas de siembra.
- Respeten lo que el clima permite: la compatibilidad de un cultivo nunca supera lo que toleran la temperatura media y los días dentro de su rango, y se descartan los que no se adaptan.

El agricultor indica qué prioriza (agua, balance, humedad, ajuste temporal), qué tan exigente quiere ser y qué cultivos quiere incluir. La app entrega un podio de rotaciones con su **fiabilidad histórica** (en qué porcentaje de las fechas de inicio 2020–2025 cumplen lo pedido), los **mejores meses para iniciar**, y advertencias de pH del suelo.

### Regiones

| Región | Humedad del suelo |
|---|---|
| Santander, Quindío, Córdoba, Boyacá | Medida por satélite (NASA SMAP L4) |
| Cundinamarca, Valle del Cauca, Meta, Nariño | **Estimada** con un balance hídrico a partir de NASA POWER (rotulada así en la app) |

Agregar una región es cuestión de datos, no de código: ver [`docs/como_agregar_una_region.md`](docs/como_agregar_una_region.md).

## Fuentes de datos

| Fuente | Variable | Uso |
|---|---|---|
| [NASA POWER](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) | Temperatura, humedad, viento, radiación (diario) | Clima base y cálculo de ETo/ETc |
| [NASA GPM IMERG](https://gpm.nasa.gov/data/imerg) | Lluvia diaria (satélite + pluviómetros, 0,1°) | **Fuente de la lluvia**, con la magnitud ajustada a CHIRPS |
| [NASA SMAP L4](https://nsidc.org/data/spl4smgp/versions/8) | Humedad del suelo superficial y de zona radicular | Estado hídrico del suelo |
| [FAO ECOCROP](https://www.fao.org/geospatial/data-and-tools/data-portals/ecocrop/) | Requerimientos de temperatura, lluvia, pH, ciclo por cultivo | Compatibilidad climática de cultivos |
| [ISRIC SoilGrids](https://soilgrids.org/) | Textura, pH y carbono orgánico del suelo (0–30 cm, 250 m) | Suelo de la región y alertas de pH |
| [CHIRPS](https://www.chc.ucsb.edu/data/chirps) | Lluvia mensual (satélite + pluviómetros) | Referencia para ajustar la magnitud de IMERG y validar |

## Calidad de los datos y límites

La lluvia es la de **NASA GPM IMERG**, con la magnitud ajustada a los totales mensuales de CHIRPS. Se compararon las tres fuentes (`python/validar_precipitacion.py`, resultados en `python/data/validation/`):

- **NASA POWER se descartó para la lluvia:** correlación mensual con CHIRPS r = 0,44–0,81 (media 0,66), 2021 sale ~70 % más seco en Santander y Boyacá queda 2× más húmeda.
- **IMERG sin ajustar** sigue mejor la variación entre meses y años (r = 0,62–0,92, media 0,77), pero **sobrestima los totales** en varias zonas de montaña (Santander +81 %, Valle +74 %, Nariño +109 %, Cundinamarca +124 %). Por eso se conserva su distribución diaria y se escala cada mes a CHIRPS, que coincide mejor con las climatologías conocidas.
- Los **milímetros absolutos siguen siendo aproximados** (no se validó contra estaciones del IDEAM) y 92 de 2.192 días no tienen archivo IMERG: ahí se usa NASA POWER. La app muestra la comparación en la pestaña *Cómo funciona*.
- La humedad modelada (usada en 4 regiones) se contrastó con SMAP en las 4 regiones que lo tienen (`python/validar_humedad_modelo.py`): la climatología mensual correlaciona r = 0,69–0,96 y el orden diario (Spearman) 0,65–0,82. Es una estimación, no una medición.
- El suelo es una estimación global (SoilGrids): confirma pH y fertilidad con un análisis de laboratorio.
- Cada región es un **punto de referencia**, no la finca exacta. No se consideran precios, costos ni plagas.
- **Temperatura ajustada a la altitud:** NASA POWER entrega la temperatura de una celda de ~50 km a su elevación media (p. ej. 2.112 m para un punto del valle del Cauca que está a 1.000 m); se ajusta al punto con el gradiente estándar de 6,5 °C/km (`agroshift/downscaling.py`). Con el ajuste, las temperaturas medias de las 8 regiones coinciden con las conocidas (±1 °C).
- ECOCROP no tiene límites de altitud útiles (café hasta 2.800 m) ni temperatura letal para casi todos los cultivos, y la celda de 50 km no captura heladas locales: en zonas sobre 2.000 m la app avisa de verificar el riesgo de helada.

## Estructura del proyecto

```
AgroShift/
├── app.py                          # Punto de entrada Streamlit: selectores, barra lateral, pestañas
├── ui/                             # Capa de presentación
│   ├── theme.py                    #   paleta, CSS y plantilla de gráficos
│   ├── components.py               #   tarjetas, KPI, insignias, avisos
│   ├── i18n.py / textos.py         #   idioma ES/EN (catálogo de textos por clave)
│   ├── data.py                     #   carga y caché de datos por región
│   └── views/                      #   una vista por pestaña (inicio, clima, cultivos, agua, rotacion, metodologia)
├── tests/                          # pytest: dominio, recomendador, catálogo de textos y CSV de resultados
├── .github/workflows/tests.yml     # CI: corre las pruebas en cada push
├── .streamlit/config.toml          # Tema (colores y tipografía) de la app
├── requirements.txt                # Dependencias de la app (Streamlit Cloud las usa)
├── docs/                           # Guía para agregar regiones y materiales de entrega
└── python/
    ├── run_pipeline.py             # Orquestador: --region, --fecha-inicio, --fecha-fin
    ├── agregar_region.py           # Registra una región nueva (humedad modelada)
    ├── validar_precipitacion.py    # IMERG y POWER vs CHIRPS; totales mensuales para ajustar IMERG
    ├── 20_descargar_imerg.py       # lluvia diaria NASA GPM IMERG (opcional, requiere Earthdata)
    ├── agroshift/                  # Paquete de soporte (arquitectura, ver abajo)
    ├── 01_descargar_nasa_power.py  # ── Adquisición de datos ──
    ├── 02_descargar_nasa_smap.py
    ├── 03_recuperar_smap_faltantes.py
    ├── 04_descargar_catalogo_ecocrop.py
    ├── 05_extraer_caracteristicas_ecocrop.py
    ├── 18_descargar_suelo_soilgrids.py     # (se ejecuta junto a la adquisición; opcional)
    ├── 06_integrar_datos_ambientales.py   # ── Análisis ──
    ├── 07_analizar_clima.py
    ├── 08_calcular_evapotranspiracion_referencia.py
    ├── 09_calcular_evapotranspiracion_cultivo.py
    ├── 10_calcular_balance_hidrico.py
    ├── 11_analizar_estado_hidrico.py
    ├── 12_analizar_compatibilidad_cultivos.py
    ├── 13_generar_escenarios_rotacion.py  # ── Motor de rotación ──
    ├── 14_comparar_fechas_inicio.py
    ├── 15_resumir_etapas_rotacion.py
    ├── 16_priorizar_escenarios.py
    ├── 17_consolidar_resumen_etapas.py
    └── data/
        ├── power/                   # Crudo NASA POWER, por región
        ├── soil/                    # Suelo estimado por región (SoilGrids)
        ├── imerg/                   # Lluvia diaria IMERG por región
        ├── validation/              # IMERG y POWER vs CHIRPS
        ├── analysis/<region>/       # CSVs y gráficas generadas, por región
        └── crops/                   # Catálogo de cultivos y compatibilidad ECOCROP (global)
```

El orden real de ejecución lo define `run_pipeline.py`: cada script lee la salida del anterior y escribe la suya en `python/data/analysis/<región>/`. Cada uno sigue siendo ejecutable de forma independiente (`python 07_analizar_clima.py`) porque solo depende de archivos en disco; la región activa se pasa por la variable de entorno `AGROSHIFT_REGION` (`run_pipeline.py` la fija por ti).

### Arquitectura (`python/agroshift/`)

La lógica científica de cada script (cálculos FAO-56, balance hídrico, clasificación de escenarios) se conserva; alrededor hay una capa delgada de organización con patrones de diseño estándar:

| Módulo | Patrón | Qué resuelve |
|---|---|---|
| `config.py` | **Singleton / Config centralizado** | Un único `Settings` con las rutas base |
| `regions.py` | **Registro / Value Object** | `Region` por cada punto soportado; las regiones nuevas se registran en JSON |
| `repository.py` | **Repository** | `DataRepository(region=...)` lee los CSV de una región por nombre lógico |
| `recommender.py` | **Servicio de dominio** | Prioridades del agricultor → ranking de rotaciones (fiabilidad histórica, descarte de cultivos no aptos, mejor mes de inicio), sin dependencias de Streamlit |
| `hydrology.py` | **Servicio de dominio** | ETo FAO-56 reutilizable y humedad del suelo modelada (balance de balde) |
| `soil.py` / `water.py` / `crops.py` | **Dominio** | Lectura agronómica del suelo, balance de agua por cultivo, nombres comunes |
| `imerg.py` | **Dominio** | Lluvia diaria: IMERG ajustada a totales mensuales, con respaldo en POWER |
| `sources/` | **Strategy** | `DataSource.fetch()` con POWER, SMAP, ECOCROP y SoilGrids |
| `pipeline/` | **Pipeline / Chain of Responsibility** | `Pipeline` ejecuta pasos ordenados, mide tiempos, se detiene en el primer error (salvo pasos *opcionales*) |
| `retry.py` | **Retry con backoff** | Reintenta errores de red transitorios |

### Notas de rendimiento

- **SMAP:** publica una imagen cada 3 horas. Bajar las 8 diarias por 6 años no es viable (~7 s por archivo), así que `smap_sampling.py` conserva **1 lectura por día** (la más cercana a las 13:30 UTC) y descarga en lotes paralelos.
- **Motor de rotación:** el paso 13 (`generar_escenarios_rotacion`) tarda ~50 min por región; el resto del análisis, minutos.

## Cómo correr la app localmente

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
streamlit run app.py
```

Abre `http://localhost:8501`. Para correr las pruebas: `pip install pytest && python -m pytest`.

## Cómo regenerar los datos de análisis (opcional)

```bash
cd python
pip install -r requirements.txt

# Pipeline completo para una región (descarga + análisis; SMAP requiere credenciales NASA Earthdata)
python run_pipeline.py --region quindio --fecha-inicio 2020-01-01 --fecha-fin 2025-12-31

# Solo reprocesar el análisis con los datos crudos que ya están en data/
python run_pipeline.py --region quindio --analysis-only

# Una región nueva con humedad modelada (solo requiere internet)
python agregar_region.py --slug meta --nombre "Meta (piedemonte llanero)" \
  --clima "Cálido y húmedo, arroz, palma y maíz" --latitud 4.15 --longitud -73.63 --altitud 467 --ejecutar
```

Las credenciales de NASA Earthdata (solo para regiones SMAP) se configuran una vez con `python -c "import earthaccess; earthaccess.login(persist=True)"`.

## Despliegue

La app se despliega gratis en [Streamlit Community Cloud](https://streamlit.io/cloud):

1. Conecta este repositorio de GitHub.
2. Archivo principal: `app.py`.
3. Streamlit Cloud instala automáticamente `requirements.txt` de la raíz.
4. En **Settings → General → Python version** elige **3.12** (la versión por defecto más nueva no tiene aún paquetes precompilados de pandas y la instalación se queda compilando).

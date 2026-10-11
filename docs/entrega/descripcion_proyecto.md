# AgroShift — Project description / Descripción del proyecto

**Challenge / Reto:** Field Shift: Adapting Farms with NASA Data — NASA Space Apps Challenge 2026
**Live app / App en vivo:** https://agroshift.streamlit.app
**Code / Código:** https://github.com/GabrielOrtega01/AgroShift

---

## English

### One-line summary
AgroShift tells a farmer **what to plant, in what order and in which month**, using NASA satellite climate and soil-moisture data matched against what each crop needs.

### The problem
Rainfall patterns are shifting and farmers who plant by habit are exposed: the wrong crop in the wrong season wastes water, money and a harvest. Satellite data that could guide them exists, but it is raw, technical and not tied to the decisions a farmer actually faces.

### What we built
A free web app (Spanish and English) where a farmer:

1. **Chooses their region** (8 regions of Colombia, from cold Andean highlands to the dry Caribbean).
2. **Sees their climate** — month-by-month temperature, rainfall and soil moisture, and which crops fit, in plain language.
3. **Sees the water picture** — whether rainfall will cover each crop or irrigation is needed.
4. **Tells us what matters** (water, balance, soil moisture, timing), how strict to be and which crops to include, and gets a **podium of rotations** with how reliably each one has worked historically and **which month to start**.

### How it works
- **NASA POWER** — daily temperature, humidity, wind and radiation, 2020–2025.
- **NASA GPM IMERG** — daily rainfall; its magnitude is adjusted to CHIRPS monthly totals because unadjusted IMERG overestimates rainfall in several mountain areas.
- **NASA SMAP L4** — soil moisture (surface and root zone) for four regions; in the other four it is estimated with a water-balance model, clearly labelled.
- **FAO-56 Penman–Monteith** evapotranspiration and crop-stage coefficients to compute the water each crop needs.
- **FAO ECOCROP** crop requirements; a crop's suitability is capped by what temperature allows (temperature is adjusted from NASA POWER's ~50 km cell to the region's elevation), so crops the climate cannot support are excluded.
- **ISRIC SoilGrids** soil pH and texture, with warnings when the pH does not suit a crop.
- Every rotation is simulated on hundreds of historical start dates; the ranking uses **reliability** (the share of dates on which it meets the farmer's request) rather than one lucky best case.

### Honest validation
We compared three rainfall sources (NASA POWER, NASA GPM IMERG and CHIRPS). POWER missed year-to-year variation (2021 looked anomalously dry in Santander) so we use IMERG, whose magnitude we adjust to CHIRPS. Absolute millimetres are still approximate and not validated against stations; rotations are compared with each other on the same data. The app shows this comparison to the user. Modelled soil moisture correlates with SMAP at r = 0.69–0.96 (monthly climatology).

### Impact and next steps
Farmers get a recommendation they can act on without a data-science background. Adding a region needs only coordinates and about an hour of compute. Next: more regions and crops, validation against IDEAM stations, local soil tests, and prices.

### Tech
Python, Streamlit, Plotly, pandas; automated tests and CI; open source.

---

## Español

### Resumen en una línea
AgroShift le dice al agricultor **qué sembrar, en qué orden y en qué mes**, cruzando datos satelitales de clima y humedad del suelo de la NASA con lo que necesita cada cultivo.

### El problema
Los patrones de lluvia están cambiando y quien siembra por costumbre queda expuesto: el cultivo equivocado en la época equivocada desperdicia agua, dinero y una cosecha. Existen datos satelitales que podrían guiarlo, pero son técnicos y no están ligados a las decisiones reales del agricultor.

### Qué construimos
Una app web gratuita (español e inglés) donde el agricultor:

1. **Elige su región** (8 regiones de Colombia, del altiplano frío al Caribe seco).
2. **Ve su clima** — temperatura, lluvia y humedad del suelo mes a mes, y qué cultivos se adaptan, en lenguaje llano.
3. **Ve el panorama del agua** — si la lluvia alcanza para cada cultivo o necesitará riego.
4. **Dice qué le importa** (agua, balance, humedad del suelo, ajuste temporal), qué tan exigente ser y qué cultivos incluir, y recibe un **podio de rotaciones** con qué tan fiables han sido históricamente y **en qué mes iniciar**.

### Cómo funciona
- **NASA POWER** — temperatura, humedad, viento y radiación diarios 2020–2025.
- **NASA GPM IMERG** — lluvia diaria; su magnitud se ajusta a los totales mensuales de CHIRPS porque IMERG sin ajustar sobrestima la lluvia en varias zonas de montaña.
- **NASA SMAP L4** — humedad del suelo (superficie y zona de raíces) en cuatro regiones; en las otras cuatro se estima con un modelo de balance de agua, y se rotula como tal.
- **Evapotranspiración FAO-56 Penman–Monteith** y coeficientes por etapa para calcular el agua que necesita cada cultivo.
- **FAO ECOCROP**: requisitos de cada cultivo; la compatibilidad queda limitada por lo que permite la temperatura (ajustada a la altitud de la región desde la celda de ~50 km de NASA POWER), así se excluyen los cultivos que el clima no admite.
- **ISRIC SoilGrids**: pH y textura del suelo, con alertas cuando el pH no conviene a un cultivo.
- Cada rotación se simula en cientos de fechas de inicio históricas; el ranking usa la **fiabilidad** (porcentaje de fechas en que cumple lo pedido) y no un único mejor caso.

### Validación honesta
Comparamos tres fuentes de lluvia (NASA POWER, NASA GPM IMERG y CHIRPS). POWER no reproducía la variación entre años (2021 salía anómalamente seco en Santander), así que usamos IMERG con su magnitud ajustada a CHIRPS. Los milímetros absolutos siguen siendo aproximados y no se validaron contra estaciones; las rotaciones se comparan entre sí con los mismos datos. La app muestra esta comparación al usuario. La humedad modelada correlaciona con SMAP r = 0,69–0,96 (climatología mensual).

### Impacto y próximos pasos
El agricultor recibe una recomendación accionable sin necesidad de ser científico de datos. Agregar una región solo requiere coordenadas y cerca de una hora de cómputo. Siguiente: más regiones y cultivos, validación con estaciones del IDEAM, análisis de suelo locales y precios.

### Tecnología
Python, Streamlit, Plotly, pandas; pruebas automáticas y CI; código abierto.

"""Catálogo de textos de la interfaz: clave -> (español, inglés).

Cada clave lleva sus dos idiomas juntos, de modo que no puede haber un
texto sin traducir. Los campos {entre llaves} deben ser los mismos en
ambos idiomas (hay un test que lo comprueba).
"""

TEXTOS: dict[str, tuple[str, str]] = {
    # ------------------------------------------------------------ página
    "tab.inicio": ("🏠 Inicio", "🏠 Home"),
    "tab.clima": ("🌤️ Mi clima", "🌤️ My climate"),
    "tab.cultivos": ("🌾 Cultivos", "🌾 Crops"),
    "tab.agua": ("💧 Agua", "💧 Water"),
    "tab.rotacion": ("🔄 Mi rotación", "🔄 My rotation"),
    "tab.info": ("ℹ️ Cómo funciona", "ℹ️ How it works"),
    "hero.subtitulo": (
        "Decide qué sembrar y en qué orden, usando el clima y la humedad del suelo medidos por satélites de la NASA.",
        "Decide what to plant and in what order, using climate and soil moisture measured by NASA satellites.",
    ),
    "hero.chip_nasa": ("🛰️ NASA POWER + GPM + SMAP", "🛰️ NASA POWER + GPM + SMAP"),
    "hero.chip_fao": ("🌾 FAO ECOCROP", "🌾 FAO ECOCROP"),
    "hero.chip_historial": ("📅 Historial 2020–2025", "📅 Record 2020–2025"),
    "sel.region": ("📍 ¿Dónde está tu finca?", "📍 Where is your farm?"),
    "sel.zona": ("🧭 Zona de {depto}", "🧭 Zone of {depto}"),
    "sel.region_ayuda": (
        "Cada región tiene su propio clima e historial de datos.",
        "Each region has its own climate and data record.",
    ),
    "sel.idioma": ("🌐 Idioma", "🌐 Language"),
    "app.sin_datos": (
        "Todavía no hay datos calculados para **{region}**. Genera los datos con "
        "`python run_pipeline.py --region {slug}` e inténtalo de nuevo.",
        "There is no computed data for **{region}** yet. Generate it with "
        "`python run_pipeline.py --region {slug}` and try again.",
    ),
    "aviso.humedad_modelada": (
        "<b>Ojo:</b> en esta región la humedad del suelo no se midió con el satélite SMAP; es una "
        "<b>estimación</b> calculada con un balance de agua a partir de la lluvia y el clima de NASA POWER. "
        "Úsala como referencia aproximada.",
        "<b>Note:</b> in this region soil moisture was not measured by the SMAP satellite; it is an "
        "<b>estimate</b> computed with a water balance from NASA POWER rainfall and climate. "
        "Use it as an approximate reference.",
    ),
    # ------------------------------------------------------------ barra lateral
    "side.lema": ("Qué sembrar y cuándo, con datos de la NASA", "What to plant and when, with NASA data"),
    "side.clima": ("Clima", "Climate"),
    "side.altitud": ("Altitud", "Elevation"),
    "side.altitud_valor": ("{v:.0f} m s. n. m.", "{v:.0f} m a.s.l."),
    "side.punto": ("Punto de referencia", "Reference point"),
    "side.humedad": ("Humedad del suelo", "Soil moisture"),
    "side.humedad_smap": ("medida por satélite (NASA SMAP)", "satellite-measured (NASA SMAP)"),
    "side.humedad_modelo": ("estimada con modelo", "model estimate"),
    "side.como_se_usa": ("¿Cómo se usa?", "How to use it"),
    "side.pasos": (
        "1. Elige tu región.\n2. Revisa clima, cultivos y agua.\n3. En **Mi rotación**, dinos qué priorizas.",
        "1. Choose your region.\n2. Review climate, crops and water.\n3. In **My rotation**, tell us your priorities.",
    ),
    "side.datos": (
        "Datos: NASA POWER · NASA GPM IMERG · NASA SMAP · FAO ECOCROP · ISRIC SoilGrids",
        "Data: NASA POWER · NASA GPM IMERG · NASA SMAP · FAO ECOCROP · ISRIC SoilGrids",
    ),
    "side.reto": ("NASA Space Apps Challenge 2026", "NASA Space Apps Challenge 2026"),
    # ------------------------------------------------------------ niveles y estados
    "nivel.excelente": ("Excelente", "Excellent"),
    "nivel.buena": ("Buena", "Good"),
    "nivel.regular": ("Regular", "Fair"),
    "nivel.baja": ("Baja", "Low"),
    "estado.optimo": ("✅ Óptimo", "✅ Optimal"),
    "estado.tolerable": ("⚠️ Tolerable", "⚠️ Tolerable"),
    "estado.fuera": ("❌ Fuera de rango", "❌ Out of range"),
    "fert.alta": ("Alta", "High"),
    "fert.moderada": ("Moderada", "Moderate"),
    "fert.baja": ("Baja", "Low"),
    # ------------------------------------------------------------ inicio
    "inicio.que_es": ("¿Qué es AgroShift?", "What is AgroShift?"),
    "inicio.que_es_texto": (
        "Una herramienta que te ayuda a decidir **qué sembrar y en qué orden**. Cruza el clima y la humedad "
        "del suelo que miden los satélites de la NASA con lo que necesita cada cultivo, y te propone "
        "**rotaciones** que aprovechan mejor el agua de tu región.",
        "A tool that helps you decide **what to plant and in what order**. It combines the climate and soil "
        "moisture measured by NASA satellites with what each crop needs, and proposes **rotations** that make "
        "better use of your region's water.",
    ),
    "inicio.paso1_titulo": ("Elige tu región", "Choose your region"),
    "inicio.paso1_texto": (
        "Usa el selector «¿Dónde está tu finca?» de arriba. Cada región tiene su propio clima e historial.",
        "Use the “Where is your farm?” selector above. Each region has its own climate and record.",
    ),
    "inicio.paso2_titulo": ("Conoce tu clima y tus cultivos", "Learn your climate and crops"),
    "inicio.paso2_texto": (
        "Revisa lluvias, temperaturas y qué cultivos se adaptan mejor.",
        "Check rainfall, temperatures and which crops fit best.",
    ),
    "inicio.paso3_titulo": ("Recibe tu rotación", "Get your rotation"),
    "inicio.paso3_texto": (
        "Dinos qué es importante para ti y te mostramos las mejores opciones y cuándo iniciarlas.",
        "Tell us what matters to you and we show the best options and when to start them.",
    ),
    "inicio.vistazo": ("Tu región de un vistazo", "Your region at a glance"),
    "inicio.lectura": ("Lectura rápida", "Quick read"),
    "inicio.lectura_lluvia": (
        "En promedio llueve <b>{total:.0f} mm al año</b>. El mes más lluvioso es <b>{mes_max}</b> "
        "({v_max:.0f} mm) y el más seco <b>{mes_min}</b> ({v_min:.0f} mm).",
        "On average it rains <b>{total:.0f} mm per year</b>. The rainiest month is <b>{mes_max}</b> "
        "({v_max:.0f} mm) and the driest is <b>{mes_min}</b> ({v_min:.0f} mm).",
    ),
    "inicio.lectura_temperatura": (
        "Las temperaturas van de <b>{tmin:.0f} °C</b> a <b>{tmax:.0f} °C</b>. El mes más cálido es "
        "<b>{caliente}</b> y el más fresco <b>{frio}</b>.",
        "Temperatures range from <b>{tmin:.0f} °C</b> to <b>{tmax:.0f} °C</b>. The warmest month is "
        "<b>{caliente}</b> and the coolest is <b>{frio}</b>.",
    ),
    "inicio.lectura_suelo": (
        "La humedad del suelo es más alta en <b>{alta}</b> y más baja en <b>{baja}</b>: ahí conviene vigilar el riego.",
        "Soil moisture is highest in <b>{alta}</b> and lowest in <b>{baja}</b>: that is when to watch irrigation.",
    ),
    "inicio.lectura_cultivo": (
        "El cultivo mejor adaptado a este clima es <b>{cultivo}</b> ({pct:.0f} % de compatibilidad).",
        "The crop best suited to this climate is <b>{cultivo}</b> ({pct:.0f} % compatibility).",
    ),
    "inicio.top3": ("Los 3 cultivos que mejor se adaptan", "The 3 best-suited crops"),
    "inicio.ciclo": ("Ciclo de {min:.0f}–{max:.0f} días", "Cycle of {min:.0f}–{max:.0f} days"),
    "inicio.siguiente": (
        "Siguiente paso: abre la pestaña **🔄 Mi rotación** y dinos qué es importante para ti.",
        "Next step: open the **🔄 My rotation** tab and tell us what matters to you.",
    ),
    "inicio.mapa_tu_region": ("Tu región", "Your region"),
    "inicio.mapa_otras": ("Otras regiones", "Other regions"),
    "kpi.temperatura": ("🌡️ Temperatura media", "🌡️ Mean temperature"),
    "kpi.temperatura_ayuda": ("Promedio de todo el historial", "Average over the whole record"),
    "kpi.lluvia": ("🌧️ Lluvia al año", "🌧️ Rainfall per year"),
    "kpi.lluvia_ayuda": ("Promedio anual ({fuente})", "Annual average ({fuente})"),
    "kpi.dias_lluvia": ("☔ Días de lluvia", "☔ Rainy days"),
    "kpi.dias_lluvia_ayuda": ("Días con 1 mm o más", "Days with 1 mm or more"),
    "kpi.al_anio": ("al año", "per year"),
    "kpi.historial": ("🗓️ Historial", "🗓️ Record"),
    "kpi.anios": ("años", "years"),
    "kpi.historial_ayuda": ("{a0} a {a1}, datos diarios", "{a0} to {a1}, daily data"),
    # ------------------------------------------------------------ clima
    "clima.titulo": ("El clima de tu región mes a mes", "Your region's climate, month by month"),
    "clima.intro": (
        "Promedios de {a0} a {a1} (NASA POWER para el clima, {fuente} para la lluvia y NASA SMAP para "
        "la humedad del suelo). Úsalos para saber cuándo esperar lluvias y cuándo vigilar el riego.",
        "Averages for {a0}–{a1} (NASA POWER for climate, {fuente} for rainfall and NASA SMAP for soil "
        "moisture). Use them to know when to expect rain and when to watch irrigation.",
    ),
    "clima.maxima": ("Máxima", "Maximum"),
    "clima.minima": ("Mínima", "Minimum"),
    "clima.media": ("Media", "Mean"),
    "clima.grafica_temperatura": ("🌡️ Temperatura (°C)", "🌡️ Temperature (°C)"),
    "clima.nota_temperatura": (
        "La franja muestra el rango entre la mínima y la máxima de cada mes.",
        "The band shows the range between each month's minimum and maximum.",
    ),
    "clima.lluvia": ("Lluvia", "Rainfall"),
    "clima.grafica_lluvia": ("🌧️ Lluvia por mes (mm)", "🌧️ Rainfall per month (mm)"),
    "clima.nota_lluvia": ("La barra más oscura es el mes más lluvioso.", "The darkest bar is the rainiest month."),
    "clima.superficie": ("Superficie (0–5 cm)", "Surface (0–5 cm)"),
    "clima.raices": ("Zona de raíces (hasta 1 m)", "Root zone (down to 1 m)"),
    "clima.grafica_humedad": ("🌱 Humedad del suelo (m³/m³)", "🌱 Soil moisture (m³/m³)"),
    "clima.nota_humedad": (
        "Más alto = suelo más húmedo. La zona de raíces es la que usan los cultivos.",
        "Higher = wetter soil. The root zone is the one crops use.",
    ),
    "clima.promedio": ("Promedio {v:.0f} mm", "Average {v:.0f} mm"),
    "clima.grafica_anual": ("📆 Lluvia total por año (mm)", "📆 Total rainfall per year (mm)"),
    "clima.nota_anual": (
        "Azul: año más lluvioso que el promedio. Naranja: año más seco.",
        "Blue: wetter than average year. Orange: drier year.",
    ),
    "clima.tabla": ("Ver la tabla de datos mensuales", "View the monthly data table"),
    # ------------------------------------------------------------ cultivos
    "cultivos.titulo": ("¿Qué cultivos se adaptan a tu clima?", "Which crops fit your climate?"),
    "cultivos.intro": (
        "El puntaje compara la temperatura y la lluvia de tu región con lo que cada cultivo necesita "
        "según la base de datos FAO ECOCROP. Nunca supera lo que permite la temperatura: la lluvia que "
        "falta se puede suplir con riego; el frío o el calor excesivo, no.",
        "The score compares your region's temperature and rainfall with what each crop needs, "
        "according to the FAO ECOCROP database. It never exceeds what temperature allows: missing rain "
        "can be supplied by irrigation; excessive cold or heat cannot.",
    ),
    "cultivos.aviso_helada": (
        "<b>Alerta de heladas:</b> tu región está a {altitud:.0f} m de altitud, donde pueden darse heladas "
        "nocturnas. Los datos son de una celda de ~50 km y <b>no capturan heladas locales</b>: consulta "
        "el riesgo con productores o técnicos de la zona antes de sembrar cultivos sensibles.",
        "<b>Frost alert:</b> your region is at {altitud:.0f} m elevation, where night frosts can occur. "
        "The data come from a ~50 km cell and <b>do not capture local frosts</b>: ask local growers or "
        "advisors about the risk before planting sensitive crops.",
    ),
    "cultivos.eje": ("Compatibilidad climática (%)", "Climate suitability (%)"),
    "cultivos.suelo_titulo": ("Suelo estimado de tu región (0–30 cm)", "Estimated soil of your region (0–30 cm)"),
    "cultivos.detalle": ("Mira un cultivo en detalle", "Look at one crop in detail"),
    "cultivos.selector": ("Cultivo", "Crop"),
    "cultivos.compatibilidad": ("Compatibilidad con tu clima", "Suitability for your climate"),
    "cultivos.ciclo": ("Ciclo del cultivo: {min:.0f} a {max:.0f} días.", "Crop cycle: {min:.0f} to {max:.0f} days."),
    "cultivos.sin_suelo": ("Sin datos de suelo", "No soil data"),
    "cultivos.aviso_sin_suelo": (
        "<b>Ojo con el suelo:</b> aún no hay estimación de suelo para esta región. Antes de sembrar, "
        "confirma el pH y la fertilidad con un análisis de suelo o con tu asistente técnico.",
        "<b>Mind the soil:</b> there is no soil estimate for this region yet. Before planting, confirm pH "
        "and fertility with a soil test or your agricultural advisor.",
    ),
    "cultivos.aviso_suelo": (
        "<b>Sobre el suelo:</b> los valores de suelo son una estimación de ISRIC SoilGrids (250 m, mediana de "
        "{n} puntos cerca de tu región), no una medición de tu finca. Confírmalos con un análisis de "
        "laboratorio o con tu asistente técnico.",
        "<b>About the soil:</b> soil values are an ISRIC SoilGrids estimate (250 m, median of {n} points "
        "near your region), not a measurement of your farm. Confirm them with a lab test or your "
        "agricultural advisor.",
    ),
    "var.temperatura": ("🌡️ Temperatura media", "🌡️ Mean temperature"),
    "var.extremos": ("📅 Días en rango tolerable", "📅 Days in tolerable range"),
    "var.extremos_necesita": (
        "media diaria entre {tmin:.0f} y {tmax:.0f} °C",
        "daily mean between {tmin:.0f} and {tmax:.0f} °C",
    ),
    "var.extremos_region": ("{pct:.0f} % de los días", "{pct:.0f} % of days"),
    "var.lluvia": ("🌧️ Lluvia al año", "🌧️ Rainfall per year"),
    "var.ph": ("🧪 pH del suelo", "🧪 Soil pH"),
    "var.fertilidad": ("🌱 Fertilidad del suelo", "🌱 Soil fertility"),
    "suelo.ph": ("pH del suelo", "Soil pH"),
    "suelo.ph_ayuda": ("Estimado, 0–30 cm", "Estimated, 0–30 cm"),
    "suelo.textura": ("Textura", "Texture"),
    "suelo.textura_ayuda": (
        "Arcilla {arcilla:.0f} % · arena {arena:.0f} % · limo {limo:.0f} %",
        "Clay {arcilla:.0f} % · sand {arena:.0f} % · silt {limo:.0f} %",
    ),
    "suelo.materia_organica": ("Materia orgánica", "Organic matter"),
    "suelo.mo_ayuda": ("Indicador de fertilidad, 0–30 cm", "Fertility indicator, 0–30 cm"),
    "suelo.mo_valor": ("Materia orgánica {mo:.1f} %", "Organic matter {mo:.1f} %"),
    "suelo.estimado": ("estimado", "estimated"),
    # ------------------------------------------------------------ agua
    "agua.titulo": ("¿Alcanza el agua de la lluvia?", "Is rainfall enough?"),
    "agua.intro": (
        "Para cada cultivo comparamos la lluvia con el agua que necesita (evapotranspiración, ETc), "
        "promediando un ciclo en todas las fechas de inicio entre {a0} y {a1}. Es el dato clave para "
        "decidir si necesitarás riego.",
        "For each crop we compare rainfall with the water it needs (evapotranspiration, ETc), averaging "
        "one cycle over all start dates between {a0} and {a1}. It is the key figure to decide whether "
        "you will need irrigation.",
    ),
    "agua.serie_lluvia": ("Lluvia recibida", "Rainfall received"),
    "agua.serie_necesidad": ("Agua que necesita", "Water needed"),
    "agua.grafica_comparacion": (
        "Lluvia vs. agua que necesita el cultivo (mm por ciclo)",
        "Rainfall vs. crop water need (mm per cycle)",
    ),
    "agua.grafica_saldo": ("Saldo de agua: lluvia − necesidad (mm)", "Water balance: rainfall − need (mm)"),
    "agua.leyenda_saldo": (
        "Verde: sobra agua. Rojo: falta agua y probablemente necesitarás riego.",
        "Green: water surplus. Red: water shortfall; you will probably need irrigation.",
    ),
    "agua.sin_deficit": (
        "<b>Buenas noticias:</b> en {region} la lluvia cubre, en promedio, la necesidad de agua de todos "
        "los cultivos analizados.",
        "<b>Good news:</b> in {region} rainfall covers, on average, the water need of all analysed crops.",
    ),
    "agua.con_deficit": (
        "<b>Atención:</b> con la lluvia sola, estos cultivos quedan con déficit de agua en promedio: "
        "<b>{cultivos}</b>. Considera riego o ajustar la fecha de siembra.",
        "<b>Heads up:</b> with rainfall alone, these crops end up with an average water deficit: "
        "<b>{cultivos}</b>. Consider irrigation or adjusting the planting date.",
    ),
    "agua.detalle": ("Ver el detalle por cultivo", "View the detail by crop"),
    "agua.nota_cobertura": (
        "«Lluvia cubre» es el porcentaje de la necesidad de agua que cubre la lluvia durante el ciclo "
        "(tope 100 %). Es un promedio histórico: un año seco puede quedar muy por debajo.",
        "“Rainfall covers” is the share of the crop's water need covered by rainfall during the cycle "
        "(capped at 100 %). It is a historical average: a dry year can fall well below it.",
    ),
    # ------------------------------------------------------------ rotación
    "rot.titulo": ("Encuentra tu rotación de cultivos", "Find your crop rotation"),
    "rot.intro": (
        "Elige qué es importante para ti y AgroShift revisa cientos de combinaciones de cultivos y fechas "
        "de siembra usando el historial de tu región.",
        "Choose what matters to you and AgroShift reviews hundreds of crop combinations and planting dates "
        "using your region's record.",
    ),
    "rot.paso1": ("1 · ¿Qué es lo más importante para ti?", "1 · What matters most to you?"),
    "rot.prioridades_etiqueta": (
        "Condiciones que la rotación debe cumplir (puedes elegir varias)",
        "Conditions the rotation must meet (you can pick several)",
    ),
    "rot.sin_seleccion": (
        "Sin selección: se muestran las rotaciones más equilibradas en general.",
        "No selection: the most balanced rotations overall are shown.",
    ),
    "rot.paso2": ("2 · Afina tu búsqueda", "2 · Fine-tune your search"),
    "rot.exigencia": ("Nivel de exigencia", "Strictness"),
    "rot.exigencia_flexible": ("Flexible", "Flexible"),
    "rot.exigencia_equilibrado": ("Equilibrado", "Balanced"),
    "rot.exigencia_exigente": ("Exigente", "Strict"),
    "rot.exigencia_ayuda": (
        "Cuántos de los 4 criterios (agua, balance, humedad, ajuste temporal) debe cumplir. "
        "Flexible: 2 de 4 · Equilibrado: 3 de 4 · Exigente: 4 de 4.",
        "How many of the 4 criteria (water, balance, moisture, timing) it must meet. "
        "Flexible: 2 of 4 · Balanced: 3 of 4 · Strict: 4 of 4.",
    ),
    "rot.n_cultivos": ("Cultivos por rotación", "Crops per rotation"),
    "rot.cualquiera": ("Cualquiera", "Any"),
    "rot.adaptacion_min": (
        "Adaptación mínima al clima de los cultivos (%)",
        "Minimum climate suitability of crops (%)",
    ),
    "rot.adaptacion_ayuda": (
        "Descarta rotaciones que incluyan cultivos poco adaptados a la temperatura y la lluvia de tu región "
        "(puntaje FAO ECOCROP de la pestaña Cultivos).",
        "Drops rotations that include crops poorly suited to your region's temperature and rainfall "
        "(FAO ECOCROP score from the Crops tab).",
    ),
    "rot.incluir": ("Quiero que incluya…", "I want it to include…"),
    "rot.incluir_vacio": ("Cualquier cultivo", "Any crop"),
    "rot.descartados": (
        "🌡️ Descartados por no adaptarse al clima de tu región: {cultivos}. "
        "Cambia la adaptación mínima para incluirlos.",
        "🌡️ Excluded because they do not fit your region's climate: {cultivos}. "
        "Change the minimum suitability to include them.",
    ),
    "rot.paso3": ("3 · Tus mejores opciones", "3 · Your best options"),
    "rot.sin_resultados": (
        "<b>Ninguna rotación cumple todo lo que pediste.</b> Prueba bajando el nivel de exigencia, la "
        "adaptación mínima al clima, quitando alguna condición o dejando que el sistema elija los cultivos.",
        "<b>No rotation meets everything you asked for.</b> Try lowering the strictness or the minimum "
        "climate suitability, removing a condition, or letting the system choose the crops.",
    ),
    "rot.encontramos": (
        "Encontramos **{n}** combinaciones de cultivos posibles ({total} si cuentas el orden). "
        "Estas son las mejores:",
        "We found **{n}** possible crop combinations ({total} counting order). These are the best:",
    ),
    "rot.podio_fiabilidad": (
        "de las fechas de inicio históricas cumplen lo que pediste",
        "of historical start dates meet what you asked for",
    ),
    "rot.podio_duracion": ("~{dias:.0f} días en total · {n} cultivos", "~{dias:.0f} days in total · {n} crops"),
    "rot.podio_adaptacion": ("Adaptación al clima: {pct:.0f}%", "Climate suitability: {pct:.0f}%"),
    "rot.podio_meses": ("Mejores meses: {meses}", "Best months: {meses}"),
    "rot.podio_sin_mes": ("Sin mes destacado", "No standout month"),
    "rot.paso4": ("4 · Mira el detalle", "4 · See the detail"),
    "rot.selector": ("Rotación", "Rotation"),
    "rot.linea_tiempo": ("Así se ve la rotación en el tiempo", "The rotation over time"),
    "rot.dias_abrev": ("días", "days"),
    "rot.eje_dias": ("Días desde el inicio de la rotación", "Days since the rotation starts"),
    "rot.mes_inicio": ("¿En qué mes conviene iniciar?", "Which month is best to start?"),
    "rot.eje_fechas_cumplen": ("% de fechas que cumplen", "% of dates that comply"),
    "rot.mejores_meses": ("Mejores meses para iniciar: **{meses}**.", "Best months to start: **{meses}**."),
    "rot.cultivo_por_cultivo": ("Cultivo por cultivo", "Crop by crop"),
    "rot.por_que": (
        "<b>Por qué se recomienda:</b> en el {fiabilidad:.0f} % de las fechas de inicio históricas, esta "
        "rotación ({cultivos}) cumplió lo que pediste. En promedio la lluvia cubre <b>{cobertura:.0f} %</b> "
        "del agua que necesitan los cultivos y la humedad del suelo se ubica en el <b>percentil "
        "{percentil:.0f}</b> de su historial.",
        "<b>Why it is recommended:</b> in {fiabilidad:.0f} % of historical start dates, this rotation "
        "({cultivos}) met what you asked for. On average rainfall covers <b>{cobertura:.0f} %</b> of the "
        "water the crops need and soil moisture sits at the <b>{percentil:.0f}th percentile</b> of its record.",
    ),
    "rot.ph_tolerable": (
        "<b>Ojo con el suelo:</b> el pH estimado de tu región ({ph:.1f}) es tolerable pero no óptimo para "
        "{cultivo} (óptimo {pmin:.1f}–{pmax:.1f}); podría afectar el rendimiento. Confírmalo con un análisis de suelo.",
        "<b>Mind the soil:</b> your region's estimated pH ({ph:.1f}) is tolerable but not optimal for "
        "{cultivo} (optimal {pmin:.1f}–{pmax:.1f}); it could reduce yield. Confirm it with a soil test.",
    ),
    "rot.ph_fuera": (
        "<b>Alerta de suelo:</b> el pH estimado ({ph:.1f}) está fuera del rango tolerable de {cultivo} "
        "({amin:.1f}–{amax:.1f}). Confirma con un análisis de suelo antes de sembrar.",
        "<b>Soil alert:</b> the estimated pH ({ph:.1f}) is outside {cultivo}'s tolerable range "
        "({amin:.1f}–{amax:.1f}). Confirm with a soil test before planting.",
    ),
    "rot.todas": ("Ver las {n} rotaciones y descargar", "See all {n} rotations and download"),
    "rot.descargar": ("⬇️ Descargar ranking (CSV)", "⬇️ Download ranking (CSV)"),
    # ------------------------------------------------------------ prioridades
    "prioridad.agua.nombre": ("Agua", "Water"),
    "prioridad.agua.explicacion": (
        "La lluvia cubre al menos el 75 % del agua que necesitan los cultivos.",
        "Rainfall covers at least 75 % of the water the crops need.",
    ),
    "prioridad.balance.nombre": ("Balance", "Balance"),
    "prioridad.balance.explicacion": (
        "La lluvia compensa la demanda de agua: no queda déficit neto (≥ 0 mm).",
        "Rainfall offsets water demand: there is no net deficit (≥ 0 mm).",
    ),
    "prioridad.humedad.nombre": ("Humedad del suelo", "Soil moisture"),
    "prioridad.humedad.explicacion": (
        "La humedad del suelo se mantiene por encima del 25 % histórico más seco.",
        "Soil moisture stays above the driest 25 % of its record.",
    ),
    "prioridad.temporal.nombre": ("Ajuste temporal", "Timing fit"),
    "prioridad.temporal.explicacion": (
        "Lluvia (≥ 60 %) y humedad del suelo son suficientes al mismo tiempo.",
        "Rainfall (≥ 60 %) and soil moisture are both sufficient at the same time.",
    ),
    # ------------------------------------------------------------ columnas de tablas
    "col.anio": ("Año", "Year"),
    "col.mes": ("Mes", "Month"),
    "col.cultivo": ("Cultivo", "Crop"),
    "col.rotacion": ("Rotación", "Rotation"),
    "col.etapa": ("Etapa", "Stage"),
    "col.dias": ("Días", "Days"),
    "col.dias_ciclo": ("Días del ciclo", "Cycle days"),
    "col.lluvia_mm": ("Lluvia (mm)", "Rainfall (mm)"),
    "col.necesita_mm": ("Necesita (mm)", "Needs (mm)"),
    "col.necesidad_mm": ("Necesidad (mm)", "Need (mm)"),
    "col.saldo_mm": ("Saldo (mm)", "Balance (mm)"),
    "col.cobertura_pct": ("Lluvia cubre (%)", "Rainfall covers (%)"),
    "col.temp_media": ("Temp. media (°C)", "Mean temp. (°C)"),
    "col.temp_minima": ("Temp. mínima (°C)", "Min. temp. (°C)"),
    "col.temp_maxima": ("Temp. máxima (°C)", "Max. temp. (°C)"),
    "col.humedad_raices": ("Humedad raíces (m³/m³)", "Root-zone moisture (m³/m³)"),
    "col.variable": ("Variable", "Variable"),
    "col.necesita": ("Lo que necesita", "What it needs"),
    "col.tu_region": ("Tu región", "Your region"),
    "col.estado": ("Estado", "Status"),
    "col.fiabilidad": ("Fiabilidad (%)", "Reliability (%)"),
    "col.adaptacion": ("Adaptación al clima (%)", "Climate suitability (%)"),
    "col.criterios": ("Criterios (de 4)", "Criteria (of 4)"),
    "col.duracion": ("Duración (días)", "Duration (days)"),
    "col.cobertura_agua": ("Cobertura de agua (%)", "Water coverage (%)"),
    "col.fuente": ("Fuente", "Source"),
    "col.aporta": ("Qué aporta", "What it provides"),
    "col.resolucion": ("Resolución", "Resolution"),
    "col.power_mm": ("NASA POWER (mm)", "NASA POWER (mm)"),
    "col.imerg_mm": ("IMERG sin ajustar (mm)", "Unadjusted IMERG (mm)"),
    "col.diferencia_imerg_pct": ("IMERG vs CHIRPS (%)", "IMERG vs CHIRPS (%)"),
    "col.chirps_mm": ("CHIRPS (mm)", "CHIRPS (mm)"),
    "col.diferencia_pct": ("Diferencia (%)", "Difference (%)"),
    # ------------------------------------------------------------ cómo funciona
    "met.titulo": ("¿Cómo llega AgroShift a sus recomendaciones?", "How does AgroShift reach its recommendations?"),
    "met.intro": (
        "AgroShift **no adivina**: combina datos medidos por satélite con las necesidades conocidas de "
        "cada cultivo. Estos son los pasos.",
        "AgroShift **does not guess**: it combines satellite measurements with the known needs of each "
        "crop. These are the steps.",
    ),
    "met.p1_titulo": ("Medimos el clima y la lluvia", "We measure climate and rainfall"),
    "met.p1_texto": (
        "Temperatura (ajustada a la altitud), viento y radiación diaria (NASA POWER) y lluvia diaria "
        "(NASA GPM IMERG) desde 2020.",
        "Daily temperature (adjusted to elevation), wind and radiation (NASA POWER) and daily rainfall "
        "(NASA GPM IMERG) since 2020.",
    ),
    "met.p2_titulo": ("Medimos el suelo", "We measure the soil"),
    "met.p2_texto": (
        "Humedad de la superficie y de la zona de raíces (NASA SMAP) y características del suelo (SoilGrids).",
        "Surface and root-zone moisture (NASA SMAP) and soil characteristics (SoilGrids).",
    ),
    "met.p3_titulo": ("Calculamos el agua", "We compute the water"),
    "met.p3_texto": (
        "Estimamos cuánta agua pierde y pide cada cultivo etapa por etapa (método FAO‑56).",
        "We estimate how much water each crop loses and needs, stage by stage (FAO‑56 method).",
    ),
    "met.p4_titulo": ("Probamos rotaciones", "We test rotations"),
    "met.p4_texto": (
        "Simulamos cada rotación en muchas fechas de inicio del historial y las comparamos.",
        "We simulate each rotation on many start dates from the record and compare them.",
    ),
    "met.criterios_titulo": ("Los 4 criterios de evaluación", "The 4 evaluation criteria"),
    "met.criterios_nota": (
        "Una rotación suma un punto por cada criterio que cumple. El máximo es 4.",
        "A rotation earns one point for each criterion it meets. The maximum is 4.",
    ),
    "met.fiabilidad_titulo": ("¿Qué significa «fiabilidad»?", "What does “reliability” mean?"),
    "met.fiabilidad_texto": (
        "Nadie puede predecir exactamente el clima del próximo año. Por eso AgroShift prueba cada rotación "
        "en **todas las fechas de inicio del historial (2020–2025)** y te dice en qué porcentaje de ellas "
        "se cumplió lo que pediste. Un **90 %** significa que la rotación funcionó casi siempre; un "
        "**30 %**, que depende mucho del año.",
        "Nobody can predict next year's weather exactly. So AgroShift tests each rotation on **all start "
        "dates in the record (2020–2025)** and tells you in what share of them what you asked for was met. "
        "**90 %** means the rotation worked almost always; **30 %**, that it depends a lot on the year.",
    ),
    "met.clima_titulo": (
        "¿Y si un cultivo no se da bien en mi clima?",
        "What if a crop does not do well in my climate?",
    ),
    "met.clima_texto": (
        "El cálculo de agua por sí solo no sabe si hace demasiado frío o calor para un cultivo. Por eso "
        "AgroShift cruza cada rotación con la **adaptación al clima** de la pestaña Cultivos y, por "
        "defecto, descarta las que incluyen cultivos con menos de **50 %** (la lluvia que falta se puede "
        "suplir con riego; el frío o el calor excesivo, no). Además, la temperatura se ajusta a la "
        "**altitud** de tu región con el gradiente estándar de 6,5 °C por km, porque NASA POWER entrega "
        "la temperatura de una celda de ~50 km a su altitud media. Puedes cambiar el mínimo en **Mi "
        "rotación**.",
        "The water calculation alone does not know if it is too cold or too hot for a crop. That is why "
        "AgroShift cross-checks each rotation with the **climate suitability** from the Crops tab and, by "
        "default, drops those that include crops under **50 %** (missing rain can be supplied by "
        "irrigation; excessive cold or heat cannot). The temperature is also adjusted to your region's "
        "**elevation** with the standard 6.5 °C per km lapse rate, because NASA POWER gives the "
        "temperature of a ~50 km cell at its mean elevation. You can change the minimum in **My "
        "rotation**.",
    ),
    "met.fuentes_titulo": ("De dónde salen los datos", "Where the data comes from"),
    "met.fuente_power": (
        "Clima diario: temperatura, lluvia, humedad relativa, viento, radiación",
        "Daily climate: temperature, rainfall, relative humidity, wind, radiation",
    ),
    "met.res_power": ("~50 km, diaria", "~50 km, daily"),
    "met.fuente_smap": (
        "Humedad del suelo (superficie y zona de raíces)",
        "Soil moisture (surface and root zone)",
    ),
    "met.res_smap": ("9 km, una muestra al día", "9 km, one sample per day"),
    "met.fuente_ecocrop": (
        "Temperatura, lluvia, pH y ciclo que necesita cada cultivo",
        "Temperature, rainfall, pH and cycle each crop needs",
    ),
    "met.res_ecocrop": ("Por especie", "Per species"),
    "met.fuente_suelo": (
        "Textura, pH y carbono orgánico del suelo estimados (0–30 cm)",
        "Estimated soil texture, pH and organic carbon (0–30 cm)",
    ),
    "met.res_suelo": ("250 m", "250 m"),
    "met.fuente_imerg": (
        "Lluvia diaria satelital calibrada con pluviómetros (fuente de la lluvia de AgroShift)",
        "Daily satellite rainfall calibrated with rain gauges (AgroShift's rainfall source)",
    ),
    "met.res_imerg": ("~10 km, diaria", "~10 km, daily"),
    "met.fuente_chirps": (
        "Totales mensuales de lluvia (satélite + pluviómetros): referencia para ajustar la magnitud de IMERG",
        "Monthly rainfall totals (satellite + rain gauges): reference to adjust IMERG's magnitude",
    ),
    "met.res_chirps": ("5 km, mensual", "5 km, monthly"),
    "met.calidad_titulo": ("Calidad de los datos de lluvia", "Rainfall data quality"),
    "met.calidad_texto": (
        "La lluvia que usa AgroShift es la de **NASA GPM IMERG**, que sigue bien los años secos y húmedos, "
        "con su magnitud ajustada a los totales mensuales de **CHIRPS** (satélite + pluviómetros) porque "
        "IMERG sin ajustar sobrestima la lluvia en varias zonas de montaña. NASA POWER se descartó para la "
        "lluvia: no reproducía bien la variación entre años. La tabla compara las tres fuentes.",
        "The rainfall AgroShift uses is **NASA GPM IMERG**, which follows dry and wet years well, with its "
        "magnitude adjusted to the monthly totals of **CHIRPS** (satellite + rain gauges) because "
        "unadjusted IMERG overestimates rainfall in several mountain areas. NASA POWER was dropped for "
        "rainfall: it did not reproduce year-to-year variation well. The table compares the three sources.",
    ),
    "met.calidad_alerta": (
        "<b>Atención:</b> en {region}, los totales anuales de IMERG sin ajustar difieren en promedio "
        "<b>{medio:.0f} %</b> de CHIRPS (el año más distinto fue {anio}: {dif:+.0f} %). Por eso se ajusta "
        "su magnitud; aun así, los milímetros absolutos son aproximados y las rotaciones se comparan entre "
        "sí con los mismos datos.",
        "<b>Heads up:</b> in {region}, unadjusted IMERG annual totals differ on average <b>{medio:.0f} %</b> "
        "from CHIRPS (the most different year was {anio}: {dif:+.0f} %). That is why its magnitude is "
        "adjusted; absolute millimetres are still approximate and rotations are compared with each other "
        "on the same data.",
    ),
    "met.calidad_ok": (
        "Los totales anuales de IMERG sin ajustar difieren en promedio solo <b>{medio:.0f} %</b> de "
        "CHIRPS: buena concordancia.",
        "Unadjusted IMERG annual totals differ on average by only <b>{medio:.0f} %</b> from CHIRPS: good "
        "agreement.",
    ),
    "met.calidad_sin_datos": (
        "Aún no hay comparación disponible para esta región.",
        "No comparison is available for this region yet.",
    ),
    "met.glosario_titulo": ("Glosario", "Glossary"),
    "met.glosario_ver": ("Ver términos técnicos", "See technical terms"),
    "met.glosario_texto": (
        "- **ETo (evapotranspiración de referencia):** agua que pierde un cultivo de referencia por "
        "evaporación y transpiración.\n"
        "- **ETc:** agua que realmente necesita *tu* cultivo en cada etapa (ETo × coeficiente del cultivo).\n"
        "- **Balance hídrico:** lluvia menos ETc. Positivo = sobra agua; negativo = falta.\n"
        "- **Percentil de humedad:** compara la humedad del suelo con su propio historial. P25 significa que "
        "el suelo está más húmedo que el 25 % de los días registrados.\n"
        "- **m³/m³:** volumen de agua por volumen de suelo (0,30 = 30 % del suelo es agua).",
        "- **ETo (reference evapotranspiration):** water lost by a reference crop through evaporation and "
        "transpiration.\n"
        "- **ETc:** water *your* crop really needs at each stage (ETo × crop coefficient).\n"
        "- **Water balance:** rainfall minus ETc. Positive = surplus; negative = shortfall.\n"
        "- **Moisture percentile:** compares soil moisture with its own record. P25 means the soil is "
        "wetter than 25 % of recorded days.\n"
        "- **m³/m³:** volume of water per volume of soil (0.30 = 30 % of the soil is water).",
    ),
    "met.limites_titulo": ("Límites que debes conocer", "Limits you should know"),
    "met.limites": (
        "<ul style='margin:0;padding-left:1.2rem'>"
        "<li>Los datos representan un <b>punto de referencia por región</b>, no tu finca exacta; el "
        "microclima, la altitud y la pendiente pueden variar.</li>"
        "<li>La humedad del suelo viene de un satélite con celdas de <b>9 km</b>; en {modelo} de las "
        "{regiones} regiones es una <b>estimación con modelo</b>, no una medición.</li>"
        "<li>El suelo es una <b>estimación global (SoilGrids, 250 m)</b>: confirma pH y fertilidad con un "
        "análisis de laboratorio.</li>"
        "<li>La lluvia absoluta puede diferir de otras fuentes (ver Calidad de los datos).</li>"
        "<li>Hoy cubre <b>{regiones} regiones</b> y <b>{cultivos} cultivos</b>; no considera precios, "
        "costos ni plagas.</li>"
        "<li>Es una <b>herramienta de apoyo</b>: no reemplaza la asesoría de un técnico agropecuario.</li>"
        "</ul>",
        "<ul style='margin:0;padding-left:1.2rem'>"
        "<li>The data represent a <b>reference point per region</b>, not your exact farm; microclimate, "
        "elevation and slope may vary.</li>"
        "<li>Soil moisture comes from a satellite with <b>9 km</b> cells; in {modelo} of the {regiones} "
        "regions it is a <b>model estimate</b>, not a measurement.</li>"
        "<li>Soil is a <b>global estimate (SoilGrids, 250 m)</b>: confirm pH and fertility with a lab "
        "test.</li>"
        "<li>Absolute rainfall may differ from other sources (see Data quality).</li>"
        "<li>It currently covers <b>{regiones} regions</b> and <b>{cultivos} crops</b>; it does not "
        "consider prices, costs or pests.</li>"
        "<li>It is a <b>decision-support tool</b>: it does not replace the advice of an agricultural "
        "technician.</li>"
        "</ul>",
    ),
    "met.pie": (
        "Proyecto desarrollado para el NASA Space Apps Challenge 2026 — «Field Shift: Adapting Farms with "
        "NASA Data». Código abierto (licencia MIT): [{repo}]({repo}). Datos de NASA (POWER, GPM IMERG, "
        "SMAP), CHIRPS, ISRIC SoilGrids (CC BY 4.0) y FAO ECOCROP; las citas y los términos de cada "
        "fuente están en el README.",
        "Project built for the NASA Space Apps Challenge 2026 — “Field Shift: Adapting Farms with NASA "
        "Data”. Open source (MIT license): [{repo}]({repo}). Data from NASA (POWER, GPM IMERG, SMAP), "
        "CHIRPS, ISRIC SoilGrids (CC BY 4.0) and FAO ECOCROP; citations and terms for each source are "
        "in the README.",
    ),
    # ------------------------------------------------------------ regiones
    "region.santander.nombre": (
        "Santander · Bucaramanga (mesa de Bucaramanga)",
        "Santander · Bucaramanga (Bucaramanga plateau)",
    ),
    "region.santander.corto": ("Santander · Bucaramanga", "Santander · Bucaramanga"),
    "region.santander.zona": ("Bucaramanga", "Bucaramanga"),
    "region.santander.clima": ("Valle intermedio, cálido-húmedo", "Warm, humid mid-elevation valley"),
    "region.santander_magdalena.nombre": (
        "Santander · Magdalena Medio (Barrancabermeja)",
        "Santander · Middle Magdalena (Barrancabermeja)",
    ),
    "region.santander_magdalena.corto": ("Santander · Magdalena Medio", "Santander · Middle Magdalena"),
    "region.santander_magdalena.zona": ("Magdalena Medio", "Middle Magdalena"),
    "region.santander_magdalena.clima": (
        "Cálido y húmedo de llanura, palma, arroz y ganadería",
        "Warm, humid lowland: oil palm, rice and cattle",
    ),
    "region.santander_chicamocha.nombre": (
        "Santander · Chicamocha (cañón de San Gil)",
        "Santander · Chicamocha (San Gil canyon)",
    ),
    "region.santander_chicamocha.corto": ("Santander · Chicamocha", "Santander · Chicamocha"),
    "region.santander_chicamocha.zona": ("Chicamocha", "Chicamocha"),
    "region.santander_chicamocha.clima": (
        "Templado y seco de cañón, caña, tabaco y cebolla",
        "Dry, temperate canyon: sugarcane, tobacco and onion",
    ),
    "region.santander_garcia_rovira.nombre": (
        "Santander · García Rovira (altiplano de Málaga)",
        "Santander · García Rovira (Málaga highlands)",
    ),
    "region.santander_garcia_rovira.corto": ("Santander · García Rovira", "Santander · García Rovira"),
    "region.santander_garcia_rovira.zona": ("García Rovira", "García Rovira"),
    "region.santander_garcia_rovira.clima": (
        "Frío de montaña, papa, cebolla y arveja",
        "Cold mountain climate: potato, onion and peas",
    ),
    "region.quindio.nombre": ("Quindío (eje cafetero)", "Quindío (coffee-growing axis)"),
    "region.quindio.corto": ("Quindío", "Quindío"),
    "region.quindio.clima": ("Templado de montaña, zona cafetera", "Temperate mountain climate, coffee zone"),
    "region.cordoba.nombre": ("Córdoba (Caribe seco)", "Córdoba (dry Caribbean)"),
    "region.cordoba.corto": ("Córdoba", "Córdoba"),
    "region.cordoba.clima": (
        "Tropical seco, ganadería y cultivos de secano",
        "Dry tropical, cattle and rainfed crops",
    ),
    "region.boyaca.nombre": ("Boyacá (altiplano cundiboyacense)", "Boyacá (Cundiboyacense highlands)"),
    "region.boyaca.corto": ("Boyacá", "Boyacá"),
    "region.boyaca.clima": ("Frío de altiplano andino, papa y cereales", "Cold Andean highland, potato and cereals"),
    "region.cundinamarca.nombre": ("Cundinamarca (sabana de Bogotá)", "Cundinamarca (Bogotá savanna)"),
    "region.cundinamarca.corto": ("Cundinamarca", "Cundinamarca"),
    "region.cundinamarca.clima": (
        "Altiplano frío y húmedo, flores, papa y hortalizas",
        "Cold, humid highland: flowers, potato and vegetables",
    ),
    "region.valle.nombre": ("Valle del Cauca (valle del río Cauca)", "Valle del Cauca (Cauca River valley)"),
    "region.valle.corto": ("Valle del Cauca", "Valle del Cauca"),
    "region.valle.clima": (
        "Valle cálido y soleado, caña de azúcar y frutales",
        "Warm, sunny valley: sugarcane and fruit",
    ),
    "region.meta.nombre": ("Meta (piedemonte llanero)", "Meta (Llanos foothills)"),
    "region.meta.corto": ("Meta", "Meta"),
    "region.meta.clima": ("Cálido y húmedo, arroz, palma y maíz", "Warm and humid: rice, oil palm and maize"),
    "region.narino.nombre": ("Nariño (altiplano de Pasto)", "Nariño (Pasto highlands)"),
    "region.narino.corto": ("Nariño", "Nariño"),
    "region.narino.clima": (
        "Frío andino del sur, papa, maíz y lácteos",
        "Cold southern Andes: potato, maize and dairy",
    ),
    "region.antioquia.nombre": ("Antioquia (altiplano de Rionegro)", "Antioquia (Rionegro highlands)"),
    "region.antioquia.corto": ("Antioquia", "Antioquia"),
    "region.antioquia.clima": (
        "Altiplano templado y fresco, papa, hortalizas y flores",
        "Cool temperate highland: potato, vegetables and flowers",
    ),
    "region.huila.nombre": ("Huila (zona cafetera de Pitalito)", "Huila (Pitalito coffee zone)"),
    "region.huila.corto": ("Huila", "Huila"),
    "region.huila.clima": (
        "Templado de montaña del sur, café, frijol y frutales",
        "Temperate southern mountains: coffee, beans and fruit",
    ),
    "region.tolima.nombre": ("Tolima (valle del Magdalena)", "Tolima (Magdalena valley)"),
    "region.tolima.corto": ("Tolima", "Tolima"),
    "region.tolima.clima": (
        "Valle cálido y seco, arroz, maíz y algodón",
        "Warm, dry valley: rice, maize and cotton",
    ),
    "region.casanare.nombre": ("Casanare (llanos de Yopal)", "Casanare (Yopal plains)"),
    "region.casanare.corto": ("Casanare", "Casanare"),
    "region.casanare.clima": (
        "Llanos cálidos y de lluvias marcadas, arroz, palma y maíz",
        "Warm plains with a marked rainy season: rice, oil palm and maize",
    ),
}

MESES_CORTOS: dict[str, list[str]] = {
    "es": ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
}

MESES_ES_EN: dict[str, str] = {
    "Enero": "January", "Febrero": "February", "Marzo": "March", "Abril": "April",
    "Mayo": "May", "Junio": "June", "Julio": "July", "Agosto": "August",
    "Septiembre": "September", "Octubre": "October", "Noviembre": "November", "Diciembre": "December",
}

TEXTURAS_EN: dict[str, str] = {
    "arenoso": "sand",
    "arenoso franco": "loamy sand",
    "franco arenoso": "sandy loam",
    "franco": "loam",
    "franco limoso": "silt loam",
    "limoso": "silt",
    "franco arcillo arenoso": "sandy clay loam",
    "franco arcilloso": "clay loam",
    "franco arcillo limoso": "silty clay loam",
    "arcillo arenoso": "sandy clay",
    "arcillo limoso": "silty clay",
    "arcilloso": "clay",
}

"""Configuracion central del pipeline.

Un unico sitio donde viven rutas, parametros y supuestos numericos.
Todo parametro que afecte a un resultado esta aqui y sale citado en el Excel.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_REFERENCIA = RAIZ / "data" / "referencia"
DIR_RAW = RAIZ / "data" / "raw"
DIR_INTERIM = RAIZ / "data" / "interim"
DIR_PROCESSED = RAIZ / "data" / "processed"
DIR_REAL = RAIZ / "data" / "real"
DIR_OUTPUTS = RAIZ / "outputs"

F_DISTRITOS = DIR_REFERENCIA / "distritos_madrid.csv"
F_CORPUS = DIR_RAW / "anuncios.jsonl"
F_VERDAD = DIR_RAW / "verdad_terreno.csv"
F_EXTRAIDO = DIR_INTERIM / "extraido.csv"
F_NORMALIZADO = DIR_PROCESSED / "inmuebles.csv"
F_VALORADO = DIR_PROCESSED / "valoraciones.csv"
F_METRICAS = DIR_PROCESSED / "metricas.json"
F_EXCEL = DIR_OUTPUTS / "valoraciones_madrid.xlsx"
F_DASHBOARD = DIR_OUTPUTS / "dashboard.html"

# Salidas del circuito con datos REALES (idealista18). Son opcionales: el
# pipeline sintetico se ejecuta igual sin ellas, y el Excel se limita a omitir
# la hoja correspondiente. Se generan con r00 -> r01 -> r04.
F_METRICAS_REALES = DIR_REAL / "metricas_2018.json"
F_DIAGNOSTICO_REAL = DIR_REAL / "diagnostico_coeficientes_2018.json"

# --- Generacion del corpus sintetico -----------------------------------------
SEMILLA = 20260904
N_ANUNCIOS = 2000
FECHA_INICIO = "2025-09-01"   # ventana temporal simulada de captacion
FECHA_FIN = "2026-08-31"

# Factor de actualizacion de los precios de 2022 al nivel simulado de 2026.
# SUPUESTO DECLARADO. Derivado de la variacion del valor tasado de vivienda libre
# en Espana entre 4T2022 y 1T2026 segun el Ministerio de Vivienda y Agenda Urbana
# (~1.760 EUR/m2 -> 2.315 EUR/m2). Se aplica igual a los 21 distritos, lo cual es
# falso en la realidad: Madrid no se ha revalorizado de forma homogenea.
# No afecta a la logica de comparables, que es relativa dentro de cada distrito.
FACTOR_ACTUALIZACION = 1.32

# Sobreprecio/descuento medio asociado al estado de conservacion.
# SUPUESTO DECLARADO: no medido, son coeficientes plausibles de mercado usados
# para dar estructura al dato sintetico y como ajuste del motor de valoracion.
COEF_ESTADO = {
    "obra nueva": 1.18,
    "reformado": 1.10,
    "buen estado": 1.00,
    "a reformar": 0.82,
}
COEF_EXTERIOR = {True: 1.04, False: 0.94}
# Penalizacion de planta alta sin ascensor (planta >= 3)
COEF_SIN_ASCENSOR_ALTA = 0.90

# Proporcion de anuncios a los que se inyecta una desviacion deliberada de precio.
# Sirve para poder medir si el motor los recupera. Ver SUPUESTOS.md: esto es
# circular por construccion y NO demuestra capacidad predictiva en datos reales.
PROP_INFRAPRECIO = 0.08
PROP_SOBREPRECIO = 0.08
MAGNITUD_DESVIACION = (0.12, 0.28)   # rango del descuento/prima inyectado

RUIDO_LOG_SIGMA = 0.13   # dispersion idiosincratica del EUR/m2 dentro del distrito

# --- Motor de valoracion por comparables -------------------------------------
BANDA_SUPERFICIE = 0.20      # +/-20% de superficie para considerar comparable
VENTANA_DIAS = 270           # solo comparables publicados en los N dias ANTERIORES
MIN_COMPARABLES = 5          # por debajo de esto no se valora: "sin muestra suficiente"
UMBRAL_OPORTUNIDAD = -0.10   # desviacion <= -10% se marca como oportunidad

# --- Extraccion ---------------------------------------------------------------
# Haiku 4.5 va sobrado para extraer campos de un documento corto y cuesta
# 1 $/5 $ por millon de tokens (entrada/salida) frente a los 5 $/25 $ de Opus.
MODELO_LLM = "claude-haiku-4-5"

# Cuantos anuncios pasan por el LLM. El resto se extraen con reglas.
# 25 documentos bastan para demostrar el paso y cuestan del orden de 0,15 $.
# Pasar el corpus entero saldria por unos 9 $ (4,50 $ con la API de lotes),
# y no aporta nada a la demostracion.
MUESTRA_LLM = 25
CAMPOS = [
    "distrito", "superficie_m2", "habitaciones", "banos", "planta",
    "ascensor", "estado", "anio_construccion", "exterior", "precio_eur",
]

FUENTES = [
    ("Precio medio declarado y transacciones por distrito, Madrid 2022",
     "Ayuntamiento de Madrid, Anuario Estadistico 2023, cap. 8 (Colegio de Registradores)",
     "consultado 04/09/2026"),
    ("Valor tasado de vivienda libre, Espana, 4T2022 y 1T2026 (factor de actualizacion)",
     "Ministerio de Vivienda y Agenda Urbana, Estadistica de valor tasado de la vivienda",
     "consultado 04/09/2026"),
]

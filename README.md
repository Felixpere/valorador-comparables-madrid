# Valoración por comparables — mercado residencial de Madrid

De anuncios en texto libre a una lista priorizada de inmuebles cuyo precio se
aparta de lo que piden los pisos equivalentes de su distrito.

```
anuncios en texto libre  →  extracción con IA  →  limpieza en Python
                                                       ↓
                                    dashboard  ←  Excel / Power BI
```

Una sola orden reconstruye todo:

```bash
pip install -r requirements.txt
python run_pipeline.py
```

Salida en `outputs/`: `valoraciones_madrid.xlsx` y `dashboard.html`.
Diez segundos de principio a fin.

---

## Qué es esto

Una demostración técnica del circuito completo, montada sobre datos del mercado
residencial de Madrid. El motor de valoración es el mismo enfoque que
[car-flip-opportunity-detector](https://github.com/Felixpere/car-flip-opportunity-detector),
trasladado de coches a inmuebles: donde allí había modelo, año y kilómetros,
aquí hay distrito, superficie, año y estado.

**Qué no es**: un producto, ni una herramienta de tasación. Los anuncios son
sintéticos y las conclusiones sobre el mercado de Madrid no se sostienen sobre
ellos. Lo que sí se sostiene es la mecánica: la extracción, la limpieza, el
control de fugas de información y la trazabilidad. Los límites están todos
recogidos en [SUPUESTOS.md](SUPUESTOS.md), y también en el propio Excel y en el
dashboard, no escondidos en un anexo.

## Dos vías de datos

| Vía | Datos | Para qué |
|---|---|---|
| **Real** (`src/r00`–`src/r04`) | 94.815 anuncios de Madrid de 2018, `idealista18`, licencia ODbL | Motor por barrio y **validación fuera de muestra**. Error mediano del 12,0 % frente al 15,2 % de la línea base ingenua. Ver [docs/validacion_2018.md](docs/validacion_2018.md), la hoja `Validación 2018` del Excel y `outputs/dashboard_real.html` |
| **Sintética** (`src/p00`–`p06`) | Corpus generado, calibrado con estadística registral | Demostrar el paso de **extracción con IA**, que no se puede enseñar con datos que ya vienen en tabla |

Los datos reales son de 2018: sirven para estructura de mercado y para validar el
motor, no para hablar del nivel de precios de hoy.

## Por qué el corpus de extracción es sintético

Los términos de uso de los portales inmobiliarios prohíben el scraping. No hay
dataset público de anuncios de Madrid con licencia de uso libre. Así que el
corpus se genera, y se calibra con estadística pública real:

| Dato | Fuente | Ejercicio |
|---|---|---|
| Precio medio declarado en escritura por distrito (€/m²) | Colegio de Registradores, vía Ayuntamiento de Madrid, Anuario Estadístico 2023, cap. 8 | 2022 |
| Distribución de superficies y volumen de transacciones por distrito | misma fuente | 2022 |
| Factor de actualización a nivel 2026 | Ministerio de Vivienda y Agenda Urbana, valor tasado de vivienda libre | 4T2022 → 1T2026 |

Ambas consultadas el 04/09/2026. La tabla vive en
`data/referencia/distritos_madrid.csv`, con su procedencia en la cabecera.

El catálogo completo de fuentes públicas usables para análisis inmobiliario en
España —qué da cada una, con qué granularidad, cada cuánto se actualiza y qué se
puede y no se puede hacer con ella— está en
[docs/investigacion_fuentes.md](docs/investigacion_fuentes.md).

Ningún dato personal de vendedores ni de terceros interviene en ninguna fase.

## Los seis pasos

| Paso | Archivo | Qué hace |
|---|---|---|
| 00 | `src/p00_generar_corpus.py` | Genera 2.000 anuncios en cinco formatos de redacción distintos, calibrados por distrito. Guarda aparte la verdad de terreno, que sólo se usa para medir. |
| 01 | `src/p01_extraer.py` | Texto libre → JSON con esquema fijo. Dos motores intercambiables: modelo de lenguaje o expresiones regulares. |
| 02 | `src/p02_normalizar.py` | Tipado, unificación de distritos, rangos plausibles, duplicados. Ninguna fila se descarta en silencio. |
| 03 | `src/p03_valorar.py` | Motor de comparables con control de fugas de información. |
| 04 | `src/p04_evaluar.py` | Mide la extracción y el motor contra la verdad de terreno. |
| 05-06 | `src/p05_exportar_excel.py`, `src/p06_dashboard.py` | Excel con fórmulas y dashboard autocontenido. |

## El circuito con datos reales

| Paso | Archivo | Qué hace |
|---|---|---|
| R00 | `src/r00_cargar_idealista18.py` | Descarga `idealista18` y asigna barrio por punto en polígono. |
| R01 | `src/r01_valorar_real.py` | Parte pool y evaluación, estima los coeficientes y valida fuera de muestra. |
| R02 | `src/r02_caso.py` | Reconstruye una valoración concreta paso a paso. |
| R03 | `src/r03_dashboard_real.py` | Dashboard de los resultados reales. |
| R04 | `src/r04_diagnostico_coeficientes.py` | Errores estándar, VIF, correlaciones, efecto del centrado y regresión secuencial de los coeficientes que estaban en cuarentena. |

## Extracción: dos motores, y quién extrajo qué

```bash
python run_pipeline.py --motor reglas          # determinista, sin red, gratis
python run_pipeline.py --motor llm             # Claude Haiku 4.5 sobre la muestra
python run_pipeline.py --motor llm --muestra-llm 100
python run_pipeline.py                         # auto: LLM si hay clave, reglas si no
```

Por defecto el modo con LLM procesa **25 anuncios con el modelo y los 1.975
restantes con reglas**. Es deliberado: veinticinco documentos bastan para
demostrar el paso y cuestan del orden de 0,15 $ con Haiku 4.5. Pasar el corpus
entero saldría por unos 9 $ (4,50 $ con la API de lotes) y no añadiría nada a la
demostración.

Esa mezcla no se esconde. Cada fila lleva su columna `motor_extraccion` hasta el
Excel, y `data/processed/metricas.json` reporta la exactitud **por separado para
cada motor**, nunca mezclada en una sola cifra.

Sobre el resultado del motor de reglas hay que ser claro: acierta el 98 % de los
campos **porque las expresiones regulares se escribieron contra estas cinco
plantillas**. Es exactamente el sesgo que rompe estos sistemas en producción: el
día que entra una plantilla nueva, se cae. El modelo de lenguaje no tiene esa
ventaja. Comparar ambos motores sobre el mismo corpus es la forma honesta de ver
la diferencia.

## Fugas de información

Es el error que arruina en silencio este tipo de modelos: el resultado sale
excelente porque el modelo está mirando datos que en la vida real no tendría.
Aquí se bloquea en tres sitios:

1. El inmueble evaluado se excluye por referencia de su propio conjunto de comparables.
2. El filtro temporal es estricto: nada del mismo día ni posterior.
3. Los coeficientes de ajuste por estado, orientación y ascensor se reestiman cada
   mes usando sólo meses anteriores. El primer tramo no se valora, porque no hay
   histórico.

No basta con escribirlo. Hay tests que lo comprueban, incluido uno que verifica
que añadir anuncios posteriores no altera ni una valoración ya emitida. Y el
paso 04 vuelve a comprobarlo sobre la salida real: si detecta una sola fuga, el
proceso termina en error y no publica nada.

```bash
python -m pytest tests -q      # 25 tests
```

## Automatización

`.github/workflows/pipeline.yml` ejecuta el proceso cada lunes, en cada push y a
demanda. Si un test falla o salta el control de fugas, la ejecución se marca en
rojo y el Excel no se publica: prefiere no entregar nada antes que entregar un
número que no se sostiene.

## Cómo regenerar los entregables

El orden importa, y hay una forma de hacerlo mal que no da ningún error:

```bash
python src/r01_valorar_real.py              # validación contra datos reales
python src/r04_diagnostico_coeficientes.py  # diagnóstico de coeficientes
python src/r02_caso.py                      # el caso trazado paso a paso
python src/r03_dashboard_real.py            # -> outputs/dashboard_real.html
python run_pipeline.py --motor llm          # -> Excel y outputs/dashboard.html
```

`src/r03` **no** forma parte de `run_pipeline.py`: va suelto y necesita que
`r01`, `r02` y `r04` hayan corrido antes, porque lee los tres JSON que dejan en
`data/real/`. Si falta el de `r04`, se detiene indicando qué ejecutar.

**`--motor llm` no es opcional.** Sin esa opción, o sin `ANTHROPIC_API_KEY` en el
entorno, el pipeline cae al motor de reglas y **degrada el entregable en
silencio**: el Excel pierde la comparación entre los dos motores de extracción y
la hoja Resumen vuelve a decir sólo «reglas». El proceso termina en 0 y no avisa.

Los tres ficheros terminados se copian a `entregables/`, que es una foto fija y
no se actualiza sola. Ver `entregables/LEEME.md`.

Para saber si algo quedó desfasado: los dos HTML son deterministas, así que si
regeneras y cambian, estaban viejos. El Excel no sirve para eso, porque
`openpyxl` le escribe la hora de creación en cada escritura y cambia siempre.

## Power BI

La hoja `Valoraciones` es una tabla plana sin celdas combinadas ni encabezados a
dos alturas, pensada para cargarse sin transformaciones. La hoja
`Validación 2018` lleva la validación contra `idealista18` en seis tablas con
nombre, cargables sueltas. Ver [docs/power_bi.md](docs/power_bi.md). Las hojas de
resumen usan fórmulas de Excel, no valores pegados desde Python: si alguien filtra
o corrige un dato, los totales se mueven solos.

## Para retomar el trabajo

`CLAUDE.md` tiene las reglas del proyecto y `docs/ESTADO.md` dice qué está hecho,
qué falta y por qué se decidió cada cosa.

## Estructura

```
data/referencia/   tabla oficial por distrito, con su fuente en la cabecera
data/raw/          corpus de anuncios y verdad de terreno
data/interim/      salida cruda de la extracción
data/processed/    dato limpio, valoraciones, informe de calidad, métricas
outputs/           Excel y dashboard
src/               los seis pasos del circuito sintético (p00–p06) y el real (r00–r04)
tests/             54 tests
docs/              validación con datos reales, investigación de fuentes, estado, guion
```

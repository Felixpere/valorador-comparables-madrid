# Valorador por comparables · Madrid

Los datos de inmuebles llegan como documento suelto y alguien los pasa a mano a
una hoja de cálculo, sin rastro de cómo se llegó a cada número. Este circuito lo
hace solo: extracción con IA, limpieza, valoración por comparables, Excel y panel.

**Validado fuera de muestra con 22.643 anuncios reales de Madrid que el motor no
había visto: error mediano del 12,0 %, frente al 15,2 % de la mediana del barrio.**
Sobre precio de anuncio, no de cierre (idealista18, 2018).

**Sin instalar nada:**
[validación con datos reales](https://felixpere.github.io/valorador-comparables-madrid/entregables/dashboard_real.html)
· [circuito de extracción](https://felixpere.github.io/valorador-comparables-madrid/entregables/dashboard.html)
· [resumen en una página (PDF)](https://felixpere.github.io/valorador-comparables-madrid/entregables/one_pager_valoracion_comparables_v2.pdf)

---

El recorrido:

```
documento en texto libre  →  extracción con IA  →  limpieza en Python
                                                       ↓
                                    dashboard  ←  Excel / Power BI
```

Una sola orden reconstruye todo:

```bash
pip install -r requirements.txt
python run_pipeline.py
```

Salida en `outputs/`: `valoraciones_madrid.xlsx` y `dashboard.html`. Diez
segundos de principio a fin. Y también se ejecuta **solo**: cada lunes y en cada
cambio del código, mediante GitHub Actions.

Lo que lo distingue de un proceso montado a mano es qué hace cuando algo va mal:
**si el control de fugas detecta un solo comparable que el motor no debería haber
visto, se detiene y no publica nada.**

---

## Por qué el ejemplo es vivienda

Un circuito así no se demuestra en abstracto: hacen falta datos reales contra los
que medir si acierta.

Por eso el ejemplo es la **valoración de pisos por comparables**. En vivienda
existe el único conjunto de datos abierto, con licencia libre y detalle inmueble
a inmueble, que cubre un mercado entero: 94.815 anuncios de Madrid publicados por
idealista junto a dos universidades. En oficinas o logística ese dato no existe
en abierto —lo publican las consultoras en informes en PDF, cada una con su
definición—, así que allí no habría contra qué medir el acierto. Ese mapa está en
[docs/investigacion_terciario.md](docs/investigacion_terciario.md).

Vivienda es el sector donde **se puede demostrar que el circuito acierta**. Lo que
queda demostrado es el método, no el mercado.

## Qué es esto

Una demostración técnica del circuito completo, montada sobre el mercado
residencial de Madrid. El motor de valoración es el mismo enfoque que
[car-flip-opportunity-detector](https://github.com/Felixpere/car-flip-opportunity-detector),
trasladado de coches a inmuebles: donde allí había modelo, año y kilómetros,
aquí hay barrio, superficie, año y estado.

**Qué no es**: un producto, ni una herramienta de tasación. El corpus con el que
se demuestra la extracción es sintético, y sobre él no se sostiene ninguna
conclusión de mercado. Lo que sí se sostiene, porque está medido contra 22.643
anuncios reales que el motor no había visto, es la mecánica: la extracción, la
limpieza, el control de fugas de información y la trazabilidad. Los límites están
todos recogidos en [SUPUESTOS.md](SUPUESTOS.md), y también en el propio Excel y
en el dashboard, no escondidos en un anexo.

Si prefiere el recorrido completo sin tecnicismos, está en
[docs/recorrido_del_proyecto.md](docs/recorrido_del_proyecto.md).

## Dos vías de datos

| Vía | Datos | Para qué |
|---|---|---|
| **Real** (`src/r00`–`src/r04`) | 94.815 anuncios de Madrid de 2018, `idealista18`, licencia ODbL | Motor por barrio y **validación fuera de muestra**. Error mediano del 12,0 % frente al 15,2 % de la línea base simple. Ver [docs/validacion_2018.md](docs/validacion_2018.md), la hoja `Validación 2018` del Excel y `outputs/dashboard_real.html` |
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

Para **oficinas y logística** el terreno es distinto: no hay capa pública de
rentas ni de disponibilidad, el dato lo publican las consultoras en PDF y las
cifras no coinciden entre fuentes. Ese mapa está en
[docs/investigacion_terciario.md](docs/investigacion_terciario.md), con cada
cifra marcada según sea de fuente primaria o de segunda mano.

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
demostrar el paso, y pasar el corpus entero serían ochenta veces más llamadas sin
añadir nada a la demostración.

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
python -m pytest tests -q      # 69 tests
```

## Automatización

`.github/workflows/pipeline.yml` ejecuta el proceso cada lunes, en cada push y a
demanda. Si un test falla o salta el control de fugas, la ejecución se marca en
rojo y el Excel no se publica: prefiere no entregar nada antes que entregar un
número que no se sostiene.

Las ejecuciones de Actions, la programada de cada lunes y las de cada push, usan
el extractor de reglas. La extracción con modelo de lenguaje necesita
`ANTHROPIC_API_KEY` y se ejecuta bajo demanda, en local, con
`python run_pipeline.py --motor llm`: la clave no está en los secretos del
repositorio, para no tener un gasto recurrente. Por eso cada ejecución de
Actions sale marcada como «entregable incompleto», y el aviso es correcto: ese
entregable no lleva el resultado del modelo. El panel publicado en
`entregables/` sí se generó con `--motor llm` (25 anuncios por el modelo y
1.975 por reglas).

## Cómo regenerar los entregables

El orden importa, y hay una forma de hacerlo mal que no da error, sólo un aviso:

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

**El entregable completo necesita `--motor llm`.** Sin esa opción, o sin
`ANTHROPIC_API_KEY` en el entorno, la extracción va sólo por reglas. Es un modo
válido, pero el Excel sale sin la comparación entre los dos motores, y el
pipeline no lo esconde: avisa por consola al arrancar y al terminar (en GitHub
Actions, además, como *warning*), y lo deja escrito en `metricas.json`
(`entregable.estado`: `completo`, `parcial` o `solo_reglas`) y en la primera
línea de la hoja Resumen. Termina en 0 porque el resultado por reglas es
correcto; lo que ya no puede es pasar por completo.

Los dos HTML terminados se copian a `entregables/`, que es una foto fija y no se
actualiza sola. El Excel no: se queda en `outputs/`, y el `.pbix` ya lleva sus
datos dentro. Ver `entregables/LEEME.md`.

Para saber si algo quedó desfasado: `dashboard_real.html` es determinista, así
que si lo regeneras y cambia, estaba viejo. Los otros dos no sirven para eso:
`dashboard.html` lleva impresa la fecha y hora de ejecución, y el Excel también,
porque `openpyxl` le escribe la hora de creación en cada escritura.

## Power BI

**El modelo está montado y viaja en el repositorio**: `valorador_madrid.pbix`.
Una página con filtros por distrito, estado, fiabilidad y fecha; los cuatro
indicadores de cabecera; €/m² por distrito; la distribución de la desviación; la
tabla de mayor desviación a la baja **con su número de comparables a la vista**, y
el desglose de por qué un inmueble no se valora. Lleva además un panel de límites:
corpus sintético calibrado con estadística registral de 2022, precio pedido y no
de cierre, que el panel demuestra el circuito y no mide precisión, que la
precisión se valida aparte con `idealista18` (12,0 % de error mediano) y que la
fiabilidad no discrimina en este corpus.

**Corre sobre el corpus sintético, no sobre `idealista18`**: carga la hoja
`Valoraciones` del Excel, los 1.996 anuncios aptos de los 2.000 que se generan.
Por eso sus cifras (75,5 % con valoración) no son las del panel de datos reales
(22.643 anuncios, 96,1 %). El 12,0 % de su panel de límites es de la vía real,
citado como contexto.

La hoja `Valoraciones` es una tabla plana sin celdas combinadas ni encabezados a
dos alturas, pensada para cargarse sin transformaciones. La hoja
`Validación 2018` lleva la validación contra `idealista18` en seis tablas con
nombre, cargables sueltas. Ver [docs/power_bi.md](docs/power_bi.md). Los
indicadores de la hoja Resumen y los totales de la hoja Por distrito son fórmulas
de Excel sobre la hoja Valoraciones: si alguien corrige un dato, se mueven solos.
Las métricas de calidad del proceso y la comparación entre motores, en cambio,
son valores calculados en Python y escritos tal cual.

## Para retomar el trabajo

`CLAUDE.md` tiene las reglas del proyecto y `docs/ESTADO.md` dice qué está hecho,
qué falta y por qué se decidió cada cosa.

## Estructura

```
data/referencia/   tabla oficial por distrito, con su fuente en la cabecera
data/raw/          corpus de anuncios y verdad de terreno
data/interim/      salida cruda de la extracción
data/processed/    dato limpio, valoraciones, informe de calidad, métricas
valorador_madrid.pbix  modelo de Power BI sobre la hoja Valoraciones
outputs/           Excel y dashboard
src/               los seis pasos del circuito sintético (p00–p06) y el real (r00–r04)
tests/             69 tests
docs/              recorrido para negocio, validación con datos reales, fuentes
                   (residencial y terciario), estado del proyecto
```

# Estado del proyecto

Última actualización: **7 de septiembre de 2026** (investigación de terciario incorporada; titular del dashboard corregido).

El trabajo de código y los cuatro commits son del **5 de septiembre**, verificado
contra el historial de git. La investigación de terciario se hizo el **6 y 7**.

**El proyecto vive ahora en `C:\Users\user\proyectos\valorador-comparables-madrid`.**
Antes estaba en Descargas, con una carpeta anidada dentro de otra del mismo
nombre, y eso hacía abrir ficheros equivocados. Los duplicados sueltos están
borrados, incluido un `dashboard_real_corregido.html` editado a mano que llevaba
una cifra mal. **Lo que no sale del código no es de fiar.**

Este fichero es el traspaso entre sesiones y entre herramientas. El contexto no
viaja: lo que no esté aquí escrito, se pierde. **Actualízalo al cerrar cada
sesión.**

---

## Dónde estamos

El circuito completo funciona de punta a punta. `python run_pipeline.py` tarda
unos diez segundos y produce el Excel y el dashboard. 54 tests en verde.

| Pieza | Estado |
|---|---|
| Generación del corpus sintético calibrado por distrito | terminado |
| Extracción LLM + reglas, con reparto declarado por fila | terminado, **pasada real con Haiku hecha el 5 sept** |
| Limpieza, validación e informe de calidad | terminado |
| Motor de comparables con control de fugas | terminado |
| Métricas y barrido de umbrales | terminado |
| Excel de siete hojas con fórmulas | terminado |
| Copia de los entregables en `entregables/` | terminado (5 sept), con su `LEEME.md` |
| Dashboard HTML autocontenido | terminado |
| Tests y workflow de GitHub Actions | terminado |
| Investigación de fuentes públicas (residencial) | terminado (`docs/investigacion_fuentes.md`) |
| Investigación de fuentes en terciario (oficinas y logística) | terminado 6-7 sept (`docs/investigacion_terciario.md`) |
| Carga de datos reales (idealista18, 94.815 anuncios) | terminado |
| Validación fuera de muestra con línea base | terminado (`docs/validacion_2018.md`) |
| Granularidad de barrio en el motor real (135 barrios) | terminado |
| Caso trazado paso a paso (`src/r02`) | terminado |
| Dashboard de datos reales (`src/r03`) | terminado |
| Verificación de los dos coeficientes en cuarentena (`src/r04`) | terminado, sospecha descartada por tres vías |
| Resultados reales en el Excel (hoja `Validación 2018`) | terminado |
| Tests del circuito real (`tests/test_valoracion_real.py`) | terminado |
| Dashboard sin cifras escritas a mano, con test que lo vigila | terminado (5 sept) |
| Pasada real con Haiku sobre los 25 anuncios | terminado (5 sept). Sobre los **mismos** 25 anuncios: LLM 100,0 %, reglas 99,6 %. **Un fallo de 250 no distingue a ningún motor**, y las reglas juegan en casa |
| Granularidad de barrio en el motor sintético | pendiente, ya no prioritario |
| Línea base del valor de referencia del Catastro | **pendiente** |
| Modelo de Power BI (.pbix) | **pendiente**, siguiendo `docs/power_bi.md` |

## Cifras con DATOS REALES (idealista18, Madrid 2018)

Fuera de muestra, 22.643 anuncios que el motor no había visto.

- Motor de comparables por barrio: **error mediano 12,0 %**, 43,0 % dentro de
  ±10 %, sesgo −0,1 %. Cobertura 96,1 %
- Línea base mediana del barrio: 15,2 %. Mediana de la ciudad: 34,3 %
- La etiqueta de fiabilidad **sí discrimina** con datos reales: 10,4 % / 12,7 % /
  15,9 %. Con el corpus sintético no lo hacía, y la explicación que dimos era
  correcta
- Del barrio más caro (Recoletos, 7.440 €/m²) al más barato (San Cristóbal,
  1.169 €/m²) hay un factor 6,4

**No se pueden comparar con las cifras sintéticas de abajo**: objetivos distintos
medidos sobre datos distintos.

### Los dos coeficientes en cuarentena, ya verificados (5 sept)

Estaban escritos como anomalía con la sospecha de colinealidad con barrio y
superficie. **La sospecha era falsa por tres vías independientes.** Verificado con
`python src/r04_diagnostico_coeficientes.py`, que deja
`data/real/diagnostico_coeficientes_2018.json`.

1. **VIF y correlaciones.** El VIF más alto de todo el modelo es 2,30 (jardín
   1,92). La correlación más fuerte entre regresores es jardín-piscina, 0,665, y
   ninguna pareja llega a 0,7. Correlacionadas sí, colineales no.
2. **Quitar el centrado por barrio-trimestre.** Es el contraste directo de la
   sospecha, porque el modelo ya centra. Sin centrar, el jardín se va a **−8,5 %**
   en vez de −1,4 %, y la calidad a +13,0 % en vez de +1,4 %. O sea que la zona
   empujaba hacia abajo y el centrado ya la quita: si el barrio fuera la causa,
   quitar el centrado tendría que empeorar el signo, no arreglarlo.
3. **Controlar por superficie** deja el jardín *más* positivo (+12,6 % frente a
   +10,1 %), otra vez lo contrario de lo que decía la sospecha.

- **Calidad catastral: no era una anomalía, era la variable leída al revés.**
  `CADASTRALQUALITYID` no es una nota de calidad, es la categoría catastral, y
  empeora según crece el número. El €/m² mediano cae sin excepciones del código 0
  al 7 (97,7 % del pool), de 5.995 € a 2.114 €. Sobre el código original el signo
  negativo era el correcto. `r01` ahora **invierte** la variable y el coeficiente
  sale en **+1,4 %**.
  - Que la inversión no mueve ninguna valoración es **demostrable, no empírico**:
    sustituir `v` por `9 − v` deja el espacio de columnas intacto, así que
    `β' = −β` y el intercepto absorbe `9β`; como el factor excluye el intercepto,
    el cambio es una constante global que se cancela exactamente al dividir cada
    comparable por su propio factor. El test sigue como guardia, no como prueba.
  - Ojo al presentarlo: la tabla del gradiente fija **el sentido, no la magnitud**.
    La caída cruda es −13,8 % por grado; el coeficiente centrado, +1,4 %. No se
    contradicen: en la tabla no se ha descontado el barrio.
- **Jardín: se queda en −1,4 %, y hay que contarlo en dos niveles.**
  - *Probado*: no es barrio, ni superficie, ni colinealidad. Efecto parcial real,
    distinguible de cero (t = −3,9, IC 95 % de −2,1 % a −0,7 %).
  - *Interpretado, no medido*: que «jardín y nada más» marque promoción periférica
    encaja con el cruce (2.794 €/m² con jardín y sin piscina, frente a 3.407 € sin
    ninguna de las dos) y con que el 64,2 % de los anuncios con jardín lleven
    piscina, pero **no hay variable que separe jardín privado de zona común**. Es
    una lectura del patrón. No se presenta como hallazgo.

Lo detallado, con sus tablas, en `docs/validacion_2018.md`.

### El dashboard ya no tiene cifras escritas a mano (5 sept)

Se encontraron cuatro fallos en `outputs/dashboard_real.html` que eran **el mismo
fallo**: cifras tecleadas en la prosa en vez de leídas del JSON. Todas eran
correctas el día que se escribieron; el problema es que no se recalculaban, así
que el HTML se desincronizaba en silencio al cambiar los datos.

Corregido en `src/r03_dashboard_real.py`: **toda** cifra publicada sale ahora de
`metricas_2018.json`, `caso_trazado.json` o `diagnostico_coeficientes_2018.json`.
Lo vigila `tests/test_dashboard_real.py`, que ancla cada cifra a su sitio en el
texto y la compara con el JSON. Comprobado por mutación: reintroducir las cuatro
cifras a mano hace fallar el test con los cuatro nombres.

Efectos secundarios que hubo que arreglar por el camino:

- `r01` publica ahora `n_anuncios_origen`, `n_identificadores_unicos`,
  `n_barrios` y `error_por_n_comparables`. Los tres primeros los citaba el
  dashboard sin tenerlos en ningún sitio; el cuarto sostiene la frase de que lo
  que discrimina es la dispersión y no el número de comparables.
- `r02` guarda la mediana ajustada con **dos decimales**. Iba redondeada a entero
  y la ecuación publicada no cuadraba: 5.162 × 73 son 376.826, no los 376.817
  que se publicaban. El resultado era correcto y la ecuación, falsa.
- `_n()` usa **redondeo comercial** en vez del redondeo al par de Python. Era la
  causa de que Castellana saliera 6.522 en el dashboard y 6.523 en la
  documentación: misma cifra, dos valores, ninguno de los dos mal.
- El pie del histograma estaba en y=186 dentro de un `viewBox` de alto 184 y se
  recortaba. Ahora el alto se calcula contando el margen superior: 194.

### La pasada con Haiku, por fin ejecutada (5 sept)

25 anuncios por `claude-haiku-4-5`, los 1.975 restantes por reglas. Reproducible
con `python run_pipeline.py --motor llm`.

**Los dos motores sobre los MISMOS 25 anuncios** (250 observaciones cada uno:
25 anuncios × 10 campos). Es la única comparación que compara:

| Motor | Campos correctos | Anuncios sin errores | Campos fallados |
|---|---|---|---|
| `llm:claude-haiku-4-5` | **100,0 %** | 100,0 % | 0 de 250 |
| reglas | 99,6 % | 96,0 % | 1 de 250 |

**Cada motor sobre los anuncios que le tocaron.** Estas dos cifras **no se pueden
enfrentar entre sí**, porque salen de conjuntos distintos, y se dan sólo para no
esconderlas:

| Motor | Anuncios | Campos correctos |
|---|---|---|
| `llm:claude-haiku-4-5` | 25 | 100,0 % |
| reglas | 1.975 | 98,0 % |

**Lo que NO se puede concluir de aquí, y es lo importante:**

1. **Un fallo de diferencia no distingue a nadie.** Con 250 observaciones por
   motor, 0 fallos frente a 1 está muy dentro del ruido. La comparación no tiene
   potencia para responder la pregunta, y decir «el LLM gana» sería inventarse un
   resultado.
2. **Las reglas juegan en casa.** Sus regex se escribieron mirando estas mismas
   cinco plantillas. Ese 99,6 % es sobreajuste de manual y no sobrevive a un
   formato nuevo, que es justo donde el LLM no necesita que nadie toque el código.
   El corpus, además, es sintético y regular; el texto real es más sucio.
3. **La comparación se hizo con el medidor mal, y se corrigió.** Ver abajo.

**Corrección declarada, y me favorece, así que conviene decirlo alto.** En la
primera medición el LLM salía en 99,2 % con dos fallos de `distrito`. Al mirarlos
eran **sólo tildes**: escribió «Tetuán» y «Chamartín», y la verdad de terreno usa
la forma sin tilde. Pero `p02._canon_distrito` quita los diacríticos, así que para
todo lo que viene después son **el mismo dato**: no era un error de extracción.

`p04._iguales` comparaba en minúsculas pero sin normalizar acentos, es decir con
un criterio **más estricto que el del propio pipeline**. Eso penalizaba
sistemáticamente a cualquier motor que escriba español natural y premiaba al que
emite formas canónicas de una lista, o sea a las reglas, por un motivo que no
tiene nada que ver con extraer bien. Corregido: `_iguales` normaliza acentos igual
que `p02`. El LLM pasa de 99,2 % a 100,0 %; las reglas no se mueven.

**Dónde falló cada uno**: el único fallo de las reglas es `anio_construccion`
(96,0 %, 1 de 25). El LLM no falla ninguno.

## Cifras del corpus sintético

Medidas sobre corpus sintético con verdad de terreno conocida. No son medidas de
rendimiento sobre anuncios reales.

- 2.000 anuncios generados, 1.996 aptos para valorar
- Cobertura del motor: 75,5 %. El 24,5 % restante no se valora, y se distingue
  entre "ventana inicial sin histórico" y "segmento con pocas operaciones"
- Error mediano de valoración: 10,0 %
- Correlación entre desviación estimada e inyectada: 0,46
- Umbral −10 %: 391 marcados, 23,8 % de precisión, 81,6 % de cobertura
- Extracción por reglas: 98,0 % de campos correctos
- Control de fugas: limpio (0 autoinclusiones, 0 comparables futuros)

## Cómo regenerar los entregables, y la trampa que tiene

**El orden importa y hay una forma de hacerlo mal que no da ningún error.**

```bash
python src/r01_valorar_real.py              # valida contra los datos reales
python src/r04_diagnostico_coeficientes.py  # diagnóstico de coeficientes
python src/r02_caso.py                      # el caso trazado
python src/r03_dashboard_real.py            # dashboard_real.html
python run_pipeline.py --motor llm          # Excel + dashboard.html
```

**`r03` no va dentro de `run_pipeline.py`.** Es un script suelto y necesita que
`r01`, `r02` y `r04` se hayan ejecutado antes, porque lee los tres JSON que
dejan. Si falta el de `r04`, se para con un mensaje que dice qué ejecutar.

**La trampa: `--motor llm` no es opcional.** Si se lanza `run_pipeline.py` a
secas, o con la clave fuera del entorno, el pipeline cae al motor de reglas **sin
avisar de que eso degrada el entregable**: el Excel pierde la tabla de
comparación entre motores y la hoja Resumen vuelve a decir sólo «reglas». El
proceso termina en 0 y todo parece correcto. Requiere `ANTHROPIC_API_KEY`.

Después hay que copiar los tres ficheros a `entregables/`, que es una foto y no
se actualiza sola. Ver `entregables/LEEME.md`.

**Cómo saber si algo está desfasado**: los dos HTML son deterministas, así que si
regeneras y cambian, es que estaban viejos. El Excel **no** sirve para eso:
`openpyxl` le estampa la hora de creación en cada escritura y cambia siempre,
aunque los datos sean idénticos.

## Decisiones tomadas y por qué

- **Datos sintéticos**: los portales prohíben el scraping y no hay dataset
  público de anuncios de Madrid con licencia libre. Calibrados con la Estadística
  Registral Inmobiliaria de 2022 por distrito.
- **Factor de actualización 1,32** de 2022 a nivel 2026, uniforme en los 21
  distritos. Es un supuesto fuerte y declarado; no contamina la señal porque la
  comparación es relativa dentro de cada distrito.
- **Coeficientes de ajuste estimados de los datos**, no fijados a mano, y
  reestimados cada mes sólo con meses anteriores.
- **Extracción híbrida**: 25 anuncios por Claude Haiku 4.5 y el resto por reglas.
  25 documentos bastan para demostrar el paso y cuestan del orden de 0,15 $. El
  corpus entero saldría por unos 9 $ y no añadiría nada. La exactitud se reporta
  **por separado para cada motor**, nunca mezclada.
- **Dashboard en HTML además del Power BI**: respaldo por si el .pbix da
  problemas, y permite sacar capturas.

## Cosas que hay que contar tal cual, no esconder

1. El extractor por reglas acierta el 98 % **porque las regex se escribieron
   mirando estas cinco plantillas**. Sobreajuste de manual. Y cuando por fin se
   comparó contra Haiku sobre los mismos 25 anuncios, la diferencia fue de **un
   solo campo de 250**: no hay resultado que presumir en ninguna de las dos
   direcciones, y presentarlo como que un motor gana sería inventarse una
   conclusión que los datos no sostienen.
2. La etiqueta de fiabilidad **no discrimina** en este corpus: mismo error en los
   tres niveles, porque la dispersión del generador es homogénea. Se podría haber
   retocado el generador para que la métrica quedara bien. No se hizo.
3. Las desviaciones que el motor recupera fueron inyectadas al generar los datos.
4. El identificador de `idealista18` **no enlaza entre trimestres** en la versión
   publicada, aunque la documentación del paquete diga lo contrario. Eso descarta
   la validación longitudinal (¿se vende antes lo que está barato?). Se detectó
   porque una tabla de transiciones daba 0,0 % en las tres celdas.
5. Uno de los dos «coeficientes raros» **no era un hallazgo, era un error de
   lectura del dato**: la calidad catastral estaba interpretada al revés. Se
   contó, se verificó y se corrigió. Esa es la razón de tenerlos en cuarentena en
   vez de en la presentación, y merece contarse así: el proceso funcionó.
6. **La pasada con `--motor llm` NO es reproducible byte a byte, y es la única
   excepción a la regla 8 del proyecto.** Todo lo demás tiene semilla fija y da
   exactamente el mismo resultado siempre. Haiku no: puede extraer distinto entre
   dos ejecuciones sobre los mismos 25 anuncios, y como la exactitud por campo y
   por formato se calcula sobre los 2.000, un solo campo distinto mueve los
   decimales. Comprobado: `anio_construccion` pasó de 0,8145 a 0,8150 y el
   formato `ficha` de 0,9000 a 0,9003 entre dos ejecuciones idénticas.

   No es un fallo, es la naturaleza del motor, pero **hay que declararlo** en vez
   de dar a entender que el circuito entero es determinista. Por eso cada fila
   guarda en `motor_extraccion` quién la extrajo, y esa columna viaja hasta el
   Excel: ante cualquier cifra se puede saber qué parte viene de un motor
   determinista y qué parte de uno que no lo es. Si dos ejecuciones dan números
   ligeramente distintos, se mira esa columna antes de buscar un error.

   El resto del circuito sí es reproducible: `run_pipeline.py` sin `--motor llm`,
   y todo el circuito real (`r00`–`r04`), dan siempre lo mismo.
7. **Los códigos catastrales 8 y 9 siguen sin resolver, y la recodificación puede
   estar colocándolos mal.** Repuntan en precio en vez de seguir bajando, y la
   inversión `9 − v` les asigna la calidad más baja de la escala justo a los que
   se pagan más caros que el código 7. Si no significan «peor calidad» sino otra
   cosa (marcador de desconocido, escala distinta), están al revés. Son 1.201
   anuncios de 52.833, el 2,3 %: no cambia nada material, pero no se da por
   resuelto y no se dice que lo esté.

---

## Cola de trabajo

### (a) Prioridad alta — **cerrada el 5 de septiembre**

1. ~~Llevar los resultados reales al Excel.~~ **Hecho.** Hoja `Validación 2018`
   en `outputs/valoraciones_madrid.xlsx`, con seis tablas con nombre (`tblReal*`)
   que Power BI carga sueltas y sin transformar. Sale del libro sólo si
   `data/real/metricas_2018.json` existe, así que la integración continua, que no
   tiene los datos reales, sigue generando el Excel con una hoja menos.
   Documentada en `docs/power_bi.md`.
2. ~~Verificar los dos coeficientes anómalos.~~ **Hecho**, y la sospecha que
   había anotada era falsa. Ver «Los dos coeficientes en cuarentena» más arriba y
   `src/r04_diagnostico_coeficientes.py`.

**Pendiente que sale de aquí**: la única línea de la cola (a) que sigue viva es la
**línea base del valor de referencia del Catastro**, que ya estaba en la tabla de
estado y no en esta lista.

### (b) Prioridad media — cierra lo prometido

3. ~~Pasada real con Haiku sobre los 25 anuncios.~~ **Hecha el 5 de septiembre.**
   Resultados y salvedades en «La pasada con Haiku» más arriba. Resumen: con 250
   observaciones por motor la diferencia es de un campo, así que **no distingue**,
   y las reglas juegan en casa. Publicado por separado, nunca mezclado.

4. **Modelo de Power BI (.pbix)** siguiendo `docs/power_bi.md`. El dashboard
   HTML existe precisamente como respaldo, así que esto no bloquea nada.

### (c) Si sobra tiempo

5. Cruzar renta por sección censal (INE ADRH) y renta de alquiler (SERPAVI) para
   calcular rentabilidad bruta por zona.
6. Tabla de desfase temporal de cada fuente: qué se puede saber y con cuánto
   retraso.
7. Validación retrospectiva: entrenar hasta una fecha y comprobar contra lo
   posterior.

**Regla de corte**: lo que no esté listo se documenta aquí como siguiente
iteración y se dice en voz alta. Un pendiente declarado suma; uno oculto resta.

---

## Mapa rápido del repo

```
CLAUDE.md                    reglas permanentes, leer primero
README.md                    qué es, cómo se ejecuta
SUPUESTOS.md                 límites de lo que se puede afirmar
run_pipeline.py              orquestador, una sola orden
src/config.py                todos los parámetros y supuestos numéricos
src/p00..p06                 los seis pasos del circuito sintético
tests/                       54 tests, el bloque de fugas es el importante
data/real/                   idealista18 procesado (no versionado)
src/r00..r04                 carga, validación, caso trazado, dashboard y
                             diagnóstico de coeficientes con datos reales
tests/test_dashboard_real.py vigila que el HTML no tenga cifras a mano
docs/validacion_2018.md      resultados con datos reales
docs/investigacion_terciario.md  fuentes y estado de oficinas y logistica
docs/recorrido_del_proyecto.md  el proyecto entero para alguien de negocio,
                             sin jerga, cinco minutos de lectura
docs/investigacion_fuentes.md  catálogo de fuentes públicas usables
docs/power_bi.md             cómo montar el modelo
docs/ESTADO.md               este fichero
```

# Fuentes de datos abiertas para análisis del mercado residencial en España

Investigación realizada el **4 de septiembre de 2026**. Toda cifra lleva su
fuente y su fecha. Cuando una cifra procede de un proveedor comercial sin
metodología publicada, se dice, y no se usa como si fuera oficial.

El objetivo es doble: saber **con qué datos se puede trabajar legalmente** para
analizar el mercado inmobiliario español, y tener el **contexto de mercado** al
día para poder hablar del sector con cifras propias.

---

## 1. El problema de partida

Los datos que un analista inmobiliario quiere de verdad son los precios de
oferta a nivel de inmueble, y esos están en los portales, cuyos términos de uso
prohíben el scraping. Lo que sí hay es una capa pública notablemente rica,
infrautilizada, y con la ventaja de que es **precio de transacción real** en
lugar de precio de oferta.

La conclusión práctica: para nivel de mercado y comparación entre zonas, el dato
público sobra. Para nivel de inmueble individual, hay que tener acuerdo de acceso
con quien tenga el dato, o generar datos sintéticos y declararlo.

---

## 2. Catálogo de fuentes

### Resumen

| Fuente | Qué aporta | Granularidad mínima | Actualización | Formato |
|---|---|---|---|---|
| Catastro — Sede Electrónica | Valor de referencia por inmueble | Inmueble | Anual | Web / certificado PDF |
| Catastro — servicios INSPIRE | Parcelas, edificios, direcciones georreferenciadas | Parcela | ATOM cada ~6 meses; WFS continuo | GML |
| Ayuntamiento de Madrid — Estadística Registral | Precio declarado en escritura, transacciones, superficies | **Barrio** | Anual | XLSX |
| SERPAVI (Mº Vivienda) | Rentas de alquiler declaradas en IRPF | **Sección censal** | Anual | XLSX + shapefiles |
| Mº Vivienda — Valor tasado | €/m² de tasación | Municipio >25.000 hab. | Trimestral | XLSX |
| Mº Vivienda — Transacciones | Nº y valor de compraventas | Provincia / CC. AA. | Trimestral | XLSX |
| INE — IPV | Índice de precios con método hedónico | CC. AA. | Trimestral | API + tablas |
| INE — Atlas de renta (ADRH) | Renta de los hogares, Gini | **Sección censal** | Anual | API + tablas |
| INE — Censo de Viviendas 2021 | Parque de vivienda, régimen de tenencia | Sección censal | Decenal | Tablas |
| Colegio de Registradores | IPVVR, periodo de posesión, crédito hipotecario | Provincia | Trimestral | PDF / XLSX |
| Notariado | Compraventas ante notario, precio | Provincia | Mensual | Portal estadístico |
| datos.gob.es | Catálogo federado de todo lo anterior | — | — | Catálogo |

### Fichas

**Catastro — valor de referencia.** Desde el 1 de enero de 2022, la Dirección
General del Catastro asigna a cada inmueble un valor de referencia que actúa como
base imponible mínima del ITP y del Impuesto de Sucesiones y Donaciones. Se
calcula a partir de los precios de compraventa comunicados por notarios y
registradores. La consulta es **gratuita y pública**, a diferencia del valor
catastral, que sólo puede consultar el titular.

Esto es, de hecho, un modelo de valoración automática estatal, y es el
competidor conceptual directo de cualquier motor de valoración privado. Conviene
saberlo antes de que lo pregunten.

Dato de contexto relevante: el Tribunal Constitucional avaló el sistema en la
**STC 13/2026, de 12 de febrero de 2026**, desestimando la cuestión planteada por
el TSJ de Andalucía. Sigue siendo impugnable caso a caso, pero el método está
respaldado.

*Utilidad para el proyecto*: como línea base contra la que comparar. Si un motor
propio no mejora al valor de referencia del Catastro, no aporta — y saberlo
también es un resultado.

**Catastro — servicios INSPIRE.** Ofrece parcelas catastrales, edificios y
direcciones. Dos vías de descarga: WFS, actualizado en continuo pero no apto para
descarga masiva, y ATOM, que sí permite bajar municipios completos y se
regenera aproximadamente cada seis meses. Los ficheros llegan en GML.

Detalle importante del modelo de datos: los bienes inmuebles no tienen geometría
propia, se asocian a una parcela, que sí está georreferenciada. Para geolocalizar
un piso concreto hay que pasar por el centroide de su parcela.

La descarga masiva de cartografía catastral requiere certificado digital; los
servicios INSPIRE tienen su propia licencia de acceso y uso publicada, que hay
que leer antes de redistribuir nada.

*Utilidad*: georreferenciación, superficies y antigüedad de edificación reales.
Es la vía para pasar de "distrito" a "coordenada".

**Ayuntamiento de Madrid — Estadística Registral Inmobiliaria.** El hallazgo más
directamente aprovechable. El Colegio de Registradores elabora una explotación
específica para el Ayuntamiento con **desglose por distrito y por barrio**, en
XLSX, incluyendo precio medio declarado en escritura (€/m²), transacciones por
tipo y por tramo de superficie, superficie media transmitida y periodo medio de
posesión.

Cubre el 95,6 % de las transmisiones registradas del municipio. Sólo publica el
dato de barrio cuando hay al menos 15 casos, lo cual es exactamente el criterio
de umbral mínimo de muestra que este proyecto aplica por su cuenta.

*Utilidad*: es lo que permite subir la granularidad del motor de distrito a
barrio, que es la mejora pendiente más importante. Un distrito de Madrid es
demasiado heterogéneo para ser unidad de comparación.

**SERPAVI — Sistema Estatal de Referencia del Precio del Alquiler.** Explotación
de los datos de IRPF sobre arrendamientos de vivienda habitual, cruzada con
Catastro para las características físicas del inmueble. Publica renta media en
€/m² al mes, cuantía mensual y superficie media, hasta **sección censal**. Se
descarga como XLSX, y las capas geográficas de secciones, distritos y municipios
como shapefiles.

Es la base legal para el límite de renta en zonas de mercado residencial
tensionado, según el artículo 17.7 de la LAU tras la Ley 12/2023 por el derecho
a la vivienda. El Ayuntamiento de Madrid republica el corte municipal por
distrito y por sección censal.

*Utilidad*: rentabilidad bruta por zona, que es la métrica que pide cualquier
inversor. Con precio de compra por barrio y renta por sección censal, sale.

**INE — Atlas de Distribución de Renta de los Hogares (ADRH).** Explotación
íntegra de registros administrativos (IRPF), con renta media y mediana por
persona y por hogar, fuentes de ingreso, índice de Gini y P80/P20, hasta
**sección censal** con al menos 100 habitantes.

Del último dato publicado (año 2023, difundido en octubre de 2025): Madrid fue
la segunda capital de provincia por porcentaje de secciones censales con renta
por habitante en el decil más alto, un 39,3 %, por detrás de Donostia con un
61,7 %. La provincia de Madrid quedó tercera en renta neta por habitante con
18.142 €, tras Gipuzkoa y Bizkaia.

*Utilidad*: la variable socioeconómica que mejor explica precio a nivel micro, y
que no está en ninguna fuente inmobiliaria.

**INE — Índice de Precios de Vivienda (IPV).** Calculado con precios hedónicos
sobre transacciones registradas. En el primer trimestre de 2026 la variación
anual fue del 12,9 %: 9,1 % en vivienda nueva y 13,5 % en segunda mano, con una
subida trimestral del 3,5 %. Publicado el 8 de junio de 2026.

*Utilidad*: es el deflactor correcto para comparar precios entre años.

**Ministerio de Vivienda y Agenda Urbana.** Publica valor tasado de la vivienda
(trimestral, municipios de más de 25.000 habitantes), transacciones inmobiliarias
de compraventa, estimación del parque de viviendas, stock de vivienda nueva y
precios de suelo urbano.

Cierre de 2025: el precio medio de vivienda libre alcanzó 2.230 €/m², un 13,1 %
más interanual, máximo de la serie, superando el pico de 2.101 €/m² del primer
trimestre de 2008. En el primer trimestre de 2026 subió a 2.315 €/m². Madrid fue
una de las comunidades con mayor subida interanual, un 16,4 %.

**Colegio de Registradores y Notariado.** Ambos publican estadística propia.
Registradores aporta el Índice de Precio de Ventas Repetidas (IPVVR), que es
metodológicamente el más limpio para medir revalorización porque compara el mismo
inmueble consigo mismo, además de periodo medio de posesión y distribución del
crédito hipotecario. El Portal Estadístico del Notariado publica compraventas
autorizadas ante notario con periodicidad mensual, antes que casi nadie.

**datos.gob.es.** Catálogo federado. Es el sitio por el que empezar a buscar
cualquier conjunto, porque agrega los de los tres ministerios, el INE y los
ayuntamientos.

### Lo que NO se puede usar

- **Scraping de Idealista, Fotocasa y equivalentes**: prohibido por sus términos
  de uso. Existe un dataset público en Zenodo con anuncios de los distritos de
  Salamanca y Villaverde extraídos en abril de 2022, declarado por sus autores
  como de uso exclusivamente académico. No es base para una pieza de portfolio
  pública.
- Ojo con una trampa: la tabla de **precio de vivienda de segunda mano por
  distrito** que publica el propio Ayuntamiento de Madrid procede de Idealista,
  no del Registro. Es precio de **oferta**, no de cierre. Está en la misma
  publicación que la tabla registral y es fácil confundirlas.

---

## 3. Contexto del mercado, con fechas

Para poder sostener una conversación de sector sin repetir titulares.

**Precios.** Máximos históricos, por encima de la burbuja de 2007. España cerró
2025 en 2.230 €/m² de valor tasado y llegó a 2.315 €/m² en el primer trimestre de
2026 (Ministerio de Vivienda). El IPV del INE marcó 12,9 % interanual en el
primer trimestre de 2026.

**Volumen.** 2025 cerró con 714.237 transmisiones de vivienda en España, un
11,5 % más que 2024, con la obra nueva creciendo un 16,1 % (INE). En enero de
2026 las compraventas cayeron un 5 % en España y un 19,6 % en la Comunidad de
Madrid en tasa interanual. La lectura razonable: el mercado se enfría en ritmo,
no en precio.

**Financiación.** El Euríbor a 12 meses cerró julio de 2026 en 2,855 %, el nivel
más alto del año, más de 0,77 puntos por encima de julio de 2025. Es un giro
respecto al ciclo de bajadas de 2025 y cambia el perfil del comprador: pesa más
el que compra al contado o con poca hipoteca.

**El cuello de botella es la oferta.** Falta de suelo finalista, tramitación
urbanística que se mide en años, costes de construcción altos y escasez de mano
de obra. Se construye menos de lo que el mercado absorbe. Este es el consenso de
prácticamente todas las fuentes revisadas, públicas y privadas.

**Alquiler en Madrid.** Fotocasa situaba la renta media de la Comunidad en
20,20 €/m² en febrero de 2026 y la de la capital en 21,59 €/m²; en mayo de 2026
elevaba la capital a 22,75 €/m², equivalente a unos 1.820 € al mes para 80 m².
*Fuente privada con metodología propia basada en oferta publicada; útil como
orden de magnitud, no como dato oficial. La cifra pública equivalente es la de
SERPAVI, que es renta declarada y sale más baja.*

**Cifras que he descartado.** Circulan bastantes datos de precio de Madrid
capital que van de 4.500 a más de 6.000 €/m² según la fuente. La horquilla es
tan amplia porque mezclan oferta y cierre, capital y comunidad, y metodologías
distintas. No conviene citar ninguna sin decir cuál es y de qué fecha. Es
justamente el error que este proyecto intenta no cometer.

---

## 4. Cómo se está usando la IA en el sector

Relevante porque parte del encargo es ayudar a integrar IA en los procesos.

**Valoración automática (AVM).** No es nuevo. Idealista ofrece valoración
gratuita desde hace años, y las tasadoras tienen modelos propios: Gloval publica
que su AVM, basado en gradient boosting, se ha usado en valoraciones masivas para
CaixaBank, Sabadell, BBVA y Deutsche Bank. Lo que cambia es la frecuencia de
actualización y el número de variables cruzadas.

El límite conocido de los AVM está bien documentado y conviene nombrarlo: pierden
fiabilidad en zonas con pocas transacciones, en inmuebles singulares, en activos
con cargas o problemas legales y en mercados que giran rápido, porque los datos
llegan con retraso. Es exactamente el mismo motivo por el que este proyecto se
niega a valorar el 24 % de la cartera.

**Extracción documental.** Es el hueco menos cubierto y el más fácil de defender:
pasar de nota de captación, escritura, nota simple o ficha a datos estructurados.
No requiere reentrenar nada ni acumular histórico, y el retorno se ve el primer
día. Es lo que demuestra el paso 01 de esta demo.

**Visión por computador sobre fotos** para detectar estado de conservación y
reformas, y **staging virtual**. Restb.ai, empresa española, es la referencia
citada con más frecuencia.

**IA conversacional** para cualificar leads y agendar visitas, integrada en web y
WhatsApp.

**Cifras que NO voy a citar.** He encontrado afirmaciones del tipo "más del 60 %
de las agencias españolas ya usan AVM" o cifras de valor global del mercado en
miles de millones. Todas proceden de blogs de proveedores que venden esas mismas
herramientas y ninguna publica metodología ni muestra. No son citables.

---

## 5. Qué hacer con esto en el proyecto

En orden de relación entre valor y esfuerzo:

1. **Bajar de distrito a barrio.** El XLSX de precio medio declarado por barrio
   del Ayuntamiento de Madrid existe y es descargable. Es la mejora que más sube
   la credibilidad técnica, y responde por adelantado a la objeción obvia de
   cualquiera del sector: un distrito de Madrid no es una unidad de comparación.
2. **Añadir el valor de referencia del Catastro como línea base.** Da contexto a
   la métrica de error, que ahora mismo no lo tiene. Un error mediano del 10 %
   no significa nada hasta que se sabe qué error tiene la alternativa gratuita.
3. **Cruzar renta por sección censal (ADRH) y renta de alquiler (SERPAVI).**
   Permite calcular rentabilidad bruta por zona, que es la métrica que un
   inversor pide de verdad, y es la clase de cruce que ninguna herramienta
   comercial hace bien porque exige entender tres fuentes públicas distintas.
4. **Documentar la línea de tiempo de cada fuente.** Los datos de barrio son
   anuales y llegan con retraso; el IPV es trimestral; el Notariado es mensual.
   Una tabla que diga qué se puede saber y con cuánto desfase vale más que
   cualquier gráfico.

Lo que **no** haría: intentar acceder a datos de portales por ninguna vía. El
repo es público y va enlazado desde un perfil profesional.

---

## 6. Fuentes consultadas

Todas el 4 de septiembre de 2026.

- Ayuntamiento de Madrid, *Anuario Estadístico 2023*, capítulo 8, y sección de
  estadística de mercado de la vivienda (compraventa y alquiler).
  `madrid.es/estadistica`
- Colegio de Registradores de la Propiedad, *Estadística Registral Inmobiliaria*.
  `registradores.org`
- Ministerio de Vivienda y Agenda Urbana: valor tasado de la vivienda,
  transacciones inmobiliarias, precios de suelo urbano, SERPAVI.
  `mivau.gob.es`, `transportes.gob.es`
- INE: Índice de Precios de Vivienda base 2025, primer trimestre de 2026
  (publicado el 08/06/2026); Atlas de Distribución de Renta de los Hogares, año
  2023 (nota de prensa de octubre de 2025); Censo de Viviendas 2021. `ine.es`
- Dirección General del Catastro: servicios INSPIRE y documentación de conjuntos
  de datos y servicios ATOM; Sede Electrónica, valor de referencia.
  `catastro.hacienda.gob.es`, `sedecatastro.gob.es`
- `datos.gob.es`, catálogo nacional de datos abiertos.
- Sentencia del Tribunal Constitucional 13/2026, de 12 de febrero de 2026, sobre
  el valor de referencia catastral.
- Prensa y análisis sectorial para el contexto de mercado: idealista/news
  (19/02/2026), El Debate (29/01/2026), y varios informes de portales y agencias
  publicados entre febrero y agosto de 2026. Marcados como fuente privada donde
  se citan.

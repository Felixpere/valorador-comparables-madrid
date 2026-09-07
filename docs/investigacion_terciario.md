# Oficinas y logística: cómo funciona el dato en el terciario

Investigación realizada y verificada el **6 y 7 de septiembre de 2026**. Último
dato disponible: **segundo trimestre de 2026**.

Es el complemento de `investigacion_fuentes.md`, que cubre residencial. El terreno
aquí es otro y conviene entender por qué antes de mirar ninguna cifra.

**Cómo leer las cifras de este documento.** Cada una lleva marcada su procedencia:

- **[P]** primaria — publicada directamente por la consultora que la produce.
- **[S]** secundaria — prensa sectorial citando a una consultora. Verosímil, pero
  sin acceso al informe original.

La distinción importa: citar una cifra de segunda mano como si fuera de primera
es exactamente el error que este repositorio evita en el resto de su
documentación.

---

## 1. El cambio de terreno

En residencial hay una capa pública densa: Registro, Catastro, INE, Ministerio de
Vivienda. Se puede analizar el mercado sin pedirle permiso a nadie.

**En oficinas y logística esa capa no existe.** Ningún organismo público publica
rentas de oficinas, tasas de disponibilidad ni rentabilidades. El dato lo producen
y lo publican las consultoras: CBRE, JLL, Savills, Cushman & Wakefield, BNP Paribas
Real Estate, Knight Frank, Colliers y alguna más. Cada una con su propia red de
datos, su propia metodología y su propio informe trimestral en PDF.

Tres consecuencias:

- **El dato llega como documento, no como tabla.** PDF trimestral, con gráficos y
  texto. Nadie lo publica en CSV.
- **Las cifras no coinciden entre fuentes**, y no es un error de nadie.
- **Lo único público y estructurado a nivel de activo** son los informes de las
  SOCIMI cotizadas, que por obligación legal detallan su cartera.

## 2. Cinco consultoras, cinco números, el mismo trimestre

Es el hallazgo más útil de esta investigación.

**Contratación de oficinas en Madrid, primer trimestre de 2026:**

| Fuente | Cifra | |
|---|---|---|
| Savills | 110.000 m² | [P] |
| CBRE | ~102.000 m² (−2 % interanual) | [P] |
| JLL | 100.376 m² | [P] |
| BNP Paribas RE | 95.333 m² (−25 % interanual, 100 operaciones) | [P] |
| Forcadell | 90.000 m² (−28 % interanual, 73 operaciones) | [S] |

Del más alto al más bajo hay un **22 % de diferencia**. Y hay algo más llamativo
que la diferencia de nivel: CBRE ve una caída del 2 % interanual y BNP una del
25 %. No sólo discrepan en el nivel,
discrepan en la magnitud de la tendencia.

**Renta prime logística en Madrid, primer trimestre de 2026:**

| Fuente | Cifra | |
|---|---|---|
| Savills | 6,75 €/m²/mes (+8 % interanual) | [S] |
| MVGM | 7,30 €/m²/mes (+6,5 % interanual) | [S] |
| BNP Paribas RE | 7,50 €/m²/mes (+7,14 % interanual) | [P] |
| Cushman & Wakefield | «por encima de 7 €/m²/mes» (+4 %) | [S] |

**Renta prime de oficinas en Madrid, 2026:**

| Fuente | Cifra | |
|---|---|---|
| Cushman & Wakefield | 43,50 €/m²/mes en CBD (T1) y 44 €/m²/mes (T2) | [P] |
| JLL | 44,50 €/m²/mes (T1, +8,5 % interanual) | [P] |
| BNP Paribas RE | ≈46 €/m²/mes (T1) | [P] |
| Savills | máximos de 46 €/m²/mes (cierre de 2025) | [P] |

**Stock de oficinas de Madrid:** JLL lo sitúa en 16,3 millones de m² [P]; otras
fuentes hablan de unos 18 millones [S]. La diferencia son 1,7 millones de metros,
más del 10 %.

**Volumen de inversión inmobiliaria en España, primer semestre de 2026:**

| Fuente | Cifra | |
|---|---|---|
| Colliers | ~12.500 M€ (suma de su desglose por sectores) | [P] |
| Cushman & Wakefield | 10.500 M€ | [S] |
| JLL | «más de 10.000 M€», +50 % interanual | [P] |

### Por qué difieren

Las causas son de definición, no de rigor:

- **Qué entra en el cómputo**: renovaciones de contrato sí o no, operaciones de uso
  propio sí o no, prealquileres sobre obra futura sí o no.
- **Qué perímetro es «Madrid»**: sólo el municipio, el área metropolitana, o los
  corredores logísticos hasta la tercera corona.
- **Qué significa «prime»**: la renta máxima firmada en el trimestre, o una media
  de los mejores activos.
- **Renta de cierre o de salida**: lo firmado o lo pedido.
- **Inversión directa o total**: si se incluyen operaciones corporativas, cambios de
  uso y compras para uso propio.

**Qué exige esto de un análisis serio.** No consiste en elegir el número más
alto. Consiste en saber que hay cinco, saber por qué difieren, declarar cuál se
usa y con qué definición, y mantener ese criterio en el tiempo. Es la misma
disciplina que aplica este repositorio en residencial, en un sector donde el
problema es mayor.

## 3. Vocabulario

El terciario tiene un vocabulario propio que no aparece en el resto del
repositorio, porque residencial habla otro idioma. Sin él, las cifras de arriba
no se interpretan bien.

| Término | Qué es |
|---|---|
| **Contratación / take-up / absorción bruta** | Metros alquilados en un periodo. La métrica de actividad por excelencia |
| **Absorción neta** | Contratación menos superficie desocupada. Mide si el mercado crece de verdad |
| **Renta prime** | La renta más alta que se paga por un activo de máxima calidad en la mejor ubicación. En €/m²/mes, no en €/m² totales |
| **Renta media de cierre** | Lo que se firma de media. Muy por debajo de la prime |
| **Tasa de disponibilidad / vacancy** | Porcentaje del stock desocupado y ofertado |
| **Stock** | Superficie total del mercado |
| **Oferta futura / pipeline** | Metros en construcción o proyecto, con fecha prevista de entrega |
| **Yield / rentabilidad prime** | Renta anual dividida entre el precio del activo. Baja cuando sube el precio |
| **Compresión de yields** | Que bajen. Señal de que suben los precios |
| **CBD** | Central Business District. En Madrid, el eje Castellana-Azca-Cuzco |
| **Grado A / B+ / B** | Calidad del edificio. Grado A es obra reciente o rehabilitación integral |
| **Coronas** | Anillos de distancia en logística. La primera pegada a la ciudad, la tercera a más de 50 km |
| **Última milla** | Naves pequeñas y urbanas para reparto final |
| **Big box** | Naves grandes de distribución, decenas de miles de metros |
| **Cross-dock** | Nave con muelles a ambos lados, para tránsito sin almacenaje |
| **WAULT** | Vida media pendiente de los contratos, ponderada. Mide estabilidad de ingresos |
| **NOI** | Ingreso operativo neto del activo |
| **GAV / NAV / EPRA NTA** | Valor bruto de los activos, valor neto, y la versión estandarizada europea del valor neto |
| **LTV** | Deuda sobre valor de los activos |
| **Sale & leaseback** | Vender el inmueble y quedarse como inquilino |
| **Core / core-plus / value-add** | Perfiles de riesgo de inversión, de menor a mayor |
| **Living** | Categoría que agrupa residencial en alquiler, residencias de estudiantes y flex living |
| **PBSA / BTR / BTS** | Residencias de estudiantes, build-to-rent y build-to-suit |
| **SOCIMI** | Sociedad cotizada de inversión inmobiliaria, con régimen fiscal propio a cambio de repartir dividendos |
| **ESG / BREEAM / LEED** | Criterios y certificaciones de sostenibilidad, hoy determinantes en la demanda corporativa |

## 4. El mapa de fuentes

### Consultoras

Informes trimestrales gratuitos, en PDF, algunos con registro previo.

| Consultora | Publicación | Cadencia |
|---|---|---|
| CBRE | *Figures* por sector | Trimestral |
| JLL | *Market Dynamics* | Trimestral |
| Savills | *Market in Minutes*, *Office Pulse* | Trimestral |
| BNP Paribas RE | *At a Glance* | Trimestral |
| Knight Frank | *In Focus* | Trimestral |
| Cushman & Wakefield | *Marketbeat*, *The Investment Atlas* | Trimestral |
| Colliers | *Snapshot* | Trimestral |
| MVGM | *Informe de mercado inmobiliario en Iberia* | Trimestral |

**Uso legal**: son documentos con derechos de autor. Se pueden leer, citar con
atribución y usar sus cifras nombrando fuente y fecha. **No** se pueden republicar
íntegros ni raspar de forma automatizada.

### Lo público, estructurado y legal: las SOCIMI vía CNMV

Por obligación legal, las inmobiliarias cotizadas publican con detalle su cartera:
activo por activo, superficie alquilable, ocupación, rentas brutas, valoración y
rentabilidad. Es información pública, gratuita y descargable de la CNMV.

Las grandes: **Merlin Properties** (oficinas, logística, centros comerciales y
centros de datos) e **Inmobiliaria Colonial** (oficinas prime en Madrid, Barcelona
y París). Además, más de un centenar de SOCIMI pequeñas en BME Growth.

Ejemplo de lo que sale de ahí, del primer semestre de 2026 de Merlin [S, resumen de
prensa del hecho relevante; el original está en la CNMV]: ocupación media de cartera
del 94,7 %, con subidas de rentas comparables del 2,4 % en oficinas, 1,2 % en
logística y 6,4 % en centros comerciales; valor bruto de activos de 13.508 millones,
EPRA NTA de 9.913 millones y LTV del 24,5 %.

**Es el equivalente en terciario de lo que `idealista18` fue en residencial**: dato
real, a nivel de activo, publicado por ley. Con una diferencia importante: sólo
cubre las carteras de las cotizadas, no el mercado entero.

### Catastro

Publica estadísticas de inmuebles urbanos por uso. La normativa de valoración
distingue expresamente los usos residencial, industrial, oficinas, comercial,
deportes y espectáculos, sanidad, y culturales y religiosos (Real Decreto 1020/1993,
norma 20, citado en el BOE-A-2024-632). Da stock y valor catastral por municipio,
**no rentas**. Sirve para dimensionar el parque, no para valorarlo.

La Comunidad de Madrid republica el catastro urbano por municipios y zonas
estadísticas en su Anuario de la Construcción.

### Lo que no existe

No hay estadística pública de rentas de oficinas ni de logística. Ni INE, ni
Ministerio, ni Registro. Quien quiera esa serie, o la compra o la construye leyendo
informes.

## 5. Estado del mercado

Último dato disponible: segundo trimestre de 2026.

### Oficinas Madrid

**Contratación.** 112.431 m² en el segundo trimestre, un 12 % más que el trimestre
anterior. Pero el acumulado del semestre se quedó en 212.958 m², **un 26 % por
debajo** del mismo periodo de 2025, por escasez de espacio dentro de la M-30 [S,
citando a JLL].

Ese matiz es importante: trimestre a trimestre sube, año contra año baja. Según qué
comparación se elija, la misma realidad se cuenta de dos maneras opuestas.

**Rentas.** Renta prime entre 43,50 y 46 €/m²/mes según fuente, con tendencia
alcista sostenida. La renta media del conjunto del mercado está en 23,66 €/m²/mes,
con 38,86 €/m²/mes en el CBD y 14,94 €/m²/mes en la periferia [P, BNP, T1 2026].

**Disponibilidad.** El dato que explica todo lo demás. En torno al 8,7-8,9 % en el
conjunto, pero **2,4-2,6 % dentro de la M-30** y 2,36 % en el CBD, frente al 12,47 %
fuera de la M-30 [P, Savills y BNP, T1 2026]. En Grado A dentro de la M-30 se han
roto mínimos por debajo del 1,5 % [P, Cushman & Wakefield].

Es un mercado partido en dos: escasez severa en el centro, holgura en la periferia.

**Rentabilidad prime.** 4,50 % en Madrid y 4,70 % en Barcelona a cierre del segundo
trimestre [P, Colliers].

### Logística Madrid

**Contratación.** 299.873 m² en el segundo trimestre y 620.193 m² en el semestre, un
56,6 % más que en 2025 [P, BNP]. JLL da 620.000 m² y lo describe como el mejor primer
semestre de su serie histórica, con un crecimiento del 58 % [P].

**Rentas.** Renta prime de 7,50 €/m²/mes, un 7,14 % más que doce meses antes [P,
BNP]. Renta media de 5,50 €/m²/mes [P, BNP, T1].

**Disponibilidad.** 8,36 % a cierre del segundo trimestre, 99 puntos básicos menos
que un año antes [P, BNP].

**Rentabilidad prime.** 5,00 % en Madrid y 4,85 % en Barcelona [P, Colliers, T2].

**Cataluña** marca la renta prime más alta de España, en torno a 9,2 €/m²/mes, con
una disponibilidad muy ajustada, del 3,07 % [S].

Los motores son el comercio electrónico, la presión de la última milla sobre naves
pequeñas cerca de las ciudades, y la relocalización industrial.

### Inversión

El primer semestre de 2026 fue el mayor de la serie histórica según JLL, con más de
10.000 millones y un crecimiento del 50 % interanual [P]. El primer trimestre solo
sumó 5.955 millones, un 99 % más interanual [S].

Desglose por sector del primer semestre [P, Colliers]:

| Sector | Volumen | Peso |
|---|---|---|
| Living | 4.593 M€ (+320,4 %) | 37 % |
| Hoteles | 2.460 M€ (+26,5 %) | 20 % |
| Oficinas | 1.634 M€ | 13 % |
| Retail | 1.586 M€ | 13 % |
| Alternativos | 1.414 M€ | 11 % |
| Industrial y logístico | 800 M€ | 6 % |

**El dato que más llama la atención**: Living es hoy el primer sector por volumen de
inversión, con un crecimiento del 320 %. Oficinas y logística, que son las dos
primeras patas del negocio de una consultora de terciario por actividad, están muy
por detrás en captación de capital.

Las previsiones para el conjunto de 2026 van de 17.000 a más de 20.000 millones
[S, citando a Cushman & Wakefield y a Savills].

## 6. Encaje con el circuito de este repositorio

**El problema que resuelve el circuito es más real en terciario que en residencial.**

En residencial hubo que generar anuncios sintéticos porque el dato de oferta a nivel
de inmueble no está disponible legalmente. El paso de extracción quedó demostrado
sobre un corpus inventado.

En oficinas y logística **el problema del documento no estructurado es real y no
está resuelto**. Ocho consultoras publican cada trimestre un PDF con las mismas
métricas definidas de forma distinta. Alguien, hoy, los lee a mano y los pasa a una
hoja, trimestre tras trimestre. Eso es exactamente lo que hace el paso 01 del
circuito, y el problema de la reconciliación entre fuentes es exactamente lo que
hace el resto.

Segundo frente igual de real: los informes de las SOCIMI, públicos, en PDF, con la
cartera activo por activo.

**Lo que NO se puede afirmar a partir de este documento:**

- **No se ha construido ni probado nada sobre oficinas o logística.** Esto es un
  mapa de fuentes y un estado del mercado, no un resultado.
- **El motor de comparables no se traslada tal cual.** En terciario la unidad de
  comparación no es el barrio y los metros construidos, sino la zona, el grado del
  edificio, la altura libre, los muelles, y sobre todo el contrato: duración,
  garantías e indexación pesan tanto como el inmueble.
- **La muestra es mucho más pequeña.** En Madrid se firman del orden de 70 a 100
  operaciones de oficinas por trimestre, no miles. Con esos números, un motor de
  comparables se quedaría sin muestra suficiente casi siempre — que es justo lo que
  el sistema ya sabe declarar en lugar de inventarse un número.
- **Las cifras de este documento son de segunda mano en varios casos**, y están
  marcadas como tales. Antes de usar cualquiera en un entregable habría que ir al
  informe original.

## 7. Fuentes consultadas

Consultadas el 6 y 7 de septiembre de 2026.

**Primarias**
- JLL, *Dinámicas del Mercado de Oficinas en Madrid* y *Mercado Logístico Madrid*, T1 y T2 2026; nota de prensa sobre inversión, junio de 2026
- CBRE, *Figures Oficinas España* T1 2026; *Tendencias en Oficinas 2026*
- Savills, *Market in Minutes Oficinas* T1 2026; *Office Pulse*
- BNP Paribas Real Estate, *At a Glance* Oficinas Madrid T1 2026 y Mercado Logístico Madrid T1 y T2 2026
- Colliers, *Snapshot Oficinas Madrid y Barcelona* T1 2026 y *Snapshot Inversión inmobiliaria en España* T2 2026
- Knight Frank, *In Focus Logística* T1 2026
- Cushman & Wakefield, *Marketbeat Oficinas España* T1 y T2 2026
- CNMV, portal de información regulada de Merlin Properties e Inmobiliaria Colonial
- Dirección General del Catastro, estadísticas catastrales; BOE-A-2024-632 sobre los usos catastrales
- Comunidad de Madrid, Anuario de la Construcción

**Secundarias** (prensa sectorial citando a consultoras)
- Brains Real Estate News, julio y agosto de 2026
- EjePrime y El Inmobiliario, abril y agosto de 2026
- idealista/news, mayo de 2026
- MuyPymes, junio de 2026
- Observatorio Inmobiliario, abril de 2026
- Forcadell, nota de prensa de junio de 2026

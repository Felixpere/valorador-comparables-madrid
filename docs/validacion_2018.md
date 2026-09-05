# Validación con datos reales — Madrid, 2018

Ejecutable con `python src/r00_cargar_idealista18.py && python src/r01_valorar_real.py`.
Todas las cifras de este documento salen de esa ejecución, con semilla 20260904.

---

## Los datos

**`idealista18`**: 94.815 anuncios de venta de vivienda en Madrid, los cuatro
trimestres de 2018, con 41 variables por anuncio y coordenadas aproximadas. Los
publicaron la propia idealista y dos universidades:

> Rey-Blanco, D., Arbués, P. (idealista), López, F. (Universidad Politécnica de
> Cartagena) y Páez, A. (McMaster University). *A geo-referenced micro-data set
> of real estate listings for Spain's three largest cities*. Environment and
> Planning B: Urban Analytics and City Science, 2024.
> [doi:10.1177/23998083241242844](https://doi.org/10.1177/23998083241242844) ·
> [github.com/paezha/idealista18](https://github.com/paezha/idealista18)

Licencia **ODbL-1.0**. No es scraping: es un producto de datos abiertos
publicado por el propio portal.

Los 135 barrios de idealista, con sus polígonos, permiten asignar cada anuncio a
su barrio por punto en polígono. El 99,9 % quedó asignado.

## Cómo está montada la validación

Los anuncios se parten en dos por sorteo con semilla fija:

- **Pool (70 %, 52.833 anuncios)** — el único conjunto del que salen
  comparables, y el único con el que se estiman los coeficientes de ajuste.
- **Evaluación (30 %, 22.643 anuncios)** — anuncios que el motor no ha visto
  nunca. Se estima su valor y se compara con lo que realmente pedían.

Ningún anuncio de evaluación participa en su propia valoración, ni directamente
ni a través de los coeficientes. La partición es por anuncio, no por fila.

Comparable = mismo barrio, mismo trimestre, superficie ±20 %, mínimo cinco.
Cobertura: **96,1 %**.

## El resultado

| Método | Error mediano | Dentro de ±10 % | Dentro de ±20 % | Sesgo |
|---|---|---|---|---|
| **Comparables por barrio** | **12,0 %** | 43,0 % | 71,7 % | −0,1 % |
| Mediana del barrio y trimestre | 15,2 % | 34,7 % | 62,2 % | 0,0 % |
| Mediana de la ciudad | 34,3 % | 13,3 % | 28,0 % | −1,5 % |

Leído con honestidad: **el motor mejora la línea base ingenua en 3,2 puntos**, una
reducción del error del 21 %. No es espectacular. Y la lectura incómoda es la
otra: la simple mediana del €/m² del barrio ya te lleva a un 15,2 %, así que la
mayor parte del trabajo la hace saber en qué barrio está el piso, no el motor.

Contra la mediana de la ciudad sin distinguir zona, el error es del 34,3 %. Eso
sí es la diferencia entre tener un método y no tenerlo.

## La etiqueta de fiabilidad, que con datos sintéticos no servía

| Fiabilidad | Error mediano |
|---|---|
| Alta | 10,4 % |
| Media | 12,7 % |
| Baja | 15,9 % |

Con el corpus sintético, esta etiqueta daba el mismo error en los tres niveles y
lo dejamos escrito como un fallo abierto. Con datos reales **sí discrimina**: hay
5,5 puntos entre el nivel alto y el bajo. La explicación de por qué fallaba era
correcta: la dispersión del generador era homogénea por construcción, y el
mercado real no lo es.

Un matiz: lo que discrimina es la **dispersión** de los comparables, no cuántos
hay. Pasar de 5-9 comparables a más de 50 solo baja el error del 12,7 % al
11,9 %.

## Qué pesa en el precio por metro cuadrado

Coeficientes estimados sobre el pool, centrados por barrio y trimestre, así que
miden el atributo aislado del efecto de la zona.

| Atributo | Efecto sobre €/m² |
|---|---|
| Superficie (elasticidad) | −16,0 % |
| Obra nueva | +13,4 % |
| Ascensor | +12,0 % |
| Segunda mano a reformar | −9,5 % |
| Aire acondicionado | +6,7 % |
| Garaje | +6,0 % |
| Piscina | +5,7 % |
| Interior | −4,3 % |

El signo de la superficie es el esperado: los pisos grandes valen más en total y
menos por metro. El ascensor pesa tanto como la obra nueva, que es un resultado
que a cualquiera del sector le suena.

### Los dos coeficientes que estaban en cuarentena, ya verificados

Aquí quedaron escritos dos coeficientes como anomalía sin verificar: jardín en
−1,4 % y calidad catastral en −1,4 %, ambos «con el signo contrario al
esperado», con la sospecha anotada de colinealidad con barrio y superficie.

Verificado con `python src/r04_diagnostico_coeficientes.py`. **La sospecha era
falsa** y los dos casos resultaron ser cosas distintas.

**Calidad catastral: no era una anomalía, era la variable leída al revés.**
`CADASTRALQUALITYID` no es una nota de calidad, es la categoría catastral, y
empeora según crece el número. En el pool el €/m² mediano cae sin excepciones del
código 0 al 7 —el 97,7 % de los anuncios—, de 5.995 € a 2.114 €:

| Código catastral | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| €/m² mediano | 5.995 | 5.839 | 5.076 | 4.622 | 4.088 | 3.568 | 2.247 | 2.114 | 2.464 | 2.883 |
| Anuncios | 200 | 351 | 1.429 | 6.766 | 13.595 | 11.692 | 11.624 | 5.975 | 860 | 341 |

Sobre el código tal y como venía, el signo negativo era el correcto: la dirección
de la variable no estaba documentada en el paquete ni escrita en este repositorio,
y se leyó al revés. `r01` ahora **invierte** la variable para que crezca con la
calidad, y el coeficiente pasa a **+1,4 %** por grado.

**Esta tabla establece el sentido de la variable, no la magnitud del efecto, y las
dos cifras no se pueden comparar.** La caída de 5.995 € a 2.114 € es un −64,7 % en
bruto, un −13,8 % por grado. El coeficiente del modelo es +1,4 % por grado, diez
veces menos, y no hay contradicción: en la tabla no se ha descontado el barrio, y
el barrio se lleva casi toda esa caída. La tabla dice hacia dónde va la variable;
el coeficiente dice cuánto pesa una vez aislada de la zona.

**Que la inversión no mueve ninguna valoración no es un resultado empírico, es
demostrable.** Sustituir `v` por `9 − v` deja el espacio de columnas intacto
porque el modelo lleva término independiente, así que mínimos cuadrados devuelve
`β' = −β` y el intercepto absorbe `9β`. Como el factor de ajuste excluye el
intercepto, queda `factor_nuevo = factor_viejo × exp(−9β)`: una constante global.
Y en la valoración cada comparable se divide por su propio factor y se multiplica
por el del sujeto, con lo que la constante se cancela **exactamente**, no
aproximadamente. El test
(`test_invertir_la_calidad_no_mueve_ninguna_valoracion`) mide una diferencia
máxima de 0,0 y sigue ahí, pero como guardia por si alguien mete el intercepto en
el factor en el futuro, no como prueba: la prueba es el álgebra.

**El cabo suelto de los códigos 8 y 9, con su filo.** Los dos últimos códigos
repuntan en precio en vez de seguir bajando, y son 1.201 anuncios de 52.833. Aquí
hay algo peor que un dato raro: la recodificación `9 − v` les asigna la **calidad
más baja de la escala**, y son precisamente los que se pagan más caros que el
código 7. Si 8 y 9 no significan «peor calidad» sino otra cosa —un marcador de
valor desconocido, una escala distinta—, mi recodificación los coloca al revés.
No cambia nada material, porque son el 2,3 % del pool y el coeficiente es pequeño,
pero **no está resuelto** y no lo doy por resuelto.

**Jardín: tampoco era colinealidad, y el −1,4 % se queda.** Tres comprobaciones
distintas, y las tres dicen que no.

*Uno, la colinealidad se mide.* El VIF del jardín es 1,92 y el máximo de todo el
modelo es 2,30. Por debajo de 5 no hay problema. La correlación más fuerte entre
regresores de todo el modelo es la de **jardín con piscina, 0,665**, y ninguna
pareja llega a 0,7. Detrás van jardín con garaje (0,478) y garaje con piscina
(0,546). Correlacionadas sí; colineales, no. Guárdese ese 0,665, que es la pista.

*Dos, la sospecha era «colinealidad con el barrio», y el modelo ya centra por
barrio y trimestre.* Así que la forma directa de contrastarla es estimar también
**sin centrar** y ver hacia dónde se mueve:

| | Centrado por barrio-trimestre (producción) | Sin centrar |
|---|---|---|
| Jardín | −1,4 % | **−8,5 %** |
| Calidad catastral | +1,4 % | +13,0 % |

**Pasa lo contrario de lo que decía la sospecha.** Sin centrar, el jardín es seis
veces más negativo: el efecto de zona empujaba hacia abajo, porque las promociones
con jardín están en barrios baratos, y el centrado ya lo quita. Si el barrio fuera
la causa del signo negativo, quitar el centrado tendría que empeorarlo, no
arreglarlo. El −1,4 % es lo que sobrevive *después* de descontar la zona.

(El centrado mueve mucho más que estos dos: «interior» pasa de +17,0 % sin centrar
a −4,3 % centrado, o sea que cambia de signo. Por eso el modelo centra.)

*Tres, controlar por superficie lo hace más positivo, no menos*, que es también lo
contrario de lo que decía la sospecha.

Lo que sí pasa es otra cosa, y se ve añadiendo controles de uno en uno:

| Modelo | Efecto del jardín sobre el €/m² |
|---|---|
| Sin controles | **+10,1 %** |
| + superficie | +12,6 % |
| + piscina | +2,4 % |
| + garaje, trastero y portero | −0,7 % |
| + ascensor | −1,3 % |
| Modelo completo | **−1,4 %** |

El signo cambia al entrar la piscina. El motivo está en el cruce: el 64,2 % de los
anuncios con jardín tienen además piscina, y son los caros.

| | Sin piscina | Con piscina |
|---|---|---|
| **Sin jardín** | 3.407 €/m² (42.015) | 3.673 €/m² (1.492) |
| **Con jardín** | **2.794 €/m² (3.339)** | 3.721 €/m² (5.987) |

**Aquí hay que separar dos cosas que no están al mismo nivel de prueba, y no las
voy a presentar como si lo estuvieran.**

*Lo probado*: el −1,4 % no viene del barrio, ni de la superficie, ni de
colinealidad. Eso lo sostienen tres comprobaciones independientes y numéricas, y
el coeficiente es pequeño pero distinguible de cero (t = −3,9, IC 95 % de −2,1 %
a −0,7 %). Es un efecto parcial real y se queda como está.

*Lo interpretado*: que «jardín y nada más» marque promoción periférica es una
**lectura del patrón, no una medición**. Encaja con el cruce de arriba y con que
el valor lo lleve el paquete de zonas comunes, pero no hay en estos datos ninguna
variable que separe el jardín privado de la zona común de una urbanización. Sin
eso, la explicación es plausible y no está demostrada. Se cuenta como lo que es.

**La lección, que vale más que los dos coeficientes**: uno de los dos «hallazgos
raros» era un error de lectura de la documentación del dato, no un hallazgo. Por
eso estaban en cuarentena y no en la presentación.

## La estructura del mercado

Del barrio más caro al más barato hay un factor **6,4**:

| Barrio | €/m² mediano | Anuncios |
|---|---|---|
| Recoletos | 7.440 | 962 |
| Castellana | 6.523 | 1.096 |
| Almagro | 6.033 | 1.243 |
| … | | |
| Entrevías | 1.369 | 682 |
| San Cristóbal | 1.169 | 307 |

Los niveles son de 2018 y hoy no valen. **El orden sí.** Esa es la parte del
análisis que sobrevive al paso del tiempo, y es la que conviene enseñar.

## Lo que estos datos no permiten hacer

**El identificador de anuncio no enlaza entre trimestres.** Esperaba poder seguir
el mismo inmueble a lo largo de 2018, ver cuáles desaparecían (proxy de venta) y
cuáles bajaban de precio. Sería la validación fuerte: comprobar si un piso
marcado por debajo de sus comparables se vende antes.

No se puede. En la versión publicada, los 75.804 identificadores aparecen cada
uno en **un solo trimestre**. Las 19.011 filas repetidas lo son dentro del mismo
trimestre, con precios y coordenadas ligeramente distintos. La documentación del
paquete dice lo contrario, así que o el identificador se regeneró en el proceso
de anonimización, o la documentación no describe la versión distribuida.

Lo comprobé porque el resultado inicial parecía demasiado limpio, y una tabla de
transiciones con 0,0 % en las tres celdas no es un dato, es un aviso.

**Otras limitaciones:**

- El objetivo es el **precio pedido**, no el de cierre. El motor reproduce lo que
  pide un anuncio, no lo que vale el piso ni por cuánto se vendió.
- Los datos son de 2018. Ninguna cifra de nivel es trasladable a hoy.
- Los autores añadieron ruido aleatorio a coordenadas y precios por protección de
  datos. Eso pone un suelo al error alcanzable que no he cuantificado.
- El error del 12,0 % no se puede comparar con el 10,0 % del corpus sintético.
  Son objetivos distintos medidos sobre datos distintos. Compararlos sería
  exactamente el error de medir dos versiones con métodos diferentes.

## Lo que haría falta para cerrar el círculo

Precios de escritura a nivel de inmueble. No están en ningún conjunto abierto.
La vía realista es un acuerdo de acceso con quien los tenga, y ahí es donde una
inmobiliaria con histórico propio aporta lo que ningún dato público da.

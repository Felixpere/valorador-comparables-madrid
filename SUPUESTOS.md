# Supuestos y límites

Todo lo que hay aquí condiciona cómo hay que leer los resultados. Está también
en la hoja «Supuestos y fuentes» del Excel y en el pie del dashboard, para que
nadie lea una cifra sin ver al lado lo que esa cifra no dice.

---

## 1. Los anuncios son sintéticos

Los términos de uso de los portales inmobiliarios prohíben el scraping, y no hay
dataset público de anuncios de Madrid con licencia de uso libre. El corpus se
genera con `src/p00_generar_corpus.py`, semilla fija, reproducible.

**Qué está calibrado con dato real**: el nivel de precio de cada distrito, la
distribución de superficies dentro de cada distrito y el peso relativo de cada
distrito en el volumen de operaciones. Los tres salen de la Estadística Registral
Inmobiliaria de 2022 publicada por el Ayuntamiento de Madrid.

**Qué es inventado**: cada anuncio concreto, su redacción, y la dispersión
individual de precios alrededor de la media de su distrito.

**Consecuencia**: ninguna conclusión sobre el mercado real de Madrid se sostiene
sobre estos datos. Los precios que aparecen en el dashboard son verosímiles, no
son ciertos.

## 2. El factor de actualización 2022 → 2026

Los datos por distrito son de 2022. Para que la demo no muestre precios de hace
cuatro años se aplica un factor de **1,32**, derivado de la variación del valor
tasado de vivienda libre en España entre 4T2022 (~1.760 €/m²) y 1T2026
(2.315 €/m²) según el Ministerio de Vivienda y Agenda Urbana.

Es un supuesto fuerte y probablemente falso en el detalle: se aplica igual a los
21 distritos, y Madrid no se ha revalorizado de forma homogénea. Los distritos
centrales han subido más que la periferia.

**Por qué no contamina el resultado**: el motor compara cada inmueble contra
otros del mismo distrito. Un factor que multiplica a todo un distrito por igual
se cancela en la comparación. Afecta al nivel absoluto que se ve en pantalla, no
a la señal.

## 3. La referencia es el precio pedido, no el de cierre

La desviación mide la distancia entre lo que pide un inmueble y lo que piden los
comparables de su distrito. No mide descuento sobre valor de mercado real, que
exigiría precios de escritura.

Es la misma limitación que tiene el proyecto de coches, donde la validación
contra 2.100 anuncios usa como referencia el último precio pedido antes de
retirarse el anuncio, no el precio de cierre.

Un piso marcado por debajo de sus comparables **no es necesariamente una ganga**.
Puede tener una servidumbre, una ocupación, una derrama pendiente, un vecino
imposible, o simplemente estar bien valorado y ser el resto los que están caros.
Lo que la herramienta produce es una lista de llamadas que merece la pena hacer,
por orden.

## 4. Las desviaciones que el motor recupera están inyectadas

Al generar el corpus, a un 8 % de los anuncios se le resta un descuento
deliberado y a otro 8 % se le suma una prima. Que el motor recupere el 82 % de
los primeros demuestra que la mecánica funciona.

**No demuestra capacidad predictiva.** Es circular por construcción: encontramos
lo que nosotros mismos escondimos. Con datos reales no habría verdad de terreno
y habría que validar contra operaciones cerradas.

## 5. La etiqueta de fiabilidad no discrimina en este corpus

El motor clasifica cada valoración como fiabilidad alta, media o baja según
cuántos comparables tenga y cuánto se dispersen. El error mediano de valoración
sale **prácticamente igual en los tres niveles** (~10 %).

La razón es el propio generador: la dispersión individual que introduce es
homogénea, la misma en todos los segmentos. Con esa estructura, tener más
comparables no reduce el error, porque el error es irreducible por construcción.

Con datos reales la etiqueta sí debería discriminar, porque los segmentos
delgados son realmente más dispersos. Aquí no lo hace, y se dice en lugar de
retocar el generador para que la métrica quedara bien.

## 6. El motor de reglas parte con ventaja

El extractor por expresiones regulares acierta el 98 % de los campos porque las
reglas se escribieron mirando estas cinco plantillas. Es el sobreajuste clásico:
funciona hasta el día en que llega un formato nuevo, y entonces falla en
silencio. La cifra es real pero no es extrapolable.

## 7. Los coeficientes de ajuste

El ajuste por estado de conservación, orientación y ascensor se estima por
mínimos cuadrados sobre el logaritmo del €/m², reestimado cada mes con datos
anteriores. Si un mes no llega a 80 observaciones históricas, no se aplica
ajuste: los comparables se toman en crudo y la fila queda marcada.

Sobre este corpus, los coeficientes que recupera el modelo son por construcción
los que usó el generador. Con datos reales habría que reestimarlos y no hay
garantía de que fueran estables entre distritos ni en el tiempo.

## 8. Parámetros del motor

| Parámetro | Valor | Por qué |
|---|---|---|
| Banda de superficie | ±20 % | Compromiso entre parecido y tamaño de muestra |
| Ventana temporal | 270 días | Suficiente histórico sin arrastrar precios obsoletos |
| Mínimo de comparables | 5 | Por debajo, la mediana no es informativa |
| Umbral de aviso | −10 % | Arbitrario. La hoja «Umbral de aviso» del Excel muestra qué pasa al moverlo |

Todos viven en `src/config.py` y cambiarlos y volver a lanzar `run_pipeline.py`
regenera todo.

## 9. Protección de datos

No interviene ningún dato personal de vendedores ni de terceros en ninguna fase.
El corpus no contiene nombres, teléfonos, direcciones postales ni referencias
catastrales.

## 10. Lo que haría falta para convertir esto en algo real

1. Datos de operaciones cerradas, no de oferta. Sin eso no hay validación posible.
2. Un acuerdo de acceso a datos con quien los tenga, en lugar de scraping.
3. Reestimar los coeficientes de ajuste sobre datos reales y comprobar su
   estabilidad entre distritos y en el tiempo.
4. Granularidad de barrio, no de distrito. Un distrito de Madrid es demasiado
   grande y heterogéneo para ser una unidad de comparación.
5. Validación retrospectiva: entrenar con datos hasta una fecha y comprobar
   contra lo que pasó después.

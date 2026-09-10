# Supuestos y límites

Todo lo que hay aquí condiciona cómo hay que leer los resultados. Está también
en la hoja «Supuestos y fuentes» del Excel y en el pie de los dos dashboards,
para que nadie lea una cifra sin ver al lado lo que esa cifra no dice.

---

## 0. Cuál es cuál: el proyecto tiene dos vías de datos

Este documento cubre las dos, y **cada cifra pertenece a una sola**. Confundirlas
es el error que este documento existe para evitar.

| | **Vía real** | **Vía sintética** |
|---|---|---|
| Datos | `idealista18`: 94.815 anuncios de venta de Madrid, cuatro trimestres de 2018, licencia ODbL-1.0 | Corpus generado por `src/p00_generar_corpus.py`, calibrado con estadística registral |
| Unidad de comparación | Barrio (135) | Distrito (21) |
| Scripts | `src/r00`, `src/r01` | `src/p00`–`p06`, vía `run_pipeline.py` |
| Salida | `outputs/dashboard_real.html` | `outputs/valoraciones_madrid.xlsx`, `outputs/dashboard.html` |
| Para qué sirve | Validar el motor fuera de muestra y describir la estructura del mercado | Demostrar el paso de extracción con IA, que no se puede enseñar con datos que ya vienen en tabla |
| Qué **no** demuestra | Nada sobre el nivel de precios de hoy: es 2018 | Nada sobre el mercado real de Madrid: los anuncios son inventados |

Las secciones 1, 2, 4, 5, 6 y 7 son de la **vía sintética**. La sección 11 es de
la **vía real**. Las secciones 3, 8, 9 y 10 valen para las dos.

---

## 1. Los anuncios del corpus de extracción son sintéticos · *vía sintética*

Los términos de uso de los portales inmobiliarios prohíben el scraping, y no hay
dataset público de anuncios de Madrid **en texto libre** con licencia de uso
libre. El corpus se genera con `src/p00_generar_corpus.py`, semilla fija,
reproducible.

**Qué está calibrado con dato real**: el nivel de precio de cada distrito, la
distribución de superficies dentro de cada distrito y el peso relativo de cada
distrito en el volumen de operaciones. Los tres salen de la Estadística Registral
Inmobiliaria de 2022 publicada por el Ayuntamiento de Madrid.

**Qué es inventado**: cada anuncio concreto, su redacción, y la dispersión
individual de precios alrededor de la media de su distrito.

**Consecuencia**: ninguna conclusión sobre el mercado real de Madrid se sostiene
sobre estos datos. Los precios que aparecen en el dashboard sintético son
verosímiles, no son ciertos.

## 2. El factor de actualización 2022 → 2026 · *vía sintética*

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

## 3. La referencia es el precio pedido, no el de cierre · *las dos vías*

La desviación mide la distancia entre lo que pide un inmueble y lo que piden los
comparables de su zona. No mide descuento sobre valor de mercado real, que
exigiría precios de escritura.

Es la misma limitación que tiene el proyecto de coches, donde la validación
contra 2.100 anuncios usa como referencia el último precio pedido antes de
retirarse el anuncio, no el precio de cierre. *(Esa cifra viene de un proyecto
anterior y no es verificable desde este repositorio.)*

Un piso marcado por debajo de sus comparables **no es necesariamente una ganga**.
Puede tener una servidumbre, una ocupación, una derrama pendiente, un vecino
imposible, o simplemente estar bien valorado y ser el resto los que están caros.
Lo que la herramienta produce es una lista de llamadas que merece la pena hacer,
por orden.

## 4. Las desviaciones que el motor recupera están inyectadas · *vía sintética*

Al generar el corpus, a un 8 % de los anuncios se le resta un descuento
deliberado y a otro 8 % se le suma una prima. Que el motor recupere el 82 % de
los primeros demuestra que la mecánica funciona.

**No demuestra capacidad predictiva.** Es circular por construcción: encontramos
lo que nosotros mismos escondimos. Esa es exactamente la razón de ser de la vía
real, donde no hay verdad de terreno inyectada y la medición es fuera de muestra.

## 5. La etiqueta de fiabilidad no discrimina *en el corpus sintético*

El motor clasifica cada valoración como fiabilidad alta, media o baja según
cuántos comparables tenga y cuánto se dispersen. Sobre el corpus sintético el
error mediano sale **prácticamente igual en los tres niveles** (~10 %).

La razón es el propio generador: la dispersión individual que introduce es
homogénea, la misma en todos los segmentos. Con esa estructura, tener más
comparables no reduce el error, porque el error es irreducible por construcción.

**Sobre datos reales sí discrimina**, y así consta en la sección 11: 10,4 % de
error mediano en fiabilidad alta, 12,7 % en media y 15,9 % en baja. Las dos
afirmaciones son ciertas, cada una en su corpus. Si se citan juntas sin decir de
cuál es cada una, parecen una contradicción y no lo son.

## 6. El motor de reglas parte con ventaja · *vía sintética*

El extractor por expresiones regulares acierta el 98 % de los campos porque las
reglas se escribieron mirando estas cinco plantillas. Es el sobreajuste clásico:
funciona hasta el día en que llega un formato nuevo, y entonces falla en
silencio. La cifra es real pero no es extrapolable a documentos de verdad.

## 7. Los coeficientes de ajuste · *vía sintética*

El ajuste por estado de conservación, orientación y ascensor se estima por
mínimos cuadrados sobre el logaritmo del €/m², reestimado cada mes con datos
anteriores. Si un mes no llega a 80 observaciones históricas, no se aplica
ajuste: los comparables se toman en crudo y la fila queda marcada.

Sobre este corpus, los coeficientes que recupera el modelo son por construcción
los que usó el generador. Con datos reales habría que reestimarlos y no hay
garantía de que fueran estables entre zonas ni en el tiempo. Con los datos de
2018 están estimados y verificados uno a uno — ver la sección 11.

## 8. Parámetros del motor · *las dos vías*

| Parámetro | Valor | Por qué |
|---|---|---|
| Banda de superficie | ±20 % | Compromiso entre parecido y tamaño de muestra |
| Ventana temporal | 270 días | Suficiente histórico sin arrastrar precios obsoletos |
| Mínimo de comparables | 5 | Por debajo, la mediana no es informativa |
| Umbral de aviso | −10 % | Arbitrario. La hoja «Umbral de aviso» del Excel muestra qué pasa al moverlo |

Todos viven en `src/config.py` y cambiarlos y volver a lanzar `run_pipeline.py`
regenera todo.

## 9. Protección de datos · *las dos vías*

No interviene ningún dato personal de vendedores ni de terceros en ninguna fase.
El corpus sintético no contiene nombres, teléfonos, direcciones postales ni
referencias catastrales. El conjunto de la vía real viene ya anonimizado por sus
autores, y no se redistribuye desde este repositorio.

## 10. Control de fugas de información · *las dos vías*

El inmueble evaluado nunca entra en sus propios comparables, ni directamente ni a
través de los coeficientes de ajuste, y nunca se miran datos posteriores a la
fecha que se evalúa. En la vía real los anuncios se parten en dos por sorteo con
semilla fija: de una mitad salen los comparables y se estiman los coeficientes, y
sobre la otra se mide.

---

## 11. La vía real: qué se midió y qué no · *vía real*

**Los datos.** `idealista18`, 94.815 anuncios de venta de Madrid de los cuatro
trimestres de 2018, licencia ODbL-1.0. La medición se hace sobre los **22.643
anuncios que el motor no había visto**. Unidad de comparación: el barrio, 135 en
total.

**Lo que sale.** Error mediano del **12,0 %**, con el **43,0 %** de las
estimaciones dentro de ±10 %, cobertura del **96,1 %** y sesgo de **−0,1 %**.
Frente a la mediana simple del barrio, que da **15,2 %**, y frente a no
distinguir zona, que da **34,3 %**.

**Cómo hay que leerlo, y es la lectura honesta.** La mejora sobre la mediana del
barrio es de tres puntos: modesta. El salto grande es de 34,3 % a 15,2 %, y ese
salto no es mérito del motor, es saber en qué barrio está el piso. Se dice así,
en ese orden, en todos los documentos del proyecto.

**La etiqueta de fiabilidad aquí sí cumple**: 10,4 % de error mediano en alta,
12,7 % en media, 15,9 % en baja.

**Estructura del mercado.** Del barrio más caro al más barato hay un factor
**6,4**: Recoletos a 7.440 €/m² y San Cristóbal a 1.169 €/m². Son niveles de
2018 y hoy no valen; lo que sobrevive al paso del tiempo es el orden.

### Lo que esta vía no demuestra

1. **No hay validación contra precio de cierre.** No existen precios de escritura
   por inmueble en ningún conjunto abierto. Sería la validación fuerte y no se ha
   podido hacer.
2. **No se puede seguir un piso a lo largo del tiempo.** Los 75.804
   identificadores aparecen cada uno en un solo trimestre, así que no se puede
   comprobar si lo marcado barato desaparece antes. Se detectó porque la tabla de
   transiciones daba 0,0 % tres veces seguidas: un cero perfecto repetido no es un
   dato, es un aviso.
3. **Los datos son de 2018.** Ningún nivel de precio es trasladable a hoy.
4. **Los autores añadieron ruido aleatorio** a coordenadas y precios por
   protección de datos. Eso pone un suelo al error alcanzable que **no está
   cuantificado**.
5. **Dos coeficientes salían con el signo contrario al esperado** — jardín y
   calidad catastral, ambos en −1,4 %. Se verificó el 5 de septiembre con
   `src/r04_diagnostico_coeficientes.py` y **la sospecha de colinealidad resultó
   falsa**: el VIF más alto de todo el modelo es 2,30 y ninguna correlación entre
   regresores llega a 0,7. Los dos casos resultaron ser cosas distintas.

   **La calidad catastral no era una anomalía: la variable estaba leída al
   revés.** `CADASTRALQUALITYID` no es una nota, es la categoría catastral, y
   empeora según crece el número. Corregida, sale en **+1,4 %**, y ninguna
   valoración se mueve.

   **El jardín se queda en −1,4 %, y es un efecto real.** Aislado vale +10,1 %;
   el signo cambia al controlar por piscina, con la que va casi siempre junta. Lo
   *probado* es que no viene del barrio ni de la superficie. Que «jardín y nada
   más» marque promoción periférica es una **interpretación del patrón, no una
   medición**: no hay variable que separe jardín privado de zona común. Detalle en
   `docs/validacion_2018.md`.

---

## 12. Lo que haría falta para convertir esto en algo real

1. Datos de operaciones cerradas, no de oferta. Sin eso no hay validación fuerte.
2. Un acuerdo de acceso a datos con quien los tenga, en lugar de scraping.
3. Reestimar los coeficientes de ajuste sobre datos reales recientes y comprobar
   su estabilidad entre barrios y en el tiempo. Los de 2018 ya están verificados,
   incluidos los dos que estuvieron en cuarentena, pero nada garantiza que se
   mantengan con datos de otro año.
4. Cuantificar el suelo de error que impone el ruido añadido al conjunto de 2018.
5. Validación retrospectiva de verdad: entrenar con datos hasta una fecha y
   comprobar contra lo que pasó después, con un conjunto que permita seguir el
   mismo inmueble.

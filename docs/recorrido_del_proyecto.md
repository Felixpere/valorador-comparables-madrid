# El proyecto de principio a fin

Siete minutos de lectura. Sin tecnicismos. Todas las cifras salen de los ficheros
de resultados del repositorio; ninguna está puesta a mano ni derivada a ojo.

---

## El problema

En cualquier equipo que trabaje con inmuebles hay información que llega como
**documento suelto**: un correo, un mensaje, una ficha, un PDF trimestral. Y hay
alguien que la pasa a mano a una hoja de cálculo, semana tras semana, sin que
quede rastro de cómo se llegó a cada número.

**Esto es un circuito que hace ese recorrido entero por su cuenta.** Entra texto
libre y salen un Excel y un panel listos para abrir en una reunión: saca los
datos del texto, los limpia, calcula, mide su propio acierto y publica. Se lanza
con una orden, y también solo, **cada lunes y cada vez que alguien toca el
código**.

Lo que lo distingue de un proceso montado a mano es qué hace cuando algo va mal:
**si detecta que un número no se sostiene, se detiene y no publica nada.**

## Por qué el ejemplo es vivienda

Un circuito así no se demuestra en abstracto: hacen falta datos reales contra los
que medir si acierta.

Por eso el ejemplo es la **valoración de pisos por comparables**. En vivienda
existe el único conjunto de datos abierto, con licencia libre y detalle inmueble
a inmueble, que cubre un mercado entero: 94.815 anuncios de Madrid publicados por
idealista junto a dos universidades. En oficinas o logística ese dato no existe
en abierto —lo publican las consultoras en PDF, cada una con su definición—, así
que allí no hay forma de comprobar si un resultado es bueno.

Vivienda es, sencillamente, **el sector donde se puede demostrar que el circuito
acierta**. Lo que queda demostrado es el método, no el mercado.

La pregunta que responde el ejemplo: **¿lo que piden por este piso está en línea
con lo que piden pisos parecidos?** Fácil de enunciar y difícil de contestar
bien. ¿Parecidos en qué? ¿Y si el nuestro tiene ascensor y los otros no?

## Qué hace el sistema con cada piso

Para cada piso busca sus **comparables**: pisos del mismo barrio, del mismo
trimestre, con una superficie parecida (hasta un 20 % arriba o abajo) y con al
menos cinco casos. Si no encuentra cinco, no da un número: dice que no puede.

Después corrige las diferencias. Un piso con ascensor no vale lo mismo que uno
sin él, y el sistema sabe cuánto pesa cada característica porque lo ha calculado
a partir de los propios anuncios, no porque alguien lo haya decidido.

Con eso calcula un precio de referencia y lo compara con lo que se pide. El
resultado no es un veredicto, es **una lista de llamadas ordenada**: estos son
los que más se apartan de sus comparables, empieza por aquí.

## Un caso real, entero

Un piso de **73 m² en Arapiles**. Piden **313.000 €**.

El sistema encuentra **24 comparables**, ajusta cada uno a las condiciones de ese
piso y calcula que debería estar en torno a **376.817 €**. Se pide un **16,9 %
menos** de lo que dicen sus comparables.

Eso **no significa que sea una ganga**. Significa que merece una llamada para
averiguar por qué. Puede tener una derrama pendiente, un inquilino dentro, una
servidumbre, o estar bien de precio y ser los demás los que están caros. Lo que
aporta el sistema es que esa llamada aparece la primera en la lista, y que se
puede ver exactamente de dónde sale el número.

## Cómo sabemos que funciona

Aquí está el trabajo de verdad, y es lo que distingue esto de una hoja de cálculo
con buena pinta.

**Se probó con anuncios que el sistema nunca había visto.** Se partieron 75.476
anuncios reales de Madrid de 2018 en dos montones: con el 70 % aprendió, y el
30 % restante —**22.643 anuncios**— se guardó aparte. Después se le pidió que
estimara el valor de esos 22.643 sin enseñarle el precio, y se comparó con lo que
pedían de verdad.

Es la diferencia entre estudiar para un examen y corregirte tú mismo con las
respuestas delante.

**Resultado: se equivoca un 12,0 %.** En la mitad de los casos falla menos de eso
y en la otra mitad más. Cuatro de cada diez estimaciones se quedan a menos de un
10 % del precio real, y siete de cada diez a menos de un 20 %.

**Y aquí viene la parte incómoda, que contamos igual.** Comparamos el sistema con
el método más simple que se nos ocurrió: coger el precio por metro cuadrado
típico del barrio y multiplicarlo por los metros. Sin ajustar nada.

| Método | Se equivoca un |
|---|---|
| El sistema completo | **12,0 %** |
| El precio típico del barrio, sin más | 15,2 % |
| El precio típico de Madrid, sin mirar la zona | 34,3 % |

La lectura honesta: **el sistema mejora poco al método simple**, tres puntos. La
mayor parte del acierto viene de saber en qué barrio está el piso, no de la
maquinaria. Lo que sí marca una diferencia enorme es distinguir la zona: sin
hacerlo, el error se triplica.

Decimos esto porque es verdad, y porque un sistema que no sabe cuánto mejora a la
alternativa barata no se puede defender delante de nadie.

**El sistema avisa cuando no está seguro.** En el 96,1 % de los casos da un
número; en el resto se niega y explica por qué. Además etiqueta cada valoración
según la confianza que merece, y esa etiqueta funciona:

| Confianza | Se equivoca un |
|---|---|
| Alta | 10,4 % |
| Media | 12,7 % |
| Baja | 15,9 % |

Sirve para saber de qué filas fiarse.

## La otra mitad: leer los anuncios

Los anuncios llegan como texto suelto: un correo, un mensaje de WhatsApp, una
ficha. Alguien tiene que sacar de ahí los metros, el precio, la planta y si tiene
ascensor.

El sistema lo hace de dos maneras y **mide las dos por separado**: con reglas
fijas escritas a mano, y con inteligencia artificial. Sobre los mismos 25
anuncios, la IA acertó los 250 campos y las reglas fallaron uno.

**Ese resultado sólo apareció al descubrir que lo medíamos mal.** La IA salía
peor por dos fallos que eran de acentuación: escribió «Tetuán» y «Chamartín»
donde la respuesta estaba guardada sin tilde, y el propio sistema quita las
tildes en el paso siguiente, así que son el mismo dato. El medidor comparaba con
un criterio más estricto que el del sistema, y eso castigaba al motor que escribe
español natural y premiaba al que copia de una lista. Al corregirlo, **el
resultado cambió a favor de la IA**: lo contamos precisamente porque el arreglo
beneficia a una de las partes.

**Aun así no concluimos que la IA sea mejor.** Un fallo de diferencia sobre 250 no
distingue a nadie, y además las reglas juegan en casa: están escritas mirando
exactamente esos formatos de texto, así que aciertan mucho aquí y se romperían
con un formato nuevo. Ahí es donde la IA no necesita que nadie toque nada.

## Lo que este trabajo NO puede afirmar

Esta sección es tan importante como las anteriores.

**El precio de referencia es el que se PIDE, no el precio al que se vende.** El sistema
reproduce lo que pide un anuncio, no lo que vale el piso ni por cuánto se cerró
la operación. Los precios de escritura por inmueble no están en ningún dato
público. Para cerrar el círculo haría falta el histórico de una inmobiliaria.

**Los datos son de 2018.** Los niveles de precio de entonces no son los de hoy.
Lo que sí sigue valiendo es el **orden**: del barrio más caro de Madrid
(Recoletos, 7.440 €/m² en 2018) al más barato (San Cristóbal, 1.169 €/m²) hay un
factor de **6,4**, y esa estructura cambia despacio.

**Una parte de la demostración usa anuncios inventados.** Los portales
inmobiliarios prohíben en sus condiciones que se descarguen sus anuncios, así que
para enseñar cómo se leen textos libres se generaron 2.000 anuncios artificiales.
Están declarados como tales en todas partes. Los anuncios reales de Madrid, los
94.815, sí son reales: los publicó idealista junto a dos universidades como datos
abiertos, con licencia que permite usarlos citando la fuente.

**No hay ningún dato personal** de vendedores ni de terceros en ninguna fase.

## Cómo está construido para que sea creíble

Cuatro decisiones que sostienen todo lo anterior:

**Un piso nunca se valora consigo mismo.** Ni con datos posteriores a la fecha
que se está evaluando. Si el sistema detecta que eso ha pasado, **se detiene y no
publica nada**. Prefiere no entregar a entregar un número que no se sostiene.

**Toda cifra que se enseña sale del código**, no de haberla tecleado en un
informe. Hubo un momento en que no era así, y las cifras escritas a mano se
quedaron viejas sin que saltara nada. Ahora hay 54 comprobaciones automáticas, y
una de ellas verifica que cada número del panel coincide con el resultado del que
dice venir.

**Cada valoración se puede abrir entera**: qué comparables se usaron, cuáles se
descartaron y por qué, y qué ajuste se aplicó a cada uno.

**Los límites van dentro del entregable, no en un anexo.** En el propio Excel, en
rojo y antes de la primera tabla, pone que los datos son de 2018 y que se mide el
precio pedido y no el de venta.

## Lo que falta

Se dice en voz alta porque un pendiente declarado suma y uno escondido resta:

- Falta comparar contra el valor de referencia del Catastro.
- Hay un código del Catastro, en dos de sus diez niveles, cuyo significado no
  hemos podido confirmar. Afecta al 2,3 % de los datos y no cambia nada
  material, pero sigue sin resolverse.
- La comparación entre los dos métodos de lectura de anuncios se hizo con 25
  documentos. Son pocos para concluir nada.

---

**En una frase:** un circuito que lleva un documento suelto hasta un Excel y un
panel terminados, que se actualiza solo, que sabe cuánto se equivoca, que avisa
cuando no puede responder y que prefiere no publicar antes que publicar un número
que no se sostiene.

La valoración de vivienda es **la prueba de que funciona**, no el destino: era el
sector donde había datos abiertos con los que medir el acierto de verdad. El
recorrido —sacar datos de un texto, limpiarlos declarando lo que se aparta,
calcular, medirse contra alternativas más simples y publicar con los límites
delante— no cambia el día que la entrada sea otro tipo de documento. Cambia el
contenido; el método es el mismo, y es lo que aquí queda demostrado.

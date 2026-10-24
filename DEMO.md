# Guion de la demo · 10 minutos

Para enseñar la herramienta a una agente inmobiliaria de Madrid, compartiendo
pantalla. Objetivo: que vea qué hace con pisos suyos, que vea dónde falla, y
proponerle probarla con los precios de cierre de su oficina.

## Los tiempos: 30 minutos, 10 de demo y 20 de conversación

Lo que yo digo suma unos 10 minutos. El resto es ella hablando, y eso es lo que
quiero: cada pregunta abierta está puesta para que hable. La tabla da, por
tramo, lo que dura el guion, cuánto es esperable que se alargue, y **por qué
minuto debería ir** si la conversación va por el medio de lo esperable.

| Tramo | Guion | Conversación esperable | Debería acabar hacia | Se alarga |
|---|---|---|---|---|
| 1. La cobertura | 0:30 | 0 – 1 min (si pregunta por Alcorcón) | 1:00 | poco |
| 2. El problema | 0:45 | **2 – 4 min**: la invito a hablar | 4:30 | **sí** |
| 3. Cómo funciona, en una frase | 0:30 | 0 – 1 min | 5:30 | poco |
| 4. Goya, en vivo | 1:45 | **2 – 3 min**: «¿alta, baja o razonable?» | 10:00 | **sí** |
| 5. La barra | 1:00 | **2 – 4 min**: «¿cuánto se negocia hoy?» | 14:00 | **sí** |
| 6. El mapa | 0:45 | 0 – 1 min | 15:00 | poco |
| 7. Trafalgar | 0:45 | 1 – 2 min: los garajes y el estado | 17:30 | algo |
| 8. Arapiles | 1:00 | **2 – 4 min**: que explique su precio | 21:30 | **sí** |
| 9. La Elipa | 0:30 | 0 | 22:00 | no |
| 10. La propuesta | 1:15 | **2 – 3 min**: formato, datos, fechas | 25:30 | **sí** |
| 11. Preguntas y cierre | 1:30 | 2 – 3 min | 30:00 | sí |

Con la conversación en su mínimo, la llamada dura unos 22 minutos y sobran 8.
Con todo en su máximo, dura 37 y faltan 7. **El margen son esos 7 minutos, y
se gastan en los tramos 2, 4 y 5**: si ella se extiende ahí, lo que se come es
el final, que es lo que no puede faltar.

**Tres relojes de control:**

- **A las 14:00 debería haber terminado la barra.** Si aún estoy en Goya: el
  mapa se queda en diez segundos y Trafalgar en un solo botón.
- **A las 19:00 debería haber terminado Trafalgar.** Si no: fuera La Elipa y
  fuera las preguntas del final (van por WhatsApp).
- **A las 24:00 tengo que estar empezando Arapiles.** Es el límite: Arapiles con
  su conversación, la propuesta con su petición y el cierre necesitan 6
  minutos. Si a las 24:00 no he llegado, salto a Arapiles desde donde esté,
  con lo que haya en pantalla.

**Plan de emergencia, si va todo pasado** (es un plan de emergencia, no la
previsión): recorto en este orden las preguntas (11) → La Elipa (9) → el mapa
(6: diez segundos y sigo) → Trafalgar (7: sólo el botón de buen estado) → cómo
funciona (3: lo digo dentro del problema).

**Lo que no se recorta nunca:** la cobertura (1), Arapiles (8) y la petición
del final (10): la llamada tiene que acabar con «¿me pasas tus cierres?» aunque
sea en treinta segundos.

## Frase preparada: cuando diga «lo publicado no es lo cerrado»

Lo ha dicho dos veces y lo va a decir una tercera. La respuesta, tal cual:

> «Tienes razón, y es justo por eso por lo que está esa barra: arriba lo que se
> pide, abajo lo que se firma. Lo que yo no tengo es lo que se firma piso a
> piso. Eso lo tienes tú.»

Si lo dice antes de llegar a la barra y ya hay un piso en pantalla, bajo a la
barra en ese momento y la enseño; si no, «ahora te la enseño» y sigo el orden.

## Antes de la llamada (15 minutos antes)

1. **Cierra la demo vieja.** Desde el 19 de octubre hay una instancia abierta
   en `localhost:8501` con código antiguo (Ctrl+C en su terminal). Si no se
   cierra, no salen ni la barra, ni el mapa, ni los pisos de la oficina.
2. Arranca la nueva, desde la raíz del repositorio:

   ```powershell
   cd C:\Users\user\proyectos\valorador-comparables-madrid
   .venv\Scripts\python -m streamlit run demo\app.py
   ```

   **Mira en la terminal la línea `Local URL: http://localhost:XXXX` y abre
   ese puerto.** Si el cierre del paso 1 falló, Streamlit salta al 8502 (o al
   8503) sin avisar, y el 8501 seguiría enseñando la demo vieja. El puerto bueno
   es el que diga la terminal de la instancia que acabas de arrancar. La
   primera vez en un equipo puede pedir un correo en la terminal: Enter y sigue.
3. **Comprueba que sale la fila azul «Pisos de la oficina»** con cinco botones:
   Goya, Trafalgar · buen estado, Trafalgar · a reformar, Arapiles y La Elipa.
   Si no sale, falta o está roto `demo/ejemplos_locales.json` (es local, git lo
   ignora).
4. **Pulsa todos los botones, los tres inventados y los cinco de la oficina**, y
   en cada uno espera a que cargue el mapa (unos diez segundos; el fondo viene de
   internet). Así en la llamada todo sale al instante.
5. Comparte **sólo la ventana del navegador**, no la pantalla entera.
6. Ten a mano `data/agencia/plantilla_cierres.csv` por si pide ver el formato.

## 1 · 0:00 – 0:30 · La cobertura — no se recorta

Lo primero que digo, antes de enseñar nada:

> «Antes de empezar, para que no haya sorpresas: esto cubre Madrid capital, sus
> 21 distritos. No cubre Alcorcón ni el resto de la Comunidad. Para llegar ahí
> hacen falta datos piso a piso que hoy no son públicos, y eso enlaza con lo que
> te quiero proponer al final.»

## 2 · 0:30 – 1:15 · El problema

> «Hoy, para saber cuánto vale un piso, se miran anuncios parecidos a ojo, en
> una hoja de cálculo, y no queda rastro de por qué se llegó a la cifra. Y lo que
> se mira es lo que se **pide**, no lo que se **firma**. Tú sabes mejor que nadie
> que no es lo mismo.»

Déjala hablar si quiere. Lo que diga aquí es lo más valioso de la llamada. Si
aquí suelta lo de «lo publicado no es lo cerrado», la frase preparada.

## 3 · 1:15 – 1:45 · Cómo funciona, en una frase

> «Busca en el mismo barrio pisos de tamaño parecido, corrige cada uno por sus
> diferencias con el tuyo —estado, ascensor, planta— y se queda con el valor del
> medio. Luego lo lleva a precios de hoy con datos públicos de escrituras.»

## 4 · 1:45 – 3:30 · Goya, en vivo

Pulsa **Goya**. Es un piso de su oficina, firmado por ella, y la herramienta da
casi lo mismo que ellos: la diferencia es de un **−2 %**.

- La nota azul lleva el precio publicado; la tarjeta de la izquierda, el
  estimado. Que mire los dos números: no hace falta decirlos.
- Antes de explicar nada: **«¿La cifra te parece alta, baja o razonable?»** Que
  reaccione ella primero.
- Luego las **tres tarjetas**: anuncio estimado, firma estimada (un rango) y
  error típico.

Frase para el error, tal cual:

> «Lo probamos con 22.643 anuncios reales de 2018 que el modelo no había visto.
> Valoró el 96 %, y en la mitad de esos se quedó a menos de un 12 % del precio
> pedido; en la otra mitad, más lejos. Es una referencia rápida, no una tasación.»

Si pregunta por hoy: ese 12 % es de 2018 y sobre precio pedido. Cuánto se
equivoca con precios de hoy o de firma **no está medido**; para medirlo hacen
falta, precisamente, cierres reales.

## 5 · 3:30 – 4:30 · La barra: lo publicado no es lo cerrado

Baja a la barra. El título ya lo dice: «Lo publicado no es lo cerrado».

- **La raya azul** es el precio de anuncio estimado; **la franja clara**, su
  margen: en la prueba de 2018, la mitad de los precios pedidos quedó dentro.
- **La franja verde** es la firma estimada. Sale de datos públicos:

> «El Registro publica cuánto se escrituró de media en cada distrito, pero no
> piso a piso. Comparando eso con los anuncios de 2018, lo escriturado queda
> desde un 16 % por debajo de lo anunciado, en Villaverde, hasta un 7 % por
> encima, en Hortaleza, según el distrito y según cómo se mida. Por eso la
> firma es un rango, y no por prudencia: con datos públicos no se puede hacer
> mejor. Y esa diferencia no es sólo negociación: mezcla pisos que nunca se
> vendieron, pisos distintos y el tiempo que tarda una escritura en
> inscribirse.»

El dato: `data/real/factores_distrito.csv`, columnas `brecha_min` y
`brecha_max`, que calcula `src/r06_actualizacion_cierre.py` como (anuncio −
escritura) / anuncio. Extremos: −7,3 % en Hortaleza y +16,4 % en Villaverde.
Signo positivo = se escrituró por debajo del anuncio.

Y que el rango verde **sólo** recoge esa duda: el error del modelo va además.

Pregunta abierta aquí: **«¿Cuánto se negocia de verdad hoy en tu zona?»**

Si sale el tema, en la recámara: en **Hortaleza** los datos públicos dicen que
se escrituró de media *por encima* de lo anunciado, y en **Barajas**, más o
menos lo mismo. Lo más probable no es que allí no se negocie, sino que lo que se
vende no se parece a lo que se anuncia; con estos datos no se puede saber cuál
de las dos cosas es. Lo cuento hablando, sin pantalla.

## 6 · 4:30 – 5:15 · El mapa

Baja al mapa, «Dónde están».

> «Estos son todos los pisos del barrio de los que sale la cifra; en azul, los
> ocho de la tabla. Si pasas el ratón por uno, ves sus metros, lo que se pedía
> en 2018 y lo que valdría si fuera como el tuyo, hoy. No hay nada escondido:
> cada número se puede seguir hasta el anuncio del que sale.»

Pasa el ratón por un punto azul y por uno gris. Si voy pasado: diez segundos,
«esto es de dónde sale», y sigo.

## 7 · 5:15 – 6:00 · Trafalgar

Pulsa **Trafalgar · buen estado**. Aquí la herramienta queda por debajo de lo
publicado (**+6 %** el anuncio sobre lo estimado) y la nota azul dice por qué
no se puede comparar sin más: **el anuncio incluye dos plazas de garaje, que la
herramienta no valora**, y el estado no viene en el anuncio.

> «La cifra es sólo por el piso; los garajes no los cuenta. Y como el anuncio no
> dice el estado, lo he puesto en buen estado. Mira lo que pasa si lo pongo a
> reformar.»

Pulsa **Trafalgar · a reformar**: el anuncio queda un **+18 %** por encima.

Pregunta: **«¿Cuánto valen dos garajes ahí? ¿Y en qué estado está de verdad?»**
Con sus dos respuestas, la diferencia se explica o no se explica; es ella quien
lo sabe.

Si voy pasado: sólo el botón de buen estado y la frase de los garajes.

## 8 · 6:00 – 7:00 · Arapiles — no se recorta

Pulsa **Arapiles**. Aquí lo publicado queda un **27 % por debajo** de lo que
estima la herramienta: fuera del margen del 12 %. **No digo que el piso esté
barato.** Digo esto, tal cual:

> «Aquí la herramienta y vosotros no coincidís, y de largo. No sé cuál de los
> dos tiene razón: puede que esté puesto para vender rápido, puede que una
> reforma a estrenar valga más de lo que el modelo capta, o puede que el modelo
> se equivoque. Eso no lo resuelven los datos públicos. Lo resuelven tus
> cierres: con el precio al que se firmó, sabríamos quién acertó.»

Y me callo. Es el momento de la llamada: la diferencia es el argumento de la
propuesta, no un reproche. Si se pone a explicar el precio, que explique: todo
lo que diga es lo que la herramienta no sabe.

## 9 · 7:00 – 7:30 · La Elipa: se niega a inventar

Pulsa **La Elipa (Ventas)**. Sale la nota y, debajo, el aviso: no hay pisos
suficientemente parecidos (hacen falta al menos 5).

> «Esto no es un fallo. Con tres pisos parecidos, prefiere no dar un número a
> dar uno que no se sostiene. Si os parece poco, es que es poco.»

## 10 · 7:30 – 8:45 · La propuesta — la petición no se recorta

> «Lo que lo convertiría en algo útil para vosotros son vuestros cierres: para
> cada piso vendido, el último precio anunciado y el de la escritura. Desde 10
> operaciones en un distrito, el rango de firma deja de salir de una media de
> 2018 y pasa a salir de vuestros cierres, y la pantalla lo dice. Con más
> operaciones, el rango depende menos de cada una.»

- Formato: una fila por operación, siete columnas (distrito, m², fechas de
  publicación y firma, precio inicial, precio final, precio de escritura).
- **Sin datos personales**: ni nombres, ni direcciones, ni referencias
  catastrales. Si llega una columna así, el programa se niega a cargarla.
- Se quedan en su equipo o en el mío, fuera del repositorio público.
- Y es el camino para que cubra Alcorcón y el oeste: hoy no hay dato público
  piso a piso ahí; sus cierres sí lo son.

**La petición, en treinta segundos si hace falta:** «Una prueba con los cierres
de los últimos 12 meses. Te enseño el resultado distrito a distrito, también
donde salga peor, y empezamos por Arapiles.»

## 11 · 8:45 – 10:00 · Preguntas y cierre

Las que quepan; el resto, por WhatsApp después.

1. ¿Cuánto se suele negociar hoy en tus zonas, y cuánto ha cambiado desde 2018?
2. ¿Qué miras tú que esto no mira? (orientación, reforma reciente, vistas, comunidad…)
3. ¿Cuántas operaciones cerráis al año, y en qué distritos?
4. ¿Guardáis el primer precio anunciado y las rebajas, o sólo el último?
5. ¿Para qué lo usaríais: captar (enseñárselo al propietario), fijar el precio
   de salida, o justificar una rebaja?
6. ¿Cómo justifican hoy el precio tus agentes delante del propietario?

Cierre: quedar en una fecha para que me pase los cierres, no en «ya te digo».

## Si algo falla

- **La app no arranca**: comprueba que existe `data/real/madrid_2018.csv`
  (`python src/r00_cargar_idealista18.py`) y `data/real/factores_distrito.csv`
  (`python src/r06_actualizacion_cierre.py`).
- **No sale la fila «Pisos de la oficina»**: falta o está mal formado
  `demo/ejemplos_locales.json`. La demo sigue con los tres inventados; el guion
  vale igual con Chamberí · Trafalgar (90 m²) en el papel de Goya, sin la
  comparación con lo publicado.
- **El mapa sale en blanco**: sin internet no carga el fondo; los puntos y el
  tooltip se ven igual.
- **«No hay pisos suficientemente parecidos»** en un piso que no es La Elipa: no
  es un error, es la herramienta negándose a inventar. Cuéntalo así y cambia la
  superficie o el barrio.
- **Plan B**: el panel de validación publicado,
  `entregables/dashboard_real.html`, se abre sin instalar nada.

## Lo que no hay que decir

- Que el modelo predice el precio de **venta**. Aprende de precios **pedidos**.
- Que el descuento es «el margen de negociación». Es una brecha que lo contiene.
- Que es una tasación.
- Que un piso de la oficina «está caro» o «está barato». Se dice que la
  herramienta y ellos no coinciden, y que sólo sus cierres dicen quién acierta.
- Que se actualiza sola cada semana, que la IA lee anuncios reales del mercado,
  o que es mejor que «los métodos habituales». Nada de eso está medido así.

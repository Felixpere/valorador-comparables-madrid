# Guion de la demo · 10 minutos

Para enseñar la herramienta a una agente inmobiliaria de Madrid, compartiendo
pantalla. Objetivo: que vea qué hace, que vea dónde falla, y proponerle probarla
con precios de cierre de su agencia.

## Lo primero: la cobertura

**La herramienta cubre Madrid capital: sus 21 distritos y 135 barrios. No cubre
Alcorcón ni el resto de municipios de la Comunidad.** Lo digo yo, al empezar la
llamada, antes de enseñar nada. Así no hay sorpresas si piensa probarla con un
piso suyo de fuera de Madrid capital.

> «Antes de empezar, para que no haya sorpresas: esto cubre Madrid capital, sus
> 21 distritos. No cubre Alcorcón ni el resto de la Comunidad. Para llegar ahí
> hacen falta datos piso a piso que hoy no son públicos, y eso enlaza con lo que
> te quiero proponer al final.»

## Antes de la llamada (15 minutos antes)

```powershell
cd C:\Users\user\proyectos\valorador-comparables-madrid
.venv\Scripts\python -m streamlit run demo\app.py
```

- **Si ya había una demo abierta de otro día, ciérrala antes** (Ctrl+C en su
  terminal) y arráncala de nuevo: Streamlit guarda en memoria el código que
  cargó al arrancar y no enseñaría lo añadido después.
- Se abre en el navegador (`http://localhost:8501`). Tarda unos 3 segundos en
  cargar los anuncios. La primera vez que se usa Streamlit en un equipo puede
  pedir un correo en la terminal: Enter y sigue.
- Pulsa los tres ejemplos una vez, para que todo esté en memoria.
- Comparte **sólo la ventana del navegador**, no la pantalla entera.
- Ten a mano `data/agencia/plantilla_cierres.csv` por si pide ver el formato.

## 0:00 – 0:30 · La cobertura

La frase de arriba, «Lo primero: la cobertura». Es lo primero que digo.

## 0:30 – 1:30 · El problema

> «Hoy, para saber cuánto vale un piso, se miran anuncios parecidos a ojo, en
> una hoja de cálculo, y no queda rastro de por qué se llegó a la cifra. Y lo que
> se mira es lo que se **pide**, no lo que se **firma**. Tú sabes mejor que nadie
> que no es lo mismo.»

Déjala hablar si quiere. Lo que diga aquí es lo más valioso de la llamada.

## 1:30 – 2:30 · Cómo funciona, en una frase

> «Busca en el mismo barrio pisos de tamaño parecido, corrige cada uno por sus
> diferencias con el tuyo —estado, ascensor, planta— y se queda con el valor del
> medio. Luego lo lleva a precios de hoy con datos públicos de escrituras.»

## 2:30 – 5:30 · Ejemplo en vivo

1. **Chamberí · Trafalgar** (90 m², 3 habitaciones, buen estado, con ascensor).
   - Señala las **tres cifras**: anuncio, firma (rango) y margen de error.
   - Baja a la tabla: «estos son los pisos con los que compara; la última
     columna es lo que valdría cada uno si fuera como el tuyo, hoy».
2. **Cambia algo en directo**: quita el ascensor, o ponlo «a reformar». La cifra
   se mueve al momento. Pregúntale si el sentido y el tamaño del cambio le
   parecen razonables.
3. **Carabanchel · Vista Alegre** (70 m², a reformar, sin ascensor): otra zona,
   otro orden de precio, y aquí el rango de firma es más ancho.
4. Si queda tiempo, **Tetuán · Bellas Vistas**.

Frase para el margen de error, tal cual:

> «Lo probamos con 22.643 anuncios reales de 2018 que el modelo no había visto.
> Valoró el 96 %, y en la mitad de esos se quedó a menos de un 12 % del precio
> pedido; en la otra mitad, más lejos. Es una referencia rápida, no una tasación.»

Si pregunta por hoy: ese 12 % es de 2018 y sobre precio pedido. Cuánto se
equivoca con precios de hoy o de firma **no está medido**; para medirlo hacen
falta, precisamente, cierres reales.

## 5:30 – 7:30 · Precio de cierre: lo que no se puede saber con datos públicos

Abre «Cómo se llega a la cifra, paso a paso».

> «El precio de firma es un **rango**, y no por prudencia: con datos públicos no
> se puede hacer mejor. El Registro publica cuánto se escrituró de media en cada
> distrito, pero no piso a piso. Comparando eso con los anuncios de 2018, la
> diferencia va de un 16 % menos a un 7 % más, según el distrito y según cómo se
> mida. Y esa diferencia no es sólo negociación: mezcla pisos que nunca se
> vendieron, pisos distintos y el tiempo que tarda una escritura en
> inscribirse.»

Y que el rango de firma de la pantalla **sólo** recoge esa duda: el error del
modelo va además.

Pregunta abierta aquí: **«¿Cuánto se negocia de verdad hoy en tu zona?»**

Si sale el tema, ten este dato en la recámara: en **Hortaleza** los datos
públicos dicen que se escrituró de media *por encima* de lo anunciado, y en
**Barajas**, más o menos lo mismo. Lo más probable no es que allí no se negocie,
sino que lo que se vende no se parece a lo que se anuncia; con estos datos no se
puede saber cuál de las dos cosas es. Es el mejor ejemplo de por qué hacen falta
cierres reales.

## 7:30 – 9:00 · Qué le propongo

> «Lo que lo convertiría en algo útil para ti son tus cierres: para cada piso
> vendido, el último precio anunciado y el de la escritura. Desde 10 operaciones en
> un distrito, el rango de firma deja de salir de una media de 2018 y pasa a salir
> de tus cierres, y la pantalla lo dice. Con más operaciones, el rango depende
> menos de cada una.»

- Formato: una fila por operación, siete columnas (distrito, m², fechas de
  publicación y firma, precio inicial, precio final, precio de escritura).
- **Sin datos personales**: ni nombres, ni direcciones, ni referencias
  catastrales. Si llega una columna así, el programa se niega a cargarla.
- Se quedan en su equipo o en el mío, fuera del repositorio público.
- La herramienta ya lo usa sola en cada distrito con 10 cierres o más.

Propuesta concreta: **una prueba con los cierres de los últimos 12 meses**, y
le enseño el resultado distrito a distrito, también donde salga peor.

## 9:00 – 10:00 · Preguntas que le haré

1. ¿Cuánto se suele negociar hoy en tus zonas, y cuánto ha cambiado desde 2018?
2. ¿Qué miras tú que esto no mira? (orientación, reforma reciente, vistas, comunidad…)
3. Del ejemplo que hemos visto, ¿la cifra te parece alta, baja o razonable?
4. ¿Cuántas operaciones cerráis al año, y en qué distritos?
5. ¿Guardáis el primer precio anunciado y las rebajas, o sólo el último?
6. ¿Para qué lo usarías: captar (enseñárselo al propietario), fijar el precio
   de salida, o justificar una rebaja?

## Si algo falla

- **La app no arranca**: comprueba que existe `data/real/madrid_2018.csv`
  (`python src/r00_cargar_idealista18.py`) y `data/real/factores_distrito.csv`
  (`python src/r06_actualizacion_cierre.py`).
- **«No hay pisos suficientemente parecidos»**: no es un error, es la herramienta
  negándose a inventar. Cuéntalo así y cambia la superficie o el barrio.
- **Plan B**: el panel de validación publicado,
  `entregables/dashboard_real.html`, se abre sin instalar nada.

## Lo que no hay que decir

- Que el modelo predice el precio de **venta**. Aprende de precios **pedidos**.
- Que el descuento es «el margen de negociación». Es una brecha que lo contiene.
- Que es una tasación.

"""Demo para compartir pantalla: cuanto se pide y cuanto se firma por un piso en Madrid.

Arranque, desde la raiz del repositorio:

    .venv\\Scripts\\streamlit run demo\\app.py

Necesita data/real/madrid_2018.csv (python src/r00_cargar_idealista18.py) y los
factores de src/r06_actualizacion_cierre.py.
"""
from __future__ import annotations

import streamlit as st

from graficos import barra_pedido_firma, mapa_comparables
from motor import ESTADOS, EJEMPLOS, Motor
from motor import _redondear as redondear
from r01_valorar_real import MIN_COMPARABLES

st.set_page_config(page_title="Valorador de pisos · Madrid", page_icon="🏠",
                   layout="wide")

NOMBRE_DISTRITO = {
    "Chamartin": "Chamartín", "Tetuan": "Tetuán", "Chamberi": "Chamberí",
    "Vicalvaro": "Vicálvaro",
}


def miles(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


def eur(x: float) -> str:
    return f"{miles(x)} €"


def pct(x: float, decimales: int = 0) -> str:
    return f"{x * 100:.{decimales}f} %".replace(".", ",")


def num(x: float, decimales: int = 2) -> str:
    return f"{x:.{decimales}f}".replace(".", ",")


def extremo(d: float) -> str:
    """Un extremo del rango de descuento, dicho con palabras y sin signos."""
    if abs(d) < 0.005:
        return "lo anunciado"
    return f"un {pct(abs(d))} {'por debajo' if d > 0 else 'por encima'} del anuncio"


def distrito_bonito(d: str) -> str:
    return NOMBRE_DISTRITO.get(d, d)


@st.cache_resource(show_spinner="Cargando los anuncios de Madrid…")
def motor() -> Motor:
    return Motor()


m = motor()
barrios = m.barrios.sort_values("barrio")
distritos = sorted(barrios["distrito"].unique(), key=distrito_bonito)
trimestre = m.resumen["trimestre_actual"]
trimestre_txt = f"{trimestre[-1]}.º trimestre de {trimestre[:4]}"


def cargar_ejemplo(nombre: str) -> None:
    e = EJEMPLOS[nombre]
    st.session_state.update(
        distrito=barrios.set_index("barrio").loc[e["barrio"], "distrito"],
        barrio=e["barrio"], m2=e["superficie_m2"], hab=e["habitaciones"],
        banos=e["banos"], planta=e["planta"], ascensor=e["ascensor"],
        terraza=e["terraza"], estado=e["estado"])


if "distrito" not in st.session_state:
    cargar_ejemplo(next(iter(EJEMPLOS)))

# --- Cabecera ---------------------------------------------------------------
st.title("¿Cuánto vale este piso?")
st.markdown(
    "Estimación por **pisos comparables** del mismo barrio, a partir de anuncios "
    f"reales de Madrid **de 2018**, llevada a precios del **{trimestre_txt}** con "
    "datos públicos de escrituras.")

cols = st.columns(len(EJEMPLOS) + 1)
cols[0].markdown("**Ejemplos:**")
for c, nombre in zip(cols[1:], EJEMPLOS):
    c.button(nombre, on_click=cargar_ejemplo, args=(nombre,), width="stretch")

# --- Formulario -------------------------------------------------------------
with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        distrito = st.selectbox("Distrito", distritos, key="distrito",
                                format_func=distrito_bonito)
        # Fuera los barrios que nunca llegarian al minimo de comparables
        del_distrito = barrios[(barrios["distrito"] == distrito)
                               & (barrios["n"] >= MIN_COMPARABLES)]
        opciones = del_distrito["barrio"].tolist()
        if st.session_state.get("barrio") not in opciones:
            st.session_state["barrio"] = del_distrito.loc[del_distrito["n"].idxmax(), "barrio"]
        barrio = st.selectbox("Barrio", opciones, key="barrio")
        m2 = st.number_input("Superficie construida (m²)", 25, 400, step=5, key="m2")
    with c2:
        hab = st.number_input("Habitaciones", 0, 8, key="hab")
        banos = st.number_input("Baños", 1, 5, key="banos")
        planta = st.number_input("Planta (0 = bajo)", 0, 30, key="planta")
    with c3:
        estado = st.radio("Estado", ESTADOS, key="estado", horizontal=True)
        ascensor = st.toggle("Ascensor", key="ascensor")
        terraza = st.toggle("Terraza", key="terraza")

r = m.valorar(dict(barrio=barrio, superficie_m2=m2, habitaciones=hab, banos=banos,
                   planta=planta, ascensor=ascensor, terraza=terraza, estado=estado))

# --- Resultado --------------------------------------------------------------
if not r.valorable:
    st.warning(
        f"No hay pisos suficientemente parecidos en {barrio} para dar una cifra "
        f"({r.n_comparables} con una superficie parecida; hacen falta al menos 5). "
        "Preferimos no inventar un número: pruebe con otra superficie o un barrio vecino.")
    st.stop()

err = r.error_mediano
c1, c2, c3 = st.columns(3)
with c1, st.container(border=True):
    st.markdown("##### Precio de anuncio estimado")
    st.markdown(f"## {eur(r.oferta_hoy)}")
    st.caption(f"Estimación de lo que se pediría hoy por un piso así en {barrio}. "
               f"En la prueba de 2018, la mitad de las veces el precio pedido real "
               f"quedó a menos de un {pct(err)}; aquí sería entre "
               f"{eur(redondear(r.oferta_hoy * (1 - err)))} y "
               f"{eur(redondear(r.oferta_hoy * (1 + err)))}. La otra mitad, más lejos.")
with c2, st.container(border=True):
    st.markdown("##### Precio de firma estimado")
    st.markdown(f"## {eur(r.cierre_min)} – {eur(r.cierre_max)}")
    # Por debajo de medio punto se lee como "lo anunciado", sin signo
    sobre = -r.descuento_min >= 0.005
    if r.descuento_max < 0.005:
        frase = ("Aquí los datos públicos no muestran rebaja: de media se escrituró "
                 "igual o por encima de lo anunciado.")
    elif sobre:
        frase = (f"Desde un {pct(-r.descuento_min)} por encima del anuncio hasta un "
                 f"{pct(r.descuento_max)} por debajo.")
    elif r.descuento_min < 0.005:
        frase = f"Entre lo anunciado y hasta un {pct(r.descuento_max)} menos."
    else:
        frase = (f"Entre un {pct(r.descuento_min)} y un {pct(r.descuento_max)} "
                 "por debajo del anuncio.")
    st.caption(f"{frase} Fuente del descuento: {r.origen_descuento}. Este rango solo "
               "recoge la duda sobre el descuento: el error del modelo, de la "
               "tarjeta de al lado, va además.")
with c3, st.container(border=True):
    st.markdown("##### Error típico del modelo")
    st.markdown(f"## {pct(err)}")
    st.caption(
        f"Probado con {miles(m.metricas['n_evaluacion'])} anuncios reales de 2018 que "
        f"el modelo no había visto. Valoró el {pct(m.metricas['cobertura'])} y, en la "
        f"mitad de esos, se quedó a menos de un {pct(err)} del precio pedido. "
        f"Para este piso la muestra es de fiabilidad **{r.fiabilidad}** (en ese "
        f"grupo, {pct(r.error_fiabilidad, 1)}). Sobre precios de hoy o de firma, "
        "el error no se ha podido medir.")

st.markdown("#### Lo publicado no es lo cerrado")
st.altair_chart(barra_pedido_firma(
    oferta=r.oferta_hoy,
    margen_min=redondear(r.oferta_hoy * (1 - err)),
    margen_max=redondear(r.oferta_hoy * (1 + err)),
    firma_min=r.cierre_min, firma_max=r.cierre_max), width="stretch")
st.caption(
    "La raya azul es el precio de anuncio estimado, y la franja azul clara su margen: "
    "en la prueba de 2018, la mitad de los precios pedidos quedó dentro. La franja "
    "verde es el precio de firma estimado; solo recoge la duda sobre el descuento "
    "entre anuncio y escritura, y el error del modelo va además.")

st.markdown(f"#### Los {len(r.comparables)} pisos más parecidos")
st.caption(
    f"El precio sale de **{r.n_comparables} pisos** anunciados en {barrio} con una "
    "superficie parecida (±20 %). Aquí se ven los más parecidos en habitaciones y "
    "baños. La última columna corrige cada uno por sus diferencias con su piso "
    "(estado, ascensor, planta…) y lo lleva a precios de hoy.")
tabla = r.comparables.copy()
for col in ["€/m² pedido (2018)", "€/m² equivalente a su piso, hoy"]:
    tabla[col] = tabla[col].map(eur)
st.dataframe(tabla, hide_index=True, width="stretch")

st.markdown("#### Dónde están")
st.pydeck_chart(mapa_comparables(r.mapa), width="stretch", height=420)
st.caption(
    f"Los {r.n_comparables} pisos de {barrio} con superficie parecida de los que sale el "
    "precio. En azul, los de la tabla. Al pasar el ratón: sus metros, lo que se pedía "
    "en 2018 y lo que valdría cada uno si fuera como su piso, hoy. "
    "Posición tal como la publicaba cada anuncio.")

# --- Transparencia ----------------------------------------------------------
with st.expander("Cómo se llega a la cifra, paso a paso"):
    st.markdown(f"""
1. **Comparables de 2018.** Mediana del precio por m² de los {r.n_comparables} pisos
   parecidos, corregidos por sus diferencias con el suyo: **{eur(r.eur_m2_2018)}/m²**,
   o unos **{eur(redondear(r.valor_2018))}** para {m2} m², a precios de finales de 2018.
2. **A precios de hoy.** Se multiplica por **{num(r.factor_actualizacion)}**: lo que
   ha subido el precio escriturado de vivienda usada en {distrito_bonito(r.distrito)}
   entre 2018 y {m.resumen['anio_escrituras']} (dato del distrito), y de ahí al
   {trimestre_txt} con el índice del INE para toda la Comunidad. Solo con el índice
   del INE saldría {num(r.factor_solo_ine)}.
3. **Del anuncio a la firma.** Se aplica el rango de descuento del distrito
   (de {extremo(r.descuento_min)} a {extremo(r.descuento_max)}),
   según {r.origen_descuento}.
""")
    st.caption("Habitaciones y baños sirven para elegir qué comparables se enseñan; "
               "en este modelo, su efecto en el precio llega a través de la superficie.")

with st.expander("De dónde salen los datos y cuándo se actualizaron"):
    f = m.resumen["fuentes"]
    st.markdown(f"""
- **Anuncios:** idealista18, conjunto de datos abierto publicado por sus autores
  (licencia ODbL), con los anuncios de venta de Madrid de 2018. Es precio **pedido**.
- **Precio escriturado por distrito, 2018:** Colegio de Registradores, publicado por
  el Ayuntamiento de Madrid (Anuario Estadístico 2019, tabla 3.2).
- **Precio escriturado por distrito, {m.resumen['anio_escrituras']}:** misma
  estadística, Banco de Datos del Ayuntamiento. Consultado el {f['escrituras_actual_consultado']}.
- **Evolución hasta el {trimestre_txt}:** Índice de Precios de Vivienda del INE,
  Comunidad de Madrid, vivienda de segunda mano. Consultado el {f['ipv_consultado']}.
""")
    st.caption("Las cifras públicas se actualizan cuando el Ayuntamiento o el INE "
               "publican dato nuevo; el paso a paso está en el README del proyecto.")

with st.expander("Lo que esta estimación no es"):
    st.markdown("""
- **No es una tasación.** Es una referencia rápida a partir de pisos parecidos.
- **El modelo aprende de precios pedidos, no firmados.** Lo que se firmó solo se
  conoce por distrito y en media, así que el precio de firma es un rango.
- **El descuento público no es solo negociación.** Mezcla pisos que nunca se
  vendieron, pisos distintos entre lo anunciado y lo vendido y el tiempo que tarda
  una escritura en inscribirse. Se midió en 2018; hoy puede ser otro.
- **Los anuncios son de 2018.** Se llevan a hoy con la evolución del precio
  escriturado de cada distrito, suponiendo que la distancia entre lo que se pide y
  lo que se firma no ha cambiado. Si un barrio ha cambiado más que su distrito, la
  cifra no lo recoge.
- **El error del 12 % se midió en 2018, sobre precio pedido.** Cuánto se equivoca
  con precios de hoy, o con precios de firma, no se ha podido medir.
- **Lo que mejoraría todo esto:** precios de cierre reales de una agencia, operación
  a operación. La herramienta ya tiene preparado dónde cargarlos.
""")

"""Graficos de la demo. Solo dibujan cifras que ya calcula el motor: no calculan nada.

`barra_pedido_firma` pone en una misma escala de euros lo que se pediria hoy por
el piso y lo que se firmaria:

  fila 1, lo que se pide:  el anuncio estimado, con el margen del modelo (la
                           mitad de los precios pedidos de la prueba de 2018
                           quedo dentro de esa franja)
  fila 2, lo que se firma: el rango de firma, que solo recoge la duda sobre el
                           descuento entre anuncio y escritura

Una linea discontinua une el anuncio con la fila de la firma, para que se vea de
un vistazo cuanto se separa lo cerrado de lo publicado. Las etiquetas van por
encima y por debajo de las filas, donde la linea no pasa.
"""
from __future__ import annotations

import altair as alt
import pandas as pd

AZUL = "#1f5f8b"        # primaryColor de .streamlit/config.toml
AZUL_CLARO = "#c9dcec"
VERDE = "#2e7d4f"
GRIS = "#5f6b76"
TINTA = "#1d2730"

PIDE = "Lo que se pide"
FIRMA = "Lo que se firma"
FILAS = [PIDE, FIRMA]


def _eur(x: float) -> str:
    return f"{x:,.0f} €".replace(",", ".")


def datos_barra(oferta: float, margen_min: float, margen_max: float,
                firma_min: float, firma_max: float) -> pd.DataFrame:
    """Una fila por elemento del grafico, con su etiqueta ya escrita.

    `x` es donde se ancla la etiqueta; `alinear` y `dy` dicen hacia donde sale.
    """
    filas = [
        dict(fila=PIDE, pieza="margen", desde=margen_min, hasta=margen_max),
        dict(fila=PIDE, pieza="anuncio", desde=oferta, hasta=oferta),
        dict(fila=FIRMA, pieza="firma", desde=firma_min, hasta=firma_max),
    ]
    etiquetas = [
        dict(fila=PIDE, x=oferta, texto=f"Anuncio estimado: {_eur(oferta)}",
             alinear="center", dy=-30, tamano=15, color=AZUL, negrita=True),
        dict(fila=PIDE, x=margen_min, texto=f"margen del modelo · {_eur(margen_min)}",
             alinear="left", dy=30, tamano=12, color=GRIS, negrita=False),
        dict(fila=PIDE, x=margen_max, texto=_eur(margen_max),
             alinear="right", dy=30, tamano=12, color=GRIS, negrita=False),
        dict(fila=FIRMA, x=(firma_min + firma_max) / 2,
             texto=f"Firma estimada: {_eur(firma_min)} – {_eur(firma_max)}",
             alinear="center", dy=30, tamano=15, color=VERDE, negrita=True),
    ]
    return pd.DataFrame(filas), pd.DataFrame(etiquetas)


def barra_pedido_firma(oferta: float, margen_min: float, margen_max: float,
                       firma_min: float, firma_max: float) -> alt.LayerChart:
    piezas, etiquetas = datos_barra(oferta, margen_min, margen_max, firma_min, firma_max)
    lo = min(margen_min, firma_min, oferta)
    hi = max(margen_max, firma_max, oferta)
    holgura = (hi - lo) * 0.06
    escala_x = alt.Scale(domain=[lo - holgura, hi + holgura], zero=False, nice=False)
    eje_x = alt.Axis(
        labelExpr="replace(format(datum.value, ',.0f'), regexp(',', 'g'), '.') + ' €'",
        tickCount=6, grid=True, gridColor="#e6e9ec", domain=False,
        labelColor=GRIS, labelFontSize=12)
    y = alt.Y("fila:N", title=None, sort=FILAS, scale=alt.Scale(domain=FILAS),
              axis=alt.Axis(labelFontSize=16, labelFontWeight="bold", labelColor=TINTA,
                            labelPadding=14, ticks=False, domain=False))

    base = alt.Chart(piezas).encode(y=y)
    x = alt.X("desde:Q", title=None, scale=escala_x, axis=eje_x)
    margen = base.transform_filter(alt.datum.pieza == "margen").mark_bar(
        height=36, color=AZUL_CLARO, cornerRadius=6).encode(x=x, x2="hasta:Q")
    firma = base.transform_filter(alt.datum.pieza == "firma").mark_bar(
        height=36, color=VERDE, cornerRadius=6).encode(x=x, x2="hasta:Q")
    anuncio = base.transform_filter(alt.datum.pieza == "anuncio").mark_tick(
        thickness=6, size=52, color=AZUL).encode(x=x)

    # Del anuncio hasta la fila de la firma, y nada mas: no cruza ninguna etiqueta
    guia = alt.Chart(pd.DataFrame({"x": [oferta], "desde": [PIDE], "hasta": [FIRMA]})).mark_rule(
        strokeDash=[6, 4], color=AZUL, strokeWidth=2, opacity=0.85).encode(
        x=alt.X("x:Q", scale=escala_x),
        y=alt.Y("desde:N", sort=FILAS, scale=alt.Scale(domain=FILAS)), y2="hasta:N")

    capas = [margen, firma, guia, anuncio]
    for _, e in etiquetas.iterrows():
        capas.append(alt.Chart(pd.DataFrame([e])).mark_text(
            align=e["alinear"], dy=int(e["dy"]), fontSize=int(e["tamano"]), color=e["color"],
            fontWeight="bold" if e["negrita"] else "normal").encode(
            x=alt.X("x:Q", scale=escala_x),
            y=alt.Y("fila:N", sort=FILAS, scale=alt.Scale(domain=FILAS)),
            text="texto:N"))

    return (alt.layer(*capas)
            .properties(height=260, padding={"left": 5, "right": 20, "top": 10, "bottom": 5})
            .configure_view(stroke=None)
            .configure_axisY(labelLimit=220))


# ------------------------------------------------------------------ mapa
TOOLTIP_MAPA = {
    "html": "<b>{m2} m²</b><br/>{eur_m2_2018_txt} €/m² pedido en 2018"
            "<br/><b>{eur_m2_hoy_txt} €/m²</b> equivalente a su piso, hoy",
    "style": {"backgroundColor": "#1d2730", "color": "white", "fontSize": "13px"},
}


def _miles(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def mapa_comparables(puntos: pd.DataFrame):
    """Un punto por comparable; los de la tabla, en azul y mas grandes.

    `puntos` es `Resultado.mapa`: lat, lon, m2, eur_m2_2018, eur_m2_hoy, destacado.
    El fondo es de Carto (sin clave), asi que hace falta internet para verlo.
    """
    import pydeck as pdk

    d = puntos.copy()
    d["eur_m2_2018_txt"] = d["eur_m2_2018"].map(_miles)
    d["eur_m2_hoy_txt"] = d["eur_m2_hoy"].map(_miles)
    resto, destacados = d[~d["destacado"]], d[d["destacado"]]

    capa_resto = pdk.Layer(
        "ScatterplotLayer", data=resto, get_position="[lon, lat]",
        get_fill_color=[95, 107, 118, 140], get_radius=28, radius_min_pixels=5,
        pickable=True, stroked=True, get_line_color=[255, 255, 255, 200], line_width_min_pixels=1)
    capa_destacados = pdk.Layer(
        "ScatterplotLayer", data=destacados, get_position="[lon, lat]",
        get_fill_color=[31, 95, 139, 235], get_radius=42, radius_min_pixels=8,
        pickable=True, stroked=True, get_line_color=[255, 255, 255, 255], line_width_min_pixels=2)

    vista = pdk.ViewState(latitude=float(d["lat"].mean()), longitude=float(d["lon"].mean()),
                          zoom=14.6, pitch=0)
    return pdk.Deck(layers=[capa_resto, capa_destacados], initial_view_state=vista,
                    tooltip=TOOLTIP_MAPA, map_provider="carto", map_style="light")

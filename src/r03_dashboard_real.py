"""Paso R03 — Dashboard de los resultados con DATOS REALES.

Un unico HTML sin dependencias externas. Responde a una pregunta concreta:
como sabemos que esto funciona.

La respuesta tiene dos mitades. La agregada: el error del motor sobre los
anuncios que no habia visto, comparado con dos alternativas mas tontas. Y la
individual: una valoracion abierta en canal, con sus comparables uno a uno.

Ninguna cifra de este fichero va escrita a mano. Todas salen de
`metricas_2018.json`, `caso_trazado.json` o `diagnostico_coeficientes_2018.json`.
Es deliberado: con numeros tecleados en la prosa, el dashboard se desincroniza en
silencio cuando cambian los datos y nadie se entera. Lo vigila
`test_dashboard_real.py`.
"""
from __future__ import annotations

import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DIR_REAL = RAIZ / "data" / "real"
F_SALIDA = RAIZ / "outputs" / "dashboard_real.html"

TINTA, REGISTRO, PAPEL = "#16202B", "#1F3A5F", "#EEF0F1"
OLIVA, GRANATE, GRIS, LINEA, BLANCO = "#4A6741", "#8C3A3A", "#61707C", "#C9D0D6", "#FFFFFF"


def _redondear(v, dec: int) -> Decimal:
    """Redondeo comercial: el medio se va siempre hacia arriba en magnitud.

    El formato de Python redondea al par, asi que 6.522,5 salia 6.522 aqui y
    6.523 en la documentacion, escrita a mano. Dos cifras distintas para el mismo
    dato, y ninguna de las dos mal. Se fija la regla en un solo sitio.

    Se pasa por `str` a proposito: Decimal(0.1) es 0,1000...0055511, y quantize
    sobre eso reintroduce el error del binario que se intenta evitar.
    """
    return Decimal(str(v)).quantize(Decimal(1).scaleb(-dec), rounding=ROUND_HALF_UP)


def _n(v, dec=0):
    return (f"{_redondear(v, dec):,.{dec}f}"
            .replace(",", "@").replace(".", ",").replace("@", "."))


def _p(v, dec=1):
    # El x100 se hace en Decimal, no en float, por lo mismo de arriba.
    d = _redondear(Decimal(str(v)) * 100, dec)
    return f"{d:.{dec}f}".replace(".", ",") + " %"


# Los dos extremos del reparto por numero de comparables, que es lo que se cita
# en la prosa. Las claves las escribe r01 en metricas_2018.json.
TRAMOS_EXTREMOS = ("5-9", "50 o mas")


def barras_metodos(m: dict) -> str:
    datos = [("Comparables por barrio", m["motor_comparables"]["error_absoluto_mediano"], REGISTRO),
             ("Mediana del barrio", m["base_mediana_barrio"]["error_absoluto_mediano"], GRIS),
             ("Mediana de la ciudad", m["base_mediana_ciudad"]["error_absoluto_mediano"], GRIS)]
    izq, ancho, alto_fila = 178, 300, 40
    mx = max(d[1] for d in datos) * 1.15
    p = [f'<svg viewBox="0 0 {izq + ancho + 70} {len(datos) * alto_fila + 20}" '
         f'width="100%" role="img" aria-label="Error mediano por método">']
    for i, (nombre, v, color) in enumerate(datos):
        y = 8 + i * alto_fila
        w = v / mx * ancho
        p.append(f'<text x="{izq - 10}" y="{y + 19}" font-size="12.5" fill="{TINTA}" '
                 f'text-anchor="end">{nombre}</text>')
        p.append(f'<rect x="{izq}" y="{y + 4}" width="{w:.1f}" height="22" fill="{color}"/>')
        p.append(f'<text x="{izq + w + 8}" y="{y + 20}" font-size="13" font-weight="600" '
                 f'fill="{TINTA}">{_p(v)}</text>')
    p.append("</svg>")
    return "".join(p)


def escalera_barrios(b: pd.DataFrame, n=10) -> str:
    ocultos = len(b) - 2 * n
    top, bot = b.head(n), b.tail(n).iloc[::-1]
    filas = [(r.barrio, r.eur_m2_mediano, False) for r in top.itertuples()]
    filas.append((None, None, True))
    filas += [(r.barrio, r.eur_m2_mediano, False) for r in bot.itertuples()]
    izq, ancho, alto_fila = 158, 340, 20
    mx = b["eur_m2_mediano"].max() * 1.08
    alto = len(filas) * alto_fila + 24
    p = [f'<svg viewBox="0 0 {izq + ancho + 62} {alto}" width="100%" '
         f'role="img" aria-label="Precio por metro cuadrado y barrio">']
    for i, (nombre, v, corte) in enumerate(filas):
        y = 14 + i * alto_fila
        if corte:
            p.append(f'<text x="{izq - 10}" y="{y + 10}" font-size="11" fill="{GRIS}" '
                     f'text-anchor="end">… {_n(ocultos)} barrios más …</text>')
            continue
        w = v / mx * ancho
        p.append(f'<text x="{izq - 10}" y="{y + 11}" font-size="11.5" fill="{TINTA}" '
                 f'text-anchor="end">{nombre}</text>')
        p.append(f'<rect x="{izq}" y="{y + 2}" width="{w:.1f}" height="13" '
                 f'fill="{REGISTRO}" opacity="0.86"/>')
        p.append(f'<text x="{izq + w + 7}" y="{y + 13}" font-size="10.5" '
                 f'fill="{GRIS}">{_n(v)}</text>')
    p.append("</svg>")
    return "".join(p)


def histograma_error(v: pd.DataFrame) -> str:
    e = (v["valor_estimado"] / v["precio_pedido"] - 1).dropna()
    bordes = np.arange(-0.6, 0.625, 0.05)
    cuentas, _ = np.histogram(e.clip(-0.6, 0.6), bins=bordes)
    ancho, alto, izq, arriba = 500, 140, 32, 10
    bw, mx = ancho / len(cuentas), cuentas.max()
    # El pie va en arriba+alto+36 = 186. El viewBox se calculaba sin contar
    # `arriba`, daba 184, y el texto quedaba fuera y se recortaba. Contandolo son
    # 194 y quedan 8 px de aire por debajo.
    alto_svg = arriba + alto + 44
    p = [f'<svg viewBox="0 0 {izq + ancho + 12} {alto_svg}" width="100%" '
         f'role="img" aria-label="Distribución del error de estimación">']
    for i, c in enumerate(cuentas):
        h = c / mx * alto
        centro = (bordes[i] + bordes[i + 1]) / 2
        col = REGISTRO if abs(centro) <= 0.10 else GRIS
        p.append(f'<rect x="{izq + i * bw + 1:.1f}" y="{arriba + alto - h:.1f}" '
                 f'width="{bw - 2:.1f}" height="{h:.1f}" fill="{col}" opacity="0.8"/>')
    p.append(f'<line x1="{izq}" y1="{arriba + alto}" x2="{izq + ancho}" '
             f'y2="{arriba + alto}" stroke="{LINEA}"/>')
    for val in [-0.5, -0.25, 0, 0.25, 0.5]:
        x = izq + (val + 0.6) / 1.2 * ancho
        p.append(f'<text x="{x:.1f}" y="{arriba + alto + 16}" font-size="10" '
                 f'fill="{GRIS}" text-anchor="middle">{int(val * 100)} %</text>')
    p.append(f'<text x="{izq + ancho / 2}" y="{arriba + alto + 36}" font-size="10.5" '
             f'fill="{GRIS}" text-anchor="middle">azul: estimación dentro de ±10 % '
             f'del precio pedido</text>')
    p.append("</svg>")
    return "".join(p)


def construir() -> None:
    m = json.loads((DIR_REAL / "metricas_2018.json").read_text(encoding="utf-8"))
    v = pd.read_csv(DIR_REAL / "valoraciones_2018.csv")
    b = pd.read_csv(DIR_REAL / "barrios_madrid.csv")
    caso = json.loads((DIR_REAL / "caso_trazado.json").read_text(encoding="utf-8"))

    # El bloque de limites cita el diagnostico de coeficientes entero. Si no
    # esta, se para: es preferible no publicar el dashboard a publicarlo con esas
    # afirmaciones escritas a mano, que es justo el fallo que se esta corrigiendo.
    f_diag = DIR_REAL / "diagnostico_coeficientes_2018.json"
    if not f_diag.exists():
        raise SystemExit(
            f"Falta {f_diag.name}. Ejecuta antes:\n"
            f"    python src/r04_diagnostico_coeficientes.py")
    diag = json.loads(f_diag.read_text(encoding="utf-8"))

    mo, bb, bc = (m["motor_comparables"], m["base_mediana_barrio"],
                  m["base_mediana_ciudad"])
    fiab = m["error_por_fiabilidad"]
    por_n = m["error_por_n_comparables"]
    tramo_pocos, tramo_muchos = TRAMOS_EXTREMOS
    coef, vif = m["coeficientes"], diag["vif"]
    centrado, tramo_cal = diag["efecto_del_centrado"], diag["tramo_monotono_calidad"]
    corr_max = abs(diag["correlaciones"]["correlacion_maxima"])

    filas_metodo = "".join(
        f"<tr{' class=destacada' if k == 'motor_comparables' else ''}>"
        f"<td>{nombre}</td><td class='n'>{_p(m[k]['error_absoluto_mediano'])}</td>"
        f"<td class='n'>{_p(m[k]['dentro_de_10pct'])}</td>"
        f"<td class='n'>{_p(m[k]['dentro_de_20pct'])}</td>"
        f"<td class='n'>{_p(m[k]['sesgo_mediano'])}</td></tr>"
        for nombre, k in [("Comparables por barrio", "motor_comparables"),
                          ("Mediana del barrio y trimestre", "base_mediana_barrio"),
                          ("Mediana de la ciudad", "base_mediana_ciudad")])

    filas_fiab = "".join(
        f"<tr><td>{f.capitalize()}</td><td class='n'>{_p(e)}</td></tr>"
        for f, e in sorted(fiab.items(), key=lambda x: x[1]))

    s, r = caso["sujeto"], caso["resultado"]
    filas_embudo = "".join(
        f"<tr><td>{p['paso']}</td><td class='n'>{_n(p['quedan'])}</td></tr>"
        for p in caso["embudo"])

    comps = caso["comparables"]
    filas_comps = "".join(
        f"<tr><td class='n'>{c['superficie_m2']}</td>"
        f"<td class='n'>{_n(c['precio'])} €</td>"
        f"<td class='n'>{_n(c['eur_m2'])}</td>"
        f"<td class='n'><b>{_n(c['eur_m2_ajustado'])}</b></td>"
        f"<td class='rasgos'>{c['rasgos']}</td></tr>" for c in comps)

    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Validación con datos reales — Madrid 2018</title>
<style>
 * {{ box-sizing: border-box; }}
 body {{ margin:0; background:{PAPEL}; color:{TINTA};
   font-family:"Segoe UI",Roboto,-apple-system,"Helvetica Neue",Arial,sans-serif;
   font-size:15px; line-height:1.55; font-variant-numeric:tabular-nums; }}
 .hoja {{ max-width:940px; margin:0 auto; padding:40px 26px 72px; }}
 header {{ border-bottom:3px solid {REGISTRO}; padding-bottom:18px; }}
 h1 {{ font-family:Georgia,"Iowan Old Style","Times New Roman",serif; font-size:31px;
   line-height:1.16; font-weight:600; margin:0 0 8px; letter-spacing:-.01em; }}
 header p {{ margin:0; color:{GRIS}; font-size:14px; max-width:66ch; }}
 .sello {{ font-size:12.5px; color:{GRIS}; margin-top:14px; }}
 section {{ margin-top:44px; }}
 h2 {{ font-family:Georgia,"Iowan Old Style",serif; font-size:20px; font-weight:600;
   margin:0 0 6px; }}
 h3 {{ font-size:15px; margin:22px 0 6px; }}
 .pie {{ color:{GRIS}; font-size:13px; margin:6px 0 18px; max-width:72ch; }}
 .panel {{ background:{BLANCO}; border:1px solid {LINEA}; padding:22px 24px; }}
 .cifras {{ display:flex; flex-wrap:wrap; border-top:1px solid {LINEA}; }}
 .cifra {{ flex:1 1 150px; padding:16px 20px 14px; background:{BLANCO};
   border-bottom:1px solid {LINEA}; border-right:1px solid {LINEA}; }}
 .cifra:last-child {{ border-right:0; }}
 .cifra b {{ display:block; font-size:25px; font-weight:600; letter-spacing:-.01em; }}
 .cifra span {{ font-size:12.5px; color:{GRIS}; }}
 table {{ width:100%; border-collapse:collapse; font-size:13.5px; background:{BLANCO}; }}
 th {{ text-align:left; font-weight:600; font-size:12.5px; color:{BLANCO};
   background:{REGISTRO}; padding:8px 10px; }}
 td {{ padding:7px 10px; border-bottom:1px solid {LINEA}; }}
 td.n, th.n {{ text-align:right; white-space:nowrap; }}
 td.rasgos {{ color:{GRIS}; font-size:12.5px; }}
 tr.destacada td {{ background:#E8EDF3; font-weight:600; }}
 .ficha {{ background:{BLANCO}; border:1px solid {LINEA}; border-left:4px solid {REGISTRO};
   padding:18px 22px; }}
 .ficha dl {{ display:grid; grid-template-columns:auto 1fr; gap:2px 18px; margin:0;
   font-size:13.5px; }}
 .ficha dt {{ color:{GRIS}; }}
 .ficha dd {{ margin:0; }}
 .veredicto {{ background:{BLANCO}; border:1px solid {LINEA}; padding:18px 22px;
   margin-top:18px; font-size:15px; }}
 .veredicto b {{ font-size:20px; color:{OLIVA}; }}
 .dos {{ display:grid; grid-template-columns:1fr 1fr; gap:26px; align-items:start; }}
 @media (max-width:720px) {{ .dos {{ grid-template-columns:1fr; }} }}
 .limites {{ border-left:4px solid {GRANATE}; padding:4px 0 4px 20px; }}
 .limites li {{ margin-bottom:9px; max-width:74ch; }}
 .scroll {{ max-height:420px; overflow:auto; border:1px solid {LINEA}; }}
 footer {{ margin-top:52px; padding-top:16px; border-top:1px solid {LINEA};
   color:{GRIS}; font-size:12.5px; }}
</style></head><body><div class="hoja">

<header>
  <h1>¿Cómo sabemos que funciona?</h1>
  <p>Dos respuestas. Una agregada, sobre {_n(m['n_evaluacion'])} anuncios reales
     que el motor no había visto. Y una individual: una valoración abierta en
     canal, con sus comparables uno a uno.</p>
  <p class="sello">Datos: <b>idealista18</b>, {_n(m['n_anuncios_origen'])} anuncios
     de venta en Madrid, cuatro trimestres de 2018, licencia ODbL-1.0. Los niveles de precio son de
     2018 y no representan el mercado actual.</p>
</header>

<div class="cifras">
  <div class="cifra"><b>{_p(mo['error_absoluto_mediano'])}</b><span>error mediano fuera de muestra</span></div>
  <div class="cifra"><b>{_p(mo['dentro_de_10pct'])}</b><span>estimaciones dentro de ±10 %</span></div>
  <div class="cifra"><b>{_p(m['cobertura'])}</b><span>cobertura</span></div>
  <div class="cifra"><b>{_p(mo['sesgo_mediano'])}</b><span>sesgo</span></div>
</div>

<section>
  <h2>Contra qué se compara</h2>
  <p class="pie">Un error del {_p(mo['error_absoluto_mediano'])} no significa nada
     por sí solo. Sólo tiene
     sentido frente a alternativas más simples y más baratas de montar. La
     partición es por anuncio: el 70 % sirve de referencia para comparar, y el
     30 % restante nunca interviene en su propia valoración.</p>
  <table><thead><tr><th>Método</th><th class="n">Error mediano</th>
    <th class="n">Dentro de ±10 %</th><th class="n">Dentro de ±20 %</th>
    <th class="n">Sesgo</th></tr></thead><tbody>{filas_metodo}</tbody></table>
  <div class="panel" style="margin-top:18px">{barras_metodos(m)}</div>
  <p class="pie">La lectura honesta: el motor mejora la línea base del barrio en
     {_n((bb['error_absoluto_mediano'] - mo['error_absoluto_mediano']) * 100, 1)} puntos,
     un {_n((1 - mo['error_absoluto_mediano'] / bb['error_absoluto_mediano']) * 100, 0)} %
     menos de error. Mejora, pero la mediana simple del barrio ya te lleva al
     {_p(bb['error_absoluto_mediano'])}: la mayor parte del trabajo la hace saber
     en qué barrio está el piso. Frente a no distinguir zona
     ({_p(bc['error_absoluto_mediano'])}) sí hay una diferencia de método.</p>
</section>

<section class="dos">
  <div>
    <h2>Dónde cae el error</h2>
    <p class="pie">Diferencia entre valor estimado y precio pedido.</p>
    <div class="panel">{histograma_error(v)}</div>
  </div>
  <div>
    <h2>La fiabilidad sí discrimina</h2>
    <p class="pie">Con el corpus sintético esta etiqueta daba el mismo error en
       los tres niveles y lo dejamos escrito como fallo abierto. Con datos reales
       va de {_p(fiab['alta'])} en el nivel alto a {_p(fiab['baja'])} en el bajo.</p>
    <table><thead><tr><th>Fiabilidad</th><th class="n">Error mediano</th></tr></thead>
      <tbody>{filas_fiab}</tbody></table>
    <p class="pie">Lo que discrimina es la dispersión de los comparables, no
       cuántos hay: pasar de {tramo_pocos} comparables a {tramo_muchos.replace('o mas', 'o más')}
       sólo baja el error del {_p(por_n[tramo_pocos]['error_absoluto_mediano'])} al
       {_p(por_n[tramo_muchos]['error_absoluto_mediano'])}.</p>
  </div>
</section>

<section>
  <h2>Una valoración, abierta en canal</h2>
  <p class="pie">Cualquier cifra del sistema se puede abrir así. Este es un
     anuncio del conjunto de evaluación: el motor nunca lo vio.</p>

  <div class="ficha">
    <dl>
      <dt>Barrio</dt><dd>{s['barrio']} · {s['trimestre']}</dd>
      <dt>Superficie</dt><dd>{s['superficie_m2']} m² construidos</dd>
      <dt>Distribución</dt><dd>{s['habitaciones']} habitaciones, {s['banos']} baño ·
        planta {s['planta']} · finca de {s['anio']}</dd>
      <dt>Características</dt><dd>{', '.join(s['rasgos'])}</dd>
      <dt>Precio pedido</dt><dd><b>{_n(s['precio_pedido'])} €</b>
        ({_n(s['eur_m2_pedido'])} €/m²)</dd>
    </dl>
  </div>

  <h3>Paso 1 — De {_n(m['n_pool'])} anuncios a {r['n_comparables']}</h3>
  <table><thead><tr><th>Filtro</th><th class="n">Quedan</th></tr></thead>
    <tbody>{filas_embudo}</tbody></table>

  <h3>Paso 2 — Cada comparable se lleva a las condiciones del piso evaluado</h3>
  <p class="pie">La columna ajustada corrige por estado, ascensor, orientación y
     demás atributos, con coeficientes estimados sólo sobre el conjunto de
     comparables. Ordenados de menor a mayor €/m² ajustado.</p>
  <div class="scroll">
  <table><thead><tr><th class="n">m²</th><th class="n">Precio</th>
    <th class="n">€/m²</th><th class="n">€/m² ajustado</th>
    <th>Características</th></tr></thead><tbody>{filas_comps}</tbody></table>
  </div>

  <h3>Paso 3 — La mediana, y la comparación</h3>
  <div class="veredicto">
    Mediana de los {r['n_comparables']} comparables ajustados:
    <b>{_n(r['eur_m2_mediano_ajustado'])} €/m²</b><br>
    Rango intercuartílico: {_n(r['rango_intercuartilico'][0])} a
    {_n(r['rango_intercuartilico'][1])} €/m² · dispersión {_n(r['dispersion'] * 100, 1)} %<br><br>
    Valor estimado: <b>{_n(r['eur_m2_mediano_ajustado'], 2)} × {s['superficie_m2']} m²
    = {_n(r['valor_estimado'])} €</b><br>
    Precio pedido: {_n(r['precio_pedido'])} €<br><br>
    Desviación: <b>{_p(r['desviacion'])}</b> por debajo de sus comparables.
  </div>
  <p class="pie">Eso no significa que sea una ganga. Significa que merece una
     llamada para averiguar por qué: puede tener una derrama pendiente, una
     ocupación, una servidumbre, o estar bien valorado y ser el resto los que
     están caros. El sistema produce una lista de llamadas priorizada, no un
     dictamen.</p>
</section>

<section>
  <h2>Lo que estos datos no permiten</h2>
  <ul class="limites">
    <li><b>El objetivo es el precio pedido, no el de cierre.</b> El motor
        reproduce lo que pide un anuncio, no lo que vale el piso ni por cuánto se
        vendió. No hay precios de escritura por inmueble en ningún conjunto
        abierto.</li>
    <li><b>El identificador no enlaza entre trimestres.</b> Quería seguir cada
        piso durante 2018 para ver si los marcados baratos desaparecían antes.
        No se puede: los {_n(m['n_identificadores_unicos'])} identificadores
        aparecen cada uno en un solo trimestre. Se detectó porque la tabla de transiciones daba 0,0 % tres
        veces seguidas, y un cero perfecto repetido no es un dato, es un aviso.</li>
    <li><b>Los datos son de 2018.</b> El orden de los barrios sigue siendo
        informativo; los niveles de precio no.</li>
    <li><b>Los autores añadieron ruido aleatorio</b> a coordenadas y precios por
        protección de datos. Eso pone un suelo al error alcanzable que no he
        cuantificado.</li>
    <li><b>Los dos coeficientes que salían con el signo contrario ya están
        verificados</b>, y la sospecha que tenía era falsa. No era colinealidad:
        el VIF más alto de todo el modelo es {_n(max(vif.values()), 2)} y la
        correlación más fuerte entre regresores es {_n(corr_max, 3)}. Y como la
        sospecha era
        «colinealidad con el barrio», lo comprobé por la vía directa: quitando el
        centrado por barrio-trimestre. Sin centrar, el jardín se va a
        {_p(np.expm1(centrado['jardin']['sin_centrar']))} en vez de
        {_p(np.expm1(coef['jardin']))}, o sea que el centrado ya está quitando el
        efecto de zona y la sospecha apuntaba al revés de lo que pasa. La
        <b>calidad catastral</b> no era una anomalía, era la variable leída al
        revés: el código catastral empeora según crece, así que el signo negativo
        era el correcto sobre el código original. Ya está invertida, sale en
        {_p(np.expm1(coef['calidad_catastral']))} y ninguna valoración se mueve, y
        que no se mueva es demostrable algebraicamente, no sólo medido.
        El <b>jardín</b> sí se queda en {_p(np.expm1(coef['jardin']))}, y ahí hay
        que separar dos cosas: lo probado es que no viene del barrio, ni de la
        superficie, ni de colinealidad; que «jardín y nada más» marque promoción
        periférica es una <b>interpretación del patrón, no una medición</b>,
        porque no hay ninguna variable que separe el jardín privado de la zona
        común. Encaja con que el {_p(diag['pct_jardin_con_piscina'])} de los
        anuncios con jardín lleven piscina, pero no está demostrado.
        Reproducible con <code>src/r04_diagnostico_coeficientes.py</code>.</li>
    <li><b>Los códigos catastrales {_n(tramo_cal['codigo_hasta'] + 1)} y
        {_n(tramo_cal['codigo_hasta'] + 2)} siguen sin resolver.</b> Repuntan en
        precio en vez de seguir bajando, y al invertir la escala les asigno la
        peor calidad justo a los que se pagan más caros que el código
        {_n(tramo_cal['codigo_hasta'])}. Si no son «peor calidad» sino otra cosa,
        están colocados al revés. Son {_n(tramo_cal['anuncios_fuera'])} anuncios
        de {_n(m['n_pool'])} y no lo he resuelto.</li>
  </ul>
</section>

<section>
  <h2>La estructura del mercado</h2>
  <p class="pie">Del barrio más caro al más barato hay un factor
     {_n(b['eur_m2_mediano'].max() / b['eur_m2_mediano'].min(), 1)}. Niveles de
     2018: lo que sobrevive al paso del tiempo es el orden, no la cifra.</p>
  <div class="panel">{escalera_barrios(b)}</div>
</section>

<footer>
  Fuente de los datos: Rey-Blanco, D., Arbués, P., López, F. y Páez, A. (2024),
  <i>A geo-referenced micro-data set of real estate listings for Spain's three
  largest cities</i>, Environment and Planning B: Urban Analytics and City
  Science, doi:10.1177/23998083241242844. Conjunto <b>idealista18</b>, licencia
  ODbL-1.0. Publicado por idealista junto a la Universidad Politécnica de
  Cartagena y McMaster University. No se ha realizado extracción automatizada de
  ningún portal. Ningún dato personal interviene en el proceso.
</footer>

</div></body></html>"""
    F_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    F_SALIDA.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    construir()
    print(f"Dashboard generado -> {F_SALIDA}")

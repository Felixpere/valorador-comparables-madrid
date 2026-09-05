"""Paso 06 — Dashboard visual.

Un unico archivo HTML sin dependencias externas: ni CDN, ni fuentes remotas, ni
JavaScript de terceros. Se abre con doble clic en cualquier portatil, con o sin
internet. Los graficos son SVG generado aqui.

Este dashboard es la version de demostracion. El entregable equivalente en
Power BI se construye sobre la hoja "Valoraciones" del Excel, que es una tabla
plana pensada para cargarse sin transformaciones. Ver docs/power_bi.md.
"""
from __future__ import annotations

import json
from datetime import datetime

import numpy as np
import pandas as pd

import config as cfg

TINTA = "#16202B"
REGISTRO = "#1F3A5F"
PAPEL = "#EEF0F1"
BLANCO = "#FFFFFF"
OLIVA = "#4A6741"
GRANATE = "#8C3A3A"
GRIS = "#61707C"
LINEA = "#C9D0D6"


def _eur(v, dec=0):
    if pd.isna(v):
        return "—"
    return f"{v:,.{dec}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def _pct(v, dec=1):
    return "—" if pd.isna(v) else f"{v * 100:.{dec}f}".replace(".", ",") + " %"


# ------------------------------------------------------------------ graficos
def escalera_distritos(val: pd.DataFrame, ref: pd.DataFrame) -> str:
    g = (val.groupby("distrito")["eur_m2_pedido"].median()
         .sort_values(ascending=False))
    refs = dict(zip(ref["distrito"], ref["precio_m2_2022"]))
    maximo = max(g.max(), max(refs.values())) * 1.06

    alto_fila, arriba, izq, ancho = 21, 34, 168, 470
    alto = arriba + alto_fila * len(g) + 16
    p = [f'<svg viewBox="0 0 {izq + ancho + 62} {alto}" width="100%" '
         f'role="img" aria-label="Precio mediano por metro cuadrado y distrito">']

    for x in range(0, int(maximo) + 1, 2000):
        px = izq + x / maximo * ancho
        p.append(f'<line x1="{px:.1f}" y1="{arriba - 12}" x2="{px:.1f}" '
                 f'y2="{alto - 16}" stroke="{LINEA}" stroke-width="1"/>')
        p.append(f'<text x="{px:.1f}" y="{arriba - 18}" font-size="10" '
                 f'fill="{GRIS}" text-anchor="middle">{x // 1000}k</text>')

    for i, (d, v) in enumerate(g.items()):
        y = arriba + i * alto_fila
        w = v / maximo * ancho
        p.append(f'<text x="{izq - 10}" y="{y + 11}" font-size="11.5" '
                 f'fill="{TINTA}" text-anchor="end">{d}</text>')
        p.append(f'<rect x="{izq}" y="{y + 2}" width="{w:.1f}" height="13" '
                 f'fill="{REGISTRO}" opacity="0.86"/>')
        p.append(f'<text x="{izq + w + 7}" y="{y + 13}" font-size="10.5" '
                 f'fill="{GRIS}">{_eur(v)}</text>')
        r = refs.get(d)
        if r:
            xr = izq + r / maximo * ancho
            p.append(f'<line x1="{xr:.1f}" y1="{y}" x2="{xr:.1f}" y2="{y + 17}" '
                     f'stroke="{GRANATE}" stroke-width="1.8"/>')
    p.append("</svg>")
    return "".join(p)


def histograma_desviacion(val: pd.DataFrame) -> str:
    d = val["desviacion"].dropna()
    bordes = np.arange(-0.45, 0.475, 0.05)
    cuentas, _ = np.histogram(d, bins=bordes)
    ancho, alto, izq, arriba = 520, 150, 34, 12
    bw = ancho / len(cuentas)
    mx = cuentas.max()
    p = [f'<svg viewBox="0 0 {izq + ancho + 12} {alto + 52}" width="100%" '
         f'role="img" aria-label="Distribucion de la desviacion sobre comparables">']
    for i, c in enumerate(cuentas):
        h = c / mx * alto
        x = izq + i * bw
        centro = (bordes[i] + bordes[i + 1]) / 2
        color = OLIVA if centro <= cfg.UMBRAL_OPORTUNIDAD else (
            GRANATE if centro >= -cfg.UMBRAL_OPORTUNIDAD else REGISTRO)
        op = "0.9" if centro <= cfg.UMBRAL_OPORTUNIDAD else "0.55"
        p.append(f'<rect x="{x + 1:.1f}" y="{arriba + alto - h:.1f}" '
                 f'width="{bw - 2:.1f}" height="{h:.1f}" fill="{color}" opacity="{op}"/>')
    p.append(f'<line x1="{izq}" y1="{arriba + alto}" x2="{izq + ancho}" '
             f'y2="{arriba + alto}" stroke="{LINEA}"/>')
    for v in [-0.4, -0.2, 0, 0.2, 0.4]:
        x = izq + (v + 0.45) / 0.9 * ancho
        p.append(f'<text x="{x:.1f}" y="{arriba + alto + 16}" font-size="10" '
                 f'fill="{GRIS}" text-anchor="middle">{int(v * 100)} %</text>')
    xu = izq + (cfg.UMBRAL_OPORTUNIDAD + 0.45) / 0.9 * ancho
    p.append(f'<line x1="{xu:.1f}" y1="{arriba + 2}" x2="{xu:.1f}" '
             f'y2="{arriba + alto}" stroke="{OLIVA}" stroke-width="1.4" '
             f'stroke-dasharray="3 3"/>')
    p.append(f'<text x="{xu - 7:.1f}" y="{arriba + alto + 38}" font-size="10.5" '
             f'fill="{OLIVA}" text-anchor="end">aviso a partir de '
             f'{int(cfg.UMBRAL_OPORTUNIDAD * 100)} %</text>')
    p.append("</svg>")
    return "".join(p)


def construir() -> None:
    val = pd.read_csv(cfg.F_VALORADO, parse_dates=["fecha"])
    ref = pd.read_csv(cfg.F_DISTRITOS, comment="#")
    met = json.loads(cfg.F_METRICAS.read_text(encoding="utf-8"))
    calidad = pd.read_csv(cfg.DIR_PROCESSED / "informe_calidad.csv")

    con_val = val[val["desviacion"].notna()]
    e, mo, fugas = met["extraccion"], met["motor_valoracion"], met["control_de_fugas"]

    top = (con_val[con_val["fiabilidad"].isin(["alta", "media"])]
           .nlargest(12, "score_oportunidad"))

    filas_top = "".join(
        f"<tr><td>{r.ref}</td><td>{r.distrito}</td>"
        f"<td class='n'>{r.superficie_m2:.0f}</td>"
        f"<td>{r.estado}</td>"
        f"<td class='n'>{_eur(r.precio_eur)} €</td>"
        f"<td class='n'>{_eur(r.valor_estimado_eur)} €</td>"
        f"<td class='n neg'>{_pct(r.desviacion)}</td>"
        f"<td class='n'>{r.n_comparables}</td>"
        f"<td>{r.fiabilidad}</td></tr>"
        for r in top.itertuples())

    filas_umbral = "".join(
        f"<tr><td class='n'>{_pct(b['umbral'], 0)}</td>"
        f"<td class='n'>{b['marcados']}</td>"
        f"<td class='n'>{_pct(b['precision'])}</td>"
        f"<td class='n'>{_pct(b['recall'])}</td></tr>"
        for b in mo["barrido_umbrales"])

    fmt = e["exactitud_por_formato_de_texto"]
    filas_formato = "".join(
        f"<tr><td>{k}</td><td class='n'>{_pct(v)}</td></tr>"
        for k, v in sorted(fmt.items(), key=lambda x: x[1]))

    no_val = val[val["clasificacion"] == "no valorable"]
    motivos = no_val["motivo_no_valorable"].value_counts()

    pasos = [
        ("Anuncios en texto libre",
         f"{e['n_anuncios']} notas de captación, mensajes internos, correos y fichas "
         f"en cinco formatos distintos."),
        ("Extracción",
         f"Un modelo de lenguaje devuelve JSON con esquema fijo. Reparto de esta "
         f"ejecución, con la exactitud de cada motor por separado: "
         + "; ".join(f"{k} sobre {v['n_anuncios']} anuncios, {_pct(v['exactitud'])}"
                     for k, v in sorted(e["reparto_por_motor"].items())) + "."),
        ("Limpieza y validación",
         f"Tipado, unificación de nombres de distrito, rangos plausibles y "
         f"descarte trazable. {len(calidad)} incidencias registradas, ninguna silenciosa."),
        ("Valoración por comparables",
         f"Mismo distrito, superficie ±{cfg.BANDA_SUPERFICIE:.0%}, publicados antes. "
         f"Mínimo {cfg.MIN_COMPARABLES} comparables o no se emite valor."),
        ("Excel y dashboard",
         "Tabla plana lista para Power BI, más este panel. Un comando reconstruye "
         "todo de principio a fin."),
    ]
    html_pasos = "".join(
        f"<li><h3>{t}</h3><p>{d}</p></li>" for t, d in pasos)

    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Valoración por comparables — Madrid</title>
<style>
  :root {{
    --tinta: {TINTA}; --registro: {REGISTRO}; --papel: {PAPEL};
    --oliva: {OLIVA}; --granate: {GRANATE}; --gris: {GRIS}; --linea: {LINEA};
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--papel); color: var(--tinta);
    font-family: "Segoe UI", Roboto, -apple-system, "Helvetica Neue", Arial, sans-serif;
    font-size: 15px; line-height: 1.55; font-variant-numeric: tabular-nums;
  }}
  .hoja {{ max-width: 940px; margin: 0 auto; padding: 40px 26px 72px; }}
  header {{ border-bottom: 3px solid var(--registro); padding-bottom: 18px; }}
  h1 {{
    font-family: Georgia, "Iowan Old Style", "Times New Roman", serif;
    font-size: 31px; line-height: 1.16; font-weight: 600; margin: 0 0 8px;
    letter-spacing: -0.01em;
  }}
  header p {{ margin: 0; color: var(--gris); font-size: 14px; max-width: 66ch; }}
  .sello {{ font-size: 12.5px; color: var(--gris); margin-top: 14px; }}
  section {{ margin-top: 44px; }}
  h2 {{
    font-family: Georgia, "Iowan Old Style", serif; font-size: 20px;
    font-weight: 600; margin: 0 0 6px;
  }}
  .pie {{ color: var(--gris); font-size: 13px; margin: 6px 0 18px; max-width: 72ch; }}
  .panel {{ background: {BLANCO}; border: 1px solid var(--linea); padding: 22px 24px; }}
  .cifras {{ display: flex; flex-wrap: wrap; gap: 0; border-top: 1px solid var(--linea); }}
  .cifra {{
    flex: 1 1 150px; padding: 16px 20px 14px;
    border-bottom: 1px solid var(--linea); border-right: 1px solid var(--linea);
    background: {BLANCO};
  }}
  .cifra:last-child {{ border-right: 0; }}
  .cifra b {{ display: block; font-size: 25px; font-weight: 600; letter-spacing: -0.01em; }}
  .cifra span {{ font-size: 12.5px; color: var(--gris); }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; background: {BLANCO}; }}
  th {{
    text-align: left; font-weight: 600; font-size: 12.5px; color: {BLANCO};
    background: var(--registro); padding: 8px 10px;
  }}
  td {{ padding: 7px 10px; border-bottom: 1px solid var(--linea); }}
  td.n, th.n {{ text-align: right; }}
  td:first-child {{ white-space: nowrap; }}
  td.neg {{ color: var(--oliva); font-weight: 600; }}
  ol.flujo {{ list-style: none; counter-reset: p; margin: 0; padding: 0; }}
  ol.flujo li {{
    counter-increment: p; position: relative; padding: 0 0 18px 46px;
    border-left: 1px solid var(--linea); margin-left: 13px;
  }}
  ol.flujo li:last-child {{ border-left: 1px solid transparent; padding-bottom: 0; }}
  ol.flujo li::before {{
    content: counter(p); position: absolute; left: -13px; top: 0;
    width: 26px; height: 26px; border-radius: 50%; background: var(--registro);
    color: {BLANCO}; font-size: 13px; text-align: center; line-height: 26px;
  }}
  ol.flujo h3 {{ margin: 2px 0 3px; font-size: 15.5px; font-weight: 600; }}
  ol.flujo p {{ margin: 0; color: var(--gris); font-size: 13.5px; max-width: 68ch; }}
  .limites {{ border-left: 4px solid var(--granate); padding: 4px 0 4px 20px; }}
  .limites li {{ margin-bottom: 9px; max-width: 74ch; }}
  .dos {{ display: grid; grid-template-columns: 1.35fr 1fr; gap: 26px; align-items: start; }}
  @media (max-width: 720px) {{ .dos {{ grid-template-columns: 1fr; }} }}
  footer {{ margin-top: 52px; padding-top: 16px; border-top: 1px solid var(--linea);
            color: var(--gris); font-size: 12.5px; }}
  a {{ color: var(--registro); }}
</style></head>
<body><div class="hoja">

<header>
  <h1>Valoración por comparables<br>del mercado residencial de Madrid</h1>
  <p>De anuncios en texto libre a una lista priorizada de inmuebles cuyo precio
     se aparta de lo que piden los pisos equivalentes de su distrito.</p>
  <p class="sello">Ejecutado el {ahora} sobre {e['n_anuncios']} anuncios.
     Motor de extracción: {e['motor']}. Semilla {cfg.SEMILLA}.</p>
</header>

<section>
  <h2>Precio pedido por metro cuadrado, por distrito</h2>
  <p class="pie">Mediana del €/m² pedido en los anuncios procesados. La marca roja
     de cada barra es el precio medio realmente declarado en escritura en 2022
     (Colegio de Registradores). No son la misma magnitud: una es oferta y la otra
     cierre, y median cuatro años.</p>
  <div class="panel">{escalera_distritos(con_val, ref)}</div>
</section>

<div class="cifras">
  <div class="cifra"><b>{len(val)}</b><span>inmuebles procesados</span></div>
  <div class="cifra"><b>{_pct(mo['cobertura'], 0)}</b><span>con valoración emitida</span></div>
  <div class="cifra"><b>{(val['clasificacion'] == 'por debajo de comparables').sum()}</b>
    <span>por debajo de sus comparables</span></div>
  <div class="cifra"><b>{_pct(max(v['exactitud'] for v in e['reparto_por_motor'].values()))}</b>
    <span>campos bien extraídos, mejor motor de {len(e['reparto_por_motor'])}</span></div>
  <div class="cifra"><b>{fugas['inmuebles_en_sus_propios_comparables']}</b>
    <span>fugas de información detectadas</span></div>
</div>

<section>
  <h2>Cómo funciona</h2>
  <p class="pie">Cinco pasos encadenados. Cada uno deja su rastro en disco, así que
     cualquier cifra de esta página se puede reconstruir desde el anuncio original.</p>
  <ol class="flujo">{html_pasos}</ol>
</section>

<section class="dos">
  <div>
    <h2>Dónde cae cada inmueble</h2>
    <p class="pie">Distancia entre el precio pedido y la mediana de sus comparables.
       En verde, los que quedan más de un 10 % por debajo.</p>
    <div class="panel">{histograma_desviacion(con_val)}</div>
  </div>
  <div>
    <h2>Dónde poner el aviso</h2>
    <p class="pie">No hay umbral correcto. Cuanto más exigente, más limpia la lista
       y más oportunidades se escapan.</p>
    <table><thead><tr><th class="n">Umbral</th><th class="n">Marcados</th>
      <th class="n">Aciertos</th><th class="n">Cobertura</th></tr></thead>
      <tbody>{filas_umbral}</tbody></table>
  </div>
</section>

<section>
  <h2>Los doce con mayor desviación a la baja</h2>
  <p class="pie">Sólo inmuebles con fiabilidad alta o media. Un precio por debajo de
     los comparables no significa que sea una ganga: significa que merece una
     llamada para averiguar por qué.</p>
  <table><thead><tr>
    <th>Ref.</th><th>Distrito</th><th class="n">m²</th><th>Estado</th>
    <th class="n">Precio pedido</th><th class="n">Valor estimado</th>
    <th class="n">Desviación</th><th class="n">Comp.</th><th>Fiabilidad</th>
  </tr></thead><tbody>{filas_top}</tbody></table>
</section>

<section class="dos">
  <div>
    <h2>Dónde falla la extracción</h2>
    <p class="pie">Porcentaje de campos correctos según el formato del texto de origen.</p>
    <table><thead><tr><th>Formato del texto</th><th class="n">Campos correctos</th>
      </tr></thead><tbody>{filas_formato}</tbody></table>
  </div>
  <div>
    <h2>Por qué {len(no_val)} inmuebles no se valoran</h2>
    <p class="pie">El sistema prefiere callarse antes que dar un número que no
       sostiene.</p>
    <table><thead><tr><th>Motivo</th><th class="n">Inmuebles</th></tr></thead>
      <tbody>{''.join(f"<tr><td>{k}</td><td class='n'>{v}</td></tr>"
                      for k, v in motivos.items())}</tbody></table>
  </div>
</section>

<section>
  <h2>Lo que esta demo no demuestra</h2>
  <ul class="limites">
    <li>Los anuncios son sintéticos. Los términos de uso de los portales prohíben
        el scraping, así que el corpus se genera y se calibra con estadística
        pública real de precio y superficie por distrito.</li>
    <li>Las desviaciones que el motor recupera se inyectaron al generar los datos.
        Es circular por construcción: prueba que la mecánica funciona, no que el
        modelo encuentre oportunidades reales.</li>
    <li>La referencia es el precio pedido, no el de cierre. Mide distancia a la
        oferta comparable, no descuento sobre valor de mercado real.</li>
    <li>La etiqueta de fiabilidad no discrimina en este corpus: el error mediano de
        valoración es {_pct(mo['error_mediano_valoracion'])} en los tres niveles,
        porque la dispersión del generador es homogénea. Con datos reales debería
        discriminar. Aquí no lo hace y se dice.</li>
  </ul>
</section>

<footer>
  Fuentes: Ayuntamiento de Madrid, Anuario Estadístico 2023, capítulo 8, a partir de
  la Estadística Registral Inmobiliaria del Colegio de Registradores (datos de 2022);
  Ministerio de Vivienda y Agenda Urbana, estadística de valor tasado de la vivienda.
  Ambas consultadas el 04/09/2026. Ningún dato personal de vendedores o terceros
  interviene en el proceso.
</footer>

</div></body></html>"""

    cfg.DIR_OUTPUTS.mkdir(parents=True, exist_ok=True)
    cfg.F_DASHBOARD.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    construir()
    print(f"Dashboard generado -> {cfg.F_DASHBOARD}")

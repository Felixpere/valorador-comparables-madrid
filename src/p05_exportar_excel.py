"""Paso 05 — Libro de Excel.

Es a la vez el entregable que se abre en una reunion y la fuente de datos de
Power BI. Por eso la hoja "Valoraciones" es una tabla plana sin celdas
combinadas ni encabezados a dos alturas: asi Power BI la carga sin transformar.

Las hojas de resumen usan formulas (COUNTIFS, AVERAGEIFS, MEDIAN), no valores
calculados en Python y pegados. Si alguien filtra o corrige un dato, los totales
se mueven solos.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

import config as cfg

FUENTE = "Arial"
AZUL = "1F3A5F"
GRIS = "F2F2F2"
BORDE = Border(bottom=Side(style="thin", color="BFBFBF"))

EUR = '#,##0 "€"'
EUR_M2 = '#,##0 "€/m²"'
PCT = "0.0%"


def _titulo(ws, texto, fila=1, ancho=8):
    c = ws.cell(row=fila, column=1, value=texto)
    c.font = Font(name=FUENTE, size=14, bold=True, color=AZUL)
    ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=ancho)
    ws.row_dimensions[fila].height = 22


def _cabecera(ws, fila, valores):
    for j, v in enumerate(valores, start=1):
        c = ws.cell(row=fila, column=j, value=v)
        c.font = Font(name=FUENTE, size=10, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=AZUL)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[fila].height = 30


def _anchos(ws, anchos):
    for i, a in enumerate(anchos, start=1):
        ws.column_dimensions[get_column_letter(i)].width = a


def _escribir_tabla(ws, df, fila_ini, nombre_tabla=None):
    _cabecera(ws, fila_ini, list(df.columns))
    for i, (_, r) in enumerate(df.iterrows(), start=fila_ini + 1):
        for j, v in enumerate(r, start=1):
            c = ws.cell(row=i, column=j,
                        value=(None if pd.isna(v) else
                               (v.date() if isinstance(v, pd.Timestamp) else v)))
            c.font = Font(name=FUENTE, size=10)
            c.border = BORDE
    if nombre_tabla and len(df):
        ref = (f"A{fila_ini}:{get_column_letter(len(df.columns))}"
               f"{fila_ini + len(df)}")
        t = Table(displayName=nombre_tabla, ref=ref)
        t.tableStyleInfo = TableStyleInfo(name="TableStyleLight9", showRowStripes=True)
        ws.add_table(t)
    return fila_ini + len(df)


# Nombres legibles de las variables del ajuste hedonico de r01, para no volcar
# los identificadores internos en un entregable que se abre en una reunion.
ETIQUETAS_COEF = {
    "log_superficie": "Superficie (elasticidad del €/m²)",
    "obra_nueva": "Obra nueva",
    "a_reformar": "Segunda mano a reformar",
    "ascensor": "Ascensor",
    "terraza": "Terraza",
    "aire_acondicionado": "Aire acondicionado",
    "interior": "Interior",
    "planta": "Planta (por planta)",
    "ultima_planta": "Última planta",
    "garaje": "Garaje",
    "trastero": "Trastero",
    "piscina": "Piscina",
    "portero": "Portero",
    "jardin": "Jardín",
    "duplex": "Dúplex",
    "estudio": "Estudio",
    "calidad_catastral": "Calidad catastral (por grado)",
    "antiguedad": "Antigüedad (por año)",
}


def _subtitulo(ws, fila, texto):
    c = ws.cell(row=fila, column=1, value=texto)
    c.font = Font(name=FUENTE, size=11, bold=True, color=AZUL)
    return fila + 1


def _nota(ws, fila, texto, ancho=5, alto=30, aviso=False):
    """Linea de texto al ancho de la hoja. Con `aviso`, en rojo y en negrita.

    El rojo se reserva para lo que no se puede leer mal sin equivocarse con la
    cifra de al lado: de que ano son los datos y que es exactamente lo que miden.
    """
    c = ws.cell(row=fila, column=1, value=texto)
    c.font = (Font(name=FUENTE, size=9, bold=True, color="9C2A2A") if aviso
              else Font(name=FUENTE, size=9, italic=True, color="7F7F7F"))
    c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=ancho)
    ws.row_dimensions[fila].height = alto
    return fila + 1


def hoja_validacion_2018(wb, m: dict, diagnostico: dict | None = None) -> None:
    """Hoja con la validacion sobre datos REALES (idealista18, Madrid 2018).

    Es la hoja equivalente a lo que ya ensenaba `outputs/dashboard_real.html`,
    en el libro que carga Power BI. Va en tablas planas y con nombre
    (tblReal*) para que el navegador de Power BI las coja sin transformar.

    Las cifras se leen de `data/real/metricas_2018.json`, no se recalculan aqui:
    el Excel no es una segunda fuente de verdad.

    Nada de esta hoja se mezcla con el resto del libro: el resto mide el motor
    contra la verdad de terreno de un corpus sintetico y esta lo mide contra el
    precio pedido de anuncios reales. Son objetivos distintos sobre datos
    distintos, y por eso van en tablas separadas y se dice en el encabezado.
    """
    ws = wb.create_sheet("Validación 2018", 1)
    _titulo(ws, "Validación con datos reales — idealista18, Madrid, 2018", ancho=5)

    f = _nota(ws, 2,
              "DATOS DE 2018. Los niveles de precio de esta hoja no son los de hoy; lo "
              "que sigue siendo informativo es la estructura del mercado, no el nivel. "
              "Y lo que se mide es el PRECIO PEDIDO de un anuncio, NO el precio de "
              "cierre en escritura: el motor reproduce lo que pide un anuncio, no lo "
              "que vale el piso ni por cuánto se vendió.",
              ancho=5, alto=52, aviso=True)

    f = _nota(ws, f,
              "Estas cifras NO son comparables con las del resto del libro, que mide el "
              "motor contra la verdad de terreno de un corpus sintético. Objetivos "
              "distintos medidos sobre datos distintos: no se suman, no se promedian y "
              "no van en el mismo indicador.", ancho=5, alto=42)

    f = _subtitulo(ws, f + 1, "Cómo está montada la validación")
    ficha = pd.DataFrame({
        "Concepto": ["Anuncios utilizables", "Conjunto de comparables (pool)",
                     "Conjunto de evaluación (nunca visto)", "Cobertura"],
        "Valor": [m["n_anuncios_utilizables"], m["n_pool"], m["n_evaluacion"],
                  m["cobertura"]],
    })
    fin = _escribir_tabla(ws, ficha, f, "tblRealFicha")
    for i in range(f + 1, fin + 1):
        ws.cell(row=i, column=2).number_format = "#,##0"
    ws.cell(row=fin, column=2).number_format = PCT

    f = _subtitulo(ws, fin + 2, "El motor contra dos líneas base más tontas")
    metodos = pd.DataFrame([
        {"Método": nombre,
         "Error mediano": m[clave]["error_absoluto_mediano"],
         "Dentro de ±10 %": m[clave]["dentro_de_10pct"],
         "Dentro de ±20 %": m[clave]["dentro_de_20pct"],
         "Sesgo mediano": m[clave]["sesgo_mediano"]}
        for nombre, clave in [("Comparables por barrio", "motor_comparables"),
                              ("Mediana del barrio y trimestre", "base_mediana_barrio"),
                              ("Mediana de la ciudad", "base_mediana_ciudad")]])
    fin = _escribir_tabla(ws, metodos, f, "tblRealMetodos")
    for i in range(f + 1, fin + 1):
        for j in range(2, 6):
            ws.cell(row=i, column=j).number_format = PCT

    f = _nota(ws, fin + 1,
              "Leído con honestidad: la mayor parte del trabajo la hace saber en qué "
              "barrio está el piso. El motor mejora la mediana del barrio, pero no la "
              "deja atrás.", ancho=5, alto=28)

    f = _subtitulo(ws, f + 1, "La etiqueta de fiabilidad, con datos reales")
    fiab = pd.DataFrame({
        "Fiabilidad": [k.capitalize() for k in ["alta", "media", "baja"]
                       if k in m["error_por_fiabilidad"]],
        "Error mediano": [m["error_por_fiabilidad"][k] for k in ["alta", "media", "baja"]
                          if k in m["error_por_fiabilidad"]],
    })
    fin = _escribir_tabla(ws, fiab, f, "tblRealFiabilidad")
    for i in range(f + 1, fin + 1):
        ws.cell(row=i, column=2).number_format = PCT

    f = _nota(ws, fin + 1,
              "Con el corpus sintético esta etiqueta no discriminaba y quedó escrito "
              "como fallo abierto. Con datos reales sí discrimina.", ancho=5, alto=28)

    # --- Coeficientes -------------------------------------------------------
    f = _subtitulo(ws, f + 1, "Qué pesa en el precio por metro cuadrado")
    coef = m["coeficientes"]
    filas = [{"Atributo": ETIQUETAS_COEF.get(k, k),
              "Efecto sobre €/m²": round(float(np.expm1(v)), 4),
              "Coeficiente (log)": v}
             for k, v in coef.items()]
    filas.sort(key=lambda r: abs(r["Efecto sobre €/m²"]), reverse=True)
    fin = _escribir_tabla(ws, pd.DataFrame(filas), f, "tblRealCoeficientes")
    for i in range(f + 1, fin + 1):
        ws.cell(row=i, column=2).number_format = PCT
        ws.cell(row=i, column=3).number_format = "0.0000"

    f = _nota(ws, fin + 1,
              "Estimados sobre el pool y centrados por barrio y trimestre, así que "
              "miden el atributo aislado del efecto de la zona. La columna de efecto "
              "es exp(coeficiente) − 1.", ancho=5, alto=28)

    if diagnostico:
        f = _subtitulo(ws, f + 1, "Los dos coeficientes que estaban en cuarentena")
        ver = pd.DataFrame({
            "Coeficiente": [ETIQUETAS_COEF.get(k, k) for k in diagnostico["veredicto"]],
            "Veredicto tras verificarlo": list(diagnostico["veredicto"].values()),
        })
        fin = _escribir_tabla(ws, ver, f, "tblRealVeredicto")
        for i in range(f + 1, fin + 1):
            ws.cell(row=i, column=2).alignment = Alignment(wrap_text=True,
                                                           vertical="top")
            ws.row_dimensions[i].height = 76
        f = fin + 2

    # --- Limitaciones y fuente ----------------------------------------------
    f = _subtitulo(ws, f, "Lo que estos datos no permiten decir")
    lim = pd.DataFrame({"Limitación": m["limitaciones"]})
    fin = _escribir_tabla(ws, lim, f, "tblRealLimitaciones")
    for i in range(f + 1, fin + 1):
        ws.cell(row=i, column=1).alignment = Alignment(wrap_text=True, vertical="top")

    _nota(ws, fin + 2, f"Fuente: {m['fuente']}", ancho=5, alto=30)
    _anchos(ws, [40, 30, 18, 16, 16])


def construir() -> None:
    val = pd.read_csv(cfg.F_VALORADO, parse_dates=["fecha"])
    calidad = pd.read_csv(cfg.DIR_PROCESSED / "informe_calidad.csv")
    metricas = json.loads(cfg.F_METRICAS.read_text(encoding="utf-8"))
    distritos = pd.read_csv(cfg.F_DISTRITOS, comment="#")

    wb = Workbook()

    # ------------------------------------------------------- Hoja Valoraciones
    ws = wb.active
    ws.title = "Valoraciones"
    cols = ["ref", "fecha", "distrito", "superficie_m2", "estado", "precio_eur",
            "eur_m2_pedido", "valor_estimado_eur", "eur_m2_comparables",
            "desviacion", "score_oportunidad", "n_comparables", "fiabilidad",
            "clasificacion", "motivo_no_valorable"]
    tabla = val[cols].rename(columns={
        "ref": "Referencia", "fecha": "Fecha", "distrito": "Distrito",
        "superficie_m2": "Superficie (m²)", "estado": "Estado",
        "precio_eur": "Precio pedido", "eur_m2_pedido": "€/m² pedido",
        "valor_estimado_eur": "Valor estimado", "eur_m2_comparables": "€/m² comparables",
        "desviacion": "Desviación", "score_oportunidad": "Score",
        "n_comparables": "Nº comparables", "fiabilidad": "Fiabilidad",
        "clasificacion": "Clasificación", "motivo_no_valorable": "Motivo si no valorable",
    }).sort_values("Fecha")

    fin = _escribir_tabla(ws, tabla, 1, "tblValoraciones")
    _anchos(ws, [12, 11, 20, 13, 13, 14, 13, 14, 15, 11, 9, 12, 11, 24, 30])
    for fila in range(2, fin + 1):
        ws.cell(row=fila, column=2).number_format = "DD/MM/YYYY"
        ws.cell(row=fila, column=6).number_format = EUR
        ws.cell(row=fila, column=7).number_format = EUR_M2
        ws.cell(row=fila, column=8).number_format = EUR
        ws.cell(row=fila, column=9).number_format = EUR_M2
        ws.cell(row=fila, column=10).number_format = PCT
        ws.cell(row=fila, column=11).number_format = "0.0"
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:O{fin}"
    ULT = fin

    # ------------------------------------------------------------- Hoja Resumen
    rs = wb.create_sheet("Resumen", 0)
    _titulo(rs, "Valoración por comparables — mercado residencial de Madrid")
    rs["A2"] = ("Demo técnica. Los anuncios son sintéticos; los precios de referencia "
                "por distrito son reales. Ver la hoja «Supuestos y fuentes».")
    rs["A2"].font = Font(name=FUENTE, size=9, italic=True, color="7F7F7F")
    rs.merge_cells("A2:F2")

    V = f"Valoraciones!"
    kpis = [
        ("Inmuebles procesados", f"=COUNTA({V}$A$2:$A${ULT})", "#,##0"),
        ("Con valoración emitida",
         f'=COUNTIF({V}$N$2:$N${ULT},"<>no valorable")', "#,##0"),
        ("Cobertura",
         f'=IFERROR(COUNTIF({V}$N$2:$N${ULT},"<>no valorable")/'
         f'COUNTA({V}$A$2:$A${ULT}),0)', PCT),
        ("Por debajo de comparables",
         f'=COUNTIF({V}$N$2:$N${ULT},"por debajo de comparables")', "#,##0"),
        ("Por encima de comparables",
         f'=COUNTIF({V}$N$2:$N${ULT},"por encima de comparables")', "#,##0"),
        ("Desviación mediana",
         f"=IFERROR(MEDIAN({V}$J$2:$J${ULT}),0)", PCT),
        ("€/m² pedido, mediana",
         f"=IFERROR(MEDIAN({V}$G$2:$G${ULT}),0)", EUR_M2),
        ("Valor total de la cartera analizada",
         f"=SUM({V}$F$2:$F${ULT})", EUR),
    ]
    rs["A4"], rs["B4"] = "Indicador", "Valor"
    _cabecera(rs, 4, ["Indicador", "Valor"])
    for i, (nombre, formula, fmt) in enumerate(kpis, start=5):
        rs.cell(row=i, column=1, value=nombre).font = Font(name=FUENTE, size=10)
        c = rs.cell(row=i, column=2, value=formula)
        c.font = Font(name=FUENTE, size=10, bold=True)
        c.number_format = fmt
        rs.cell(row=i, column=1).border = BORDE
        c.border = BORDE

    fila = len(kpis) + 7
    rs.cell(row=fila - 1, column=1,
            value="Calidad del proceso (medido sobre corpus sintético)").font = \
        Font(name=FUENTE, size=11, bold=True, color=AZUL)
    e, mo = metricas["extraccion"], metricas["motor_valoracion"]
    med = [
        ("Motor de extracción usado", e["motor"], "@"),
        ("Campos extraídos correctamente", e["exactitud_global_por_campo"], PCT),
        ("Anuncios sin ningún error de extracción", e["anuncios_perfectos"], PCT),
        ("Error mediano de valoración", mo["error_mediano_valoracion"], PCT),
        ("Correlación desviación estimada / real",
         mo["correlacion_desviacion_estimada_vs_real"], "0.00"),
        ("Inmuebles en sus propios comparables (debe ser 0)",
         metricas["control_de_fugas"]["inmuebles_en_sus_propios_comparables"], "0"),
        ("Comparables con fecha posterior (debe ser 0)",
         metricas["control_de_fugas"]["comparables_con_fecha_igual_o_posterior"], "0"),
    ]
    _cabecera(rs, fila, ["Indicador", "Valor"])
    for i, (n, v, fmt) in enumerate(med, start=fila + 1):
        rs.cell(row=i, column=1, value=n).font = Font(name=FUENTE, size=10)
        c = rs.cell(row=i, column=2, value=v)
        c.font = Font(name=FUENTE, size=10, bold=True)
        c.number_format = fmt
    _anchos(rs, [46, 22, 14, 14, 14, 14])

    # -------------------------------------------------------- Hoja Por distrito
    pd_ws = wb.create_sheet("Por distrito")
    _titulo(pd_ws, "Resumen por distrito", ancho=6)
    _cabecera(pd_ws, 3, ["Distrito", "Inmuebles", "€/m² pedido (media)",
                         "Desviación media", "Por debajo de comparables",
                         "Referencia oficial 2022 (€/m²)"])
    for i, d in enumerate(sorted(distritos["distrito"]), start=4):
        pd_ws.cell(row=i, column=1, value=d).font = Font(name=FUENTE, size=10)
        pd_ws.cell(row=i, column=2,
                   value=f'=COUNTIF({V}$C$2:$C${ULT},$A{i})').number_format = "#,##0"
        pd_ws.cell(row=i, column=3,
                   value=f'=IFERROR(AVERAGEIF({V}$C$2:$C${ULT},$A{i},'
                         f'{V}$G$2:$G${ULT}),"")').number_format = EUR_M2
        pd_ws.cell(row=i, column=4,
                   value=f'=IFERROR(AVERAGEIF({V}$C$2:$C${ULT},$A{i},'
                         f'{V}$J$2:$J${ULT}),"")').number_format = PCT
        pd_ws.cell(row=i, column=5,
                   value=f'=COUNTIFS({V}$C$2:$C${ULT},$A{i},{V}$N$2:$N${ULT},'
                         f'"por debajo de comparables")').number_format = "#,##0"
        ref = float(distritos.loc[distritos["distrito"] == d,
                                  "precio_m2_2022"].iat[0])
        pd_ws.cell(row=i, column=6, value=ref).number_format = EUR_M2
        for j in range(1, 7):
            pd_ws.cell(row=i, column=j).font = Font(name=FUENTE, size=10)
            pd_ws.cell(row=i, column=j).border = BORDE
    nota = len(distritos) + 5
    pd_ws.cell(row=nota, column=1,
               value="La columna de referencia oficial es el precio medio declarado en "
                     "escritura en 2022 (Colegio de Registradores, vía Ayuntamiento de "
                     "Madrid). No es comparable directamente con el €/m² pedido: uno es "
                     "precio de cierre y el otro precio de oferta, y median cuatro años."
               ).font = Font(name=FUENTE, size=9, italic=True, color="7F7F7F")
    pd_ws.merge_cells(start_row=nota, start_column=1, end_row=nota, end_column=6)
    pd_ws.row_dimensions[nota].height = 45
    pd_ws.cell(row=nota, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    _anchos(pd_ws, [24, 12, 20, 18, 26, 28])

    # ---------------------------------------------------------- Hoja Umbrales
    um = wb.create_sheet("Umbral de aviso")
    _titulo(um, "Qué pasa al mover el umbral de aviso", ancho=4)
    um["A2"] = ("No hay un umbral correcto. Cuanto más exigente, más limpia es la "
                "lista de avisos y más oportunidades se escapan. La decisión es de "
                "negocio: cuántas visitas en falso se pueden asumir.")
    um["A2"].font = Font(name=FUENTE, size=9, italic=True, color="7F7F7F")
    um.merge_cells("A2:E2")
    _cabecera(um, 4, ["Umbral de desviación", "Inmuebles marcados",
                      "Precisión", "Cobertura de los infraprecios reales"])
    for i, b in enumerate(mo["barrido_umbrales"], start=5):
        um.cell(row=i, column=1, value=b["umbral"]).number_format = PCT
        um.cell(row=i, column=2, value=b["marcados"]).number_format = "#,##0"
        um.cell(row=i, column=3, value=b["precision"]).number_format = PCT
        um.cell(row=i, column=4, value=b["recall"]).number_format = PCT
        for j in range(1, 5):
            um.cell(row=i, column=j).font = Font(name=FUENTE, size=10)
            um.cell(row=i, column=j).border = BORDE
    _anchos(um, [22, 20, 14, 34])

    # ------------------------------------------------------- Hoja Calidad dato
    cd = wb.create_sheet("Calidad del dato")
    _titulo(cd, "Incidencias detectadas en la limpieza", ancho=3)
    cd["A2"] = ("Ninguna fila se descarta en silencio. Cada incidencia queda aquí "
                "con su referencia y su motivo.")
    cd["A2"].font = Font(name=FUENTE, size=9, italic=True, color="7F7F7F")
    cd.merge_cells("A2:D2")
    if len(calidad):
        resumen = (calidad.groupby(["campo", "motivo"]).size()
                   .reset_index(name="incidencias")
                   .sort_values("incidencias", ascending=False))
        f = _escribir_tabla(cd, resumen, 4)
        _escribir_tabla(cd, calidad, f + 3, None)
        cd.cell(row=f + 2, column=1, value="Detalle").font = \
            Font(name=FUENTE, size=11, bold=True, color=AZUL)
    else:
        cd["A4"] = "Sin incidencias en esta ejecución."
    _anchos(cd, [22, 46, 14, 14])

    # ---------------------------------------------------- Hoja Supuestos
    sf = wb.create_sheet("Supuestos y fuentes")
    _titulo(sf, "Supuestos, límites y fuentes", ancho=3)
    lineas = [
        ("SUPUESTO", "Los anuncios son sintéticos. Los términos de uso de los portales "
         "inmobiliarios prohíben el scraping, así que el corpus se genera "
         "artificialmente."),
        ("SUPUESTO", "El corpus se calibra con la distribución real de precio medio "
         "declarado y de superficies por distrito de Madrid (2022)."),
        ("SUPUESTO", f"Factor de actualización de 2022 a nivel 2026: "
         f"{cfg.FACTOR_ACTUALIZACION}. Se aplica igual a los 21 distritos, lo cual es "
         f"falso: Madrid no se ha revalorizado de forma homogénea. No afecta a la "
         f"lógica de comparables, que es relativa dentro de cada distrito."),
        ("SUPUESTO", f"Comparable = mismo distrito, superficie ±"
         f"{cfg.BANDA_SUPERFICIE:.0%}, publicado en los {cfg.VENTANA_DIAS} días "
         f"anteriores. Mínimo {cfg.MIN_COMPARABLES} para emitir valoración."),
        ("LÍMITE", "El precio de referencia es el precio PEDIDO, no el de cierre. La "
         "desviación mide distancia a la oferta comparable, no descuento sobre "
         "valor de mercado real."),
        ("LÍMITE", "Las métricas se miden contra la verdad de terreno del corpus "
         "sintético. Demuestran que la mecánica funciona, no que el modelo acierte "
         "precios reales de Madrid."),
        ("LÍMITE", "Las desviaciones que el motor recupera se inyectaron al generar "
         "los datos. Es circular por construcción y no prueba capacidad predictiva."),
        ("LÍMITE", "La etiqueta de fiabilidad no discrimina en este corpus: el error "
         "está dominado por dispersión idiosincrática homogénea por construcción. "
         "Con datos reales debería discriminar; aquí no lo hace y se dice."),
        ("LÍMITE", "Sin datos personales de vendedores ni de terceros en ninguna "
         "fase del proceso."),
    ]
    for src in cfg.FUENTES:
        lineas.append(("FUENTE", f"{src[0]} — {src[1]} ({src[2]})"))

    _cabecera(sf, 3, ["Tipo", "Descripción"])
    for i, (tipo, txt) in enumerate(lineas, start=4):
        c1 = sf.cell(row=i, column=1, value=tipo)
        c1.font = Font(name=FUENTE, size=10, bold=True,
                       color={"SUPUESTO": "8A6D00", "LÍMITE": "9C2A2A",
                              "FUENTE": AZUL}[tipo])
        c2 = sf.cell(row=i, column=2, value=txt)
        c2.font = Font(name=FUENTE, size=10)
        c2.alignment = Alignment(wrap_text=True, vertical="top")
        sf.row_dimensions[i].height = 42
        c1.border = c2.border = BORDE
    _anchos(sf, [14, 110])

    # ------------------------------------------------- Hoja de datos reales
    # Opcional: solo si el circuito con idealista18 se ha ejecutado. Sin ella el
    # libro sale igual, con una hoja menos, y el pipeline sintetico no depende
    # de un fichero de 26 MB que no viaja en el repositorio.
    if cfg.F_METRICAS_REALES.exists():
        diag = (json.loads(cfg.F_DIAGNOSTICO_REAL.read_text(encoding="utf-8"))
                if cfg.F_DIAGNOSTICO_REAL.exists() else None)
        hoja_validacion_2018(
            wb, json.loads(cfg.F_METRICAS_REALES.read_text(encoding="utf-8")), diag)

    cfg.DIR_OUTPUTS.mkdir(parents=True, exist_ok=True)
    wb.save(cfg.F_EXCEL)


if __name__ == "__main__":
    construir()
    print(f"Excel generado -> {cfg.F_EXCEL}")

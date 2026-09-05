# Conectar el Excel a Power BI

La hoja `Valoraciones` está diseñada para cargarse sin transformaciones: una fila
por inmueble, una cabecera en la fila 1, sin celdas combinadas y sin totales
intercalados.

## Carga

1. Power BI Desktop → **Obtener datos** → **Excel** → `outputs/valoraciones_madrid.xlsx`.
2. En el navegador, marcar la tabla **tblValoraciones** (no la hoja: la tabla ya
   trae el rango delimitado).
3. **Transformar datos** y comprobar tipos: `Fecha` como fecha, `Desviación` y
   `Score` como decimal, el resto según corresponda.
4. Cerrar y aplicar.

Las hojas de resumen del Excel usan fórmulas y no hace falta cargarlas: en Power
BI esos indicadores se rehacen como medidas.

## La hoja de datos reales

La hoja **`Validación 2018`** trae la validación contra `idealista18` (Madrid,
2018), que es la misma que enseña `outputs/dashboard_real.html`. Va en seis tablas
con nombre, así que en el navegador de Power BI se marcan sueltas, sin
transformaciones:

| Tabla | Qué trae |
|---|---|
| `tblRealFicha` | Anuncios utilizables, pool, evaluación y cobertura |
| `tblRealMetodos` | El motor contra las dos líneas base, con error, ±10 %, ±20 % y sesgo |
| `tblRealFiabilidad` | Error mediano por etiqueta de fiabilidad |
| `tblRealCoeficientes` | Cada atributo, su efecto sobre el €/m² y su coeficiente |
| `tblRealVeredicto` | Los dos coeficientes que estuvieron en cuarentena, ya verificados |
| `tblRealLimitaciones` | Lo que estos datos no permiten decir |

Son cifras ya calculadas, no una tabla de hechos: `tblRealMetodos` y
`tblRealFiabilidad` se pintan tal cual y **no se agregan**. Si se ponen en el mismo
informe que `tblValoraciones`, van en una página aparte y sin relación entre
tablas: miden cosas distintas sobre datos distintos, y cruzarlas produce números
que no significan nada.

La hoja sale del libro sólo si el circuito con datos reales se ha ejecutado
(`src/r00` → `r01` → `r04`). Sin `data/real/`, el Excel se genera igual con una
hoja menos.

## Medidas de partida

```dax
Inmuebles = COUNTROWS(tblValoraciones)

Con valoración =
CALCULATE([Inmuebles], tblValoraciones[Clasificación] <> "no valorable")

Cobertura = DIVIDE([Con valoración], [Inmuebles])

Por debajo de comparables =
CALCULATE([Inmuebles], tblValoraciones[Clasificación] = "por debajo de comparables")

Desviación mediana = MEDIAN(tblValoraciones[Desviación])

€/m² pedido mediano = MEDIAN(tblValoraciones['€/m² pedido'])

Valor de la cartera = SUM(tblValoraciones[Precio pedido])
```

## Página sugerida

- **Filtros**: Distrito, Estado, Fiabilidad, rango de Fecha.
- **Arriba**: Inmuebles, Cobertura, Por debajo de comparables, Desviación mediana.
- **Izquierda**: barras horizontales de €/m² mediano por distrito, ordenadas
  descendente.
- **Derecha**: histograma de Desviación, con el corte de aviso marcado.
- **Abajo**: tabla ordenada por Score descendente, filtrada a fiabilidad alta o
  media, con Nº comparables visible. Sin esa columna a la vista, nadie puede
  juzgar cuánto se sostiene cada fila.

## Actualización automática

El proceso se ejecuta solo mediante GitHub Actions (`.github/workflows/pipeline.yml`)
y publica el Excel como artefacto. Para que Power BI se refresque solo, la ruta
habitual es dejar el Excel en SharePoint o OneDrive y programar la actualización
en el servicio de Power BI. En esta demo el Excel es local y se refresca a mano.

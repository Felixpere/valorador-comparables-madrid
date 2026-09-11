# Entregables

Cuatro ficheros listos para abrir. Tres los produce el circuito; el cuarto, el
one-pager, es un resumen hecho a mano a partir de sus resultados. Todo lo demás
del repositorio es el código que los genera y la documentación que los sostiene.

| Fichero | Qué es | De dónde sale |
|---|---|---|
| `dashboard_real.html` | La validación con datos reales de Madrid y una valoración abierta paso a paso. Es el que responde a «¿cómo sabemos que funciona?» | `src/r03_dashboard_real.py` |
| `valoraciones_madrid.xlsx` | Siete hojas: la lista de inmuebles, el resumen por distrito y la validación de 2018. Diseñado para cargarse en Power BI sin transformaciones | `src/p05_exportar_excel.py` |
| `dashboard.html` | El circuito de extracción con IA sobre texto libre | `src/p06_dashboard.py` |
| `one_pager_valoracion_comparables_v2.pdf` | Una página con las cifras y los límites juntos | Hecho a mano: **no** lo genera el circuito |

Los dos HTML se abren con doble clic, sin internet y sin instalar nada. Los tres
ficheros de GitHub Pages se abren también desde el navegador:

- [Validación con datos reales](https://felixpere.github.io/valorador-comparables-madrid/entregables/dashboard_real.html)
- [Circuito de extracción](https://felixpere.github.io/valorador-comparables-madrid/entregables/dashboard.html)
- [Resumen de una página (PDF)](https://felixpere.github.io/valorador-comparables-madrid/entregables/one_pager_valoracion_comparables_v2.pdf)

## Esto es una copia, y no se actualiza sola

Los originales vivos de los tres ficheros del circuito están en `outputs/`, que no
se versiona. Si cambian los datos o el código, **esos tres se quedan viejos y
nadie avisa**.

Para refrescarlos hay que regenerar y volver a copiar. El orden importa y está
detallado en el README, sección «Cómo regenerar los entregables»:

```bash
python src/r01_valorar_real.py
python src/r04_diagnostico_coeficientes.py
python src/r02_caso.py
python src/r03_dashboard_real.py
python run_pipeline.py --motor llm
cp outputs/valoraciones_madrid.xlsx outputs/dashboard_real.html outputs/dashboard.html entregables/
```

**El `--motor llm` no es opcional**: sin él, el Excel pierde la comparación entre
los dos motores de extracción y vuelve a decir sólo «reglas».

**El one-pager no se regenera.** Es un PDF estático: el comando de arriba no lo
toca. Si cambian las cifras, hay que rehacerlo a mano.

## Una advertencia que vale la pena repetir

Desconfíe de cualquier copia de estos ficheros que no salga de aquí o de
`outputs/`. Hubo una editada a mano con una cifra mal, y el error sobrevivió
hasta que se comparó contra el fichero regenerado desde el código.

Todo lo que publica el circuito sale del código. Un test comprueba que cada cifra
del panel coincide con el fichero de resultados del que dice venir.

# Entregables

Tres ficheros listos para abrir. Dos los produce el circuito; el tercero, el
one-pager, es un resumen hecho a mano a partir de sus resultados. Todo lo demás
del repositorio es el código que los genera y la documentación que los sostiene.

| Fichero | Qué es | De dónde sale |
|---|---|---|
| `dashboard_real.html` | La validación con datos reales de Madrid y una valoración abierta paso a paso. Es el que responde a «¿cómo sabemos que funciona?» | `src/r03_dashboard_real.py` |
| `dashboard.html` | El circuito de extracción con IA sobre texto libre | `src/p06_dashboard.py` |
| `one_pager_valoracion_comparables_v2.pdf` | Una página con las cifras y los límites juntos | Hecho a mano: **no** lo genera el circuito |

Los dos HTML se abren con doble clic, sin internet y sin instalar nada. Los tres
ficheros se abren también desde el navegador, en GitHub Pages:

- [Validación con datos reales](https://felixpere.github.io/valorador-comparables-madrid/entregables/dashboard_real.html)
- [Circuito de extracción](https://felixpere.github.io/valorador-comparables-madrid/entregables/dashboard.html)
- [Resumen de una página (PDF)](https://felixpere.github.io/valorador-comparables-madrid/entregables/one_pager_valoracion_comparables_v2.pdf)

**El Excel no está aquí.** Lo genera el circuito en
`outputs/valoraciones_madrid.xlsx` (`src/p05_exportar_excel.py`), y el modelo de
Power BI, `valorador_madrid.pbix` en la raíz del repositorio, ya lleva sus datos
dentro.

## Esto es una copia, y no se actualiza sola

Los originales vivos de los dos HTML están en `outputs/`, que no se versiona. Si
cambian los datos o el código, las copias de aquí se quedan viejas.

Para refrescarlos hay que regenerar y volver a copiar. El orden importa y está
detallado en el README, sección «Cómo regenerar los entregables»:

```bash
python src/r01_valorar_real.py
python src/r04_diagnostico_coeficientes.py
python src/r02_caso.py
python src/r03_dashboard_real.py
python run_pipeline.py --motor llm
cp outputs/dashboard_real.html outputs/dashboard.html entregables/
```

**El `--motor llm` hace falta para el entregable completo**: sin él,
`dashboard.html` sale con la extracción sólo por reglas, sin el resultado del
modelo de lenguaje. El pipeline lo avisa al arrancar y al terminar.

**El one-pager no se regenera.** Es un PDF estático: el comando de arriba no lo
toca. Si cambian las cifras, hay que rehacerlo a mano.

## Una advertencia que vale la pena repetir

Desconfíe de cualquier copia de estos ficheros que no salga de aquí o de
`outputs/`. Hubo una editada a mano con una cifra mal, y el error sobrevivió
hasta que se comparó contra el fichero regenerado desde el código.

Todo lo que publica el circuito sale del código. Un test comprueba que cada cifra
del panel coincide con el fichero de resultados del que dice venir.

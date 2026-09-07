# Entregables

Los tres ficheros que produce el circuito, listos para abrir. Todo lo demás del
repositorio es el código que los genera y la documentación que los sostiene.

| Fichero | Qué es |
|---|---|
| `dashboard_real.html` | La validación con datos reales de Madrid y una valoración abierta paso a paso. Es el que responde a «¿cómo sabemos que funciona?» |
| `valoraciones_madrid.xlsx` | Siete hojas: la lista de inmuebles, el resumen por distrito y la validación de 2018. Diseñado para cargarse en Power BI sin transformaciones |
| `dashboard.html` | El circuito de extracción con IA sobre texto libre |

Los dos HTML se abren con doble clic, sin internet y sin instalar nada. También
están publicados y siempre al día en GitHub Pages:

- [Validación con datos reales](https://felixpere.github.io/valorador-comparables-madrid/entregables/dashboard_real.html)
- [Circuito de extracción](https://felixpere.github.io/valorador-comparables-madrid/entregables/dashboard.html)

## Esto es una copia, y no se actualiza sola

Los originales vivos están en `outputs/`, que no se versiona. Si cambian los
datos o el código, **estos tres ficheros se quedan viejos y nadie avisa**.

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

## Una advertencia que vale la pena repetir

Desconfíe de cualquier copia de estos ficheros que no salga de aquí o de
`outputs/`. Hubo una editada a mano con una cifra mal, y el error sobrevivió
hasta que se comparó contra el fichero regenerado desde el código.

Todo lo que se publica sale del código. Un test comprueba que cada cifra del
panel coincide con el fichero de resultados del que dice venir.

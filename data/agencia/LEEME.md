# Cierres de una agencia

Aquí se cargan precios de cierre reales para recalibrar el descuento entre
precio anunciado y precio firmado.

1. Copia `plantilla_cierres.csv` como `cierres.csv`. La fila de la plantilla es
   **inventada**, sólo enseña el formato: bórrala.
2. Una fila por operación cerrada. Sin nombres, direcciones, teléfonos ni
   referencias catastrales: si aparece una columna así, el script se para.
3. `python src/r07_cierres_agencia.py` deja `descuento_agencia.csv`.
4. La demo lo usa sola en los distritos con 10 cierres o más y dice en pantalla
   de dónde sale el descuento.

`cierres.csv` y `descuento_agencia.csv` **no se versionan** (`.gitignore`):
son datos de la agencia, no públicos.

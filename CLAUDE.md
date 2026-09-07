# Reglas de este repositorio

Léelas antes de tocar nada. Aplican a cualquier sesión, en cualquier herramienta.

Este es un proyecto público sobre valoración inmobiliaria por comparables. En
él no aparece el nombre de ninguna empresa ni de ningún cliente, y no debe
aparecer. Las consultoras y organismos que sí se nombran lo están como fuentes
de un dato citado, con su referencia y su fecha.

## Las diez reglas

1. **Ni un número inventado presentado como medido.** "No validado" y "no se
   puede medir con estos datos" son respuestas correctas y preferibles.
2. **Ante dos cifras, siempre la honesta aunque sea peor.** Y se cuenta la
   corrección: el proceso vale más que el número.
3. **Sin fugas de información.** El inmueble evaluado nunca entra en sus propios
   comparables. Nada de mirar datos posteriores a la fecha que se evalúa.
4. **Declarar siempre los supuestos y las limitaciones**, incluidos los
   incómodos, en el propio entregable y no en un anexo.
5. **Nada de scraping de portales inmobiliarios.** Sus términos lo prohíben.
   Sólo fuentes abiertas y legales: Catastro, INE, Ministerio de Vivienda,
   Ayuntamiento de Madrid, datos abiertos, datasets públicos. Si no hay datos
   suficientes, datos sintéticos declarados como tales.
6. **Nada de datos personales** de vendedores ni de terceros.
7. **Tests automatizados** en todo lo que se pueda.
8. **Todo lo que se mida, con su script, reproducible.** Semilla fija.
9. **Redacción, diseño, nombres y estructura: decide tú.** No preguntes por
   estilo.
10. **Cita fuentes con fecha** en todo lo que sea investigación de mercado.

## Cómo trabajar

- Avanza de forma autónoma. Acumula las dudas y pregúntalas juntas, no de una
  en una.
- Párate sólo si: encuentras algo que cambie el enfoque del proyecto, algo
  irreversible, o un dilema que estas reglas no resuelvan.
- Al cerrar sesión, actualiza `docs/ESTADO.md`. El contexto no viaja entre
  herramientas: lo que no esté escrito en el repo, se pierde.

## Comprobaciones que no se saltan

```bash
python -m pytest tests -q      # 54 tests, todos deben pasar
python run_pipeline.py         # termina en error si detecta una fuga
```

Si el control de fugas salta, el pipeline no publica nada. Ese comportamiento es
intencionado: prefiere no entregar a entregar un número que no se sostiene. No
lo desactives para "que salga el Excel".

## Trampas conocidas de este dominio

- La tabla de precio de segunda mano por distrito del Anuario del Ayuntamiento
  de Madrid **procede de Idealista**: es precio de oferta, no de cierre. Está en
  la misma publicación que la tabla registral, que sí es precio declarado en
  escritura. Usa la registral.
- El precio de referencia de todo el proyecto es el **precio pedido**, no el de
  cierre. Ninguna afirmación puede dar a entender lo contrario.
- Las desviaciones que el motor "detecta" fueron inyectadas al generar el corpus.
  Es circular por construcción. Nunca presentarlo como capacidad predictiva.
- `CADASTRALQUALITYID` de `idealista18` **no es una nota de calidad**: es la
  categoría catastral, y **empeora según crece el número**. La dirección no está
  documentada en el paquete. Se leyó al revés una vez y produjo un "coeficiente
  anómalo" que no lo era. `r01` ya la invierte. Antes de llamar anómalo a un
  signo, comprobar en qué dirección está codificada la variable.

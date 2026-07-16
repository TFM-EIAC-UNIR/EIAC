# Procedencia y trazabilidad de los datasets

Este documento identifica los archivos utilizados en los tres escenarios del
estudio. Las huellas SHA-256 permiten comprobar que los experimentos se ejecutan
sobre las mismas versiones de los datos.

| Escenario | Archivo | Filas | Columnas | SHA-256 |
| --- | --- | ---: | ---: | --- |
| CAPEC | `datasets/CAPEC/2000.csv` | 615 | 20 | `f309fbbcad62ec70084046eeaef21e88c7117031f59dc8bd6346f4dcd4d16f2d` |
| Sintético | `datasets/sintetico/dataset_sintetico_grande.csv` | 1.200 | 13 | `0e70ef418d32a4f5816fb905ce2ce4f1e17a9b3d9151cbf26e474e817b66c841` |
| SR-BH | `datasets/SR-BH/dataset_real - dataset_real_40k.csv` | 40.000 | 44 | `057e0921991575e80826c079cd00495c1ba5b6418e5aa063f2377325a9c5d71f` |

## Muestra del escenario SR-BH

El conjunto original SR-BH 2022 Multilabel contiene 907.814 registros. Debido a
su volumen y a los recursos computacionales disponibles, para el experimento se
seleccionaron aleatoriamente 40.000 registros. El archivo resultante se conserva
sin modificaciones en este repositorio y constituye la muestra experimental del
trabajo.

No se registró una semilla durante la selección original. Por ello, no se afirma
que la muestra pueda reconstruirse mediante una nueva selección aleatoria. La
reproducibilidad del escenario se garantiza mediante la publicación del archivo
exactamente utilizado y su huella SHA-256.

Fuente original: Sureda Riera et al., *SR-BH 2022 Multilabel Dataset*, Harvard
Dataverse, DOI: [10.7910/DVN/OGOIXX](https://doi.org/10.7910/DVN/OGOIXX),
distribuido bajo CC0 1.0.

## Comprobación de las huellas

En macOS se pueden comprobar los archivos con:

```bash
shasum -a 256 datasets/CAPEC/2000.csv
shasum -a 256 datasets/sintetico/dataset_sintetico_grande.csv
shasum -a 256 "datasets/SR-BH/dataset_real - dataset_real_40k.csv"
```

# Evaluación de la Relevancia Informativa de Características en Datasets CAPEC

**Trabajo Fin de Máster (TFM)**  
*Evaluación de la Relevancia Informativa de Características en Datasets basados en CAPEC de Ataques Cibernéticos Mediante Entropía de Columnas*

---

## ¿Qué es este TFM?

Este repositorio forma parte del Trabajo Fin de Máster del Máster en Visual Analytics & Big Data. El objetivo es caracterizar la relevancia informativa intrínseca de las columnas de datasets de ciberseguridad basados en [CAPEC](https://capec.mitre.org/) (*Common Attack Pattern Enumeration and Classification*, MITRE), mediante entropía de Shannon y el **Índice de Entropía Informativa Ajustada de Columna (EIAC)**.

Este repositorio contiene el código experimental, los datasets de prueba y los resultados generados para sustentar dicho trabajo.

---

## Autores


| Autor           | Correo                                                            |
| --------------- | ----------------------------------------------------------------- |
| Marco Adarme    | [madarme@ufps.edu.co](mailto:madarme@ufps.edu.co)                 |
| Ronald Benitez  | [ronaldeduardobm@ufps.edu.co](mailto:ronaldeduardobm@ufps.edu.co) |
| Jorge Hernandez | [jorgekevinhl@ufps.edu.co](mailto:jorgekevinhl@ufps.edu.co)       |


---

## Descripción

Repositorio del TFM para **calcular y comparar la relevancia informativa de las columnas** en tres tipos de dataset: catálogo CAPEC, datos sintéticos y tráfico SR-BH. El script principal aplica entropía de Shannon, la métrica **EIAC** y genera reportes en CSV, PDF y LaTeX. Un segundo script produce **gráficas comparativas** entre $H_n(X)$ y EIAC para los tres escenarios del estudio.

---

## ¿Qué es EIAC?

La **entropía de Shannon normalizada** $H_n(X)$ mide la dispersión de valores en una columna, pero puede **sobrevalorar** atributos que son casi únicos (como un identificador) o que tienen muchos datos vacíos.

**EIAC** ajusta esa interpretación combinando tres factores:

$$
\text{EIAC}(X) = H_n(X) \times C(X) \times \bigl(1 - U(X)\bigr)
$$


| Componente | Significado                                                              |
| ---------- | ------------------------------------------------------------------------ |
| $H_n(X)$      | Entropía normalizada (0 = sin variación, 1 = máxima dispersión uniforme) |
| C(X)       | Completitud: proporción de celdas con valor no vacío                     |
| U(X)       | Unicidad: proporción de valores distintos respecto al total de filas     |
| 1 - U(X)   | Penalización por columnas que se comportan como identificadores          |


Con EIAC se obtiene un **ranking de columnas** con clasificación de relevancia informativa intrínseca (alta, media o baja) y una etiqueta funcional (analítica, trazabilidad o descriptiva, entre otras). El resultado sirve como apoyo al análisis exploratorio, pero no representa por sí solo capacidad predictiva ni redundancia entre variables.

---

## Estructura del proyecto

```
EIAC/
├── scripts/
│   ├── procesar_capec_entropia.py    # Cálculo de entropía y EIAC
│   └── graficas_Hn_EIAC.py           # Gráficas comparativas Hn(X) vs EIAC
├── datasets/
│   ├── CAPEC/                        # Dataset del catálogo CAPEC
│   ├── sintetico/                    # Dataset sintético de prueba
│   └── SR-BH/                        # Dataset de tráfico HTTP (SR-BH)
├── datos/
│   ├── processed/                    # CSV enriquecido
│   └── results/                      # Rankings, LaTeX y PDF
└── capecnuevo.xml                    # Catálogo CAPEC v3.9 (referencia MITRE)
```

### Enlaces directos

| Recurso             | Ruta |
|----------------------|------|
| Script principal    | [scripts/procesar_capec_entropia.py](scripts/procesar_capec_entropia.py) |
| Script de gráficas  | [scripts/graficas_Hn_EIAC.py](scripts/graficas_Hn_EIAC.py) |
| Dataset CAPEC       | [datasets/CAPEC/2000.csv](datasets/CAPEC/2000.csv) |
| Dataset sintético   | [datasets/sintetico/dataset_sintetico_grande.csv](datasets/sintetico/dataset_sintetico_grande.csv) |
| Dataset SR-BH       | [datasets/SR-BH/dataset_real - dataset_real_40k.csv](datasets/SR-BH/dataset_real%20-%20dataset_real_40k.csv) |
| Catálogo CAPEC v3.9 | [capecnuevo.xml](capecnuevo.xml) |
| Procedencia de los datos | [DATASETS.md](DATASETS.md) |
| Contribuciones de los autores | [CONTRIBUTIONS.md](CONTRIBUTIONS.md) |
| Forma de citar el software | [CITATION.cff](CITATION.cff) |


---

## Cálculo de entropía y EIAC

Esta sección describe **cómo se calculan las métricas** implementadas en el script.

### Paso 1 — Entropía de Shannon

Para una columna X con k valores distintos y frecuencias p_i:


$$
H(X) = -\sum_{i=1}^{k} p_i \log_2 p_i
\qquad
H_n(X) = \frac{H(X)}{\log_2 k}
$$


### Paso 2 — Completitud y unicidad

$$
C(X) = \frac{\text{filas con valor}}{\text{total de filas}}
\qquad
U(X) = \frac{k}{\text{total de filas}}
$$

### Paso 3 — EIAC y clasificación

$$
\text{EIAC}(X) = H_n(X) \times C(X) \times \bigl(1 - U(X)\bigr)
$$


| Rango EIAC  | Relevancia |
| ----------- | ---------- |
| $0.66 \leq EIAC \leq 1$ | Alta |
| $0.33 \leq EIAC < 0.66$ | Media |
| $0 \leq EIAC < 0.33$ | Baja |


### Ejemplo ilustrativo

Supongamos un dataset de 100 filas. La tabla siguiente muestra cómo cambia la interpretación al pasar de $H_n(X)$ a EIAC:


| Columna (ejemplo) | Valores                    | $H_n(X)$ | C(X) | U(X) | 1 − U(X) | EIAC     | Lectura                                                      |
| ----------------- | -------------------------- | ------ | ---- | ---- | -------- | -------- | ------------------------------------------------------------ |
| `ID`              | 100 IDs distintos          | 1.00   | 1.00 | 1.00 | 0.00     | **0.00** | Identificador: alta entropía, pero nula relevancia analítica |
| `Abstraction`     | Standard, Detailed, Meta   | 0.92   | 1.00 | 0.03 | 0.97     | **0.89** | Categórica con pocos niveles: alta relevancia                |
| `Status`          | 50 Draft, 30 Stable, 20 vacíos | 0.95 | 0.80 | 0.02 | 0.98 | **0.74** | Diversidad entre los datos disponibles, ajustada por completitud |
| `Constant_Flag`   | Siempre "Standard"         | 0.00   | 1.00 | 0.01 | 0.99     | **0.00** | Sin variación: no aporta información                         |
| `Mostly_Missing`  | 90 % vacío, resto disperso | 0.95   | 0.10 | 0.08 | 0.92     | **0.09** | $H_n$ alto, pero EIAC bajo por incompletitud                   |


Este contraste muestra cómo EIAC complementa la entropía normalizada al considerar la completitud y la unicidad de cada columna.

---

## Requisitos

- Python 3.9+
- [pandas](https://pandas.pydata.org/)
- [reportlab](https://www.reportlab.com/) *(opcional, para generar PDF)*
- [matplotlib](https://matplotlib.org/) *(para gráficas comparativas)*

Las versiones utilizadas se encuentran fijadas en `requirements.txt`:

```bash
python3 -m pip install -r requirements.txt
```

---

## Uso

Desde la raíz del repositorio:

```bash
# Dataset CAPEC
python3 scripts/procesar_capec_entropia.py --input datasets/CAPEC/2000.csv

# Dataset sintético
python3 scripts/procesar_capec_entropia.py --input datasets/sintetico/dataset_sintetico_grande.csv

# Dataset SR-BH
python3 scripts/procesar_capec_entropia.py --input "datasets/SR-BH/dataset_real - dataset_real_40k.csv"
```

### Parámetros principales


| Parámetro          | Descripción             | Por defecto                                  |
| ------------------ | ----------------------- | -------------------------------------------- |
| `--input`          | CSV local o URL         | Google Sheets (CAPEC)                        |
| `--processed`      | Dataset enriquecido     | `datos/processed/capec_dataset.csv`          |
| `--entropy`        | Ranking de entropía     | `datos/results/entropia_columnas.csv`        |
| `--eiac`           | Ranking EIAC            | `datos/results/eiac_columnas.csv`            |
| `--eiac-pdf`       | Reporte PDF             | `datos/results/eiac_reporte.pdf`             |
| `--comparison-pdf` | Comparación H_n vs EIAC | `datos/results/eiac_comparacion_hn_eiac.pdf` |


Cada ejecución añade un timestamp (`YYYYMMDD_HHMMSS`) a los archivos de salida.

## Datos y reproducibilidad

Los experimentos utilizan versiones fijas de los tres datasets. Su procedencia,
dimensiones y huellas SHA-256 están registradas en [DATASETS.md](DATASETS.md).
En el escenario SR-BH se empleó una muestra aleatoria de 40.000 registros del
conjunto original por razones de viabilidad computacional. La muestra exacta
utilizada se incluye en el repositorio.

## Contribuciones de los autores

El planteamiento, la formulación de EIAC, la experimentación y la revisión del
trabajo se realizaron conjuntamente. Las responsabilidades principales de cada
integrante se describen en [CONTRIBUTIONS.md](CONTRIBUTIONS.md).

---

## Gráficas comparativas $H_n(X)$ vs EIAC

El script [scripts/graficas_Hn_EIAC.py](scripts/graficas_Hn_EIAC.py) genera visualizaciones para contrastar la entropía normalizada de Shannon con EIAC en los **tres escenarios** del TFM: CAPEC, sintético y SR-BH.

### ¿Qué hace?

1. **Carga los rankings EIAC congelados** de cada escenario desde `datos/results/` (columnas `Columna`, `Hn(X)` y `EIAC`).
2. **Gráficos de mancuerna (dumbbell)** — uno por escenario — que muestran, para cada columna, la distancia entre $H_n(X)$ (gris) y EIAC (teal). Permite ver de un vistazo qué columnas reduce EIAC respecto a Shannon.
3. **Diagrama de dispersión resumen** — superpone los tres escenarios sobre el plano $H_n(X)$ vs EIAC, con la recta $y = x$ como referencia de “sin ajuste”. Los puntos por debajo de la diagonal indican que EIAC penalizó la columna (por unicidad, datos faltantes o ambos).
4. **Empaqueta las figuras** en `graficas_eiac.zip` (PDF y PNG de cada gráfico).

### Uso

Desde la raíz del repositorio:

```bash
python3 scripts/graficas_Hn_EIAC.py
```

No requiere conexión a internet. Las figuras se generan a partir de los resultados utilizados en la memoria y se guardan en el directorio desde el que se ejecuta el comando.

### Salidas del script de gráficas

| Archivo | Contenido |
|---------|-----------|
| `comparacion_hn_eiac_escenario1.pdf` / `.png` | Escenario 1 — CAPEC |
| `comparacion_hn_eiac_escenario2.pdf` / `.png` | Escenario 2 — Sintético |
| `comparacion_hn_eiac_escenario3.pdf` / `.png` | Escenario 3 — SR-BH |
| `comparacion_hn_eiac_dispersion.pdf` / `.png` | Dispersión conjunta de los tres escenarios |
| `graficas_eiac.zip` | Paquete con todas las figuras anteriores |

> **Nota:** El archivo queda disponible en disco sin necesidad de descarga adicional.

---

## Salidas generadas


| Archivo                          | Contenido                                              |
| -------------------------------- | ------------------------------------------------------ |
| `capec_dataset_*.csv`            | Dataset original + columnas derivadas                  |
| `entropia_columnas_*.csv`        | Entropía de Shannon y entropía normalizada por columna |
| `eiac_columnas_*.csv`            | Ranking EIAC con relevancia y clasificación funcional  |
| `eiac_reporte_*.pdf`             | Reporte visual (campos obligatorios y complementarios) |
| `eiac_comparacion_hn_eiac_*.pdf` | Comparación entre H_n(X) y EIAC                        |
| `eiac_tabla_latex_*.tex`         | Tabla EIAC en LaTeX                                    |
| `eiac_comparacion_hn_eiac_*.tex` | Tabla comparativa en LaTeX                             |


### Exportación LaTeX

Los archivos `.tex` se generan como **material auxiliar** para documentos de investigación: memoria del TFM, artículos o informes técnicos que requieran tablas listas para compilar en LaTeX sin reescribir los resultados a mano. No son la salida principal del análisis; el núcleo de resultados está en los CSV y PDF.

---

## Referencias

- [MITRE CAPEC](https://capec.mitre.org/) — Common Attack Pattern Enumeration and Classification
- CAPEC v3.9 (2023-01-24) — `[capecnuevo.xml](capecnuevo.xml)`
- Shannon, C. E. (1948). *A Mathematical Theory of Communication*

---

## Licencia y uso

El código desarrollado por los autores se distribuye bajo la licencia MIT, disponible en [LICENSE](LICENSE). Los datasets y fuentes externas conservan sus propias condiciones de uso. El catálogo CAPEC pertenece a [The MITRE Corporation](https://www.mitre.org/), mientras que SR-BH 2022 Multilabel se encuentra publicado en Harvard Dataverse bajo CC0 1.0.

## Citación

La información bibliográfica para citar esta versión del software se encuentra
en [CITATION.cff](CITATION.cff). La versión utilizada para la entrega final del
TFM está identificada con la etiqueta `v1.0.0`.



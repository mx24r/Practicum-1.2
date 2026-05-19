# Pipeline AMIE-MINEDUC Ecuador

Pipeline ETL completo para el dataset del Archivo Maestro de Instituciones Educativas (AMIE) del Ministerio de Educación del Ecuador. Procesa datos históricos 2009-2024, los limpia, carga en SQLite y alimenta un dashboard con visualizaciones y métricas educativas.

# Dashboard

## Preguntas analíticas

| Pregunta                                       | Visual               | Métrica                                    |
| ---------------------------------------------- | -------------------- | ------------------------------------------ |
| ¿Distribución de matrícula por provincia?      | Barras horizontales  | `SUM(total_estudiantes)` por provincia     |
| ¿Fiscal vs. Particular en Loja (rural/urbano)? | Barras apiladas 100% | `COUNT(cod_amie)` por área y sostenimiento |
| ¿Evolución de instituciones 2015-2024?         | Línea temporal       | `COUNT(cod_amie)` por año lectivo          |

## KPIs nacionales (2024-2025 Inicio)

* 4,106,819 estudiantes
* 215,030 docentes
* 16,152 instituciones activas

# Arquitectura

```text
main.py (orquestador)
   │
   ├──► diagnostico.py
   ├──► limpieza.py
   └──► CargarASQLite.py
```

# Estructura del proyecto

```text
├── main.py
├── diagnostico.py
├── limpieza.py
├── CargarASQLite.py
├── data/
│   ├── crudo/
│   └── procesado/
└── README.md
```

# Stack tecnológico

* Python 3.10+
* pandas
* sqlalchemy
* SQLite
* Power BI / Metabase

# Ejecución

```bash
python main.py
```

El orquestador ejecuta los 3 pasos del pipeline ETL de forma secuencial. Si un paso falla, el proceso se detiene y muestra el error correspondiente.

# Hallazgos del dataset

| Problema detectado                                 | Solución aplicada                          |
| -------------------------------------------------- | ------------------------------------------ |
| Codificación incorrecta (UTF-8 leído como latin-1) | `encode('latin-1').decode('utf-8')`        |
| Separador de miles con punto                       | Eliminación mediante expresiones regulares |
| 120,114 filas completamente vacías                 | `dropna(how='all')`                        |
| Duplicados por `(AMIE, año_lectivo)`               | Priorización de `regimen_escolar='Sierra'` |
| Valores nulos en campos numéricos                  | `fillna(0)`                                |
| Inconsistencias entre totales y subtotales         | Se documenta y conserva el dato oficial    |

# Resultados clave

* 322,600 registros procesados (histórico 2015-2025)
* 25 provincias analizadas
* Guayas y Pichincha concentran el 42% de la matrícula
* En Loja, la educación rural es mayoritariamente fiscal
* Tendencia de disminución del 13.3% en instituciones entre 2015-2024

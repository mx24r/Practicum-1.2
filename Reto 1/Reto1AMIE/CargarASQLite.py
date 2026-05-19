import pandas as pd
from sqlalchemy import create_engine, text
import os

# ==============================================================================
# PASO 3: CARGA EN SQLITE Y VERIFICACION DE CONSULTAS
# ==============================================================================
print("=" * 80)
print("PASO 3: CARGA EN SQLITE Y VERIFICACION DE CONSULTAS")
print("=" * 80)

# CONFIGURACION
RUTA_DB = 'data\\procesado\\amie_mineduc.db'
RUTA_CSV_LIMPIO = 'data\\procesado\\dataset_limpio.csv'

# --- 3.0 CARGAR DATAFRAME DESDE CSV INTERMEDIO ---
print("\n[3.0] Cargando dataset limpio desde CSV intermedio...")
print("-" * 50)

if not os.path.exists(RUTA_CSV_LIMPIO):
    print(f"\n[ERROR] No se encontro: {RUTA_CSV_LIMPIO}")
    print("  Ejecuta primero el Paso 2 (limpieza).")
    exit(1)

df = pd.read_csv(
    RUTA_CSV_LIMPIO,
    sep=';',
    encoding='utf-8-sig',
    low_memory=False,
    dtype=str
)

# Convertir columnas numericas de vuelta a int
cols_numericas = [
    'cod_provincia', 'cod_canton', 'cod_parroquia',
    'docentes_femenino', 'docentes_masculino', 'total_docentes',
    'estudiantes_femenino', 'estudiantes_masculino', 'total_estudiantes',
    'ecuatoriana', 'colombiana', 'venezolana', 'peruana',
    'otros_paises_america', 'otros_continentes'
]

for col in cols_numericas:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

print(f"  [OK] Dataset cargado: {len(df):,} filas x {len(df.columns)} columnas")

engine = create_engine(f'sqlite:///{RUTA_DB}')

# --- 3.1 CARGAR EL DATASET LIMPIO ---
print("\n[3.1] Cargando dataset limpio en SQLite...")
print("-" * 50)

print(f"Dataset disponible: {len(df):,} filas x {len(df.columns)} columnas")

anio_mas_reciente = sorted(df['anio_lectivo'].unique())[-1]
print(f"\nAño lectivo más reciente detectado: {anio_mas_reciente}")

# UNA SOLA TABLA con todo el histórico
df.to_sql('instituciones', engine, if_exists='replace', index=False)
print(f"\nTabla 'instituciones' creada: {len(df):,} filas (histórico completo)")

# Verificación
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM instituciones"))
    count = result.scalar()
    print(f"Verificación SQL: {count:,} registros totales")

# --- 3.2 CONSULTA P1: Matrícula total por provincia ---
print("\n" + "=" * 80)
print("[3.2] CONSULTA P1: Matrícula total por provincia")
print("=" * 80)
print(f"Pregunta: ¿Cómo se distribuye la matrícula total por provincia en {anio_mas_reciente}?")

query_p1 = f"""
SELECT 
    provincia, 
    SUM(total_estudiantes) as matricula_total,
    COUNT(cod_amie) as num_instituciones
FROM instituciones
WHERE anio_lectivo = '2024-2025 Inicio'  
GROUP BY provincia
ORDER BY matricula_total DESC
"""

df_p1 = pd.read_sql(query_p1, engine)
print(f"\nResultados: {len(df_p1)} provincias")
print(f"Matrícula nacional total: {df_p1['matricula_total'].sum():,} estudiantes")
print(f"\nTop 10 provincias por matrícula:")
print(df_p1.head(10).to_string(index=False))

# --- 3.3 CONSULTA P2: Sostenimiento por área en Loja ---
print("\n" + "=" * 80)
print("[3.3] CONSULTA P2: Sostenimiento por área en Loja")
print("=" * 80)
print(f"Pregunta: ¿Cuál es la proporción de instituciones fiscales vs. particulares")
print(f"          por área (urbana/rural) en Loja en {anio_mas_reciente}?")

query_p2 = f"""
SELECT 
    area,
    sostenimiento,
    COUNT(cod_amie) as num_instituciones
FROM instituciones
WHERE provincia = 'LOJA' 
  AND anio_lectivo = '2024-2025 Inicio'
  AND sostenimiento IN ('Fiscal', 'Particular')
GROUP BY area, sostenimiento
ORDER BY area, sostenimiento
"""

df_p2 = pd.read_sql(query_p2, engine)
print(f"\nResultados: {len(df_p2)} combinaciones área-sostenimiento")
print(df_p2.to_string(index=False))

# Calcular totales por área
print("\nTotales por área en Loja:")
totales_loja = df_p2.groupby('area')['num_instituciones'].sum()
for area, total in totales_loja.items():
    print(f"  {area}: {total} instituciones")

# --- 3.4 CONSULTA P3: Evolución de instituciones activas (2015-2024) ---
print("\n" + "=" * 80)
print("[3.4] CONSULTA P3: Evolución de instituciones activas")
print("=" * 80)
print("Pregunta: ¿Cómo evolucionó el número de instituciones activas en Ecuador")
print("          entre 2015 y 2024?")

query_p3 = """
           SELECT
               anio_lectivo,
               COUNT(cod_amie) as num_instituciones,
               SUM(total_estudiantes) as matricula_total,
               SUM(total_docentes) as docentes_total
           FROM instituciones
           WHERE anio_lectivo LIKE '2015-2016%'
              OR anio_lectivo LIKE '2016-2017%'
              OR anio_lectivo LIKE '2017-2018%'
              OR anio_lectivo LIKE '2018-2019%'
              OR anio_lectivo LIKE '2019-2020%'
              OR anio_lectivo LIKE '2020-2021%'
              OR anio_lectivo LIKE '2021-2022%'
              OR anio_lectivo LIKE '2022-2023%'
              OR anio_lectivo LIKE '2023-2024%'
              OR anio_lectivo LIKE '2024-2025%'
           GROUP BY anio_lectivo
           ORDER BY anio_lectivo
           """

df_p3 = pd.read_sql(query_p3, engine)
print(f"\nResultados: {len(df_p3)} ciclos escolares (2015-2024)")
print(df_p3.to_string(index=False))

# --- 3.5 KPI: Matrícula nacional visible ---
print("\n" + "=" * 80)
print("[3.5] KPI: MATRÍCULA NACIONAL")
print("=" * 80)

kpi_query = f"""
SELECT 
    SUM(total_estudiantes) as matricula_nacional,
    SUM(total_docentes) as docentes_nacional,
    COUNT(DISTINCT cod_amie) as total_instituciones
FROM instituciones
WHERE anio_lectivo = '2024-2025 Inicio'
"""

df_kpi = pd.read_sql(kpi_query, engine)
print("\nKPI Dashboard:")
print(f"  Matrícula nacional ({anio_mas_reciente}): {df_kpi['matricula_nacional'].iloc[0]:,} estudiantes")
print(f"  Docentes nacionales: {df_kpi['docentes_nacional'].iloc[0]:,}")
print(f"  Instituciones activas: {df_kpi['total_instituciones'].iloc[0]:,}")

print("=" * 80)
print("FIN DEL PASO 3: CARGA EN SQLITE")
print("=" * 80)
import pandas as pd
import re

# ==============================================================================
# CONFIGURACION
# ==============================================================================
RUTA_CSV = 'data\\crudo\\registro-administrativo-historico_2009-2024-inicio(1).csv'

# Cargar TODAS las columnas como string para evitar que pandas infiera tipos
df = pd.read_csv(RUTA_CSV, sep=';', encoding='latin-1', low_memory=False, dtype=str)

print("=" * 80)
print("PASO 1: DIAGNOSTICO DEL DATASET")
print("=" * 80)

# ==============================================================================
# 0. LIMPIEZA PREVIA
# ==============================================================================

# 0.1 Eliminar filas completamente vacias
filas_antes = len(df)
df = df.dropna(how='all')
filas_eliminadas = filas_antes - len(df)

if filas_eliminadas > 0:
    print(f"\n[PRE-LIMPIEZA] Se eliminaron {filas_eliminadas} filas completamente vacias.")
    print(f"  Filas antes: {filas_antes:,}  |  Filas despues: {len(df):,}")

# 0.2 Funcion para limpiar formato numerico (ahora recibe string puro del CSV)
def limpiar_numero(valor):
    """Limpia separadores de miles en formato ecuatoriano."""
    if pd.isna(valor) or str(valor).strip() == '':
        return pd.NA

    s = str(valor).strip()

    # Formato de miles con punto: 1.060 o 12.345 o 123.456
    # Tambien cubre casos como 1.127, 11.234, 111.222
    if re.match(r'^\d{1,3}(\.\d{3})+$', s):
        return int(s.replace('.', ''))

    # Numero simple sin separadores
    try:
        return int(float(s))
    except:
        return pd.NA

# 0.3 Aplicar limpieza a columnas numericas (ahora son todas string)
cols_numericas = ['Cod_Provincia', 'Cod_Canton', 'Cod_Parroquia',
                  'Docentes_Femenino', 'Docentes_Masculino', 'Total_Docentes',
                  'Estudiantes_Femenino', 'Estudiantes_Masculino', 'Total_Estudiantes',
                  'Ecuatoriana', 'Colombiana', 'Venezolana', 'Peruana',
                  'Otros_Paises_de_America', 'Otros_Continentes']

for col in cols_numericas:
    if col in df.columns:
        df[col] = df[col].apply(limpiar_numero)

print(f"\n[PRE-LIMPIEZA] Formato numerico corregido en {len(cols_numericas)} columnas.")
# ==============================================================================
# 1. DIMENSIONES
# ==============================================================================
print("=" * 70)
print("DIAGNOSTICO DEL DATASET AMIE")
print("=" * 70)
print(f"\nDimensiones del dataset:")
print(f"  - Filas:    {df.shape[0]:,}")
print(f"  - Columnas: {df.shape[1]}")

# ==============================================================================
# 2. TIPOS DE DATO
# ==============================================================================
print("\n" + "-" * 70)
print("TIPOS DE DATO POR COLUMNA")
print("-" * 70)
print(f"\n{'#':<4} {'Columna':<30} {'Tipo':<15}")
print("-" * 55)
for i, (col, dtype) in enumerate(df.dtypes.items(), 1):
    print(f"{i:<4} {col:<30} {str(dtype):<15}")

# ==============================================================================
# 3. VALORES NULOS
# ==============================================================================
print("\n" + "-" * 70)
print("CANTIDAD DE NULOS POR COLUMNA")
print("-" * 70)
nulls = df.isnull().sum().sort_values(ascending=False)
print(f"\n{'Columna':<30} {'Nulos':<10} {'% del total':<12}")
print("-" * 55)
for col, count in nulls.items():
    pct = (count / len(df)) * 100
    print(f"{col:<30} {count:<10} {pct:<12.2f}")

# ==============================================================================
# 4. DISTRIBUCION DE CAMPOS CATEGORICOS PRINCIPALES
# ==============================================================================
print("\n" + "-" * 70)
print("DISTRIBUCION DE CAMPOS CATEGORICOS PRINCIPALES")
print("-" * 70)

cat_cols = df.select_dtypes(include=['object', 'str']).columns.tolist()
UMBRAL_VALORES_UNICOS = 20

cat_cols_filtradas = []
for col in cat_cols:
    n_unicos = df[col].nunique()
    if n_unicos <= UMBRAL_VALORES_UNICOS:
        cat_cols_filtradas.append(col)

print(f"\nCampos categoricos relevantes: {len(cat_cols_filtradas)}")
for campo in cat_cols_filtradas:
    print(f"\n{campo}:")
    print(df[campo].value_counts().to_string())

# ==============================================================================
# 5. ANALISIS DE DUPLICADOS
# ==============================================================================
print("\n" + "-" * 70)
print("ANALISIS DE DUPLICADOS")
print("-" * 70)

dupes_exactos = df.duplicated(keep=False).sum()
print(f"\nDuplicados exactos (todas las columnas): {dupes_exactos}")

posibles_nombres_anio = [c for c in df.columns if 'anio' in c.lower() or 'año' in c.lower() or 'lectivo' in c.lower()]
NOMBRE_ANIO = posibles_nombres_anio[0] if posibles_nombres_anio else None
NOMBRE_AMIE = 'AMIE'

if NOMBRE_ANIO and NOMBRE_AMIE in df.columns:
    dupes_amie = df.duplicated(subset=[NOMBRE_AMIE, NOMBRE_ANIO], keep=False).sum()
    print(f"Duplicados por (AMIE + {NOMBRE_ANIO}): {dupes_amie}")

    if dupes_amie > 0:
        print("\nEjemplos de registros duplicados:")
        dupes_df = df[df.duplicated(subset=[NOMBRE_AMIE, NOMBRE_ANIO], keep=False)]
        cols_mostrar = [NOMBRE_ANIO, NOMBRE_AMIE, 'Nombre_Institucion', 'Provincia']
        cols_mostrar = [c for c in cols_mostrar if c in df.columns]
        dupes_validos = dupes_df[dupes_df[NOMBRE_AMIE].notna()]
        print(dupes_validos[cols_mostrar].head(10).to_string(index=False))

# ==============================================================================
# 6. CONSISTENCIA NUMERICA
# ==============================================================================
print("\n" + "-" * 70)
print("CONSISTENCIA NUMERICA")
print("-" * 70)

# --- DOCENTES ---
if all(c in df.columns for c in ['Total_Docentes', 'Docentes_Femenino', 'Docentes_Masculino']):
    suma_doc = df['Docentes_Femenino'] + df['Docentes_Masculino']
    incons_doc = (df['Total_Docentes'] != suma_doc).sum()
    print(f"\nTotal_Docentes != (Femenino + Masculino): {incons_doc} registros")

    if incons_doc > 0:
        print("\nEjemplos de inconsistencias en docentes:")
        cols_d = ['AMIE', 'Nombre_Institucion', 'Total_Docentes',
                  'Docentes_Femenino', 'Docentes_Masculino']
        cols_d = [c for c in cols_d if c in df.columns]
        mask = (df['Total_Docentes'] != suma_doc) & df['Total_Docentes'].notna()
        muestra = df.loc[mask, cols_d].head(10)
        print(muestra.to_string(index=False))

        df_temp = df[['Total_Docentes', 'Docentes_Femenino', 'Docentes_Masculino']].copy()
        df_temp['suma_calc'] = df_temp['Docentes_Femenino'] + df_temp['Docentes_Masculino']
        df_temp = df_temp[df_temp['suma_calc'] > 0]
        df_temp['ratio'] = (df_temp['Total_Docentes'] / df_temp['suma_calc']).round(2)
        ratio_comun = df_temp['ratio'].value_counts().head(5)
        print(f"\nPatron de inconsistencia (ratios mas comunes):")
        print(ratio_comun.to_string())

# --- ESTUDIANTES ---
if all(c in df.columns for c in ['Total_Estudiantes', 'Estudiantes_Femenino', 'Estudiantes_Masculino']):
    suma_est = df['Estudiantes_Femenino'] + df['Estudiantes_Masculino']
    incons_est = (df['Total_Estudiantes'] != suma_est).sum()
    print(f"\nTotal_Estudiantes != (Femenino + Masculino): {incons_est} registros")

    if incons_est > 0:
        print("\nEjemplos de inconsistencias en estudiantes:")
        cols_e = ['AMIE', 'Nombre_Institucion', 'Total_Estudiantes',
                  'Estudiantes_Femenino', 'Estudiantes_Masculino']
        cols_e = [c for c in cols_e if c in df.columns]
        mask = (df['Total_Estudiantes'] != suma_est) & df['Total_Estudiantes'].notna()
        muestra = df.loc[mask, cols_e].head(10)
        print(muestra.to_string(index=False))

        df_temp = df[['Total_Estudiantes', 'Estudiantes_Femenino', 'Estudiantes_Masculino']].copy()
        df_temp['suma_calc'] = df_temp['Estudiantes_Femenino'] + df_temp['Estudiantes_Masculino']
        df_temp = df_temp[df_temp['suma_calc'] > 0]
        df_temp['ratio'] = (df_temp['Total_Estudiantes'] / df_temp['suma_calc']).round(2)
        ratio_comun = df_temp['ratio'].value_counts().head(5)
        print(f"\nPatron de inconsistencia (ratios mas comunes):")
        print(ratio_comun.to_string())

# ==============================================================================
# 7. VALORES CERO EN CAMPOS NUMERICOS
# ==============================================================================
print("\n" + "-" * 70)
print("VALORES CERO EN CAMPOS NUMERICOS")
print("-" * 70)

num_cols = ['Docentes_Femenino', 'Docentes_Masculino', 'Total_Docentes',
            'Estudiantes_Femenino', 'Estudiantes_Masculino', 'Total_Estudiantes']

print(f"\n{'Campo':<30} {'Ceros':<10} {'% del total':<12}")
print("-" * 55)
for col in num_cols:
    if col in df.columns:
        ceros = (df[col] == 0).sum()
        pct = (ceros / len(df)) * 100
        print(f"{col:<30} {ceros:<10} {pct:<12.2f}")

# ==============================================================================
# FIN
# ==============================================================================
print("\n" + "=" * 70)
print("FIN DEL DIAGNOSTICO")
print("=" * 70)
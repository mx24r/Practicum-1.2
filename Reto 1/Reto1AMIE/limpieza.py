import pandas as pd
import re

# ==============================================================================
# CONFIGURACION
# ==============================================================================
RUTA_CSV = 'data\\crudo\\registro-administrativo-historico_2009-2024-inicio(1).csv'
RUTA_DB = 'data\\procesado\\amie_mineduc.db'

print("=" * 80)
print("PASO 2: LIMPIEZA DEL DATASET AMIE")
print("Cuatro transformaciones implementadas")
print("=" * 80)

# ==============================================================================
# PASO 0: CARGA Y PRE-LIMPIEZA (heredado del diagnostico)
# ==============================================================================
print("\n[PRE] CARGA INICIAL Y PRE-LIMPIEZA")
print("-" * 50)

# Cargar como string para preservar formato numerico
df = pd.read_csv(RUTA_CSV, sep=';', encoding='latin-1', low_memory=False, dtype=str)
# ==============================================================================
# CORRECCION DE CARACTERES: Revertir doble codificacion UTF-8
# ==============================================================================

def corregir_utf8(s):
    """Revierte texto que fue guardado como UTF-8 pero leido como latin-1."""
    if pd.isna(s):
        return s
    try:
        # Los caracteres "raros" que ves son bytes UTF-8 interpretados como latin-1
        # Los codificamos de vuelta a bytes con latin-1 (conserva bytes crudos)
        # y los decodificamos correctamente como UTF-8
        return s.encode('latin-1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s

# Aplicar a TODO el DataFrame de una sola vez (mas rapido)
for col in df.columns:
    df[col] = df[col].apply(lambda x: corregir_utf8(x) if isinstance(x, str) else x)

print("Caracteres UTF-8 corregidos en todo el dataset.")

# Eliminar filas completamente vacias
filas_antes = len(df)
df = df.dropna(how='all')
print(f"Filas vacias eliminadas: {filas_antes - len(df):,}")

# Corregir formato numerico
def limpiar_numero(valor):
    if pd.isna(valor) or str(valor).strip() == '':
        return pd.NA
    s = str(valor).strip()
    if re.match(r'^\d{1,3}(\.\d{3})+$', s):
        return int(s.replace('.', ''))
    try:
        return int(float(s))
    except:
        return pd.NA

cols_numericas = ['Cod_Provincia', 'Cod_Canton', 'Cod_Parroquia',
                  'Docentes_Femenino', 'Docentes_Masculino', 'Total_Docentes',
                  'Estudiantes_Femenino', 'Estudiantes_Masculino', 'Total_Estudiantes',
                  'Ecuatoriana', 'Colombiana', 'Venezolana', 'Peruana',
                  'Otros_Paises_de_America', 'Otros_Continentes']

for col in cols_numericas:
    if col in df.columns:
        df[col] = df[col].apply(limpiar_numero)

print(f"Columnas numericas corregidas: {len(cols_numericas)}")
print(f"Filas validas para limpieza: {len(df):,}")

# ==============================================================================
# TRANSFORMACION 1: RENOMBRAR COLUMNAS
# ==============================================================================
print("\n[1] TRANSFORMACION 1: RENOMBRAR COLUMNAS")
print("-" * 50)
print("Objetivo: Nombres sin tildes, sin espacios, en snake_case")
print("Motivacion: Facilitar trabajo con SQL y Python")

# Detectar nombre real de la columna de anio (con BOM)
nombre_anio_original = [c for c in df.columns if 'anio' in c.lower() or 'año' in c.lower() or 'lectivo' in c.lower()][0]
print(f"Columna de anio detectada: '{nombre_anio_original}'")

RENAME = {
    nombre_anio_original: 'anio_lectivo',
    'Zona': 'zona',
    'Provincia': 'provincia',
    'Cod_Provincia': 'cod_provincia',
    'Canton': 'canton',
    'Cod_Canton': 'cod_canton',
    'Parroquia': 'parroquia',
    'Cod_Parroquia': 'cod_parroquia',
    'Nombre_Institucion': 'nombre_institucion',
    'AMIE': 'cod_amie',
    'Tipo_Educacion': 'tipo_educacion',
    'Sostenimiento': 'sostenimiento',
    'Area': 'area',
    'Regimen_Escolar': 'regimen_escolar',
    'Jurisdiccion': 'jurisdiccion',
    'Docentes_Femenino': 'docentes_femenino',
    'Docentes_Masculino': 'docentes_masculino',
    'Total_Docentes': 'total_docentes',
    'Estudiantes_Femenino': 'estudiantes_femenino',
    'Estudiantes_Masculino': 'estudiantes_masculino',
    'Total_Estudiantes': 'total_estudiantes',
    'Ecuatoriana': 'ecuatoriana',
    'Colombiana': 'colombiana',
    'Venezolana': 'venezolana',
    'Peruana': 'peruana',
    'Otros_Paises_de_America': 'otros_paises_america',
    'Otros_Continentes': 'otros_continentes'
}

df = df.rename(columns=RENAME)
print(f"Columnas renombradas: {len(RENAME)}")

# Mostrar mapeo
print("\nMapeo de nombres:")
for original, nuevo in RENAME.items():
    print(f"  '{original}' -> '{nuevo}'")

# ==============================================================================
# TRANSFORMACION 2: LLENAR NULOS EN COLUMNAS NUMERICAS
# ==============================================================================
print("\n[2] TRANSFORMACION 2: LLENAR NULOS EN COLUMNAS NUMERICAS")
print("-" * 50)
print("Nota: Cero representa 'sin datos reportados', no ausencia de personas")

nums = ['total_docentes', 'total_estudiantes', 'estudiantes_femenino',
        'estudiantes_masculino', 'docentes_femenino', 'docentes_masculino',
        'ecuatoriana', 'colombiana', 'venezolana', 'peruana',
        'otros_paises_america', 'otros_continentes']

for col in nums:
    if col in df.columns:
        nulos_antes = df[col].isna().sum()
        if nulos_antes > 0:
            df[col] = df[col].fillna(0).astype(int)
            print(f"  {col}: {nulos_antes} nulos -> 0 (convertido a int)")
        else:
            df[col] = df[col].astype(int)
            print(f"  {col}: 0 nulos (convertido a int)")

print("\nANOTACION IMPORTANTE:")
print("  Los valores 0 en campos numericos representan 'sin datos reportados'")
print("  segun las especificaciones del MINEDUC, no necesariamente indican")
print("  ausencia real de personas en la institucion.")

# ==============================================================================
# TRANSFORMACION 3: ELIMINAR DUPLICADOS
# ==============================================================================
print("\n[3] TRANSFORMACION 3: ELIMINAR DUPLICADOS")
print("-" * 50)

dupes_mask = df.duplicated(subset=['cod_amie', 'anio_lectivo'], keep=False)
dupes_antes = dupes_mask.sum()
print(f"Filas duplicadas detectadas: {dupes_antes} (en {dupes_antes // 2} pares)")

if dupes_antes > 0:
    print("\nAnalisis de duplicados:")
    dupes_df = df[dupes_mask].sort_values(['cod_amie', 'anio_lectivo'])

    print("\nRegistros duplicados detectados:")
    print(dupes_df[['cod_amie', 'anio_lectivo', 'nombre_institucion',
                    'provincia', 'canton', 'regimen_escolar',
                    'total_estudiantes']].to_string())

    print("\n" + "=" * 50)
    print("DECISION DE LIMPIEZA (documentada manualmente):")
    print("=" * 50)
    print("""
Los duplicados detectados comparten AMIE y anio_lectivo, pero difieren
en regimen_escolar y total_estudiantes. Ambas instituciones estan en QUITO (Pichincha), 
que geograficamente al regimen SIERRA. Las filas con regimen COSTA contienen un 
error de clasificacion territorial del MINEDUC.

Se eliminan las filas con regimen COSTA y se mantienen las de SIERRA.
    """)

    # Aplicar decision documentada
    df['prioridad'] = df.apply(
        lambda row: 0 if row['regimen_escolar'] == 'Sierra' else 1, axis=1
    )
    df = df.sort_values(['cod_amie', 'anio_lectivo', 'prioridad'])

    filas_antes_drop = len(df)
    df = df.drop_duplicates(subset=['cod_amie', 'anio_lectivo'], keep='first')
    filas_eliminadas = filas_antes_drop - len(df)
    df = df.drop(columns=['prioridad'])

    print(f"Filas eliminadas: {filas_eliminadas}")
    print(f"Filas mantenidas: {dupes_antes - filas_eliminadas}")

# ==============================================================================
# TRANSFORMACION 4: VERIFICAR CONSISTENCIA
# ==============================================================================
print("\n[4] TRANSFORMACION 4: VERIFICAR CONSISTENCIA NUMERICA")
print("-" * 50)

# Verificar docentes
df['suma_docentes_calc'] = df['docentes_femenino'] + df['docentes_masculino']
incons_doc = (df['total_docentes'] != df['suma_docentes_calc']).sum()
print(f"Total_docentes != (Femenino + Masculino): {incons_doc} registros")

if incons_doc > 0:
    print("  Registros inconsistentes en docentes:")
    muestra = df[df['total_docentes'] != df['suma_docentes_calc']][
        ['cod_amie', 'nombre_institucion', 'total_docentes',
         'docentes_femenino', 'docentes_masculino', 'suma_docentes_calc']
    ].head(5)
    print(muestra.to_string(index=False))
    print("\n  Decision: Se mantiene total_docentes original (fuente MINEDUC)")
else:
    print("  OK: Todos los registros de docentes son consistentes")

# Verificar estudiantes
df['suma_estudiantes_calc'] = df['estudiantes_femenino'] + df['estudiantes_masculino']
incons_est = (df['total_estudiantes'] != df['suma_estudiantes_calc']).sum()
print(f"\nTotal_estudiantes != (Femenino + Masculino): {incons_est} registros")

if incons_est > 0:
    print("  Registros inconsistentes en estudiantes:")
    muestra = df[df['total_estudiantes'] != df['suma_estudiantes_calc']][
        ['cod_amie', 'nombre_institucion', 'total_estudiantes',
         'estudiantes_femenino', 'estudiantes_masculino', 'suma_estudiantes_calc']
    ].head(5)
    print(muestra.to_string(index=False))
    print("\n  Decision: Se mantiene total_estudiantes original (fuente MINEDUC)")
else:
    print("  OK: Todos los registros de estudiantes son consistentes")

# Eliminar columnas temporales de calculo
df = df.drop(columns=['suma_docentes_calc', 'suma_estudiantes_calc'], errors='ignore')

# ==============================================================================
# EXPORTAR DATAFRAME LIMPIO A CSV INTERMEDIO
# ==============================================================================
RUTA_CSV_LIMPIO = 'data\\procesado\\dataset_limpio.csv'

print("\n[EXPORTACION] Guardando dataset limpio en CSV intermedio...")
df.to_csv(RUTA_CSV_LIMPIO, sep=';', index=False, encoding='utf-8-sig')
print(f"  [OK] Guardado: {RUTA_CSV_LIMPIO}")
print(f"       Filas: {len(df):,} | Columnas: {len(df.columns)}")
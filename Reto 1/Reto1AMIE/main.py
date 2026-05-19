import subprocess
import sys
import os

# ==============================================================================
# CONFIGURACION
# ==============================================================================

# Rutas de datos (estructura de carpetas)
RUTA_CSV = 'data\\crudo\\registro-administrativo-historico_2009-2024-inicio(1).csv'
RUTA_DB = 'data\\procesado\\amie_mineduc.db'
RUTA_CSV_LIMPIO = 'data\\procesado\\dataset_limpio.csv'

# Scripts del pipeline
PASO1 = 'diagnostico.py'
PASO2 = 'limpieza.py'
PASO3 = 'CargarASQLite.py'

# Verificar que existan los scripts
for script in [PASO1, PASO2, PASO3]:
    if not os.path.exists(script):
        print(f"[ERROR] No se encontro: {script}")
        print("  Asegurate de que los scripts esten en la misma carpeta que main.py")
        sys.exit(1)

# Crear carpetas si no existen
os.makedirs('data/crudo', exist_ok=True)
os.makedirs('data/procesado', exist_ok=True)

# Limpiar CSV intermedio anterior si existe (para evitar usar datos viejos)
if os.path.exists(RUTA_CSV_LIMPIO):
    os.remove(RUTA_CSV_LIMPIO)
    print(f"[INFO] CSV intermedio anterior eliminado: {RUTA_CSV_LIMPIO}")

# ==============================================================================
# FUNCIONES
# ==============================================================================

def ejecutar_paso(ruta_script):
    """
    Ejecuta cada script Python como proceso independiente.
    Espera a que termine antes de continuar con el siguiente.
    """

    try:
        resultado = subprocess.run(
            [sys.executable, ruta_script],
            check=True,
            capture_output=False,
            text=True,
            encoding='utf-8'
        )
        print(f"\n[OK] Paso completado exitosamente.")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Paso fallo con codigo de salida: {e.returncode}")
        return False

    except FileNotFoundError:
        print(f"\n[ERROR] No se encontro Python o el archivo {ruta_script}")
        return False

# ==============================================================================
# PIPELINE PRINCIPAL
# ==============================================================================

def main():
    print("\n" + "=" * 70)
    print("PIPELINE AMIE MINEDUC - EJECUCION SECUENCIAL")
    print("=" * 70)
    print(f"\nDataset fuente: {RUTA_CSV}")
    print(f"Base de datos destino: {RUTA_DB}")
    print(f"CSV intermedio: {RUTA_CSV_LIMPIO}")

    input("\nPresiona ENTER para iniciar el pipeline completo...")

    # PASO 1: Diagnostico
    if not ejecutar_paso(PASO1):
        print("\n[ABORTADO] El pipeline se detuvo en el Paso 1.")
        input("Presiona ENTER para salir...")
        return

    # PASO 2: Limpieza
    if not ejecutar_paso(PASO2):
        print("\n[ABORTADO] El pipeline se detuvo en el Paso 2.")
        input("Presiona ENTER para salir...")
        return

    # PASO 3: Carga SQLite + Consultas
    if not ejecutar_paso(PASO3):
        print("\n[ABORTADO] El pipeline se detuvo en el Paso 3.")
        input("Presiona ENTER para salir...")
        return

    # RESUMEN FINAL
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETADO EXITOSAMENTE")
    print("=" * 70)

    input("\nPresiona ENTER para cerrar...")

if __name__ == "__main__":
    main()
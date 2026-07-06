import os
import sys
import datetime
import pandas as pd
import mysql.connector
from mysql.connector import Error

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "root"
DB_NAME = "biblioteca_dw"
NOMBRE = "Diego Ricardo Amador Casillas"
BASE_DIR = r"c:\Users\amado\Downloads\examen_etl\unidad2_etl_biblioteca"
CSV_PATH = r"c:\Users\amado\Downloads\examen_etl\unidad2_etl_biblioteca\data\prestamos_biblioteca_100.csv"
REPORTE_PATH = r"c:\Users\amado\Downloads\examen_etl\unidad2_etl_biblioteca\evidencias\reporte_ejecucion.txt"


def setup_db():
    try:
        conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)
        cursor = conn.cursor()
        
        # Creamos la base de datos si no existe
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cursor.execute(f"USE {DB_NAME}")

        # Lista de queries para crear las tablas
        tables = [
            """CREATE TABLE IF NOT EXISTS dim_alumno (
                id_alumno INT AUTO_INCREMENT PRIMARY KEY,
                alumno VARCHAR(255) UNIQUE
            )""",
            """CREATE TABLE IF NOT EXISTS dim_carrera (
                id_carrera INT AUTO_INCREMENT PRIMARY KEY,
                carrera VARCHAR(100) UNIQUE
            )""",
            """CREATE TABLE IF NOT EXISTS dim_libro (
                id_libro INT AUTO_INCREMENT PRIMARY KEY,
                libro VARCHAR(255),
                categoria VARCHAR(100),
                UNIQUE (libro, categoria)
            )""",
            """CREATE TABLE IF NOT EXISTS dim_sede (
                id_sede INT AUTO_INCREMENT PRIMARY KEY,
                sede VARCHAR(100) UNIQUE
            )""",
            """CREATE TABLE IF NOT EXISTS dim_fecha (
                id_fecha INT AUTO_INCREMENT PRIMARY KEY,
                fecha DATE UNIQUE,
                anio INT,
                mes INT,
                dia INT
            )""",
            """CREATE TABLE IF NOT EXISTS fact_prestamos (
                id_prestamo INT PRIMARY KEY,
                id_fecha INT,
                id_alumno INT,
                id_carrera INT,
                id_libro INT,
                id_sede INT,
                dias_prestamo INT,
                multa_diaria DECIMAL(10,2),
                total_multa DECIMAL(10,2),
                FOREIGN KEY (id_fecha) REFERENCES dim_fecha(id_fecha),
                FOREIGN KEY (id_alumno) REFERENCES dim_alumno(id_alumno),
                FOREIGN KEY (id_carrera) REFERENCES dim_carrera(id_carrera),
                FOREIGN KEY (id_libro) REFERENCES dim_libro(id_libro),
                FOREIGN KEY (id_sede) REFERENCES dim_sede(id_sede)
            )""",
            """CREATE TABLE IF NOT EXISTS etl_errores (
                id_error INT AUTO_INCREMENT PRIMARY KEY,
                fecha_error DATETIME,
                archivo_origen VARCHAR(255),
                fila_csv INT,
                id_registro INT,
                descripcion_error TEXT,
                datos_originales TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS etl_log (
                id_log INT AUTO_INCREMENT PRIMARY KEY,
                fecha_ejecucion DATETIME,
                archivo_origen VARCHAR(255),
                filas_leidas INT,
                filas_cargadas INT,
                filas_rechazadas INT,
                estado VARCHAR(50)
            )"""
        ]
        
        for t in tables:
            cursor.execute(t)

        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        tablas_a_limpiar = [
            "fact_prestamos", "dim_alumno", "dim_carrera", 
            "dim_libro", "dim_sede", "dim_fecha", "etl_errores"
        ]
        for t in tablas_a_limpiar:
            cursor.execute(f"TRUNCATE TABLE {t}")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"Error al establecer la conexión a la base de datos: {e}")
        sys.exit(1)


def main():
    print("Iniciando el proceso ETL...")
    
    setup_db()
    print("Base de datos establecida exitosamente")
    
    # CSV
    try:
        df = pd.read_csv(CSV_PATH)
    except Exception as e:
        print(f"Error leyendo CSV: {e}")
        return

    df.columns = df.columns.str.strip().str.lower()
    
    text_cols = ['alumno', 'carrera', 'libro', 'categoria', 'sede']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    if 'fecha_prestamo' in df.columns:
        df['fecha_prestamo'] = pd.to_datetime(df['fecha_prestamo'], errors='coerce').dt.date
    
    numeric_cols = ['id_prestamo', 'dias_prestamo', 'multa_diaria', 'total_multa']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna(subset=['id_prestamo'])

    try:
        conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
        cursor = conn.cursor()
    except Error as e:
        print(f"Error de conexión a la BD: {e}")
        return

    registros_leidos = len(df)
    registros_cargados = 0
    registros_rechazados = 0
    errores = []
    ids_procesados = set()

    for idx, row in df.iterrows():
        fila_csv = idx + 2 
        id_prestamo = int(row['id_prestamo'])
        
        datos_orig = str(row.to_dict())
        error_msg = None

        # validar id único
        if id_prestamo in ids_procesados:
            error_msg = f"id_prestamo {id_prestamo} duplicado"
        else:
            ids_procesados.add(id_prestamo)
            
            # Validamos que el total de la multa sea correcto
            dias = row['dias_prestamo']
            multa_d = row['multa_diaria']
            total_m = row['total_multa']
            
            if pd.isna(dias) or pd.isna(multa_d) or pd.isna(total_m):
                error_msg = f"Valores nulos en campos numéricos para el id_prestamo {id_prestamo}"
            elif round(dias * multa_d, 2) != round(total_m, 2):
                error_msg = f"total_multa incorrecto para el id_prestamo {id_prestamo}"

        # Si hay algún error
        if error_msg:
            cursor.execute("""
                INSERT INTO etl_errores (fecha_error, archivo_origen, fila_csv, id_registro, descripcion_error, datos_originales)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (datetime.datetime.now(), "prestamos_biblioteca_100.csv", fila_csv, id_prestamo, error_msg, datos_orig))
            
            registros_rechazados += 1
            errores.append(error_msg)
            
        else:
            fecha = row['fecha_prestamo']
            alumno = row['alumno']
            carrera = row['carrera']
            libro = row['libro']
            categoria = row['categoria']
            sede = row['sede']
            
            cursor.execute("INSERT IGNORE INTO dim_fecha (fecha, anio, mes, dia) VALUES (%s, %s, %s, %s)",
                           (fecha, fecha.year, fecha.month, fecha.day))
            cursor.execute("SELECT id_fecha FROM dim_fecha WHERE fecha = %s", (fecha,))
            id_fecha = cursor.fetchone()[0]

            #  Alumno
            cursor.execute("INSERT IGNORE INTO dim_alumno (alumno) VALUES (%s)", (alumno,))
            cursor.execute("SELECT id_alumno FROM dim_alumno WHERE alumno = %s", (alumno,))
            id_alumno = cursor.fetchone()[0]

            # Carrera
            cursor.execute("INSERT IGNORE INTO dim_carrera (carrera) VALUES (%s)", (carrera,))
            cursor.execute("SELECT id_carrera FROM dim_carrera WHERE carrera = %s", (carrera,))
            id_carrera = cursor.fetchone()[0]

            # Libro
            cursor.execute("INSERT IGNORE INTO dim_libro (libro, categoria) VALUES (%s, %s)", (libro, categoria))
            cursor.execute("SELECT id_libro FROM dim_libro WHERE libro = %s AND categoria = %s", (libro, categoria))
            id_libro = cursor.fetchone()[0]

            #  Sede
            cursor.execute("INSERT IGNORE INTO dim_sede (sede) VALUES (%s)", (sede,))
            cursor.execute("SELECT id_sede FROM dim_sede WHERE sede = %s", (sede,))
            id_sede = cursor.fetchone()[0]

            # tabla de hechos
            cursor.execute("""
                INSERT INTO fact_prestamos (
                    id_prestamo, id_fecha, id_alumno, id_carrera, id_libro, id_sede,
                    dias_prestamo, multa_diaria, total_multa
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (id_prestamo, id_fecha, id_alumno, id_carrera, id_libro, id_sede, 
                  row['dias_prestamo'], row['multa_diaria'], row['total_multa']))
            
            registros_cargados += 1
            
    conn.commit()

    # log
    estado = "FINALIZADO_CON_ERRORES" if registros_rechazados > 0 else "FINALIZADO_OK"
    cursor.execute("""
        INSERT INTO etl_log (fecha_ejecucion, archivo_origen, filas_leidas, filas_cargadas, filas_rechazadas, estado)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (datetime.datetime.now(), "prestamos_biblioteca_100.csv", registros_leidos, registros_cargados, registros_rechazados, estado))
    conn.commit() 
    cursor.close()
    conn.close()

    print("-" * 50)
    print(f"Filas leidas: {registros_leidos}")
    print(f"Filas cargadas: {registros_cargados}")
    print(f"Filas rechazadas: {registros_rechazados}")
    print(f"Estado: {estado}")
    print("-" * 50)

    # Crear reporte txt
    fecha_hora_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    reporte_content = (
        f"Nombre del alumno: {NOMBRE}\n"
        f"Fecha y hora de ejecución: {fecha_hora_actual}\n"
        f"Archivo procesado: prestamos_biblioteca_100.csv\n"
        f"Filas leídas: {registros_leidos}\n"
        f"Filas cargadas: {registros_cargados}\n"
        f"Filas rechazadas: {registros_rechazados}\n"
        f"Estado final: {estado}\n"
        f"Errores detectados:\n"
    )
    for err in errores:
        reporte_content += f"- {err}\n"
        
    # guardar reporte txt
    os.makedirs(os.path.dirname(REPORTE_PATH), exist_ok=True)
    with open(REPORTE_PATH, 'w', encoding='utf-8') as f:
        f.write(reporte_content)
        
    print("Reporte de ejecución guardado exitosamente")

if __name__ == '__main__':
    main()

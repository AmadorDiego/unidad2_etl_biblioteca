# Proyecto ETL Biblioteca

## Objetivo
Desarrollar un mini proyecto de ETL usando Python y MySQL, leyendo un dataset de préstamos de biblioteca (`prestamos_biblioteca_100.csv`)
El script realiza limpieza básica, valida registros correctos (rechazando multas mal calculadas e IDs duplicados), carga las dimensiones y tabla de hechos al Data Warehouse, registra un log de las ejecuciones, y genera un reporte en texto.

## Requisitos
- **Python 3.8+** instalado
- **MySQL Server** en ejecución

## Configuración y Dependencias

Para instalar las dependencias, ejecuta:

```bash
pip install pandas mysql-connector-python
```

## Ejecución del Script

Para ejecutar el pipeline ETL, ejecuta:

```bash
python scripts/etl_biblioteca.py
```

Al hacerlo:
1. Se creará automáticamente la base de datos `biblioteca_dw` en tu MySQL (si no existía).
2. Se crearán todas las tablas y dimensiones, truncándolas de ejecuciones anteriores (excepto el log).
3. Se leerá, procesará e insertarán los datos.
4. Mostrará por consola el resultado, que debe ser exactamente:
   - Filas leidas: 100
   - Filas cargadas: 98
   - Filas rechazadas: 2
   - Estado: FINALIZADO_CON_ERRORES

Además, se creará de forma automática el archivo `evidencias/reporte_ejecucion.txt`.

## Resultados Esperados

- **fact_prestamos**: Debe contener 98 registros.
- **etl_errores**: Debe contener 2 registros (el error de multa del id 5099 y el duplicado del id 5002).
- **etl_log**: Registrará la métrica de esta ejecución.
- En tu administrador de MySQL (Workbench, DataGrip, etc.), puedes abrir el archivo `sql/consultas_verificacion.sql` y ejecutarlo para comprobar las 10 métricas pedidas.


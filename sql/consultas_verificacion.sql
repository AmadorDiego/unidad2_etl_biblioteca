use biblioteca_dw;

select * from fact_prestamos;
select * from etl_errores;
select * from etl_log;

-- 1. Cuantos registros hay en `fact_prestamos`.
SELECT COUNT(*) AS total_fact_prestamos FROM fact_prestamos;

-- 2. Cuantos registros hay en `etl_errores`.
SELECT COUNT(*) AS total_etl_errores FROM etl_errores;

-- 3. Que errores fueron registrados.
SELECT id_registro, descripcion_error, archivo_origen FROM etl_errores;

-- 4. Cual fue el último estado registrado en `etl_log`.
SELECT estado, fecha_ejecucion FROM etl_log ORDER BY id_log DESC LIMIT 1;

-- 5. Total de multas por carrera.
SELECT c.carrera, SUM(f.total_multa) AS suma_multas
FROM fact_prestamos f
JOIN dim_carrera c ON f.id_carrera = c.id_carrera
GROUP BY c.carrera;

-- 6. Total de multas por categoria de libro.
SELECT l.categoria, SUM(f.total_multa) AS suma_multas
FROM fact_prestamos f
JOIN dim_libro l ON f.id_libro = l.id_libro
GROUP BY l.categoria;

-- 7. Promedio de dias de prestamo por sede.
SELECT s.sede, AVG(f.dias_prestamo) AS promedio_dias
FROM fact_prestamos f
JOIN dim_sede s ON f.id_sede = s.id_sede
GROUP BY s.sede;

-- 8. Los 5 libros con mayor total de multa.
SELECT l.libro, SUM(f.total_multa) AS total_multa_generada
FROM fact_prestamos f
JOIN dim_libro l ON f.id_libro = l.id_libro
GROUP BY l.libro
ORDER BY total_multa_generada DESC
LIMIT 5;

-- 9. Prestamos detallados con fecha, alumno, carrera, libro, categoria, sede y total de multa.
SELECT 
    fe.fecha, 
    a.alumno, 
    c.carrera, 
    l.libro, 
    l.categoria, 
    s.sede, 
    f.total_multa
FROM fact_prestamos f
JOIN dim_fecha fe ON f.id_fecha = fe.id_fecha
JOIN dim_alumno a ON f.id_alumno = a.id_alumno
JOIN dim_carrera c ON f.id_carrera = c.id_carrera
JOIN dim_libro l ON f.id_libro = l.id_libro
JOIN dim_sede s ON f.id_sede = s.id_sede
ORDER BY f.id_prestamo;

-- 10. Conteo de prestamos por sede.
SELECT s.sede, COUNT(f.id_prestamo) AS cantidad_prestamos
FROM fact_prestamos f
JOIN dim_sede s ON f.id_sede = s.id_sede
GROUP BY s.sede;

DROP DATABASE IF EXISTS `six_sigma`;

CREATE DATABASE `six_sigma`
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE `six_sigma`;

CREATE TABLE indicadores (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    nombre_indicador VARCHAR(150) NOT NULL,
    prioridad TINYINT UNSIGNED NOT NULL,
    sentido_esperado ENUM('ASCENDENTE', 'DESCENDENTE', 'MANTENER') NOT NULL,
    formula TEXT NOT NULL,
    tipo_agregacion ENUM('AGREGABLE', 'NO_AGREGABLE') NOT NULL,
    estado TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT chk_indicadores_prioridad
        CHECK (prioridad BETWEEN 1 AND 3)
);

CREATE TABLE acciones (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    indicador_id INT UNSIGNED NOT NULL,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    nombre_accion VARCHAR(200) NOT NULL,
    descripcion TEXT NULL,
    fecha_inicio DATE NULL,
    fecha_fin DATE NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_acciones_indicador
        FOREIGN KEY (indicador_id) REFERENCES indicadores(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE gestiones (
    id SMALLINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE meses (
    id TINYINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(20) NOT NULL UNIQUE,
    numero_mes TINYINT UNSIGNED NOT NULL UNIQUE,

    CONSTRAINT chk_meses_numero
        CHECK (numero_mes BETWEEN 1 AND 12)
);

CREATE TABLE periodos (
    id SMALLINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    gestion_id SMALLINT UNSIGNED NOT NULL,
    nombre VARCHAR(50) NOT NULL,
    mes_inicio_id TINYINT UNSIGNED NOT NULL,
    mes_fin_id TINYINT UNSIGNED NOT NULL,

    CONSTRAINT fk_periodos_gestion
        FOREIGN KEY (gestion_id) REFERENCES gestiones(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_periodos_mes_inicio
        FOREIGN KEY (mes_inicio_id) REFERENCES meses(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_periodos_mes_fin
        FOREIGN KEY (mes_fin_id) REFERENCES meses(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT uq_periodo_gestion_nombre
        UNIQUE (gestion_id, nombre)
);

CREATE TABLE avances (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    indicador_id INT UNSIGNED NOT NULL,
    periodo_id SMALLINT UNSIGNED NOT NULL,
    tipo_avance ENUM('TIPO_1', 'TIPO_2') NOT NULL,
    resultado DECIMAL(12,2) NOT NULL,

    CONSTRAINT fk_avances_indicador
        FOREIGN KEY (indicador_id) REFERENCES indicadores(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_avances_periodo
        FOREIGN KEY (periodo_id) REFERENCES periodos(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT uq_avance_indicador_tipo_rango
        UNIQUE (indicador_id, periodo_id, tipo_avance)
);

CREATE TABLE lineas_base (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    indicador_id INT UNSIGNED NOT NULL,
    gestion_id SMALLINT UNSIGNED NOT NULL,
    linea_base DECIMAL(12,2) NOT NULL,
                        
    CONSTRAINT fk_lineas_base_indicador
        FOREIGN KEY (indicador_id) REFERENCES indicadores(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_lineas_base_gestion
        FOREIGN KEY (gestion_id) REFERENCES gestiones(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT uq_linea_base_indicador_gestion
        UNIQUE (indicador_id, gestion_id)
);

CREATE TABLE metas_mensuales (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    indicador_id INT UNSIGNED NOT NULL,
    gestion_id SMALLINT UNSIGNED NOT NULL,
    mes_id TINYINT UNSIGNED NOT NULL,
    meta_mensual DECIMAL(12,2) NOT NULL,

    CONSTRAINT fk_metas_indicador
        FOREIGN KEY (indicador_id) REFERENCES indicadores(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_metas_gestion
        FOREIGN KEY (gestion_id) REFERENCES gestiones(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_metas_mes
        FOREIGN KEY (mes_id) REFERENCES meses(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT uq_meta_indicador_gestion_mes
        UNIQUE (indicador_id, gestion_id, mes_id)
);

CREATE TABLE metas_anuales (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    indicador_id INT UNSIGNED NOT NULL,
    gestion_id SMALLINT UNSIGNED NOT NULL,
    meta_anual DECIMAL(12,2) NOT NULL,

    CONSTRAINT fk_metas_anuales_indicador
        FOREIGN KEY (indicador_id) REFERENCES indicadores(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_metas_anuales_gestion
        FOREIGN KEY (gestion_id) REFERENCES gestiones(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT uq_meta_anual_indicador_gestion
        UNIQUE (indicador_id, gestion_id)
);

CREATE TABLE valores_obtenidos (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    indicador_id INT UNSIGNED NOT NULL,
    gestion_id SMALLINT UNSIGNED NOT NULL,
    mes_id TINYINT UNSIGNED NOT NULL,
    valor_obtenido DECIMAL(12,2) NOT NULL,

    CONSTRAINT fk_valores_indicador
        FOREIGN KEY (indicador_id) REFERENCES indicadores(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_valores_gestion
        FOREIGN KEY (gestion_id) REFERENCES gestiones(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_valores_mes
        FOREIGN KEY (mes_id) REFERENCES meses(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT uq_valor_indicador_gestion_mes
        UNIQUE (indicador_id, gestion_id, mes_id)
);

INSERT INTO meses (nombre, numero_mes) VALUES
('Enero', 1),
('Febrero', 2),
('Marzo', 3),
('Abril', 4),
('Mayo', 5),
('Junio', 6),
('Julio', 7),
('Agosto', 8),
('Septiembre', 9),
('Octubre', 10),
('Noviembre', 11),
('Diciembre', 12);

INSERT INTO gestiones (nombre) VALUES
('2025'),
('2026'),
('2027'),
('2028'),
('2029'),
('2030');

INSERT INTO periodos (gestion_id, nombre, mes_inicio_id, mes_fin_id)
SELECT g.id, p.nombre, mi.id, mf.id
FROM gestiones g
JOIN (
    SELECT 'Semestre 1' AS nombre, 1 AS mes_inicio, 6 AS mes_fin UNION ALL
    SELECT 'Semestre 2', 7, 12
) p
JOIN meses mi ON mi.numero_mes = p.mes_inicio
JOIN meses mf ON mf.numero_mes = p.mes_fin
ORDER BY g.nombre, p.mes_inicio, p.mes_fin;

INSERT INTO indicadores
    (codigo, nombre_indicador, prioridad, sentido_esperado, formula, tipo_agregacion)
VALUES
(
    'IND.01.OES 1',
    'Porcentaje de servicios interoperables validados mediante pruebas',
    1,
    'ASCENDENTE',
    '(N° de servicios interoperables validados mediante pruebas / Total de servicios interoperables programados para validación) x 100',
    'NO_AGREGABLE'
),
(
    'IND.02.OES 2',
    'Porcentaje de disponibilidad de los servicios de interoperabilidad',
    2,
    'ASCENDENTE',
    '(Tiempo real de disponibilidad del servicio / Tiempo total programado de disponibilidad) x 100',
    'NO_AGREGABLE'
),
(
    'IND.03.OES 3',
    'Porcentaje de incidentes de interoperabilidad resueltos dentro del tiempo',
    3,
    'ASCENDENTE',
    '(N° de incidentes resueltos dentro del tiempo establecido / Total de incidentes de interoperabilidad registrados) x 100',
    'NO_AGREGABLE'
);

INSERT INTO lineas_base (indicador_id, gestion_id, linea_base)
VALUES
(1, 2, 12),
(2, 2, 10),
(3, 2, 14);

INSERT INTO metas_mensuales (indicador_id, gestion_id, mes_id, meta_mensual)
VALUES
(1, 2, 1, 20),
(1, 2, 2, 35),
(1, 2, 3, 45),
(1, 2, 4, 55),
(1, 2, 5, 65),
(1, 2, 6, 75),
(2, 2, 1, 20),
(2, 2, 2, 35),
(2, 2, 3, 45),
(2, 2, 4, 55),
(2, 2, 5, 65),
(2, 2, 6, 75),
(3, 2, 1, 20),
(3, 2, 2, 35),
(3, 2, 3, 45),
(3, 2, 4, 55),
(3, 2, 5, 65),
(3, 2, 6, 75);

INSERT INTO valores_obtenidos (indicador_id, gestion_id, mes_id, valor_obtenido)
VALUES
(1, 2, 1, 18),
(1, 2, 2, 35),
(1, 2, 3, 45),
(1, 2, 4, 58),
(1, 2, 5, 65),
(1, 2, 6, 70),
(2, 2, 1, 15),
(2, 2, 2, 40),
(2, 2, 3, 50),
(2, 2, 4, 55),
(2, 2, 5, 60),
(2, 2, 6, 65),
(3, 2, 1, 20),
(3, 2, 2, 25),
(3, 2, 3, 45),
(3, 2, 4, 55),
(3, 2, 5, 60),
(3, 2, 6, 69);

INSERT INTO acciones (indicador_id, codigo, nombre_accion, descripcion)
VALUES
(1, 'ACC.01.IND01', 'Implementar pruebas de validación', 'Diseñar y ejecutar pruebas para servicios interoperables'),
(2, 'ACC.01.IND02', 'Monitoreo de disponibilidad', 'Configurar alertas y monitoreo 24/7'),
(3, 'ACC.01.IND03', 'Protocolo de gestión de incidentes', 'Definir SLA y flujos de resolución');
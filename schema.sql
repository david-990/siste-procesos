-- Volcando estructura de base de datos para railway
CREATE DATABASE IF NOT EXISTS `six_sigma` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `six_sigma`;   
   SET FOREIGN_KEY_CHECKS=0;
CREATE TABLE users (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    role ENUM('ADMIN', 'USER') NOT NULL DEFAULT 'USER',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO users (username, password_hash, nombre, role)
VALUES (
    'admin',
    'scrypt:32768:8:1$Cah0YTnL4NXSOVhz$e21b77c781d5468e02bdbb4a98769cca915a169976eac0594cc52e0d7f71621cecacade826e0a094089814b7186a15a2f76c90411314921e4ed1c2cace208778',
    'Administrador',
    'ADMIN'
);

-- Volcando estructura para tabla railway.objetivos_estrategicos
CREATE TABLE IF NOT EXISTS `objetivos_estrategicos` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `nombre` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla railway.objetivos_estrategicos: ~1 rows (aproximadamente)
INSERT INTO `objetivos_estrategicos` (`id`, `nombre`) VALUES
	(1, 'Fortalecer la transformación digital institucional mediante la integración de sistemas de información');

-- Volcando estructura para tabla railway.acciones_estrategicas
CREATE TABLE IF NOT EXISTS `acciones_estrategicas` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `objetivo_estrategico_id` int unsigned NOT NULL,
  `nombre` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_acciones_estrategicas_objetivo` (`objetivo_estrategico_id`),
  CONSTRAINT `fk_acciones_estrategicas_objetivo` FOREIGN KEY (`objetivo_estrategico_id`) REFERENCES `objetivos_estrategicos` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla railway.acciones_estrategicas: ~1 rows (aproximadamente)
INSERT INTO `acciones_estrategicas` (`id`, `objetivo_estrategico_id`, `nombre`) VALUES
	(1, 1, 'Implementar y mantener la interoperabilidad digital entre los sistemas de información institucionales');

-- Volcando estructura para tabla railway.avances
CREATE TABLE IF NOT EXISTS `avances` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `indicador_id` int unsigned NOT NULL,
  `periodo_id` smallint unsigned NOT NULL,
  `tipo_avance` enum('TIPO_1','TIPO_2') NOT NULL,
  `resultado` decimal(12,2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_avance_indicador_tipo_rango` (`indicador_id`,`periodo_id`,`tipo_avance`),
  KEY `fk_avances_periodo` (`periodo_id`),
  CONSTRAINT `fk_avances_indicador` FOREIGN KEY (`indicador_id`) REFERENCES `indicadores` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_avances_periodo` FOREIGN KEY (`periodo_id`) REFERENCES `periodos` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=64 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla railway.avances: ~15 rows (aproximadamente)
INSERT INTO `avances` (`id`, `indicador_id`, `periodo_id`, `tipo_avance`, `resultado`) VALUES
	(1, 1, 3, 'TIPO_1', 97.33),
	(2, 2, 3, 'TIPO_1', 86.67),
	(3, 3, 3, 'TIPO_1', 66.67),
	(17, 11, 3, 'TIPO_1', 93.33),
	(18, 10, 3, 'TIPO_1', 92.00),
	(19, 9, 3, 'TIPO_1', 90.67),
	(22, 12, 3, 'TIPO_1', 84.00),
	(23, 14, 3, 'TIPO_1', 89.33),
	(24, 15, 3, 'TIPO_1', 97.33),
	(34, 16, 3, 'TIPO_1', 80.00),
	(35, 17, 3, 'TIPO_1', 75.00),
	(36, 18, 3, 'TIPO_1', 90.33),
	(55, 19, 3, 'TIPO_1', 46.67),
	(56, 20, 3, 'TIPO_1', 85.33),
	(57, 21, 3, 'TIPO_1', 90.67);

-- Volcando estructura para tabla railway.avances_acciones_estrategicas
CREATE TABLE IF NOT EXISTS `avances_acciones_estrategicas` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `accion_estrategica_id` int unsigned NOT NULL,
  `periodo_id` smallint unsigned NOT NULL,
  `tipo_avance` enum('TIPO_1','TIPO_2') NOT NULL,
  `resultado` decimal(12,2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_avance_accion_tipo_periodo` (`accion_estrategica_id`, `periodo_id`, `tipo_avance`),
  CONSTRAINT `fk_avances_acciones_accion` FOREIGN KEY (`accion_estrategica_id`) REFERENCES `acciones_estrategicas` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_avances_acciones_periodo` FOREIGN KEY (`periodo_id`) REFERENCES `periodos` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando estructura para tabla railway.avances_objetivos_estrategicos
CREATE TABLE IF NOT EXISTS `avances_objetivos_estrategicos` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `objetivo_estrategico_id` int unsigned NOT NULL,
  `periodo_id` smallint unsigned NOT NULL,
  `tipo_avance` enum('TIPO_1','TIPO_2') NOT NULL,
  `resultado` decimal(12,2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_avance_objetivo_tipo_periodo` (`objetivo_estrategico_id`, `periodo_id`, `tipo_avance`),
  CONSTRAINT `fk_avances_objetivos_objetivo` FOREIGN KEY (`objetivo_estrategico_id`) REFERENCES `objetivos_estrategicos` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_avances_objetivos_periodo` FOREIGN KEY (`periodo_id`) REFERENCES `periodos` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando estructura para tabla railway.gestiones
CREATE TABLE IF NOT EXISTS `gestiones` (
  `id` smallint unsigned NOT NULL AUTO_INCREMENT,
  `nombre` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla railway.gestiones: ~6 rows (aproximadamente)
INSERT INTO `gestiones` (`id`, `nombre`) VALUES
	(1, '2025'),
	(2, '2026'),
	(3, '2027'),
	(4, '2028'),
	(5, '2029'),
	(6, '2030');

-- Volcando estructura para tabla railway.indicadores
CREATE TABLE IF NOT EXISTS `indicadores` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `accion_estrategica_id` int unsigned NOT NULL,
  `codigo` varchar(20) NOT NULL,
  `nombre_indicador` varchar(150) NOT NULL,
  `prioridad` tinyint unsigned NOT NULL,
  `sentido_esperado` enum('ASCENDENTE','DESCENDENTE','MANTENER') NOT NULL,
  `formula` text NOT NULL,
  `tipo_agregacion` enum('AGREGABLE','NO_AGREGABLE') NOT NULL,
  `estado` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo` (`codigo`),
  KEY `fk_indicadores_accion_estrategica` (`accion_estrategica_id`),
  CONSTRAINT `fk_indicadores_accion_estrategica` FOREIGN KEY (`accion_estrategica_id`) REFERENCES `acciones_estrategicas` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_indicadores_prioridad` CHECK ((`prioridad` between 1 and 3))
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla railway.indicadores: ~15 rows (aproximadamente)
INSERT INTO `indicadores` (`id`, `accion_estrategica_id`, `codigo`, `nombre_indicador`, `prioridad`, `sentido_esperado`, `formula`, `tipo_agregacion`, `estado`, `created_at`, `updated_at`) VALUES
	(1, 1, 'IND.01.', 'Porcentaje de servicios interoperables validados mediante pruebas', 1, 'ASCENDENTE', '(N° de servicios interoperables validados mediante pruebas / Total de servicios interoperables programados para validación) x 100', 'NO_AGREGABLE', 1, '2026-06-23 22:28:07', '2026-06-24 02:34:44'),
	(2, 1, 'IND.02', 'Porcentaje de disponibilidad de los servicios de interoperabilidad', 2, 'ASCENDENTE', '(Tiempo real de disponibilidad del servicio / Tiempo total programado de disponibilidad) x 100', 'NO_AGREGABLE', 1, '2026-06-23 22:28:07', '2026-06-24 02:34:57'),
	(3, 1, 'IND.03', 'Porcentaje de incidentes de interoperabilidad resueltos dentro del tiempo', 3, 'ASCENDENTE', '(N° de incidentes resueltos dentro del tiempo establecido / Total de incidentes de interoperabilidad registrados) x 100', 'NO_AGREGABLE', 1, '2026-06-23 22:28:07', '2026-06-24 02:35:04'),
	(9, 1, 'IND.01.M 2.3.1', 'Porcentaje de Datos validados semánticamente Normalizados y entregados a M3', 1, 'ASCENDENTE', '(N° datos normalizados entregados a M3 / Total datos recibidos de M2.2) x 100', 'NO_AGREGABLE', 1, '2026-06-24 09:56:19', '2026-06-24 09:56:19'),
	(10, 1, 'IND.01.M 2.2.1', 'Porcentaje Flujos de datos recibidosVerificados contra esquemas XSD/JSON', 2, 'ASCENDENTE', '(N° flujos verificados exitosamente / Total flujos recibidos desde M1) x 100', 'NO_AGREGABLE', 1, '2026-06-24 09:57:13', '2026-06-24 09:57:13'),
	(11, 1, 'IND.01.M 2.1.1', 'Porcentaje Catálogos de vocabularios controlados Publicados y actualizados', 3, 'ASCENDENTE', '(N° catálogos administrados y publicados / Total catálogos programados) x 100', 'NO_AGREGABLE', 1, '2026-06-24 09:58:16', '2026-06-24 09:58:16'),
	(12, 1, 'IND.10', 'Porcentaje de Requerimientos de interoperabilidad Alineados a instrumentos de gestión', 2, 'ASCENDENTE', 'Requerimientos de interoperabilidad alineados a instrumentos de gestión / Requerimientos de interoperabilidad evaluados x 100', 'NO_AGREGABLE', 1, '2026-06-24 13:34:31', '2026-06-24 13:34:31'),
	(14, 1, 'IND.11', 'Porcentaje de Servicios digitales interoperables Implementados correctamente', 2, 'ASCENDENTE', 'Servicios digitales interoperables implementados correctamente / Servicios digitales interoperables planificados x 100', 'NO_AGREGABLE', 1, '2026-06-24 13:36:25', '2026-06-24 13:36:25'),
	(15, 1, 'IND.12', 'Porcentaje de Roles organizacionales Formalizados para interoperabilidad', 2, 'ASCENDENTE', 'Roles organizacionales formalizados para interoperabilidad / Roles organizacionales requeridos para interoperabilidad x 100', 'NO_AGREGABLE', 1, '2026-06-24 13:36:58', '2026-06-24 13:36:58'),
	(16, 1, 'IND.13.M4.1', 'Porcentaje de normativa legal cumplida', 1, 'ASCENDENTE', '(Procesos que cumplen normativa / Total procesos evaluados) × 100', 'NO_AGREGABLE', 1, '2026-06-24 13:38:40', '2026-06-24 13:38:40'),
	(17, 1, 'IND.14.M4.3', 'Porcentaje documentos firmados digitalmente', 2, 'ASCENDENTE', '(Documentos firmados / Total documentos) × 100', 'NO_AGREGABLE', 1, '2026-06-24 13:39:29', '2026-06-24 13:39:29'),
	(18, 1, 'IND.15.M4.5', 'Porcentaje expedientes validados conforme a requisitos legales', 1, 'ASCENDENTE', '(Expedientes válidos / Total evaluados) × 100', 'NO_AGREGABLE', 1, '2026-06-24 13:40:35', '2026-06-24 14:12:33'),
	(19, 1, 'IND.04.OES1', 'porcentajes de consultas exitosas del servicio interoperable', 1, 'ASCENDENTE', '', 'NO_AGREGABLE', 1, '2026-06-24 13:58:56', '2026-06-24 13:58:56'),
	(20, 1, 'IND.05.OES1', 'Porcentaje de acciones correctivas y de mejora implementadaS', 2, 'ASCENDENTE', '', 'NO_AGREGABLE', 1, '2026-06-24 13:59:46', '2026-06-24 13:59:46'),
	(21, 1, 'IND.06.OES1', 'Porcentaje de verificaciones de consumo seguro conforme', 1, 'ASCENDENTE', '', 'NO_AGREGABLE', 1, '2026-06-24 14:00:12', '2026-06-24 14:00:12');

-- Volcando estructura para tabla railway.lineas_base
CREATE TABLE IF NOT EXISTS `lineas_base` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `indicador_id` int unsigned NOT NULL,
  `gestion_id` smallint unsigned NOT NULL,
  `linea_base` decimal(12,2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_linea_base_indicador_gestion` (`indicador_id`,`gestion_id`),
  KEY `fk_lineas_base_gestion` (`gestion_id`),
  CONSTRAINT `fk_lineas_base_gestion` FOREIGN KEY (`gestion_id`) REFERENCES `gestiones` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_lineas_base_indicador` FOREIGN KEY (`indicador_id`) REFERENCES `indicadores` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla railway.lineas_base: ~15 rows (aproximadamente)
INSERT INTO `lineas_base` (`id`, `indicador_id`, `gestion_id`, `linea_base`) VALUES
	(1, 1, 2, 12.00),
	(2, 2, 2, 10.00),
	(3, 3, 2, 14.00),
	(4, 11, 2, 15.00),
	(5, 10, 2, 14.00),
	(6, 9, 2, 15.00),
	(7, 12, 2, 12.00),
	(8, 14, 2, 14.00),
	(9, 15, 2, 12.00),
	(10, 16, 2, 10.00),
	(11, 17, 2, 10.00),
	(12, 18, 2, 10.00),
	(13, 19, 2, 11.00),
	(15, 20, 2, 11.00),
	(16, 21, 2, 14.00);

-- Volcando estructura para tabla railway.meses
CREATE TABLE IF NOT EXISTS `meses` (
  `id` tinyint unsigned NOT NULL AUTO_INCREMENT,
  `nombre` varchar(20) NOT NULL,
  `numero_mes` tinyint unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`),
  UNIQUE KEY `numero_mes` (`numero_mes`),
  CONSTRAINT `chk_meses_numero` CHECK ((`numero_mes` between 1 and 12))
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla railway.meses: ~12 rows (aproximadamente)
INSERT INTO `meses` (`id`, `nombre`, `numero_mes`) VALUES
	(1, 'Enero', 1),
	(2, 'Febrero', 2),
	(3, 'Marzo', 3),
	(4, 'Abril', 4),
	(5, 'Mayo', 5),
	(6, 'Junio', 6),
	(7, 'Julio', 7),
	(8, 'Agosto', 8),
	(9, 'Septiembre', 9),
	(10, 'Octubre', 10),
	(11, 'Noviembre', 11),
	(12, 'Diciembre', 12);

-- Volcando estructura para tabla railway.metas_anuales
CREATE TABLE IF NOT EXISTS `metas_anuales` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `indicador_id` int unsigned NOT NULL,
  `gestion_id` smallint unsigned NOT NULL,
  `meta_anual` decimal(12,2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_meta_anual_indicador_gestion` (`indicador_id`,`gestion_id`),
  KEY `fk_metas_anuales_gestion` (`gestion_id`),
  CONSTRAINT `fk_metas_anuales_gestion` FOREIGN KEY (`gestion_id`) REFERENCES `gestiones` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_metas_anuales_indicador` FOREIGN KEY (`indicador_id`) REFERENCES `indicadores` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla railway.metas_anuales: ~15 rows (aproximadamente)
INSERT INTO `metas_anuales` (`id`, `indicador_id`, `gestion_id`, `meta_anual`) VALUES
	(1, 1, 2, 95.00),
	(2, 2, 2, 95.00),
	(3, 3, 2, 95.00),
	(4, 11, 2, 95.00),
	(5, 10, 2, 95.00),
	(6, 9, 2, 95.00),
	(7, 12, 2, 95.00),
	(8, 14, 2, 95.00),
	(9, 15, 2, 95.00),
	(10, 16, 2, 95.00),
	(11, 17, 2, 95.00),
	(12, 18, 2, 95.00),
	(15, 19, 2, 95.00),
	(16, 20, 2, 95.00),
	(17, 21, 2, 95.00);

-- Volcando estructura para tabla railway.metas_mensuales
CREATE TABLE IF NOT EXISTS `metas_mensuales` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `indicador_id` int unsigned NOT NULL,
  `gestion_id` smallint unsigned NOT NULL,
  `mes_id` tinyint unsigned NOT NULL,
  `meta_mensual` decimal(12,2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_meta_indicador_gestion_mes` (`indicador_id`,`gestion_id`,`mes_id`),
  KEY `fk_metas_gestion` (`gestion_id`),
  KEY `fk_metas_mes` (`mes_id`),
  CONSTRAINT `fk_metas_gestion` FOREIGN KEY (`gestion_id`) REFERENCES `gestiones` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_metas_indicador` FOREIGN KEY (`indicador_id`) REFERENCES `indicadores` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_metas_mes` FOREIGN KEY (`mes_id`) REFERENCES `meses` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=125 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla railway.metas_mensuales: ~89 rows (aproximadamente)
INSERT INTO `metas_mensuales` (`id`, `indicador_id`, `gestion_id`, `mes_id`, `meta_mensual`) VALUES
	(1, 1, 2, 1, 20.00),
	(2, 1, 2, 2, 35.00),
	(3, 1, 2, 3, 45.00),
	(4, 1, 2, 4, 55.00),
	(5, 1, 2, 5, 65.00),
	(6, 1, 2, 6, 75.00),
	(7, 2, 2, 1, 20.00),
	(8, 2, 2, 2, 35.00),
	(9, 2, 2, 3, 45.00),
	(10, 2, 2, 4, 55.00),
	(11, 2, 2, 5, 65.00),
	(12, 2, 2, 6, 75.00),
	(13, 3, 2, 1, 20.00),
	(14, 3, 2, 2, 35.00),
	(15, 3, 2, 3, 45.00),
	(16, 3, 2, 4, 55.00),
	(17, 3, 2, 5, 65.00),
	(18, 3, 2, 6, 75.00),
	(22, 11, 2, 1, 20.00),
	(23, 11, 2, 2, 35.00),
	(27, 11, 2, 3, 45.00),
	(31, 11, 2, 4, 55.00),
	(32, 11, 2, 5, 65.00),
	(33, 11, 2, 6, 75.00),
	(34, 10, 2, 1, 20.00),
	(36, 10, 2, 2, 35.00),
	(37, 10, 2, 3, 45.00),
	(38, 10, 2, 4, 55.00),
	(39, 10, 2, 5, 65.00),
	(40, 10, 2, 6, 75.00),
	(41, 9, 2, 1, 20.00),
	(42, 9, 2, 2, 35.00),
	(43, 9, 2, 3, 45.00),
	(46, 9, 2, 4, 55.00),
	(47, 9, 2, 5, 65.00),
	(48, 9, 2, 6, 75.00),
	(49, 12, 2, 1, 20.00),
	(54, 12, 2, 2, 35.00),
	(57, 12, 2, 3, 45.00),
	(58, 12, 2, 4, 55.00),
	(59, 12, 2, 5, 65.00),
	(60, 12, 2, 6, 75.00),
	(61, 14, 2, 1, 20.00),
	(62, 14, 2, 2, 35.00),
	(63, 14, 2, 3, 45.00),
	(64, 14, 2, 4, 55.00),
	(66, 14, 2, 5, 65.00),
	(67, 14, 2, 6, 75.00),
	(68, 15, 2, 1, 20.00),
	(69, 16, 2, 1, 20.00),
	(70, 15, 2, 2, 35.00),
	(71, 15, 2, 3, 45.00),
	(72, 15, 2, 4, 55.00),
	(73, 15, 2, 5, 65.00),
	(75, 15, 2, 6, 75.00),
	(76, 16, 2, 2, 35.00),
	(79, 16, 2, 3, 45.00),
	(81, 16, 2, 4, 55.00),
	(82, 16, 2, 5, 65.00),
	(83, 16, 2, 6, 75.00),
	(84, 17, 2, 1, 20.00),
	(85, 17, 2, 2, 35.00),
	(91, 17, 2, 3, 45.00),
	(92, 17, 2, 4, 55.00),
	(93, 17, 2, 5, 65.00),
	(94, 17, 2, 6, 75.00),
	(95, 18, 2, 1, 20.00),
	(96, 18, 2, 2, 35.00),
	(97, 18, 2, 3, 45.00),
	(99, 18, 2, 4, 55.00),
	(100, 18, 2, 5, 65.00),
	(101, 18, 2, 6, 75.00),
	(106, 19, 2, 1, 20.00),
	(107, 19, 2, 2, 35.00),
	(108, 19, 2, 3, 45.00),
	(109, 19, 2, 4, 55.00),
	(110, 19, 2, 5, 65.00),
	(111, 19, 2, 6, 75.00),
	(112, 20, 2, 1, 20.00),
	(113, 20, 2, 2, 35.00),
	(114, 20, 2, 3, 45.00),
	(115, 20, 2, 4, 55.00),
	(116, 20, 2, 5, 65.00),
	(117, 20, 2, 6, 75.00),
	(119, 21, 2, 2, 35.00),
	(120, 21, 2, 3, 45.00),
	(121, 21, 2, 4, 55.00),
	(122, 21, 2, 5, 64.00),
	(123, 21, 2, 6, 75.00);

-- Volcando estructura para tabla railway.periodos
CREATE TABLE IF NOT EXISTS `periodos` (
  `id` smallint unsigned NOT NULL AUTO_INCREMENT,
  `gestion_id` smallint unsigned NOT NULL,
  `nombre` varchar(50) NOT NULL,
  `mes_inicio_id` tinyint unsigned NOT NULL,
  `mes_fin_id` tinyint unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_periodo_gestion_nombre` (`gestion_id`,`nombre`),
  KEY `fk_periodos_mes_inicio` (`mes_inicio_id`),
  KEY `fk_periodos_mes_fin` (`mes_fin_id`),
  CONSTRAINT `fk_periodos_gestion` FOREIGN KEY (`gestion_id`) REFERENCES `gestiones` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_periodos_mes_fin` FOREIGN KEY (`mes_fin_id`) REFERENCES `meses` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_periodos_mes_inicio` FOREIGN KEY (`mes_inicio_id`) REFERENCES `meses` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla railway.periodos: ~12 rows (aproximadamente)
INSERT INTO `periodos` (`id`, `gestion_id`, `nombre`, `mes_inicio_id`, `mes_fin_id`) VALUES
	(1, 1, 'Semestre 1', 1, 6),
	(2, 1, 'Semestre 2', 7, 12),
	(3, 2, 'Semestre 1', 1, 6),
	(4, 2, 'Semestre 2', 7, 12),
	(5, 3, 'Semestre 1', 1, 6),
	(6, 3, 'Semestre 2', 7, 12),
	(7, 4, 'Semestre 1', 1, 6),
	(8, 4, 'Semestre 2', 7, 12),
	(9, 5, 'Semestre 1', 1, 6),
	(10, 5, 'Semestre 2', 7, 12),
	(11, 6, 'Semestre 1', 1, 6),
	(12, 6, 'Semestre 2', 7, 12);

-- Volcando estructura para tabla railway.valores_obtenidos
CREATE TABLE IF NOT EXISTS `valores_obtenidos` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `indicador_id` int unsigned NOT NULL,
  `gestion_id` smallint unsigned NOT NULL,
  `mes_id` tinyint unsigned NOT NULL,
  `valor_obtenido` decimal(12,2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_valor_indicador_gestion_mes` (`indicador_id`,`gestion_id`,`mes_id`),
  KEY `fk_valores_gestion` (`gestion_id`),
  KEY `fk_valores_mes` (`mes_id`),
  CONSTRAINT `fk_valores_gestion` FOREIGN KEY (`gestion_id`) REFERENCES `gestiones` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_valores_indicador` FOREIGN KEY (`indicador_id`) REFERENCES `indicadores` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_valores_mes` FOREIGN KEY (`mes_id`) REFERENCES `meses` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=125 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Volcando datos para la tabla railway.valores_obtenidos: ~89 rows (aproximadamente)
INSERT INTO `valores_obtenidos` (`id`, `indicador_id`, `gestion_id`, `mes_id`, `valor_obtenido`) VALUES
	(1, 1, 2, 1, 18.00),
	(2, 1, 2, 2, 35.00),
	(3, 1, 2, 3, 45.00),
	(4, 1, 2, 4, 58.00),
	(5, 1, 2, 5, 65.00),
	(6, 1, 2, 6, 73.00),
	(7, 2, 2, 1, 15.00),
	(8, 2, 2, 2, 40.00),
	(9, 2, 2, 3, 50.00),
	(10, 2, 2, 4, 55.00),
	(11, 2, 2, 5, 60.00),
	(12, 2, 2, 6, 65.00),
	(13, 3, 2, 1, 20.00),
	(14, 3, 2, 2, 25.00),
	(15, 3, 2, 3, 45.00),
	(16, 3, 2, 4, 55.00),
	(17, 3, 2, 5, 60.00),
	(18, 3, 2, 6, 50.00),
	(22, 11, 2, 1, 15.00),
	(23, 11, 2, 2, 26.00),
	(27, 11, 2, 3, 37.00),
	(31, 11, 2, 4, 48.00),
	(32, 11, 2, 5, 59.00),
	(33, 11, 2, 6, 70.00),
	(34, 10, 2, 1, 14.00),
	(36, 10, 2, 2, 22.00),
	(37, 10, 2, 3, 51.00),
	(38, 10, 2, 4, 60.00),
	(39, 10, 2, 5, 65.00),
	(40, 10, 2, 6, 69.00),
	(41, 9, 2, 1, 15.00),
	(42, 9, 2, 2, 20.00),
	(43, 9, 2, 3, 34.00),
	(46, 9, 2, 4, 48.00),
	(47, 9, 2, 5, 60.00),
	(48, 9, 2, 6, 68.00),
	(49, 12, 2, 1, 15.00),
	(54, 12, 2, 2, 29.00),
	(57, 12, 2, 3, 40.00),
	(58, 12, 2, 4, 48.00),
	(59, 12, 2, 5, 56.00),
	(60, 12, 2, 6, 63.00),
	(61, 14, 2, 1, 18.00),
	(62, 14, 2, 2, 30.00),
	(63, 14, 2, 3, 39.00),
	(64, 14, 2, 4, 52.00),
	(66, 14, 2, 5, 59.00),
	(67, 14, 2, 6, 67.00),
	(68, 15, 2, 1, 16.00),
	(69, 16, 2, 1, 10.00),
	(70, 15, 2, 2, 32.00),
	(71, 15, 2, 3, 38.00),
	(72, 15, 2, 4, 51.00),
	(73, 15, 2, 5, 60.00),
	(75, 15, 2, 6, 73.00),
	(76, 16, 2, 2, 19.25),
	(79, 16, 2, 3, 27.00),
	(81, 16, 2, 4, 36.30),
	(82, 16, 2, 5, 50.70),
	(83, 16, 2, 6, 60.00),
	(84, 17, 2, 1, 10.40),
	(85, 17, 2, 2, 14.00),
	(91, 17, 2, 3, 22.95),
	(92, 17, 2, 4, 33.00),
	(93, 17, 2, 5, 44.20),
	(94, 17, 2, 6, 56.25),
	(95, 18, 2, 1, 12.00),
	(96, 18, 2, 2, 15.75),
	(97, 18, 2, 3, 24.75),
	(99, 18, 2, 4, 37.95),
	(100, 18, 2, 5, 48.75),
	(101, 18, 2, 6, 67.75),
	(106, 19, 2, 1, 20.00),
	(107, 19, 2, 2, 40.00),
	(108, 19, 2, 3, 58.00),
	(109, 19, 2, 4, 68.00),
	(110, 19, 2, 5, 68.00),
	(111, 19, 2, 6, 35.00),
	(112, 20, 2, 1, 15.00),
	(113, 20, 2, 2, 45.00),
	(114, 20, 2, 3, 60.00),
	(115, 20, 2, 4, 70.00),
	(116, 20, 2, 5, 60.00),
	(117, 20, 2, 6, 64.00),
	(119, 21, 2, 2, 42.00),
	(120, 21, 2, 3, 57.00),
	(121, 21, 2, 4, 65.00),
	(122, 21, 2, 5, 65.00),
	(123, 21, 2, 6, 68.00);

   SET FOREIGN_KEY_CHECKS=1;
-- --------------------------------------------------------
-- Host:                         reseau.proxy.rlwy.net
-- Versión del servidor:         9.4.0 - MySQL Community Server - GPL
-- SO del servidor:              Linux
-- HeidiSQL Versión:             12.3.0.6589
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Volcando estructura de base de datos para railway
CREATE DATABASE IF NOT EXISTS `railway` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `railway`;

-- Volcando estructura para tabla railway.acciones_estrategicas
CREATE TABLE IF NOT EXISTS `acciones_estrategicas` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `objetivo_estrategico_id` int unsigned NOT NULL,
  `nombre` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_acciones_estrategicas_objetivo` (`objetivo_estrategico_id`),
  CONSTRAINT `fk_acciones_estrategicas_objetivo` FOREIGN KEY (`objetivo_estrategico_id`) REFERENCES `objetivos_estrategicos` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- La exportación de datos fue deseleccionada.

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
) ENGINE=InnoDB AUTO_INCREMENT=139 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- La exportación de datos fue deseleccionada.

-- Volcando estructura para tabla railway.avances_acciones_estrategicas
CREATE TABLE IF NOT EXISTS `avances_acciones_estrategicas` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `accion_estrategica_id` int unsigned NOT NULL,
  `periodo_id` smallint unsigned NOT NULL,
  `tipo_avance` enum('TIPO_1','TIPO_2') NOT NULL,
  `resultado` decimal(12,2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_avance_accion_tipo_periodo` (`accion_estrategica_id`,`periodo_id`,`tipo_avance`),
  KEY `fk_avances_acciones_periodo` (`periodo_id`),
  CONSTRAINT `fk_avances_acciones_accion` FOREIGN KEY (`accion_estrategica_id`) REFERENCES `acciones_estrategicas` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_avances_acciones_periodo` FOREIGN KEY (`periodo_id`) REFERENCES `periodos` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- La exportación de datos fue deseleccionada.

-- Volcando estructura para tabla railway.avances_objetivos_estrategicos
CREATE TABLE IF NOT EXISTS `avances_objetivos_estrategicos` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `objetivo_estrategico_id` int unsigned NOT NULL,
  `periodo_id` smallint unsigned NOT NULL,
  `tipo_avance` enum('TIPO_1','TIPO_2') NOT NULL,
  `resultado` decimal(12,2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_avance_objetivo_tipo_periodo` (`objetivo_estrategico_id`,`periodo_id`,`tipo_avance`),
  KEY `fk_avances_objetivos_periodo` (`periodo_id`),
  CONSTRAINT `fk_avances_objetivos_objetivo` FOREIGN KEY (`objetivo_estrategico_id`) REFERENCES `objetivos_estrategicos` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_avances_objetivos_periodo` FOREIGN KEY (`periodo_id`) REFERENCES `periodos` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- La exportación de datos fue deseleccionada.

-- Volcando estructura para tabla railway.fichas_caracterizacion
CREATE TABLE IF NOT EXISTS `fichas_caracterizacion` (
  `id` int NOT NULL AUTO_INCREMENT,
  `codigo_proceso` varchar(50) NOT NULL,
  `nombre_proceso` varchar(255) NOT NULL,
  `tipo_proceso` varchar(100) NOT NULL,
  `dueno_proceso` varchar(255) NOT NULL,
  `objetivo_proceso` text NOT NULL,
  `objetivo_estrategico` text NOT NULL,
  `proveedor_entrada` text NOT NULL,
  `elementos_entrada` text NOT NULL,
  `producto` text NOT NULL,
  `receptor_producto` text NOT NULL,
  `actividades_proceso_imagen` varchar(255) DEFAULT NULL,
  `riesgos` text,
  `registros` text,
  `elaborado_por` varchar(150) NOT NULL,
  `revisado_por` varchar(150) DEFAULT NULL,
  `aprobado_por` varchar(150) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- La exportación de datos fue deseleccionada.

-- Volcando estructura para tabla railway.fichas_indicadores
CREATE TABLE IF NOT EXISTS `fichas_indicadores` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ficha_caracterizacion_id` int DEFAULT NULL,
  `proceso` varchar(255) NOT NULL,
  `producto` varchar(255) NOT NULL,
  `nombre_indicador` varchar(255) NOT NULL,
  `tipo_indicador` varchar(100) NOT NULL,
  `justificacion` text NOT NULL,
  `responsable` varchar(255) NOT NULL,
  `metodo_calculo` text NOT NULL,
  `sentido_esperado` varchar(100) NOT NULL,
  `unidad_medida` varchar(100) NOT NULL,
  `frecuencia` varchar(100) NOT NULL,
  `fuente_datos` varchar(255) NOT NULL,
  `valor_enero` varchar(50) DEFAULT NULL,
  `valor_febrero` varchar(50) DEFAULT NULL,
  `valor_marzo` varchar(50) DEFAULT NULL,
  `valor_abril` varchar(50) DEFAULT NULL,
  `valor_mayo` varchar(50) DEFAULT NULL,
  `valor_junio` varchar(50) DEFAULT NULL,
  `elaborado_por` varchar(150) DEFAULT NULL,
  `revisado_por` varchar(150) DEFAULT NULL,
  `aprobado_por` varchar(150) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- La exportación de datos fue deseleccionada.

-- Volcando estructura para tabla railway.gestiones
CREATE TABLE IF NOT EXISTS `gestiones` (
  `id` smallint unsigned NOT NULL AUTO_INCREMENT,
  `nombre` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- La exportación de datos fue deseleccionada.

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

-- La exportación de datos fue deseleccionada.

-- Volcando estructura para tabla railway.indicadores_procesos
CREATE TABLE IF NOT EXISTS `indicadores_procesos` (
  `indicador_id` int unsigned NOT NULL,
  `proceso_id` int NOT NULL,
  PRIMARY KEY (`indicador_id`,`proceso_id`),
  KEY `fk_ind_proc_proceso` (`proceso_id`),
  CONSTRAINT `fk_ind_proc_indicador` FOREIGN KEY (`indicador_id`) REFERENCES `indicadores` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_ind_proc_proceso` FOREIGN KEY (`proceso_id`) REFERENCES `procesos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- La exportación de datos fue deseleccionada.

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

-- La exportación de datos fue deseleccionada.

-- Volcando estructura para tabla railway.mapa
CREATE TABLE IF NOT EXISTS `mapa` (
  `id` int NOT NULL AUTO_INCREMENT,
  `imagen` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- La exportación de datos fue deseleccionada.

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

-- La exportación de datos fue deseleccionada.

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

-- La exportación de datos fue deseleccionada.

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

-- La exportación de datos fue deseleccionada.

-- Volcando estructura para tabla railway.objetivos_estrategicos
CREATE TABLE IF NOT EXISTS `objetivos_estrategicos` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `nombre` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- La exportación de datos fue deseleccionada.

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

-- La exportación de datos fue deseleccionada.

-- Volcando estructura para tabla railway.procesos
CREATE TABLE IF NOT EXISTS `procesos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nivel` tinyint unsigned NOT NULL DEFAULT '0',
  `tipo_proceso` enum('Estratégico','Misional','Apoyo') DEFAULT NULL,
  `producto_proceso` text NOT NULL,
  `codigo_proceso` varchar(20) NOT NULL,
  `nombre_proceso` varchar(255) NOT NULL,
  `proceso_padre_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo_proceso` (`codigo_proceso`),
  KEY `fk_proceso_padre` (`proceso_padre_id`),
  CONSTRAINT `fk_proceso_padre` FOREIGN KEY (`proceso_padre_id`) REFERENCES `procesos` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `procesos_chk_1` CHECK ((`nivel` between 0 and 3))
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- La exportación de datos fue deseleccionada.

-- Volcando estructura para tabla railway.resumenes_ia
CREATE TABLE IF NOT EXISTS `resumenes_ia` (
  `gestion_id` int unsigned NOT NULL,
  `periodo_id` smallint unsigned NOT NULL,
  `resumen` text NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `kurt_lewin` text,
  PRIMARY KEY (`gestion_id`,`periodo_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- La exportación de datos fue deseleccionada.

-- Volcando estructura para tabla railway.users
CREATE TABLE IF NOT EXISTS `users` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(80) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `nombre` varchar(150) NOT NULL,
  `role` enum('ADMIN','USER') NOT NULL DEFAULT 'USER',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- La exportación de datos fue deseleccionada.

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

-- La exportación de datos fue deseleccionada.

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;

import logging

import mysql.connector
from flask import Flask


def create_app():
    logging.basicConfig(level=logging.INFO)

    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    @app.errorhandler(mysql.connector.Error)
    def handle_database_error(error):
        app.logger.exception("Database error: %s", error)
        return (
            "<h1>Error de base de datos</h1>"
            "<p>No se pudo completar la operación. Inténtalo nuevamente.</p>",
            500,
        )

    from app.routes import bp

    app.register_blueprint(bp)

    # Inicializar tablas de IA necesarias
    with app.app_context():
        try:
            from app.db import execute
            execute(
                """
                CREATE TABLE IF NOT EXISTS resumenes_ia (
                    gestion_id INT UNSIGNED NOT NULL,
                    periodo_id SMALLINT UNSIGNED NOT NULL,
                    resumen TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    PRIMARY KEY (gestion_id, periodo_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
                """
            )
            execute(
                """
                CREATE TABLE IF NOT EXISTS archivos_pendientes_eliminar (
                    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    ruta_archivo VARCHAR(1024) NOT NULL,
                    intentos TINYINT UNSIGNED NOT NULL DEFAULT 0,
                    ultimo_error TEXT NULL,
                    proximo_intento_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    procesando_at TIMESTAMP NULL,
                    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_proximo_intento (proximo_intento_at, procesando_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
                """
            )
        except Exception as e:
            app.logger.error(f"Error al inicializar tablas: {e}")

    return app

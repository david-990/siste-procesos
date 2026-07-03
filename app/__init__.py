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
    return app

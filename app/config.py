import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        if os.getenv("FLASK_ENV") == "production" or os.getenv("ENV") == "production":
            raise RuntimeError("SECRET_KEY is required in production.")
        SECRET_KEY = "six-sigma-web-dev"

    DB_CONFIG = {
        "host": os.getenv("DB_HOST", os.getenv("MYSQLHOST", "localhost")),
        "user": os.getenv("DB_USER", os.getenv("MYSQLUSER", "root")),
        "password": os.getenv("DB_PASSWORD", os.getenv("MYSQLPASSWORD", "")),
        "database": os.getenv("DB_NAME", os.getenv("MYSQLDATABASE", "six_sigma")),
        "port": int(os.getenv("DB_PORT", os.getenv("MYSQLPORT", 3306))),
    }

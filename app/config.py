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

    # S3 / Backblaze B2
    S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
    S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
    S3_BUCKET = os.getenv("S3_BUCKET", "six-sigma-images")
    S3_ENDPOINT = os.getenv("S3_ENDPOINT")
    S3_REGION = os.getenv("S3_REGION", "us-east-005")
    S3_SIGNED_URL_EXPIRES_SECONDS = int(
        os.getenv("S3_SIGNED_URL_EXPIRES_SECONDS", "900")
    )

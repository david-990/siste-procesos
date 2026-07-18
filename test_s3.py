"""
Test rapido de conexion a Backblaze B2 / S3.

Uso:
    python test_s3.py

Requiere boto3 instalado y variables S3_* en .env.
"""

import os
import sys
import io
from dotenv import load_dotenv

load_dotenv(override=True)

# --- Verificar variables de entorno ---
required_vars = ["S3_ACCESS_KEY_ID", "S3_SECRET_ACCESS_KEY", "S3_ENDPOINT"]
missing = [v for v in required_vars if not os.getenv(v)]
if missing:
    print("[ERROR] Faltan variables de entorno:", ", ".join(missing))
    print("  Revisa tu archivo .env")
    sys.exit(1)

print("[OK] Variables de entorno S3 detectadas")

# --- Importar boto3 ---
try:
    import boto3
    from botocore.config import Config as BotoConfig
except ImportError:
    print("[ERROR] boto3 no esta instalado. Ejecuta: python -m pip install boto3")
    sys.exit(1)

print("[OK] boto3 instalado")

# --- Conectar ---
try:
    client = boto3.client(
        "s3",
        endpoint_url=os.getenv("S3_ENDPOINT"),
        region_name=os.getenv("S3_REGION", "us-east-005"),
        aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY"),
        config=BotoConfig(signature_version="s3v4"),
    )
    print("[OK] Conexion a S3 establecida")
except Exception as e:
    print(f"[ERROR] Error de conexion: {e}")
    sys.exit(1)

bucket = os.getenv("S3_BUCKET", "six-sigma-images")

# --- Subir archivo de prueba ---
test_key = f"imagenes/test_{os.urandom(4).hex()}.png"
test_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"  # Cabecera PNG real

try:
    client.upload_fileobj(
        io.BytesIO(test_data),
        bucket,
        test_key,
        ExtraArgs={"ContentType": "image/png"},
    )
    print(f"[OK] Archivo subido: {test_key}")
except Exception as e:
    print(f"[ERROR] Error al subir: {e}")
    sys.exit(1)

# --- Generar URL firmada ---
try:
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": test_key},
        ExpiresIn=900,
    )
    print(f"[OK] URL firmada generada (valida 15 min)")
    print(f"     {url[:100]}...")
except Exception as e:
    print(f"[ERROR] Error al generar URL: {e}")

# --- Eliminar archivo de prueba ---
try:
    client.delete_object(Bucket=bucket, Key=test_key)
    print(f"[OK] Archivo de prueba eliminado: {test_key}")
except Exception as e:
    print(f"[ERROR] Error al eliminar: {e}")

print("\nPrueba completada. S3/B2 funciona correctamente.")

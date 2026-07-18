"""
Servicio de almacenamiento de imágenes — Backblaze B2 / S3-compatible.
SOLO almacenamiento en la nube. No hay fallback a disco local.
"""

import os
import traceback
import uuid

from flask import current_app


def _s3_client():
    import boto3
    from botocore.config import Config as BotoConfig

    return boto3.client(
        "s3",
        endpoint_url=current_app.config["S3_ENDPOINT"],
        region_name=current_app.config["S3_REGION"],
        aws_access_key_id=current_app.config["S3_ACCESS_KEY_ID"],
        aws_secret_access_key=current_app.config["S3_SECRET_ACCESS_KEY"],
        config=BotoConfig(signature_version="s3v4"),
    )


def _object_key(subfolder, ext):
    """Genera: imagenes/mapas/a1b2c3d4.png"""
    return f"imagenes/{subfolder}/{uuid.uuid4().hex}{ext}"


def upload_file(file_storage, subfolder="mapas"):
    """
    Sube un archivo a S3/B2.

    Parámetros
    ----------
    file_storage : FileStorage
        Objeto FileStorage de Flask (request.files[...]).
    subfolder : str
        'mapas' o 'fichas'.

    Retorna
    -------
    str | None
        La key/ruta del archivo en S3, o None si falló.
    """
    _, ext = os.path.splitext(file_storage.filename.lower())

    try:
        key = _object_key(subfolder, ext)
        client = _s3_client()
        client.upload_fileobj(
            file_storage,
            current_app.config["S3_BUCKET"],
            key,
            ExtraArgs={"ContentType": file_storage.content_type or "image/png"},
        )
        return key
    except Exception:
        print(f"[STORAGE ERROR] Error al subir archivo a S3:\n{traceback.format_exc()}")
        return None


def delete_file(key):
    """
    Elimina un archivo de S3/B2. Trata 404 como éxito.
    Relanza la excepción si no es NoSuchKey, para que el procesador
    de cola pueda registrar el fallo.
    """
    if not key:
        return

    try:
        client = _s3_client()
        client.delete_object(Bucket=current_app.config["S3_BUCKET"], Key=key)
    except Exception as exc:
        error_code = getattr(exc, "response", {}).get("Error", {}).get("Code", "")
        if error_code == "NoSuchKey":
            return  # 404 = ya no existe, es éxito
        raise


def get_signed_url(key, expires_in=900):
    """
    Genera URL firmada temporal para ver la imagen desde S3/B2.

    Retorna None si la key es inválida o si falla la generación.
    """
    if not key:
        return None

    try:
        client = _s3_client()
        return client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": current_app.config["S3_BUCKET"],
                "Key": key,
            },
            ExpiresIn=current_app.config.get(
                "S3_SIGNED_URL_EXPIRES_SECONDS", expires_in
            ),
        )
    except Exception:
        print(
            f"[STORAGE ERROR] Error al generar signed URL para {key}:\n{traceback.format_exc()}"
        )
        return None

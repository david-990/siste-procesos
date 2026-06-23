from contextlib import contextmanager

import mysql.connector
from flask import current_app


@contextmanager
def get_connection():
    conn = mysql.connector.connect(**current_app.config["DB_CONFIG"])
    try:
        yield conn
    finally:
        conn.close()


def fetch_all(query, params=None):
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        return cursor.fetchall()


def fetch_one(query, params=None):
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        return cursor.fetchone()


def execute(query, params=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        return cursor.lastrowid

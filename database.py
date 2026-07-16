"""
Modul database sederhana menggunakan SQLite.
SQLite dipilih karena tidak butuh instalasi server database terpisah -
cukup 1 file (db.sqlite3) yang otomatis dibuat saat aplikasi pertama kali dijalankan.
"""
import sqlite3
from contextlib import contextmanager

DB_PATH = "db.sqlite3"


def init_db():
    """Membuat tabel users jika belum ada. Dipanggil sekali saat app start."""
    with get_db() as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_verified INTEGER DEFAULT 0,
            verify_token TEXT
        )
        """)
        db.commit()


@contextmanager
def get_db():
    """Context manager supaya koneksi selalu tertutup dengan rapi."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

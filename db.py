"""
db.py
Thin PostgreSQL connection helper built on raw psycopg2 -- no ORM,
per project constraints (HTML/CSS/JS + Flask + PostgreSQL only).
"""
import os
import psycopg2
import psycopg2.extras


def get_connection():
    """Open a new connection to PostgreSQL using env vars."""
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ.get("DB_NAME", "shareplate"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", ""),
    )


def query(sql, params=None, fetchone=False, fetchall=False, commit=False):
    """
    Run a SQL statement with a fresh connection/cursor.

    - fetchone=True  -> returns a single dict row (or None)
    - fetchall=True  -> returns a list of dict rows
    - commit=True    -> commits the transaction (use for INSERT/UPDATE/DELETE)

    For INSERTs that need the new row's id, add `RETURNING id` to the SQL
    and call with fetchone=True, commit=True.
    """
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params or ())

        result = None
        if fetchone:
            row = cur.fetchone()
            result = dict(row) if row else None
        elif fetchall:
            rows = cur.fetchall()
            result = [dict(r) for r in rows]

        if commit:
            conn.commit()

        cur.close()
        return result
    finally:
        conn.close()

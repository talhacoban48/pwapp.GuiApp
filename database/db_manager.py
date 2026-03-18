import sqlite3
import os
from pathlib import Path

import pandas as pd
from cryptography.fernet import Fernet

from utils.crypto import encrypt, decrypt, looks_encrypted


class DatabaseManager:

    COLUMNS = ["appname", "username", "email", "password", "url", "aktifpasif"]

    def __init__(self, fernet: Fernet):
        """
        fernet — the Fernet instance derived from the master password.
                 Used to encrypt passwords on write and decrypt on read.
        """
        self.fernet = fernet

        basepath = Path(os.path.expanduser("~/pwapp"))
        basepath.mkdir(parents=True, exist_ok=True)
        self.db_path = str(basepath / "database.db")
        self._create_table()

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        conn = self._connect()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS passwords (
                    appname    TEXT PRIMARY KEY,
                    username   TEXT,
                    email      TEXT,
                    password   TEXT,
                    url        TEXT,
                    aktifpasif TEXT
                )
            """)
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _clean(value) -> str | None:
        """Return None for the string literal 'None' or for None/empty values."""
        if value is None:
            return None
        s = str(value)
        return None if s in ("None", "nan", "") else s

    def _row_to_dict(self, row: tuple) -> dict:
        """Convert a DB row tuple to a dict, cleaning nulls and decrypting password."""
        d = {k: self._clean(v) for k, v in zip(self.COLUMNS, row)}
        if d["password"]:
            d["password"] = decrypt(d["password"], self.fernet)
        return d

    # ------------------------------------------------------------------ #
    #  Migration                                                           #
    # ------------------------------------------------------------------ #

    def migrate_to_encrypted(self):
        """
        Encrypt any plaintext passwords already in the database.
        Safe to call multiple times — skips rows whose password already
        looks like a Fernet token (starts with 'gAAAAA').
        """
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT appname, password FROM passwords"
            ).fetchall()

            changed = 0
            for appname, password in rows:
                if password and not looks_encrypted(password):
                    conn.execute(
                        "UPDATE passwords SET password=? WHERE appname=?",
                        (encrypt(password, self.fernet), appname)
                    )
                    changed += 1

            if changed:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------ #
    #  Read operations                                                     #
    # ------------------------------------------------------------------ #

    def get_all(self) -> list[tuple]:
        """Return list of (appname, aktifpasif) tuples for all entries."""
        conn = self._connect()
        try:
            return conn.execute(
                "SELECT appname, aktifpasif FROM passwords"
            ).fetchall()
        finally:
            conn.close()

    def get_one(self, appname: str) -> dict | None:
        """Return a dict (with decrypted password) for the given appname."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM passwords WHERE appname = ?", (appname,)
            ).fetchone()
        finally:
            conn.close()
        return self._row_to_dict(row) if row else None

    def exists(self, appname: str) -> bool:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT 1 FROM passwords WHERE appname = ?", (appname,)
            ).fetchone()
        finally:
            conn.close()
        return row is not None

    # ------------------------------------------------------------------ #
    #  Write operations                                                    #
    # ------------------------------------------------------------------ #

    def insert(self, appname: str, username: str, email: str,
               password: str, url: str, aktifpasif: str):
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO passwords "
                "(appname, username, email, password, url, aktifpasif) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    appname,
                    self._clean(username),
                    self._clean(email),
                    encrypt(password, self.fernet),   # always encrypted
                    self._clean(url),
                    aktifpasif,
                )
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def update(self, appname: str, username: str, email: str,
               password: str, url: str, aktifpasif: str):
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE passwords "
                "SET username=?, email=?, password=?, url=?, aktifpasif=? "
                "WHERE appname=?",
                (
                    self._clean(username),
                    self._clean(email),
                    encrypt(password, self.fernet),   # always encrypted
                    self._clean(url),
                    aktifpasif,
                    appname,
                )
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def delete(self, appname: str):
        conn = self._connect()
        try:
            conn.execute(
                "DELETE FROM passwords WHERE appname = ?", (appname,)
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------ #
    #  Export / Import                                                     #
    # ------------------------------------------------------------------ #

    def export_to_excel(self, filepath: str):
        """Export all entries with DECRYPTED passwords to Excel."""
        self._to_dataframe().to_excel(filepath, index=False)

    def export_to_csv(self, filepath: str):
        """Export all entries with DECRYPTED passwords to CSV."""
        self._to_dataframe().to_csv(filepath, index=False)

    def import_from_dataframe(self, df: pd.DataFrame) -> tuple[int, int]:
        """
        Insert rows from df that do not already exist in the database.
        Passwords from the file are treated as plaintext and re-encrypted.
        Returns (inserted_count, skipped_count).
        Raises ValueError if required columns are missing.
        """
        missing = [c for c in self.COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(
                f"Missing columns: {', '.join(missing)}\n"
                f"Required columns: {', '.join(self.COLUMNS)}"
            )

        inserted = skipped = 0
        conn = self._connect()
        try:
            for _, row in df.iterrows():
                appname = self._clean(str(row["appname"]))
                if appname is None:
                    skipped += 1
                    continue

                already_exists = conn.execute(
                    "SELECT 1 FROM passwords WHERE appname = ?", (appname,)
                ).fetchone()
                if already_exists:
                    skipped += 1
                    continue

                aktifpasif = self._clean(str(row["aktifpasif"]))
                if aktifpasif not in ("aktif", "pasif"):
                    aktifpasif = "aktif"

                raw_password = self._clean(str(row["password"])) or ""

                conn.execute(
                    "INSERT INTO passwords "
                    "(appname, username, email, password, url, aktifpasif) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        appname,
                        self._clean(str(row["username"])),
                        self._clean(str(row["email"])),
                        encrypt(raw_password, self.fernet),
                        self._clean(str(row["url"])),
                        aktifpasif,
                    )
                )
                inserted += 1

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        return inserted, skipped

    def _to_dataframe(self) -> pd.DataFrame:
        """Return all rows as a DataFrame with DECRYPTED passwords."""
        conn = self._connect()
        try:
            rows = conn.execute("SELECT * FROM passwords").fetchall()
        finally:
            conn.close()
        data = [self._row_to_dict(row) for row in rows]
        return pd.DataFrame(data, columns=self.COLUMNS)

import sqlite3
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from cryptography.fernet import Fernet

from utils.crypto import encrypt, decrypt, looks_encrypted


def _now() -> str:
    """Return current datetime as ISO-8601 string (seconds precision)."""
    return datetime.now().isoformat(timespec="seconds")


class DatabaseManager:

    COLUMNS = [
        "appname", "username", "email", "password",
        "url", "aktifpasif", "createdDate", "updatedDate",
    ]

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
        self._migrate_schema()

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        """Create the passwords table if it does not already exist."""
        conn = self._connect()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS passwords (
                    appname     TEXT PRIMARY KEY,
                    username    TEXT,
                    email       TEXT,
                    password    TEXT,
                    url         TEXT,
                    aktifpasif  TEXT,
                    createdDate TEXT,
                    updatedDate TEXT
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def _migrate_schema(self):
        """
        Add createdDate / updatedDate columns to databases created before
        this feature was introduced.  Safe to call on already-migrated DBs.
        """
        conn = self._connect()
        try:
            existing_cols = {
                row[1]
                for row in conn.execute("PRAGMA table_info(passwords)").fetchall()
            }
            for col in ("createdDate", "updatedDate"):
                if col not in existing_cols:
                    conn.execute(
                        f"ALTER TABLE passwords ADD COLUMN {col} TEXT"
                    )
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
        Safe to call multiple times — skips rows that already look encrypted.
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
        now = _now()
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO passwords "
                "(appname, username, email, password, url, aktifpasif, createdDate, updatedDate) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    appname,
                    self._clean(username),
                    self._clean(email),
                    encrypt(password, self.fernet),
                    self._clean(url),
                    aktifpasif,
                    now,
                    now,
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
                "SET username=?, email=?, password=?, url=?, aktifpasif=?, updatedDate=? "
                "WHERE appname=?",
                (
                    self._clean(username),
                    self._clean(email),
                    encrypt(password, self.fernet),
                    self._clean(url),
                    aktifpasif,
                    _now(),
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

    def import_from_dataframe(self, df: pd.DataFrame) -> tuple[int, int, int]:
        """
        Merge rows from df into the database.

        - New entries (appname not in DB)  → INSERT with createdDate = now
        - Existing entries:
            * File has 'updatedDate' column AND imported date > DB date → UPDATE
            * Otherwise                                                  → skip

        Passwords from the file are treated as plaintext and re-encrypted.

        Returns (inserted_count, updated_count, skipped_count).
        Raises ValueError if required core columns are missing.
        """
        core_columns = [c for c in self.COLUMNS if c not in ("createdDate", "updatedDate")]
        missing = [c for c in core_columns if c not in df.columns]
        if missing:
            raise ValueError(
                f"Missing columns: {', '.join(missing)}\n"
                f"Required columns: {', '.join(core_columns)}"
            )

        has_updated_date = "updatedDate" in df.columns
        has_created_date = "createdDate" in df.columns

        inserted = updated = skipped = 0
        conn = self._connect()
        try:
            for _, row in df.iterrows():
                appname = self._clean(str(row["appname"]))
                if appname is None:
                    skipped += 1
                    continue

                aktifpasif = self._clean(str(row["aktifpasif"]))
                if aktifpasif not in ("aktif", "pasif"):
                    aktifpasif = "aktif"

                raw_password = self._clean(str(row["password"])) or ""

                db_row = conn.execute(
                    "SELECT updatedDate FROM passwords WHERE appname = ?",
                    (appname,)
                ).fetchone()

                if db_row is None:
                    # New entry — INSERT
                    created = (
                        self._clean(str(row["createdDate"])) if has_created_date else None
                    ) or _now()
                    updated_dt = (
                        self._clean(str(row["updatedDate"])) if has_updated_date else None
                    ) or _now()

                    conn.execute(
                        "INSERT INTO passwords "
                        "(appname, username, email, password, url, aktifpasif, createdDate, updatedDate) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            appname,
                            self._clean(str(row["username"])),
                            self._clean(str(row["email"])),
                            encrypt(raw_password, self.fernet),
                            self._clean(str(row["url"])),
                            aktifpasif,
                            created,
                            updated_dt,
                        )
                    )
                    inserted += 1

                else:
                    # Existing entry — update only if imported data is newer
                    db_updated_date = db_row[0]  # may be None for old rows
                    imported_updated_date = (
                        self._clean(str(row["updatedDate"])) if has_updated_date else None
                    )

                    is_newer = (
                        imported_updated_date is not None
                        and (
                            db_updated_date is None
                            or imported_updated_date > db_updated_date
                        )
                    )

                    if is_newer:
                        conn.execute(
                            "UPDATE passwords "
                            "SET username=?, email=?, password=?, url=?, aktifpasif=?, updatedDate=? "
                            "WHERE appname=?",
                            (
                                self._clean(str(row["username"])),
                                self._clean(str(row["email"])),
                                encrypt(raw_password, self.fernet),
                                self._clean(str(row["url"])),
                                aktifpasif,
                                imported_updated_date,
                                appname,
                            )
                        )
                        updated += 1
                    else:
                        skipped += 1

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        return inserted, updated, skipped

    def _to_dataframe(self) -> pd.DataFrame:
        """Return all rows as a DataFrame with DECRYPTED passwords."""
        conn = self._connect()
        try:
            rows = conn.execute("SELECT * FROM passwords").fetchall()
        finally:
            conn.close()
        data = [self._row_to_dict(row) for row in rows]
        return pd.DataFrame(data, columns=self.COLUMNS)

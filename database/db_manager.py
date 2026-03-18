import csv
import sqlite3
import os
from datetime import datetime
from pathlib import Path

import openpyxl
from cryptography.fernet import Fernet

from utils.crypto import encrypt, decrypt, looks_encrypted


def _now() -> str:
    """Return current datetime as ISO-8601 string (seconds precision)."""
    return datetime.now().isoformat(timespec="seconds")


def _to_status(value) -> int:
    """Convert True/False/1/0/'1'/'0' to SQLite INTEGER (1 or 0)."""
    if value is None:
        return 1
    s = str(value).strip().lower()
    return 0 if s in ("false", "0") else 1


class DatabaseManager:

    COLUMNS = [
        "appname", "username", "email", "password",
        "url", "recordStatus", "createdDate", "updatedDate",
    ]

    def __init__(self, fernet: Fernet):
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
                    appname      TEXT    PRIMARY KEY,
                    username     TEXT,
                    email        TEXT,
                    password     TEXT,
                    url          TEXT,
                    recordStatus INTEGER NOT NULL DEFAULT 1,
                    createdDate  TEXT,
                    updatedDate  TEXT
                )
            """)
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _clean(value) -> str | None:
        if value is None:
            return None
        s = str(value)
        return None if s in ("None", "nan", "") else s

    def _row_to_dict(self, row: tuple) -> dict:
        d = {k: self._clean(v) for k, v in zip(self.COLUMNS, row)}
        if d["password"]:
            d["password"] = decrypt(d["password"], self.fernet)
        rs = d.get("recordStatus")
        d["recordStatus"] = bool(int(rs)) if rs is not None else True
        return d

    # ------------------------------------------------------------------ #
    #  Encryption migration (first-run only)                              #
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
    #  Read                                                                #
    # ------------------------------------------------------------------ #

    def get_all(self) -> list[tuple]:
        """Return list of (appname, recordStatus) tuples; recordStatus is int 0 or 1."""
        conn = self._connect()
        try:
            return conn.execute(
                "SELECT appname, recordStatus FROM passwords"
            ).fetchall()
        finally:
            conn.close()

    def get_one(self, appname: str) -> dict | None:
        """Return a dict (decrypted password, bool recordStatus) or None."""
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
    #  Write                                                               #
    # ------------------------------------------------------------------ #

    def insert(self, appname: str, username: str, email: str,
               password: str, url: str, recordStatus: bool):
        now = _now()
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO passwords "
                "(appname, username, email, password, url, recordStatus, createdDate, updatedDate) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    appname,
                    self._clean(username),
                    self._clean(email),
                    encrypt(password, self.fernet),
                    self._clean(url),
                    int(recordStatus),
                    now, None,
                )
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def update(self, appname: str, username: str, email: str,
               password: str, url: str, recordStatus: bool):
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE passwords "
                "SET username=?, email=?, password=?, url=?, recordStatus=?, updatedDate=? "
                "WHERE appname=?",
                (
                    self._clean(username),
                    self._clean(email),
                    encrypt(password, self.fernet),
                    self._clean(url),
                    int(recordStatus),
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
        rows = self._get_all_rows()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(self.COLUMNS)
        for row in rows:
            ws.append([row.get(c) for c in self.COLUMNS])
        wb.save(filepath)

    def export_to_csv(self, filepath: str):
        rows = self._get_all_rows()
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.COLUMNS)
            writer.writeheader()
            writer.writerows(rows)

    def import_from_rows(self, rows: list[dict]) -> tuple[int, int, int]:
        """
        Merge rows into the database.

        Required keys: appname, username, email, password, url, recordStatus
        Optional keys: createdDate, updatedDate (used for merge conflict resolution)

        - New entries                               → INSERT
        - Existing + imported updatedDate is newer → UPDATE
        - Existing + no date / older date           → skip

        Returns (inserted_count, updated_count, skipped_count).
        """
        required = ["appname", "username", "email", "password", "url", "recordStatus"]
        if rows:
            missing = [c for c in required if c not in rows[0]]
            if missing:
                raise ValueError(
                    f"Missing columns: {', '.join(missing)}\n"
                    f"Required: {', '.join(required)}"
                )

        inserted = updated = skipped = 0
        conn = self._connect()
        try:
            for row in rows:
                appname = self._clean(str(row.get("appname", "")))
                if appname is None:
                    skipped += 1
                    continue

                record_status = _to_status(row.get("recordStatus"))
                raw_password  = self._clean(str(row.get("password", ""))) or ""

                db_row = conn.execute(
                    "SELECT updatedDate FROM passwords WHERE appname = ?",
                    (appname,)
                ).fetchone()

                if db_row is None:
                    created = self._clean(str(row.get("createdDate", ""))) or _now()
                    updated_dt = self._clean(str(row.get("updatedDate", "")))

                    conn.execute(
                        "INSERT INTO passwords "
                        "(appname, username, email, password, url, recordStatus, createdDate, updatedDate) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            appname,
                            self._clean(str(row.get("username", ""))),
                            self._clean(str(row.get("email", ""))),
                            encrypt(raw_password, self.fernet),
                            self._clean(str(row.get("url", ""))),
                            record_status,
                            created,
                            updated_dt,
                        )
                    )
                    inserted += 1

                else:
                    db_updated_date       = db_row[0]
                    imported_updated_date = self._clean(str(row.get("updatedDate", "")))
                    is_newer = (
                        imported_updated_date is not None
                        and (db_updated_date is None or imported_updated_date > db_updated_date)
                    )

                    if is_newer:
                        conn.execute(
                            "UPDATE passwords "
                            "SET username=?, email=?, password=?, url=?, recordStatus=?, updatedDate=? "
                            "WHERE appname=?",
                            (
                                self._clean(str(row.get("username", ""))),
                                self._clean(str(row.get("email", ""))),
                                encrypt(raw_password, self.fernet),
                                self._clean(str(row.get("url", ""))),
                                record_status,
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

    def _get_all_rows(self) -> list[dict]:
        conn = self._connect()
        try:
            rows = conn.execute("SELECT * FROM passwords").fetchall()
        finally:
            conn.close()
        return [self._row_to_dict(row) for row in rows]

"""SQLite persistence layer for the job application tracker.

Stores one row per saved analysis. UI-agnostic — no Streamlit imports.
Database file: job_tracker.db in the project root (git-ignored).
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Generator, Optional

DB_PATH = Path(__file__).parent / "job_tracker.db"

STATUSES = ["Saved", "Applied", "Interviewing", "Offer", "Rejected"]


@contextmanager
def _conn() -> Generator[sqlite3.Connection, None, None]:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init_db() -> None:
    """Create the applications table if it doesn't exist."""
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                job_title TEXT    NOT NULL,
                company   TEXT    NOT NULL DEFAULT '',
                score     INTEGER NOT NULL,
                status    TEXT    NOT NULL DEFAULT 'Saved',
                notes     TEXT    NOT NULL DEFAULT '',
                saved_on  TEXT    NOT NULL
            )
        """)


def save_application(
    job_title: str,
    score: int,
    company: str = "",
    notes: str = "",
) -> int:
    """Insert a new application row. Returns the new row id."""
    init_db()
    with _conn() as con:
        cur = con.execute(
            "INSERT INTO applications (job_title, company, score, status, notes, saved_on) "
            "VALUES (?, ?, ?, 'Saved', ?, ?)",
            (job_title.strip(), company.strip(), score, notes.strip(), date.today().isoformat()),
        )
        return cur.lastrowid  # type: ignore[return-value]


def update_status(row_id: int, status: str) -> None:
    """Update the status of an existing application."""
    init_db()
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    with _conn() as con:
        con.execute("UPDATE applications SET status = ? WHERE id = ?", (status, row_id))


def update_notes(row_id: int, notes: str) -> None:
    """Update the notes field for an existing application."""
    init_db()
    with _conn() as con:
        con.execute("UPDATE applications SET notes = ? WHERE id = ?", (notes.strip(), row_id))


def delete_application(row_id: int) -> None:
    """Delete an application by id."""
    init_db()
    with _conn() as con:
        con.execute("DELETE FROM applications WHERE id = ?", (row_id,))


def get_all_applications() -> list[dict]:
    """Return all applications newest-first as a list of dicts."""
    init_db()
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM applications ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_stats() -> dict:
    """Return summary stats: total, avg_score, status_counts."""
    init_db()
    with _conn() as con:
        total = con.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
        avg = con.execute("SELECT AVG(score) FROM applications").fetchone()[0]
        rows = con.execute(
            "SELECT status, COUNT(*) as cnt FROM applications GROUP BY status"
        ).fetchall()
    return {
        "total": total,
        "avg_score": round(avg, 1) if avg else 0,
        "by_status": {r["status"]: r["cnt"] for r in rows},
    }


def export_csv() -> str:
    """Return all applications as a CSV string."""
    apps = get_all_applications()
    if not apps:
        return "id,job_title,company,score,status,notes,saved_on\n"
    header = ",".join(apps[0].keys())
    lines = [header]
    for app in apps:
        lines.append(",".join(
            f'"{str(v).replace(chr(34), chr(39))}"' for v in app.values()
        ))
    return "\n".join(lines)

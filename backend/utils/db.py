"""
SQLite database layer for LotWise.

SQLite holds the *structured* data (suppliers, lots, batches, shipments, lab
reports). We use it for deterministic look-ups and the contamination trace,
which is a graph traversal rather than a semantic search.

The RAG layer (utils/rag.py) is separate and handles free-text questions.
"""

import csv
import os
import sqlite3
from typing import Any, Dict, List, Optional

# Project paths
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, "data")
DB_PATH = os.path.join(BACKEND_DIR, "lotwise.db")

# Maps an upload "type" -> (csv filename, table name, primary key column)
TABLES = {
    "suppliers": ("suppliers.csv", "suppliers", "supplier_id"),
    "lots": ("lots.csv", "lots", "lot_id"),
    "batches": ("batches.csv", "batches", "batch_id"),
    "shipments": ("shipments.csv", "shipments", "shipment_id"),
    "lab_reports": ("lab_reports.csv", "lab_reports", "report_id"),
}


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn


def init_db() -> None:
    """Create tables if they do not exist."""
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id TEXT PRIMARY KEY,
            name TEXT,
            city TEXT,
            country TEXT,
            ingredient_supplied TEXT,
            contact_email TEXT,
            rating REAL
        );
        CREATE TABLE IF NOT EXISTS lots (
            lot_id TEXT PRIMARY KEY,
            supplier_id TEXT,
            ingredient TEXT,
            quantity_kg INTEGER,
            received_date TEXT,
            status TEXT
        );
        CREATE TABLE IF NOT EXISTS batches (
            batch_id TEXT PRIMARY KEY,
            lot_id TEXT,
            product_name TEXT,
            production_date TEXT,
            quantity_units INTEGER,
            facility TEXT
        );
        CREATE TABLE IF NOT EXISTS shipments (
            shipment_id TEXT PRIMARY KEY,
            batch_id TEXT,
            distributor TEXT,
            destination TEXT,
            ship_date TEXT,
            status TEXT
        );
        CREATE TABLE IF NOT EXISTS lab_reports (
            report_id TEXT PRIMARY KEY,
            lot_id TEXT,
            test_type TEXT,
            test_date TEXT,
            result TEXT,
            status TEXT
        );
        """
    )
    conn.commit()
    conn.close()


def _load_csv_file(csv_path: str, table: str, pk: str) -> int:
    """Insert-or-replace every row of a CSV into a table. Returns row count."""
    if not os.path.exists(csv_path):
        return 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        return 0

    columns = list(rows[0].keys())
    placeholders = ", ".join(["?"] * len(columns))
    col_list = ", ".join(columns)
    sql = f"INSERT OR REPLACE INTO {table} ({col_list}) VALUES ({placeholders})"

    conn = get_conn()
    cur = conn.cursor()
    for row in rows:
        cur.execute(sql, [row[c] for c in columns])
    conn.commit()
    conn.close()
    return len(rows)


def seed_from_csv_dir() -> Dict[str, int]:
    """Load all default CSVs from the data/ folder into SQLite."""
    init_db()
    counts = {}
    for key, (filename, table, pk) in TABLES.items():
        path = os.path.join(DATA_DIR, filename)
        counts[key] = _load_csv_file(path, table, pk)
    return counts


def load_uploaded_csv(saved_path: str, dataset_type: str) -> int:
    """Load one uploaded CSV (already saved to disk) into the matching table."""
    if dataset_type not in TABLES:
        raise ValueError(f"Unknown dataset type: {dataset_type}")
    _, table, pk = TABLES[dataset_type]
    return _load_csv_file(saved_path, table, pk)


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------
def _rows_to_dicts(rows) -> List[Dict[str, Any]]:
    return [dict(r) for r in rows]


def table_count(table: str) -> int:
    conn = get_conn()
    n = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
    conn.close()
    return n


def lab_alert_count() -> int:
    conn = get_conn()
    n = conn.execute(
        "SELECT COUNT(*) AS c FROM lab_reports WHERE status = 'Contaminated'"
    ).fetchone()["c"]
    conn.close()
    return n


def get_supplier(supplier_id: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM suppliers WHERE supplier_id = ?", (supplier_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_lot(lot_id: str) -> Optional[Dict[str, Any]]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM lots WHERE lot_id = ?", (lot_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_batches_for_lot(lot_id: str) -> List[Dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM batches WHERE lot_id = ?", (lot_id,)
    ).fetchall()
    conn.close()
    return _rows_to_dicts(rows)


def get_shipments_for_batches(batch_ids: List[str]) -> List[Dict[str, Any]]:
    if not batch_ids:
        return []
    conn = get_conn()
    placeholders = ",".join("?" * len(batch_ids))
    rows = conn.execute(
        f"SELECT * FROM shipments WHERE batch_id IN ({placeholders})", batch_ids
    ).fetchall()
    conn.close()
    return _rows_to_dicts(rows)


def get_lab_reports_for_lot(lot_id: str) -> List[Dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM lab_reports WHERE lot_id = ?", (lot_id,)
    ).fetchall()
    conn.close()
    return _rows_to_dicts(rows)


def dashboard_stats() -> Dict[str, Any]:
    """Counts + small aggregations used by the dashboard charts."""
    conn = get_conn()

    def scalar(sql, args=()):
        return conn.execute(sql, args).fetchone()[0]

    suppliers = scalar("SELECT COUNT(*) FROM suppliers")
    lots = scalar("SELECT COUNT(*) FROM lots")
    batches = scalar("SELECT COUNT(*) FROM batches")
    shipments = scalar("SELECT COUNT(*) FROM shipments")
    alerts = scalar("SELECT COUNT(*) FROM lab_reports WHERE status = 'Contaminated'")

    # Lab result breakdown (for a pie/donut chart)
    lab_rows = conn.execute(
        "SELECT status, COUNT(*) AS c FROM lab_reports GROUP BY status"
    ).fetchall()
    lab_breakdown = [{"name": r["status"], "value": r["c"]} for r in lab_rows]

    # Top suppliers by number of lots (for a bar chart)
    sup_rows = conn.execute(
        """
        SELECT s.name AS name, COUNT(l.lot_id) AS lots
        FROM suppliers s
        LEFT JOIN lots l ON l.supplier_id = s.supplier_id
        GROUP BY s.supplier_id
        ORDER BY lots DESC
        LIMIT 6
        """
    ).fetchall()
    supplier_lots = [{"name": r["name"], "lots": r["lots"]} for r in sup_rows]

    conn.close()
    return {
        "suppliers": suppliers,
        "lots": lots,
        "batches": batches,
        "shipments": shipments,
        "lab_alerts": alerts,
        "lab_breakdown": lab_breakdown,
        "supplier_lots": supplier_lots,
    }

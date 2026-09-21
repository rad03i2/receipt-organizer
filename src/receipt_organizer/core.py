from __future__ import annotations

import csv
import io
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable


class ReceiptError(ValueError):
    pass


@dataclass(frozen=True)
class Receipt:
    id: int
    purchased_on: str
    merchant: str
    amount_cents: int
    currency: str
    category: str
    note: str
    created_at: str

    @property
    def amount(self) -> str:
        return f"{Decimal(self.amount_cents) / 100:.2f}"

    def to_dict(self) -> dict:
        data = asdict(self)
        data["amount"] = self.amount
        return data


def parse_amount(value: str) -> int:
    try:
        amount = Decimal(value.strip()).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, AttributeError):
        raise ReceiptError("amount must be a valid decimal number") from None
    if amount < 0:
        raise ReceiptError("amount must not be negative")
    if amount > Decimal("999999999.99"):
        raise ReceiptError("amount is too large")
    return int(amount * 100)


def validate_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise ReceiptError("date must use YYYY-MM-DD") from None


def clean_text(value: str, field: str, *, required: bool = False, max_length: int = 200) -> str:
    text = " ".join(value.strip().split())
    if required and not text:
        raise ReceiptError(f"{field} is required")
    if len(text) > max_length:
        raise ReceiptError(f"{field} exceeds {max_length} characters")
    return text


def normalize_currency(value: str) -> str:
    code = value.strip().upper()
    if len(code) != 3 or not code.isalpha() or not code.isascii():
        raise ReceiptError("currency must be a 3-letter code such as USD or IQD")
    return code


class ReceiptStore:
    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.execute("PRAGMA journal_mode = WAL")
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchased_on TEXT NOT NULL,
                merchant TEXT NOT NULL,
                amount_cents INTEGER NOT NULL CHECK(amount_cents >= 0),
                currency TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_receipts_date ON receipts(purchased_on)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_receipts_merchant ON receipts(merchant)")
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    @staticmethod
    def _row(row: sqlite3.Row) -> Receipt:
        return Receipt(**dict(row))

    def add(self, purchased_on: str, merchant: str, amount: str, currency: str = "USD", category: str = "", note: str = "") -> Receipt:
        values = (
            validate_date(purchased_on),
            clean_text(merchant, "merchant", required=True),
            parse_amount(amount),
            normalize_currency(currency),
            clean_text(category, "category", max_length=80),
            clean_text(note, "note", max_length=500),
            datetime.now().astimezone().isoformat(timespec="seconds"),
        )
        cur = self.db.execute("INSERT INTO receipts(purchased_on,merchant,amount_cents,currency,category,note,created_at) VALUES(?,?,?,?,?,?,?)", values)
        self.db.commit()
        return self.get(cur.lastrowid)

    def get(self, receipt_id: int) -> Receipt:
        row = self.db.execute("SELECT * FROM receipts WHERE id=?", (receipt_id,)).fetchone()
        if row is None:
            raise ReceiptError(f"receipt {receipt_id} was not found")
        return self._row(row)

    def delete(self, receipt_id: int) -> None:
        cur = self.db.execute("DELETE FROM receipts WHERE id=?", (receipt_id,))
        self.db.commit()
        if not cur.rowcount:
            raise ReceiptError(f"receipt {receipt_id} was not found")

    def list(self, *, search: str = "", category: str = "", currency: str = "", since: str = "", until: str = "", limit: int = 100) -> list[Receipt]:
        if limit < 1 or limit > 10000:
            raise ReceiptError("limit must be between 1 and 10000")
        clauses, args = [], []
        if search:
            clauses.append("(merchant LIKE ? ESCAPE '\\' OR note LIKE ? ESCAPE '\\')")
            escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            args.extend([f"%{escaped}%", f"%{escaped}%"])
        if category:
            clauses.append("category = ?")
            args.append(clean_text(category, "category", max_length=80))
        if currency:
            clauses.append("currency = ?")
            args.append(normalize_currency(currency))
        if since:
            clauses.append("purchased_on >= ?")
            args.append(validate_date(since))
        if until:
            clauses.append("purchased_on <= ?")
            args.append(validate_date(until))
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        args.append(limit)
        rows = self.db.execute(f"SELECT * FROM receipts{where} ORDER BY purchased_on DESC,id DESC LIMIT ?", args).fetchall()
        return [self._row(r) for r in rows]

    def summary(self, *, since: str = "", until: str = "") -> dict:
        receipts = self.list(since=since, until=until, limit=10000)
        currencies: dict[str, dict] = {}
        categories: dict[str, dict[str, int]] = {}
        for r in receipts:
            item = currencies.setdefault(r.currency, {"count": 0, "amount_cents": 0})
            item["count"] += 1
            item["amount_cents"] += r.amount_cents
            cat = r.category or "Uncategorized"
            categories.setdefault(r.currency, {})[cat] = categories.setdefault(r.currency, {}).get(cat, 0) + r.amount_cents
        return {
            "receipt_count": len(receipts),
            "currencies": {k: {"count": v["count"], "total": f'{Decimal(v["amount_cents"]) / 100:.2f}'} for k, v in sorted(currencies.items())},
            "categories": {cur: {cat: f"{Decimal(cents) / 100:.2f}" for cat, cents in sorted(vals.items())} for cur, vals in sorted(categories.items())},
        }

    def export_json(self, receipts: Iterable[Receipt]) -> str:
        return json.dumps({"schema": 1, "receipts": [r.to_dict() for r in receipts]}, ensure_ascii=False, indent=2)

    def export_csv(self, receipts: Iterable[Receipt]) -> str:
        out = io.StringIO(newline="")
        writer = csv.writer(out)
        writer.writerow(["id", "purchased_on", "merchant", "amount", "currency", "category", "note", "created_at"])
        for r in receipts:
            writer.writerow([r.id, r.purchased_on, r.merchant, r.amount, r.currency, r.category, r.note, r.created_at])
        return out.getvalue()

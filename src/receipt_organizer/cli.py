from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

from . import __version__
from .core import ReceiptError, ReceiptStore


def default_db() -> Path:
    configured = os.environ.get("RECEIPT_ORGANIZER_DB")
    if configured:
        return Path(configured).expanduser()
    home = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
    return home / "receipt-organizer" / "receipts.db"


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="receipt-organizer", description="Organize receipt records locally.")
    p.add_argument("--db", type=Path, default=default_db(), help="SQLite database path")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__} — Radwan Abdulhadi Ahmed (@rad03i2)")
    sub = p.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Add a receipt")
    add.add_argument("--date", default=date.today().isoformat(), dest="purchased_on")
    add.add_argument("--merchant", required=True)
    add.add_argument("--amount", required=True)
    add.add_argument("--currency", default="USD")
    add.add_argument("--category", default="")
    add.add_argument("--note", default="")

    ls = sub.add_parser("list", help="List/search receipts")
    ls.add_argument("--search", default="")
    ls.add_argument("--category", default="")
    ls.add_argument("--currency", default="")
    ls.add_argument("--since", default="")
    ls.add_argument("--until", default="")
    ls.add_argument("--limit", type=int, default=100)
    ls.add_argument("--json", action="store_true")

    show = sub.add_parser("show", help="Show one receipt")
    show.add_argument("id", type=int)
    show.add_argument("--json", action="store_true")

    delete = sub.add_parser("delete", help="Delete one receipt")
    delete.add_argument("id", type=int)

    summary = sub.add_parser("summary", help="Summarize spending without mixing currencies")
    summary.add_argument("--since", default="")
    summary.add_argument("--until", default="")
    summary.add_argument("--json", action="store_true")

    export = sub.add_parser("export", help="Export filtered records")
    export.add_argument("--format", choices=["json", "csv"], default="json")
    export.add_argument("--output", type=Path)
    export.add_argument("--search", default="")
    export.add_argument("--category", default="")
    export.add_argument("--currency", default="")
    export.add_argument("--since", default="")
    export.add_argument("--until", default="")
    export.add_argument("--limit", type=int, default=10000)
    export.add_argument("--force", action="store_true")
    return p


def _filters(args):
    return dict(search=getattr(args, "search", ""), category=getattr(args, "category", ""), currency=getattr(args, "currency", ""), since=getattr(args, "since", ""), until=getattr(args, "until", ""), limit=getattr(args, "limit", 100))


def _table(receipts):
    if not receipts:
        return "No receipts found."
    lines = ["ID  DATE        AMOUNT        CATEGORY         MERCHANT", "--  ----------  ------------  ---------------  ------------------------------"]
    for r in receipts:
        lines.append(f"{r.id:<3} {r.purchased_on:<10}  {r.amount:>10} {r.currency:<3}  {(r.category or '-'):15.15}  {r.merchant[:30]}")
    return "\n".join(lines)


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        with ReceiptStore(args.db) as store:
            if args.command == "add":
                r = store.add(args.purchased_on, args.merchant, args.amount, args.currency, args.category, args.note)
                print(f"Added receipt #{r.id}: {r.merchant} — {r.amount} {r.currency}")
            elif args.command == "list":
                rows = store.list(**_filters(args))
                print(json.dumps([r.to_dict() for r in rows], ensure_ascii=False, indent=2) if args.json else _table(rows))
            elif args.command == "show":
                r = store.get(args.id)
                print(json.dumps(r.to_dict(), ensure_ascii=False, indent=2) if args.json else _table([r]))
            elif args.command == "delete":
                store.delete(args.id)
                print(f"Deleted receipt #{args.id}.")
            elif args.command == "summary":
                data = store.summary(since=args.since, until=args.until)
                if args.json:
                    print(json.dumps(data, ensure_ascii=False, indent=2))
                else:
                    print(f"Receipts: {data['receipt_count']}")
                    for cur, info in data["currencies"].items():
                        print(f"{cur}: {info['total']} across {info['count']} receipt(s)")
                        for cat, total in data["categories"].get(cur, {}).items():
                            print(f"  {cat}: {total}")
            elif args.command == "export":
                rows = store.list(**_filters(args))
                content = store.export_json(rows) if args.format == "json" else store.export_csv(rows)
                if args.output:
                    output = args.output.expanduser()
                    if output.exists() and not args.force:
                        raise ReceiptError(f"output already exists: {output} (use --force to replace)")
                    output.parent.mkdir(parents=True, exist_ok=True)
                    temp = output.with_name(output.name + ".tmp")
                    temp.write_text(content, encoding="utf-8", newline="")
                    temp.replace(output)
                    print(f"Exported {len(rows)} receipt(s) to {output}")
                else:
                    print(content, end="" if content.endswith("\n") else "\n")
        return 0
    except (ReceiptError, OSError, sqlite3.Error) as exc:  # sqlite3 imported lazily below
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    import sqlite3
    raise SystemExit(main())
else:
    import sqlite3

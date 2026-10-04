"""Idempotent monetary ingestion with atomic batch validation and reconciliation."""

from decimal import Decimal, InvalidOperation
from pathlib import Path
import csv, hashlib, json, re, sqlite3

CURRENCIES = {"USD": 2, "EUR": 2, "INR": 2, "GBP": 2, "JPY": 0, "KWD": 3}
FIELDS = {"event_id", "reference", "kind", "currency", "amount"}


def validate(row):
    if set(row) != FIELDS or any(
        not isinstance(v, str) or not v.strip() for v in row.values()
    ):
        raise ValueError("Event fields are required")
    row = {k: v.strip() for k, v in row.items()}
    if (
        not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", row["event_id"])
        or len(row["reference"]) > 120
    ):
        raise ValueError("Invalid event identity or reference")
    if row["kind"] not in ["invoice", "settlement"]:
        raise ValueError("Kind must be invoice or settlement")
    if row["currency"] not in CURRENCIES:
        raise ValueError("Unsupported currency")
    if len(row["amount"]) > 80 or not re.fullmatch(r"\d+(?:\.\d+)?", row["amount"]):
        raise ValueError("Use a plain nonnegative decimal amount without exponents")
    try:
        amount = Decimal(row["amount"])
    except InvalidOperation as exc:
        raise ValueError("Invalid amount") from exc
    if not amount.is_finite() or amount <= 0 or amount > Decimal("1000000000000"):
        raise ValueError("Amount must be positive, finite and at most one trillion")
    if amount != amount.quantize(Decimal(1).scaleb(-CURRENCIES[row["currency"]])):
        raise ValueError("Amount exceeds currency minor-unit precision")
    factor = Decimal(10) ** CURRENCIES[row["currency"]]
    minor = amount * factor
    if minor != minor.to_integral_value():
        raise ValueError("Amount exceeds currency minor-unit precision")
    row["minor_units"] = int(minor)
    row.pop("amount")
    return row


def connect(database):
    connection = sqlite3.connect(database, timeout=15)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS events(event_id TEXT PRIMARY KEY, reference TEXT NOT NULL, kind TEXT NOT NULL,currency TEXT NOT NULL,minor_units INTEGER NOT NULL,fingerprint TEXT NOT NULL)"
    )
    connection.commit()
    return connection


def ingest(database, rows):
    connection = connect(database)
    inserted = duplicates = 0
    try:
        connection.execute("BEGIN IMMEDIATE")
        for original in rows:
            row = validate(original)
            fingerprint = hashlib.sha256(
                json.dumps(row, sort_keys=True).encode()
            ).hexdigest()
            previous = connection.execute(
                "SELECT fingerprint FROM events WHERE event_id=?", (row["event_id"],)
            ).fetchone()
            if previous:
                if previous[0] != fingerprint:
                    raise ValueError("Event ID reused with conflicting content")
                duplicates += 1
                continue
            connection.execute(
                "INSERT INTO events VALUES (?,?,?,?,?,?)",
                (
                    row["event_id"],
                    row["reference"],
                    row["kind"],
                    row["currency"],
                    row["minor_units"],
                    fingerprint,
                ),
            )
            inserted += 1
        connection.commit()
        return {"inserted": inserted, "duplicates": duplicates}
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def ingest_csv(database, source):
    with Path(source).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if (
            not reader.fieldnames
            or len(reader.fieldnames) != len(FIELDS)
            or set(reader.fieldnames) != FIELDS
        ):
            raise ValueError("CSV headers must match event fields")
        return ingest(database, reader)


def report(database):
    connection = connect(database)
    try:
        rows = connection.execute(
            "SELECT reference,currency,SUM(CASE WHEN kind='invoice' THEN minor_units ELSE 0 END),SUM(CASE WHEN kind='settlement' THEN minor_units ELSE 0 END) FROM events GROUP BY reference,currency ORDER BY reference,currency"
        ).fetchall()
        return {
            "groups": [
                {
                    "reference": ref,
                    "currency": currency,
                    "invoiced_minor": invoiced,
                    "settled_minor": settled,
                    "difference_minor": invoiced - settled,
                    "status": (
                        "matched"
                        if invoiced == settled
                        else "underpaid" if invoiced > settled else "overpaid"
                    ),
                }
                for ref, currency, invoiced, settled in rows
            ]
        }
    finally:
        connection.close()


def export_csv(database):
    from io import StringIO

    output = StringIO(newline="")
    fields = [
        "reference",
        "currency",
        "invoiced_minor",
        "settled_minor",
        "difference_minor",
        "status",
    ]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for original in report(database)["groups"]:
        row = dict(original)
        text = row["reference"]
        if text.lstrip().startswith(("=", "+", "-", "@")) or text.startswith(
            ("\t", "\r", "\n")
        ):
            row["reference"] = "'" + text
        writer.writerow(row)
    return output.getvalue()

# Event Reconciliation Ledger

Exact-money event ingestion, idempotency and settlement matching. An independent Python 3.11+ project using the standard library, with a real command-line interface and no runtime package dependencies.

## Run locally

From the cloned repository, run:

```sh
python -m event_reconciliation_ledger ingest examples/ledger.db examples/events.csv
python -m event_reconciliation_ledger report examples/ledger.db
python -m event_reconciliation_ledger --help
```

Examples contain synthetic data. First use requires no cloud account, API key or package download. Optionally install the CLI using `python -m pip install .` and run `event-reconciliation-ledger --help`.

## Verify

```sh
python -m unittest discover -v
```

GitHub Actions checks Python 3.11 and 3.13 on Linux and Windows, verifies package installation, and builds/runs the non-root Docker image.

```sh
docker build -t event-reconciliation-ledger .
docker run --rm event-reconciliation-ledger --help
```

Mount a working directory at `/workspace` to process your own files. The container runs as UID 10001; provide appropriate write permissions for outputs.

## Architecture and scope

Business algorithms live in `event_reconciliation_ledger/core.py`; `event_reconciliation_ledger/cli.py` owns argument parsing and JSON output. Tests exercise success cases and failure boundaries, with temporary storage for mutations. See [design decisions](docs/architecture.md).

Currency minor units are explicit. Repeated identical event IDs are idempotent; conflicting IDs roll back the batch. Settlements may split across events; reconciliation groups by reference and currency. No bank connection is made.

This project demonstrates implemented engineering practices. It does not claim production deployment history or external certifications.

## Spreadsheet-safe reconciliation exports

Export settlement reconciliation as CSV, with formula-like reference values neutralized before spreadsheet use. Currency groups and exact integer minor units are preserved.

```sh
python -m event_reconciliation_ledger report examples/ledger.db --format csv
```

Create the named input snapshots, databases or plan files first using the existing commands above.

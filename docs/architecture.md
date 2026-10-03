# Event Reconciliation Ledger: architecture

## Exact monetary units and durable idempotency

Amounts use Decimal, explicit currency precision and integer minor units. Each event has a semantic fingerprint; identical repeat IDs are ignored, while conflicting content rejects the entire ingestion batch. BEGIN IMMEDIATE keeps conflict checks and inserts atomic.

## Module boundaries

`event_reconciliation_ledger/core.py` contains the algorithm and persistence operations. `cli.py` validates arguments and prints JSON. The package entrypoint translates input and storage errors into structured stderr with exit status 2. Domain-specific unsuccessful results can use exit status 1. There is no shared runtime dependency on the portfolio folder.

## Failure and operational boundaries

References reconcile separately per currency, including split settlements, underpayments and overpayments. Amounts require plain decimal strings without exponent notation. The currency set is explicit rather than inferred. This is a local event ledger, not accounting advice or a bank integration. SQLite integer aggregates have a finite range.

## Verification

Core tests cover valid results and failure boundaries. Process-level CLI tests run the committed examples in temporary copies, inspect JSON output and verify domain outcomes. CI runs on Python 3.11 and 3.13, Linux and Windows, checks package installation, and builds and executes the non-root Docker image.

## Extension choices

The standard-library implementation keeps local execution inspectable and offline. A hosted or distributed version would require workload-specific authorization, resource limits, durable coordination and observability. Extend the core through tested functions rather than adding infrastructure without a scaling requirement.

import argparse, json
from .core import ingest_csv, report, export_csv


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Ingest exact-money events and export reconciliation reports"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    sub = commands.add_parser("ingest")
    sub.add_argument("database")
    sub.add_argument("source")
    sub = commands.add_parser("report")
    sub.add_argument("database")
    sub.add_argument("--format", choices=["json", "csv"], default="json")
    args = parser.parse_args(argv)
    if args.command == "report" and args.format == "csv":
        print(export_csv(args.database), end="")
        return
    print(
        json.dumps(
            (
                ingest_csv(args.database, args.source)
                if args.command == "ingest"
                else report(args.database)
            ),
            indent=2,
        )
    )

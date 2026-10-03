import argparse, json
from .core import ingest_csv, report


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Ingest exact-money events and reconcile settlements"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    load = commands.add_parser("ingest")
    load.add_argument("database")
    load.add_argument("source")
    check = commands.add_parser("report")
    check.add_argument("database")
    args = parser.parse_args(argv)
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

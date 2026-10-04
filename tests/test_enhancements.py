import unittest, json, csv, io
from tests import test_ledger as fixtures
from event_reconciliation_ledger.core import ingest, export_csv


class FeatureTests(unittest.TestCase):
    setUp = fixtures.LedgerTests.setUp
    tearDown = fixtures.LedgerTests.tearDown

    def test_csv_preserves_minor_units(self):
        ingest(self.db, [self.invoice])
        row = list(csv.DictReader(io.StringIO(export_csv(self.db))))[0]
        self.assertEqual(row["difference_minor"], "30")
        self.assertEqual(row["currency"], "USD")

    def test_csv_neutralizes_formula_reference(self):
        ingest(self.db, [dict(self.invoice, reference="=unsafe")])
        row = list(csv.DictReader(io.StringIO(export_csv(self.db))))[0]
        self.assertEqual(row["reference"], "'=unsafe")

    def test_export_empty_ledger_has_headers(self):
        self.assertEqual(list(csv.DictReader(io.StringIO(export_csv(self.db)))), [])

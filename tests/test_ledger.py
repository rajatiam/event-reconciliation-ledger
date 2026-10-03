import tempfile, unittest
from pathlib import Path
from event_reconciliation_ledger.core import ingest, report, validate


class LedgerTests(unittest.TestCase):
    def test_tiny_fraction_is_not_silently_rounded(self):
        with self.assertRaises(ValueError):
            validate(dict(self.invoice, amount="0.30000000000000000000000000001"))

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "ledger.db"
        self.invoice = {
            "event_id": "invoice-a",
            "reference": "ref-a",
            "kind": "invoice",
            "currency": "USD",
            "amount": "0.30",
        }

    def tearDown(self):
        self.tmp.cleanup()

    def test_exact_split_settlement(self):
        ingest(
            self.db,
            [
                self.invoice,
                dict(self.invoice, event_id="s-a", kind="settlement", amount="0.10"),
                dict(self.invoice, event_id="s-b", kind="settlement", amount="0.20"),
            ],
        )
        self.assertEqual(report(self.db)["groups"][0]["status"], "matched")

    def test_idempotent_duplicate(self):
        ingest(self.db, [self.invoice])
        self.assertEqual(
            ingest(self.db, [dict(self.invoice, amount="0.300")])["duplicates"], 1
        )

    def test_conflict_rolls_back_entire_batch(self):
        ingest(self.db, [self.invoice])
        with self.assertRaises(ValueError):
            ingest(
                self.db,
                [
                    dict(self.invoice, event_id="new", reference="new"),
                    dict(self.invoice, amount="1.00"),
                ],
            )
        self.assertEqual(len(report(self.db)["groups"]), 1)

    def test_invalid_row_rolls_back(self):
        with self.assertRaises(ValueError):
            ingest(
                self.db,
                [self.invoice, dict(self.invoice, event_id="bad", amount="nan")],
            )
        self.assertEqual(report(self.db)["groups"], [])

    def test_currency_precision(self):
        with self.assertRaises(ValueError):
            validate(dict(self.invoice, amount="0.001"))
        with self.assertRaises(ValueError):
            validate(dict(self.invoice, currency="JPY", amount="1.1"))

    def test_currencies_do_not_mix(self):
        ingest(
            self.db, [self.invoice, dict(self.invoice, event_id="eur", currency="EUR")]
        )
        self.assertEqual(len(report(self.db)["groups"]), 2)

    def test_overpayment(self):
        ingest(
            self.db,
            [
                self.invoice,
                dict(
                    self.invoice, event_id="settled", kind="settlement", amount="0.50"
                ),
            ],
        )
        self.assertEqual(report(self.db)["groups"][0]["difference_minor"], -20)

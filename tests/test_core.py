import json
import tempfile
import unittest
from pathlib import Path

from receipt_organizer.core import ReceiptError, ReceiptStore, parse_amount


class ReceiptStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = ReceiptStore(Path(self.tmp.name) / "test.db")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_add_get_and_decimal_rounding(self):
        r = self.store.add("2026-09-21", "Corner Shop", "12.345", "usd", "Food", "Lunch")
        self.assertEqual(r.amount_cents, 1235)
        self.assertEqual(r.amount, "12.35")
        self.assertEqual(self.store.get(r.id).currency, "USD")

    def test_filters_and_literal_wildcards(self):
        self.store.add("2026-09-20", "100% Market", "10", "USD", "Food")
        self.store.add("2026-09-21", "Other", "20", "IQD", "Travel")
        self.assertEqual(len(self.store.list(search="100%")), 1)
        self.assertEqual(len(self.store.list(currency="iqd")), 1)
        self.assertEqual(len(self.store.list(since="2026-09-21")), 1)

    def test_summary_keeps_currencies_separate(self):
        self.store.add("2026-09-21", "A", "10.00", "USD", "Food")
        self.store.add("2026-09-21", "B", "2500", "IQD", "Food")
        result = self.store.summary()
        self.assertEqual(result["currencies"]["USD"]["total"], "10.00")
        self.assertEqual(result["currencies"]["IQD"]["total"], "2500.00")

    def test_export_json_and_csv(self):
        self.store.add("2026-09-21", "A, Shop", "5", "USD")
        rows = self.store.list()
        self.assertEqual(json.loads(self.store.export_json(rows))["schema"], 1)
        self.assertIn('"A, Shop"', self.store.export_csv(rows))

    def test_validation_and_delete(self):
        with self.assertRaises(ReceiptError):
            parse_amount("-1")
        with self.assertRaises(ReceiptError):
            self.store.add("21/09/2026", "A", "1")
        r = self.store.add("2026-09-21", "A", "1")
        self.store.delete(r.id)
        with self.assertRaises(ReceiptError):
            self.store.get(r.id)


if __name__ == "__main__":
    unittest.main()

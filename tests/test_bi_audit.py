"""Confiro que uma divergência ou consulta sem resultado interrompe a publicação."""

import unittest

from src.database.build_bi_model import check_audit_result


class BIAuditTests(unittest.TestCase):
    def test_zero_discrepancy_accepted(self):
        check_audit_result("conservacao", 0)

    def test_discrepancy_rejected(self):
        with self.assertRaises(ValueError):
            check_audit_result("conservacao", 1)

    def test_empty_result_rejected(self):
        with self.assertRaises(ValueError):
            check_audit_result("calendario", None)


if __name__ == "__main__":
    unittest.main()

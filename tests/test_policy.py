import unittest

from chatbot.policy import classify


class ClassifyTests(unittest.TestCase):
    def test_under_100k_general_is_exempt(self):
        result = classify(False, False, 80_000, 0)
        self.assertEqual(result["path"], "exempt")
        self.assertIn("第五条第四项", result["basis"][0])

    def test_boundary_99999_and_100000(self):
        self.assertEqual(classify(False, False, 99_999, 0)["path"], "exempt")
        self.assertEqual(
            classify(False, False, 100_000, 0)["path"],
            "standard_contract_or_certification",
        )

    def test_boundary_999999_and_1000000(self):
        self.assertEqual(
            classify(False, False, 999_999, 0)["path"],
            "standard_contract_or_certification",
        )
        self.assertEqual(classify(False, False, 1_000_000, 0)["path"], "security_assessment")

    def test_sensitive_boundaries(self):
        self.assertEqual(
            classify(False, False, 0, 1)["path"],
            "standard_contract_or_certification",
        )
        self.assertEqual(
            classify(False, False, 50_000, 9_999)["path"],
            "standard_contract_or_certification",
        )
        self.assertEqual(classify(False, False, 0, 10_000)["path"], "security_assessment")

    def test_sensitive_blocks_volume_exemption(self):
        result = classify(False, False, 80_000, 100)
        self.assertEqual(result["path"], "standard_contract_or_certification")

    def test_stricter_path_wins(self):
        result = classify(False, False, 200_000, 10_000)
        self.assertEqual(result["path"], "security_assessment")

    def test_ciio_cannot_use_small_volume_exemption(self):
        self.assertEqual(classify(True, False, 1, 0)["path"], "security_assessment")

    def test_important_data_requires_assessment(self):
        self.assertEqual(classify(False, True, 0, 0)["path"], "security_assessment")

    def test_hr_exemption_ignores_high_volume(self):
        result = classify(False, False, 2_000_000, 20_000, "hr")
        self.assertEqual(result["path"], "exempt")
        self.assertIn("第五条第二项", result["basis"][0])

    def test_hr_does_not_cover_important_data(self):
        self.assertEqual(classify(False, True, 10, 0, "hr")["path"], "security_assessment")

    def test_contract_and_emergency(self):
        self.assertEqual(classify(True, False, 1, 0, "contract")["path"], "exempt")
        self.assertEqual(classify(True, False, 1, 0, "emergency")["path"], "exempt")

    def test_ftz_outside_list(self):
        self.assertEqual(classify(False, True, 1_000_000, 0, "ftz_outside_list")["path"], "exempt")

    def test_trade_without_personal_data(self):
        result = classify(False, False, 0, 0, "trade")
        self.assertEqual(result["path"], "exempt")
        self.assertIn("第三条", result["basis"][0])

    def test_trade_rejected_when_personal_data_present(self):
        result = classify(False, False, 80_000, 0, "trade")
        self.assertEqual(result["path"], "exempt")
        self.assertIn("第五条第四项", result["basis"][0])
        self.assertTrue(any("不能适用第三条" in note for note in result["notes"]))

    def test_overseas_roundtrip_can_include_exported_personal_data(self):
        result = classify(False, False, 500_000, 0, "overseas_roundtrip")
        self.assertEqual(result["path"], "exempt")
        self.assertIn("第四条", result["basis"][0])

    def test_no_personal_or_important_data(self):
        self.assertEqual(classify(True, False, 0, 0)["path"], "exempt")

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            classify(False, False, -1, 0)
        with self.assertRaises(ValueError):
            classify(False, False, 0, 0, "unknown")


if __name__ == "__main__":
    unittest.main()

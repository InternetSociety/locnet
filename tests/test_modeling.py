import unittest

from app.services.modeling import require_positive_system_capex


class ModelingValidationTests(unittest.TestCase):
    def test_system_capex_must_be_positive(self):
        self.assertEqual(require_positive_system_capex(1), 1)
        with self.assertRaisesRegex(
            ValueError,
            "System CapEx must be greater than zero",
        ):
            require_positive_system_capex(0)


if __name__ == "__main__":
    unittest.main()

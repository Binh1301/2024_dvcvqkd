import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from audit_direct_support_boundaries import (  # noqa: E402
    GS_COORDINATES, LEARNING_RATES, MULTIPLIERS, PS_COORDINATES, SIGNS, THRESHOLD,
)


class DirectSupportBoundaryTests(unittest.TestCase):
    def test_preregistered_grid_constants(self):
        self.assertEqual(THRESHOLD, 1e-13)
        self.assertEqual(MULTIPLIERS, (1, 3, 10, 30, 100, 300, 1000))
        self.assertEqual(SIGNS, (-1, 1))
        self.assertEqual(PS_COORDINATES, (0, 17, 42))
        self.assertEqual(GS_COORDINATES, ((0, "real"), (17, "imag"), (42, "real")))
        self.assertEqual(LEARNING_RATES, {"ps": 3e-4, "gs": 1e-4, "va": 1e-4})

    def test_schema_is_diagnostic_only(self):
        schema = json.loads(
            (ROOT / "schemas" / "direct_support_boundary_sweep.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            schema["properties"]["status"]["const"],
            "PROPOSED_DIAGNOSTIC_ONLY_NOT_FROZEN",
        )


if __name__ == "__main__":
    unittest.main()

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from audit_boundary_bisection_crn import (  # noqa: E402
    BISECTION_MAX_ITERATIONS, BISECTION_WIDTH, CRN_SEED, GS_RHOS, N_MC,
    PS_RHOS, THRESHOLD, VA_RHOS,
)


class BoundaryBisectionCrnTests(unittest.TestCase):
    def test_preregistered_constants(self):
        self.assertEqual(THRESHOLD, 1e-13)
        self.assertEqual(BISECTION_MAX_ITERATIONS, 60)
        self.assertEqual(BISECTION_WIDTH, 1e-12)
        self.assertEqual(CRN_SEED, 202615)
        self.assertEqual(N_MC, 2048)
        self.assertEqual(VA_RHOS, (1e-4, 1e-5, 1e-6, 1e-7, 1e-8))
        self.assertEqual(PS_RHOS, (1e-4, 1e-6, 1e-7))
        self.assertEqual(GS_RHOS, (1e-4, 1e-6))

    def test_schema_is_proposed_only(self):
        schema = json.loads(
            (ROOT / "schemas" / "support_boundary_bisection_crn.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(schema["properties"]["status"]["const"],
                         "PROPOSED_DIAGNOSTIC_ONLY_NOT_FROZEN")


if __name__ == "__main__":
    unittest.main()

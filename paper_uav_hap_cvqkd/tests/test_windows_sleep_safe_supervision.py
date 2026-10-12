"""Small operational-only tests; no scientific/source computation."""
import unittest
from scripts.windows_sleep_safe_supervision import AwakeOnAC, safe_power, ES_CONTINUOUS, ES_SYSTEM_REQUIRED


class FakePower:
    def __init__(self, ac=1, critical=0):
        self.state, self.calls = ES_CONTINUOUS, []
        self.status = {"ac": ac, "battery_flag": critical}
    def read(self):
        return self.status
    def execution_state(self, flags):
        self.calls.append(flags)
        old, self.state = self.state, flags
        return old


class SleepSafetyTests(unittest.TestCase):
    def test_battery_or_unknown_fails_before_request(self):
        for ac in (0, 255):
            power = FakePower(ac=ac)
            with self.assertRaises(RuntimeError):
                with AwakeOnAC(power):
                    self.fail("Unsafe power admitted")
            self.assertEqual(power.calls, [])

    def test_critical_battery_fails_closed(self):
        self.assertFalse(safe_power(FakePower(critical=4).read()))
        self.assertFalse(safe_power(FakePower(critical=255).read()))

    def test_request_verified_and_released_on_exception(self):
        power = FakePower()
        lease = AwakeOnAC(power)
        with self.assertRaises(ValueError):
            with lease:
                self.assertTrue(lease.receipt["active_verified"])
                self.assertEqual(power.state, ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
                raise ValueError("Simulated job failure")
        self.assertTrue(lease.receipt["released_verified"])
        self.assertEqual(power.state, ES_CONTINUOUS)

    def test_existing_thread_request_is_restored(self):
        power = FakePower()
        power.state = ES_CONTINUOUS | 2
        with AwakeOnAC(power):
            pass
        self.assertEqual(power.state, ES_CONTINUOUS | 2)


if __name__ == "__main__":
    unittest.main()

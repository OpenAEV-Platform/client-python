import unittest

from pyoaev.signatures.ai_marker import build_marker


class TestBuildMarker(unittest.TestCase):
    def test_marker_has_expected_prefix_and_length(self):
        marker = build_marker("inject-1", "agent-1")

        self.assertTrue(marker.startswith("oaev"))
        # "oaev" prefix (4 chars) + 16 hex chars from the sha256 digest.
        self.assertEqual(len(marker), 20)
        self.assertTrue(all(c in "0123456789abcdef" for c in marker[4:]))

    def test_marker_is_deterministic_for_same_inputs(self):
        self.assertEqual(
            build_marker("inject-1", "agent-1"),
            build_marker("inject-1", "agent-1"),
        )

    def test_marker_differs_for_different_inputs(self):
        self.assertNotEqual(
            build_marker("inject-1", "agent-1"),
            build_marker("inject-2", "agent-1"),
        )
        self.assertNotEqual(
            build_marker("inject-1", "agent-1"),
            build_marker("inject-1", "agent-2"),
        )

    def test_agent_id_defaults_to_empty(self):
        self.assertEqual(build_marker("inject-1"), build_marker("inject-1", ""))

    def test_marker_value_is_stable_across_runs(self):
        # Lock the exact value so the injector and collectors (potentially in
        # other languages) stay byte-for-byte compatible.
        self.assertEqual(build_marker("inject-1", "agent-1"), "oaev6457d87cba0698ab")


if __name__ == "__main__":
    unittest.main()

import unittest

from pyoaev.contracts.contract_config import PrimitiveType


class PrimitiveTypeTest(unittest.TestCase):
    def test_username_wire_label(self):
        # The wire label is a public contract shared with the platform enum
        # (io.openaev.database.model.PrimitiveType.Username); it must stay
        # exactly "username".
        self.assertEqual(PrimitiveType.Username.value, "username")
        self.assertEqual(PrimitiveType.Username, "username")

    def test_host_wire_label(self):
        self.assertEqual(PrimitiveType.Host.value, "host")
        self.assertEqual(PrimitiveType.Host, "host")

    def test_text_wire_label(self):
        # The platform's own normalizer defaults a missing argumentType to
        # exactly this value — it must stay "text".
        self.assertEqual(PrimitiveType.Text.value, "text")
        self.assertEqual(PrimitiveType.Text, "text")

    def test_action_output_wire_label(self):
        # Shared with ContractOutputType.ActionOutput; both enums describe the
        # same platform-side value from two different angles (an output
        # producing it vs. an input typed to receive it) and must not drift
        # apart.
        self.assertEqual(PrimitiveType.ActionOutput.value, "action_output")

    def test_every_value_matches_the_openaev_platform_enum(self):
        # io.openaev.database.model.PrimitiveType, transcribed label-for-label.
        # Keep this set in sync with that file, not just the four spot-checked
        # above.
        expected_labels = {
            "account_with_password_not_required",
            "action_output",
            "admin_username",
            "asreproastable_account",
            "asset_group_id",
            "asset_id",
            "computer_name",
            "cve",
            "delegation_account",
            "document",
            "domain",
            "file_name",
            "file_path",
            "group_name",
            "hash",
            "host",
            "ipv4",
            "ipv6",
            "ip_subnet",
            "kerberoastable_account",
            "key",
            "number",
            "password",
            "permissions",
            "port",
            "service",
            "severity",
            "share_name",
            "sid",
            "targeted-asset",
            "text",
            "username",
            "value",
            "vulnerability_name",
            "vulnerability_status",
        }
        actual_labels = {member.value for member in PrimitiveType}
        self.assertEqual(actual_labels, expected_labels)


if __name__ == "__main__":
    unittest.main()

import unittest

from pyoaev.contracts.contract_config import ContractOutputType


class ContractOutputTypeTest(unittest.TestCase):
    def test_file_wire_label(self):
        # The wire label is a public contract shared with the platform enum and every
        # injector that declares a `file` output; it must stay exactly "file".
        self.assertEqual(ContractOutputType.File.value, "file")
        self.assertEqual(ContractOutputType.File, "file")

    def test_action_output_wire_label(self):
        # The wire label is a public contract shared with the platform enum
        # (io.openaev.database.model.ContractOutputType.ActionOutput); it must stay
        # exactly "action_output".
        self.assertEqual(ContractOutputType.ActionOutput.value, "action_output")
        self.assertEqual(ContractOutputType.ActionOutput, "action_output")


if __name__ == "__main__":
    unittest.main()

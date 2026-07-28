import unittest

from pyoaev.contracts.contract_config import ContractOutputType


class ContractOutputTypeTest(unittest.TestCase):
    def test_file_wire_label(self):
        # The wire label is a public contract shared with the platform enum and every
        # injector that declares a `file` output; it must stay exactly "file".
        self.assertEqual(ContractOutputType.File.value, "file")
        self.assertEqual(ContractOutputType.File, "file")


if __name__ == "__main__":
    unittest.main()

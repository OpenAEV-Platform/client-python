import unittest

from pyoaev.signatures.signature_type import SignatureType
from pyoaev.signatures.types import MatchTypes, SignatureTypes


class TestAiSignatureTypes(unittest.TestCase):
    def test_ai_signature_type_values(self):
        self.assertEqual(
            SignatureTypes.SIG_TYPE_AI_REQUEST_MARKER.value, "ai_request_marker"
        )
        self.assertEqual(
            SignatureTypes.SIG_TYPE_AI_TARGET_ENDPOINT.value, "ai_target_endpoint"
        )

    def test_ai_request_marker_usable_in_signature_type(self):
        signature_type = SignatureType(
            label=SignatureTypes.SIG_TYPE_AI_REQUEST_MARKER,
            match_type=MatchTypes.MATCH_TYPE_SIMPLE,
        )

        struct = signature_type.make_struct_for_matching(data="oaevdeadbeef")

        self.assertEqual(struct.get("type"), MatchTypes.MATCH_TYPE_SIMPLE.value)
        self.assertEqual(struct.get("data"), "oaevdeadbeef")


if __name__ == "__main__":
    unittest.main()

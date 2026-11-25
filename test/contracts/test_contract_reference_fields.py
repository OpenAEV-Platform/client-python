import json
import unittest

from pyoaev import utils
from pyoaev.contracts.contract_config import (
    Contract,
    ContractAssetGroup,
    ContractAssetGroupReference,
    ContractConfig,
    ContractFieldKey,
    ContractFieldType,
    ContractTags,
    SupportedLanguage,
    prepare_contracts,
)
from pyoaev.contracts.contract_utils import ContractCardinality


def _serialize(field):
    return json.loads(json.dumps(field, cls=utils.EnhancedJSONEncoder))


def _contract(fields):
    return Contract(
        contract_id="00000000-0000-0000-0000-000000000389",
        label={
            SupportedLanguage.en: "Reference fields",
            SupportedLanguage.fr: "Champs",
        },
        fields=fields,
        outputs=[],
        config=ContractConfig(
            type="test",
            expose=True,
            label={SupportedLanguage.en: "Test", SupportedLanguage.fr: "Test"},
            color_dark="#000000",
            color_light="#ffffff",
        ),
        manual=False,
    )


class ContractReferenceFieldTypesTest(unittest.TestCase):
    def test_field_type_labels_match_the_platform_enum(self):
        self.assertEqual(
            ContractFieldType.AssetGroupReference.value, "asset-group-reference"
        )
        self.assertEqual(ContractFieldType.Tags.value, "tags")


class ContractAssetGroupReferenceTest(unittest.TestCase):
    def test_serializes_with_its_key_type_and_cardinality(self):
        field = ContractAssetGroupReference(
            key="asset_group_id",
            label="Asset group to add the created endpoints to",
            cardinality=ContractCardinality.One,
        )
        serialized = _serialize(field)

        self.assertEqual(serialized["key"], "asset_group_id")
        self.assertEqual(serialized["type"], "asset-group-reference")
        self.assertEqual(serialized["cardinality"], "1")

    def test_multiple_cardinality_is_kept(self):
        field = ContractAssetGroupReference(
            key="groups", label="Groups", cardinality=ContractCardinality.Multiple
        )

        self.assertEqual(_serialize(field)["cardinality"], "n")

    def test_prepare_contracts_carries_the_field(self):
        field = ContractAssetGroupReference(
            key="asset_group_id",
            label="Asset group",
            cardinality=ContractCardinality.One,
        )
        content = json.loads(
            prepare_contracts([_contract([field])])[0]["contract_content"]
        )

        self.assertEqual(content["fields"][0]["key"], "asset_group_id")
        self.assertEqual(content["fields"][0]["type"], "asset-group-reference")
        self.assertEqual(content["fields"][0]["cardinality"], "1")


class ContractTagsTest(unittest.TestCase):
    def test_serializes_as_tags_with_multiple_cardinality(self):
        field = ContractTags(key="endpoint_tags", label="Tags")
        serialized = _serialize(field)

        self.assertEqual(serialized["key"], "endpoint_tags")
        self.assertEqual(serialized["type"], "tags")
        self.assertEqual(serialized["cardinality"], "n")

    def test_cardinality_is_forced_to_multiple(self):
        field = ContractTags(
            key="endpoint_tags", label="Tags", cardinality=ContractCardinality.One
        )

        self.assertEqual(field.cardinality, ContractCardinality.Multiple)
        self.assertEqual(_serialize(field)["cardinality"], "n")

    def test_prepare_contracts_carries_both_fields(self):
        content = json.loads(
            prepare_contracts(
                [
                    _contract(
                        [
                            ContractAssetGroupReference(
                                key="asset_group_id", label="Asset group"
                            ),
                            ContractTags(key="endpoint_tags", label="Tags"),
                        ]
                    )
                ]
            )[0]["contract_content"]
        )

        self.assertEqual(
            [(f["key"], f["type"], f["cardinality"]) for f in content["fields"]],
            [
                ("asset_group_id", "asset-group-reference", "1"),
                ("endpoint_tags", "tags", "n"),
            ],
        )


class ContractAssetGroupUnchangedTest(unittest.TestCase):
    def test_targeting_field_keeps_its_fixed_key_and_type(self):
        field = ContractAssetGroup(label="Target asset groups")
        serialized = _serialize(field)

        self.assertEqual(field.key, ContractFieldKey.AssetGroup.value)
        self.assertEqual(serialized["key"], "asset_groups")
        self.assertEqual(serialized["type"], "asset-group")


if __name__ == "__main__":
    unittest.main()

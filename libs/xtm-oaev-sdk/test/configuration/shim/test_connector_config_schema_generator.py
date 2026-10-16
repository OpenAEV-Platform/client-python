import unittest
from unittest.mock import MagicMock

from pyoaev.configuration.connector_config_schema_generator import (
    ConnectorConfigSchemaGenerator,
)


class TestConnectorConfigSchemaGenerator(unittest.TestCase):
    def test_dereference_schema_resolves_internal_refs(self):
        schema = {
            "$defs": {
                "Item": {
                    "type": "object",
                    "properties": {"value": {"type": "string"}},
                }
            },
            "type": "object",
            "properties": {
                "item": {"$ref": "#/$defs/Item"},
                "items": {"type": "array", "items": [{"$ref": "#/$defs/Item"}]},
            },
        }

        resolved = ConnectorConfigSchemaGenerator.dereference_schema(schema)

        self.assertEqual(resolved["properties"]["item"]["type"], "object")
        self.assertIn("value", resolved["properties"]["item"]["properties"])
        self.assertEqual(
            resolved["properties"]["items"]["items"][0]["properties"]["value"]["type"],
            "string",
        )

    def test_dereference_schema_rejects_unsupported_refs(self):
        with self.assertRaises(ValueError):
            ConnectorConfigSchemaGenerator.dereference_schema(
                {"$ref": "external://schema"}
            )

    def test_flatten_config_loader_schema_and_filter_schema(self):
        root_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "config.schema.json",
            "additionalProperties": False,
            "properties": {
                "connector": {
                    "properties": {
                        "name": {"type": "string", "title": "Name"},
                        "id": {"type": "string"},
                    },
                    "required": ["name"],
                }
            },
        }

        flattened = ConnectorConfigSchemaGenerator.flatten_config_loader_schema(
            root_schema
        )
        flattened["properties"]["CONNECTOR_ID"] = {"type": "string"}
        flattened["required"].append("CONNECTOR_ID")

        filtered = ConnectorConfigSchemaGenerator.filter_schema(flattened)

        self.assertEqual(filtered["additionalProperties"], False)
        self.assertIn("CONNECTOR_NAME", filtered["properties"])
        self.assertNotIn("title", filtered["properties"]["CONNECTOR_NAME"])
        self.assertIn("CONNECTOR_NAME", filtered["required"])
        self.assertNotIn("CONNECTOR_ID", filtered["properties"])
        self.assertNotIn("CONNECTOR_ID", filtered["required"])

    def test_flatten_config_loader_schema_defaults_additional_properties_to_true(self):
        root_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "config.schema.json",
            "properties": {"app": {"properties": {}, "required": []}},
        }

        flattened = ConnectorConfigSchemaGenerator.flatten_config_loader_schema(
            root_schema
        )

        self.assertTrue(flattened["additionalProperties"])

    def test_nullable_schema_returns_null_when_inner_schema_is_null(self):
        generator = ConnectorConfigSchemaGenerator(by_alias=True)
        generator.generate_inner = MagicMock(return_value={"type": "null"})

        result = generator.nullable_schema(
            {"type": "nullable", "schema": {"type": "str"}}
        )

        self.assertEqual(result, {"type": "null"})

    def test_nullable_schema_returns_inner_schema_when_not_null(self):
        generator = ConnectorConfigSchemaGenerator(by_alias=True)
        generator.generate_inner = MagicMock(return_value={"type": "string"})

        result = generator.nullable_schema(
            {"type": "nullable", "schema": {"type": "str"}}
        )

        self.assertEqual(result, {"type": "string"})


if __name__ == "__main__":
    unittest.main()

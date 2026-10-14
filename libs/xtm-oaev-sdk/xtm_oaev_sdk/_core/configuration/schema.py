"""Connector manifest schema: flat, dereferenced, filtered JSON schema.

Adapted from the OpenCTI connectors configuration schema generator:
https://github.com/OpenCTI-Platform/connectors/blob/5c8cf1235f62f5651c9c08d0b67f1bd182662c8a/shared/tools/composer/generate_connectors_config_schemas/generate_connector_config_json_schema.py.sample
"""

from copy import deepcopy
from typing import Any

__all__ = ["ConnectorSchemaTransformer"]

# attributes filtered from the connector configuration before generating the manifest
_FILTERED_ATTRIBUTES = [
    # connector id is generated
    "CONNECTOR_ID",
]


class ConnectorSchemaTransformer:
    """Implements ``ConnectorSchemaPort``."""

    def dereference_schema(self, schema_with_refs: dict[str, Any]) -> dict[str, Any]:
        def _resolve(schema: Any, root: dict[str, Any]) -> Any:
            if isinstance(schema, dict):
                if "$ref" in schema:
                    ref_path = schema["$ref"]
                    if ref_path.startswith("#/$defs/"):
                        def_name = ref_path.split("/")[-1]
                        # Deep copy to avoid mutating $defs
                        resolved = deepcopy(root["$defs"][def_name])
                        return _resolve(resolved, root)
                    else:
                        raise ValueError(f"Unsupported ref format: {ref_path}")
                else:
                    return {
                        schema_key: _resolve(schema_value, root)
                        for schema_key, schema_value in schema.items()
                    }
            elif isinstance(schema, list):
                return [_resolve(item, root) for item in schema]
            else:
                return schema

        return _resolve(deepcopy(schema_with_refs), schema_with_refs)

    def flatten_config_loader_schema(
        self, root_schema: dict[str, Any]
    ) -> dict[str, Any]:
        flat_json_schema: dict[str, Any] = {
            "$schema": root_schema["$schema"],
            "$id": root_schema["$id"],
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": root_schema.get("additionalProperties", True),
        }

        for (
            config_loader_namespace_name,
            config_loader_namespace_schema,
        ) in root_schema["properties"].items():
            config_schema = config_loader_namespace_schema.get("properties", {})
            required_config_vars = config_loader_namespace_schema.get("required", [])

            for config_var_name, config_var_schema in config_schema.items():
                property_name = (
                    f"{config_loader_namespace_name.upper()}_{config_var_name.upper()}"
                )

                config_var_schema.pop("title", None)

                flat_json_schema["properties"][property_name] = config_var_schema

                if config_var_name in required_config_vars:
                    flat_json_schema["required"].append(property_name)

        return flat_json_schema

    def filter_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        for filtered_attribute in _FILTERED_ATTRIBUTES:
            if filtered_attribute in schema["properties"]:
                del schema["properties"][filtered_attribute]
                schema.update(
                    {
                        "required": [
                            item
                            for item in schema["required"]
                            if item != filtered_attribute
                        ]
                    }
                )

        return schema

    def finalize(self, json_schema: dict[str, Any], dialect: str) -> dict[str, Any]:
        json_schema["$schema"] = dialect
        json_schema["$id"] = "config.schema.json"
        dereferenced_schema = self.dereference_schema(json_schema)
        flattened_schema = self.flatten_config_loader_schema(dereferenced_schema)
        return self.filter_schema(flattened_schema)

    def collapse_nullable(self, inner_json_schema: dict[str, Any]) -> dict[str, Any]:
        null_schema = {"type": "null"}

        if inner_json_schema == null_schema:
            return null_schema
        else:
            return inner_json_schema

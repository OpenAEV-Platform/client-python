"""Connector configuration JSON schema generator.

Provides a custom Pydantic JSON schema generator that produces flattened,
dereferenced schemas suitable for connector configuration manifests.

Adapted from the OpenCTI connectors configuration schema generator.
"""

from copy import deepcopy
from typing import Any, override

from pydantic.json_schema import GenerateJsonSchema

__all__ = ["ConnectorConfigSchemaGenerator"]

_FILTERED_ATTRIBUTES = [
    "CONNECTOR_ID",
]


class ConnectorConfigSchemaGenerator(GenerateJsonSchema):
    """Custom JSON schema generator for connector configurations.

    Produces a flat schema where all config variables are at root level,
    with ``$ref`` entries fully resolved and filtered attributes removed.

    This is used by ``Configuration.schema()`` to produce manifests
    compatible with the OpenAEV platform connector registration API.
    """

    @staticmethod
    def dereference_schema(schema_with_refs: dict[str, Any]) -> dict[str, Any]:
        """Resolve all internal ``$ref`` entries in a JSON schema.

        Args:
            schema_with_refs: A JSON schema dict potentially containing
                ``$ref`` pointers to ``$defs``.

        Returns:
            A new schema with all references inlined.

        Raises:
            ValueError: If a ``$ref`` uses an unsupported format.
        """

        def _resolve(schema: Any, root: dict[str, Any]) -> Any:
            if isinstance(schema, dict):
                if "$ref" in schema:
                    ref_path = schema["$ref"]
                    if ref_path.startswith("#/$defs/"):
                        def_name = ref_path.split("/")[-1]
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

    @staticmethod
    def flatten_config_loader_schema(root_schema: dict[str, Any]) -> dict[str, Any]:
        """Flatten a hierarchical config schema to root-level properties.

        Transforms nested namespace properties into flat
        ``NAMESPACE_VARIABLE`` format suitable for environment variable
        mapping.

        Args:
            root_schema: The dereferenced schema to flatten.

        Returns:
            A flat schema with all properties at root level.
        """
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

    @staticmethod
    def filter_schema(schema: dict[str, Any]) -> dict[str, Any]:
        """Remove filtered attributes from the schema.

        Args:
            schema: The flat schema to filter.

        Returns:
            The schema with filtered attributes removed.
        """
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

    @override
    def generate(self, schema: Any, mode: str = "validation") -> dict[str, Any]:
        """Generate a flat, dereferenced, filtered JSON schema.

        Args:
            schema: The Pydantic core schema to process.
            mode: Schema generation mode.

        Returns:
            The final connector configuration schema.
        """
        json_schema = super().generate(schema, mode=mode)

        json_schema["$schema"] = self.schema_dialect
        json_schema["$id"] = "config.schema.json"
        dereferenced_schema = self.dereference_schema(json_schema)
        flattened_schema = self.flatten_config_loader_schema(dereferenced_schema)
        return self.filter_schema(flattened_schema)

    @override
    def nullable_schema(self, schema: Any) -> dict[str, Any]:
        """Generate schema for nullable fields without ``anyOf``.

        Overrides the default behavior to produce cleaner schemas
        that don't use the ``anyOf`` keyword for optional fields.

        Args:
            schema: The core schema for the nullable type.

        Returns:
            The generated JSON schema for the nullable type.
        """
        null_schema = {"type": "null"}
        inner_json_schema = self.generate_inner(schema["schema"])

        if inner_json_schema == null_schema:
            return null_schema
        else:
            return inner_json_schema

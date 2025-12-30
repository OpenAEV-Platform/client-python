## ADAPTED FROM https://github.com/OpenCTI-Platform/connectors/blob/5c8cf1235f62f5651c9c08d0b67f1bd182662c8a/shared/tools/composer/generate_connectors_config_schemas/generate_connector_config_json_schema.py.sample

from copy import deepcopy
from typing import override

from pydantic.json_schema import GenerateJsonSchema

# attributes filtered from the connector configuration before generating the manifest
__FILTERED_ATTRIBUTES__ = [
    # connector id is generated
    "CONNECTOR_ID",
]


class ConnectorConfigSchemaGenerator(GenerateJsonSchema):
    @staticmethod
    def dereference_schema(schema_with_refs):
        """Return a new schema with all internal $ref resolved."""

        def _resolve(schema, root):
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

    @staticmethod
    def flatten_config_loader_schema(root_schema: dict):
        """
        Flatten config loader schema so all config vars are described at root level.

        :param root_schema: Original schema.
        :return: Flatten schema.
        """
        flat_json_schema = {
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
    def filter_schema(schema):
        for filtered_attribute in __FILTERED_ATTRIBUTES__:
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
    def generate(self, schema, mode="validation"):
        json_schema = super().generate(schema, mode=mode)

        json_schema["$schema"] = self.schema_dialect
        json_schema["$id"] = f"config.schema.json"
        dereferenced_schema = self.dereference_schema(json_schema)
        flattened_schema = self.flatten_config_loader_schema(dereferenced_schema)
        return self.filter_schema(flattened_schema)

    @override
    def nullable_schema(self, schema):
        """Generates a JSON schema that matches a schema that allows null values.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.

        Notes:
            This method overrides `GenerateJsonSchema.nullable_schema` to generate schemas without `anyOf` keyword.
        """
        null_schema = {"type": "null"}
        inner_json_schema = self.generate_inner(schema["schema"])

        if inner_json_schema == null_schema:
            return null_schema
        else:
            return inner_json_schema

"""Tests for the contracts public surface exposed by xtm_second_oaev_sdk."""

import json

import pytest
import xtm_second_oaev_sdk as sdk


def _given_public_symbol(name: str):
    return getattr(sdk, name, None)


def _then_public_symbol_exists(symbol, name: str) -> None:
    assert symbol is not None, f"Expected xtm_second_oaev_sdk.{name} to exist on public surface"


def _given_existing_public_symbol(name: str):
    symbol = _given_public_symbol(name)
    _then_public_symbol_exists(symbol, name)
    return symbol


def _given_contract_text(key: str = "text_key", label: str = "Text label"):
    contract_text = _given_existing_public_symbol("ContractText")
    return contract_text(key=key, label=label)


def _given_contract_checkbox(key: str = "checkbox_key", label: str = "Checkbox label"):
    contract_checkbox = _given_existing_public_symbol("ContractCheckbox")
    return contract_checkbox(key=key, label=label)


def _given_contract_tuple(key: str = "tuple_key", label: str = "Tuple label"):
    contract_tuple = _given_existing_public_symbol("ContractTuple")
    return contract_tuple(key=key, label=label)


def _given_contract_select(key: str = "select_key", label: str = "Select label"):
    contract_select = _given_existing_public_symbol("ContractSelect")
    return contract_select(key=key, label=label)


def _given_contract_attachment(key: str = "attachment_key", label: str = "Attachment label"):
    contract_attachment = _given_existing_public_symbol("ContractAttachment")
    return contract_attachment(key=key, label=label)


def _given_contract_textarea(key: str = "textarea_key", label: str = "Textarea label"):
    contract_textarea = _given_existing_public_symbol("ContractTextArea")
    return contract_textarea(key=key, label=label)


def _given_contract_team(key: str = "team_key", label: str = "Team label"):
    contract_team = _given_existing_public_symbol("ContractTeam")
    return contract_team(key=key, label=label)


def _given_contract_expectations(key: str = "expectations_key", label: str = "Expectations label"):
    contract_expectations = _given_existing_public_symbol("ContractExpectations")
    return contract_expectations(key=key, label=label)


def _given_contract_payload(key: str = "payload_key", label: str = "Payload label"):
    contract_payload = _given_existing_public_symbol("ContractPayload")
    return contract_payload(key=key, label=label)


def _given_contract_asset(label: str = "Asset label"):
    contract_asset = _given_existing_public_symbol("ContractAsset")
    return contract_asset(label=label)


def _given_contract_asset_group(label: str = "Asset Group label"):
    contract_asset_group = _given_existing_public_symbol("ContractAssetGroup")
    return contract_asset_group(label=label)


def _given_contract_output_element():
    output_element = _given_existing_public_symbol("ContractOutputElement")
    contract_output_type = _given_existing_public_symbol("ContractOutputType")
    return output_element(
        type=contract_output_type.Text.value,
        field="output_field",
        labels=["Output field"],
        isFindingCompatible=True,
        isMultiple=False,
    )


def _given_contract_config():
    contract_config = _given_existing_public_symbol("ContractConfig")
    supported_language = _given_existing_public_symbol("SupportedLanguage")
    return contract_config(
        type="injector",
        expose=True,
        label={supported_language.en: "Injector", supported_language.fr: "Injecteur"},
        color_dark="#111111",
        color_light="#eeeeee",
    )


def _given_contract_instance():
    contract = _given_existing_public_symbol("Contract")
    supported_language = _given_existing_public_symbol("SupportedLanguage")
    return contract(
        contract_id="contract-1",
        label={supported_language.en: "Contract", supported_language.fr: "Contrat"},
        fields=[_given_contract_text()],
        outputs=[_given_contract_output_element()],
        config=_given_contract_config(),
        manual=False,
    )


def _given_contract_builder_instance():
    contract_builder = _given_existing_public_symbol("ContractBuilder")
    return contract_builder()


def _when_building_fluent_contract_builder_sequence(builder):
    first = builder.mandatory(_given_contract_text("f1", "F1"))
    second = builder.optional(_given_contract_checkbox("f2", "F2"))
    third = builder.mandatory_group([_given_contract_text("f3", "F3"), _given_contract_text("f4", "F4")])
    fourth = builder.add_fields([_given_contract_select("f5", "F5")])
    fifth = builder.add_outputs([_given_contract_output_element()])
    built_fields = builder.build_fields()
    built_outputs = builder.build_outputs()
    return first, second, third, fourth, fifth, built_fields, built_outputs


def _then_builder_fluent_sequence_is_chainable(builder, call_results) -> None:
    for result in call_results[:5]:
        assert result is builder


def _then_builder_accumulates_expected_fields_and_outputs(built_fields, built_outputs) -> None:
    assert [field.key for field in built_fields] == ["f1", "f2", "f3", "f4", "f5"]
    assert len(built_outputs) == 1


def _when_checking_builder_protocol(builder):
    contract_builder_protocol = _given_existing_public_symbol("ContractBuilderProtocol")
    return isinstance(builder, contract_builder_protocol)


def _then_value_is_true(value: bool) -> None:
    assert value is True


def _when_reading_element_type(element):
    return element.type


def _then_element_type_equals(actual: str, expected: str) -> None:
    assert actual == expected


def _when_reading_tuple_cardinality(contract_tuple):
    return contract_tuple.cardinality


def _then_cardinality_is_multiple(cardinality) -> None:
    contract_cardinality = _given_existing_public_symbol("ContractCardinality")
    assert cardinality == contract_cardinality.Multiple


def _when_reading_key(element):
    return element.key


def _then_key_equals(actual: str, expected: str) -> None:
    assert actual == expected


def _when_serializing_contract_add_input(contract_instance):
    return contract_instance.to_contract_add_input("injector-123")


def _when_serializing_contract_update_input(contract_instance):
    return contract_instance.to_contract_update_input()


def _then_add_input_contains_injector_and_contract_content(serialized: dict) -> None:
    assert serialized["injector_id"] == "injector-123"
    assert "contract_content" in serialized
    assert isinstance(serialized["contract_content"], str)
    assert json.loads(serialized["contract_content"])["contract_id"] == "contract-1"


def _then_update_input_omits_injector_id(serialized: dict) -> None:
    assert "injector_id" not in serialized
    assert "contract_content" in serialized


def _when_adding_attack_pattern(contract_instance):
    contract_instance.add_attack_pattern("T1234")
    return contract_instance.contract_attack_patterns_external_ids


def _then_list_contains_single_value(values: list[str], expected: str) -> None:
    assert values == [expected]


def _when_adding_vulnerability(contract_instance):
    contract_instance.add_vulnerability("CVE-2024-0001")
    return contract_instance.contract_vulnerability_external_ids


def _when_adding_variable(contract_instance):
    contract_variable = _given_existing_public_symbol("ContractVariable")
    variable_type = _given_existing_public_symbol("VariableType")
    contract_cardinality = _given_existing_public_symbol("ContractCardinality")
    new_variable = contract_variable(
        key="custom",
        label="Custom variable",
        type=variable_type.String,
        cardinality=contract_cardinality.One,
    )
    contract_instance.add_variable(new_variable)
    return contract_instance.variables


def _then_variables_include_custom_key(variables) -> None:
    assert any(variable.key == "custom" for variable in variables)


def _when_reading_default_contract_variables(contract_instance):
    return contract_instance.variables


def _then_default_variables_include_expected_keys(variables) -> None:
    keys = [variable.key for variable in variables]
    assert len(keys) == 7
    assert "user" in keys
    assert "exercise" in keys
    assert "teams" in keys
    assert "player_uri" in keys
    assert "challenges_uri" in keys
    assert "scoreboard_uri" in keys
    assert "lessons_uri" in keys


def _when_building_user_variable():
    variable_helper = _given_existing_public_symbol("VariableHelper")
    return variable_helper.user_variable()


def _when_building_exercise_variable():
    variable_helper = _given_existing_public_symbol("VariableHelper")
    return variable_helper.exercise_variable()


def _when_building_team_variable():
    variable_helper = _given_existing_public_symbol("VariableHelper")
    return variable_helper.team_variable()


def _when_building_uri_variables():
    variable_helper = _given_existing_public_symbol("VariableHelper")
    return variable_helper.uri_variables()


def _then_variable_has_children_count(variable, expected: int) -> None:
    assert len(variable.children) == expected


def _then_variable_cardinality_is_multiple(variable) -> None:
    contract_cardinality = _given_existing_public_symbol("ContractCardinality")
    assert variable.cardinality == contract_cardinality.Multiple


def _then_uri_variables_have_expected_length(uri_variables) -> None:
    assert len(uri_variables) == 4


def _when_preparing_contracts(contracts):
    prepare_contracts = _given_existing_public_symbol("prepare_contracts")
    return prepare_contracts(contracts)


def _then_prepared_contracts_have_expected_shape(serialized_contracts) -> None:
    assert len(serialized_contracts) == 1
    assert serialized_contracts[0]["contract_id"] == "contract-1"
    assert "contract_content" in serialized_contracts[0]
    assert isinstance(serialized_contracts[0]["contract_content"], str)


def _when_reading_enum_values():
    contract_cardinality = _given_existing_public_symbol("ContractCardinality")
    variable_type = _given_existing_public_symbol("VariableType")
    return contract_cardinality, variable_type


def _then_enum_values_match(contract_cardinality, variable_type) -> None:
    assert contract_cardinality.One.value == "1"
    assert contract_cardinality.Multiple.value == "n"
    assert variable_type.String.value == "String"
    assert variable_type.Object.value == "Object"


def _when_reading_contract_expectation_members():
    contract_expectation_type = _given_existing_public_symbol("ContractExpectationType")
    return list(contract_expectation_type)


def _when_reading_supported_language_members():
    supported_language = _given_existing_public_symbol("SupportedLanguage")
    return list(supported_language)


def _then_collection_has_length(collection, expected: int) -> None:
    assert len(collection) == expected


def _when_building_mandatory_group(builder):
    first = _given_contract_text("group_1", "Group 1")
    second = _given_contract_text("group_2", "Group 2")
    builder.mandatory_group([first, second])
    return first, second


def _then_elements_have_shared_mandatory_groups(elements) -> None:
    keys = [element.key for element in elements]
    for element in elements:
        assert element.mandatory is True
        assert element.mandatoryGroups == keys


@pytest.mark.parametrize(
    ("factory_name", "expected_type"),
    [
        ("_given_contract_text", "text"),
        ("_given_contract_checkbox", "checkbox"),
        ("_given_contract_tuple", "tuple"),
        ("_given_contract_asset", "asset"),
        ("_given_contract_asset_group", "asset-group"),
        ("_given_contract_attachment", "attachment"),
        ("_given_contract_select", "select"),
        ("_given_contract_textarea", "textarea"),
        ("_given_contract_team", "team"),
        ("_given_contract_expectations", "expectation"),
        ("_given_contract_payload", "payload"),
    ],
)
def test_contract_element_subclasses_set_type_from_get_type(factory_name: str, expected_type: str) -> None:
    """Verifies each ContractElement subclass sets its type via __post_init__."""
    element = globals()[factory_name]()
    actual_type = _when_reading_element_type(element)
    _then_element_type_equals(actual_type, expected_type)


@pytest.mark.parametrize(
    "symbol_name",
    [
        "ContractBuilder",
        "ContractBuilderProtocol",
        "ContractCardinality",
        "ContractVariable",
        "VariableType",
        "VariableHelper",
        "Contract",
        "ContractConfig",
        "ContractElement",
        "ContractText",
        "ContractCheckbox",
        "ContractTuple",
        "ContractAsset",
        "ContractAssetGroup",
        "ContractExpectationType",
        "ContractExpectations",
        "ContractPayload",
        "ContractSelect",
        "ContractAttachment",
        "ContractTextArea",
        "ContractTeam",
        "Expectation",
        "Domain",
        "LinkedFieldModel",
        "SupportedLanguage",
        "prepare_contracts",
        "ContractOutputElement",
        "ContractOutputType",
        "ContractFieldType",
        "ContractFieldKey",
        "ContractCardinalityElement",
    ],
)
def test_contract_public_surface_exposes_expected_symbols(symbol_name: str) -> None:
    """Verifies the xtm_second_oaev_sdk public surface exposes required contract symbols."""
    symbol = _given_public_symbol(symbol_name)
    _then_public_symbol_exists(symbol, symbol_name)


def test_contract_builder_fluent_api_is_chainable_and_accumulates_fields() -> None:
    """Verifies ContractBuilder fluent methods return self and collect fields/outputs."""
    builder = _given_contract_builder_instance()
    call_results = _when_building_fluent_contract_builder_sequence(builder)
    _then_builder_fluent_sequence_is_chainable(builder, call_results)
    _then_builder_accumulates_expected_fields_and_outputs(call_results[5], call_results[6])


def test_contract_builder_satisfies_protocol() -> None:
    """Verifies ContractBuilder satisfies ContractBuilderProtocol runtime checks."""
    builder = _given_contract_builder_instance()
    result = _when_checking_builder_protocol(builder)
    _then_value_is_true(result)


def test_contract_tuple_forces_multiple_cardinality() -> None:
    """Verifies ContractTuple forces cardinality to ContractCardinality.Multiple."""
    contract_tuple = _given_contract_tuple()
    cardinality = _when_reading_tuple_cardinality(contract_tuple)
    _then_cardinality_is_multiple(cardinality)


def test_contract_asset_key_is_auto_set_to_assets() -> None:
    """Verifies ContractAsset key is automatically set to assets."""
    contract_asset = _given_contract_asset()
    key = _when_reading_key(contract_asset)
    _then_key_equals(key, "assets")


def test_contract_asset_group_key_is_auto_set_to_asset_groups() -> None:
    """Verifies ContractAssetGroup key is automatically set to asset_groups."""
    contract_asset_group = _given_contract_asset_group()
    key = _when_reading_key(contract_asset_group)
    _then_key_equals(key, "asset_groups")


def test_contract_to_contract_add_input_includes_injector_id_and_content() -> None:
    """Verifies contract add payload includes injector_id and serialized content."""
    contract_instance = _given_contract_instance()
    serialized = _when_serializing_contract_add_input(contract_instance)
    _then_add_input_contains_injector_and_contract_content(serialized)


def test_contract_to_contract_update_input_omits_injector_id() -> None:
    """Verifies contract update payload omits injector_id."""
    contract_instance = _given_contract_instance()
    serialized = _when_serializing_contract_update_input(contract_instance)
    _then_update_input_omits_injector_id(serialized)


def test_contract_add_attack_pattern_appends_value() -> None:
    """Verifies add_attack_pattern appends values to the attack pattern list."""
    contract_instance = _given_contract_instance()
    values = _when_adding_attack_pattern(contract_instance)
    _then_list_contains_single_value(values, "T1234")


def test_contract_add_vulnerability_appends_value() -> None:
    """Verifies add_vulnerability appends values to the vulnerability list."""
    contract_instance = _given_contract_instance()
    values = _when_adding_vulnerability(contract_instance)
    _then_list_contains_single_value(values, "CVE-2024-0001")


def test_contract_add_variable_appends_to_variables_list() -> None:
    """Verifies add_variable appends a custom variable to contract variables."""
    contract_instance = _given_contract_instance()
    variables = _when_adding_variable(contract_instance)
    _then_variables_include_custom_key(variables)


def test_contract_default_variables_include_expected_core_and_uri_variables() -> None:
    """Verifies default contract variables include user, exercise, teams, and 4 URIs."""
    contract_instance = _given_contract_instance()
    variables = _when_reading_default_contract_variables(contract_instance)
    _then_default_variables_include_expected_keys(variables)


def test_variable_helper_user_variable_contains_five_children() -> None:
    """Verifies VariableHelper.user_variable returns a variable with five children."""
    user_variable = _when_building_user_variable()
    _then_variable_has_children_count(user_variable, 5)


def test_variable_helper_exercise_variable_contains_three_children() -> None:
    """Verifies VariableHelper.exercise_variable returns a variable with three children."""
    exercise_variable = _when_building_exercise_variable()
    _then_variable_has_children_count(exercise_variable, 3)


def test_variable_helper_team_variable_has_multiple_cardinality() -> None:
    """Verifies VariableHelper.team_variable returns a variable with multiple cardinality."""
    team_variable = _when_building_team_variable()
    _then_variable_cardinality_is_multiple(team_variable)


def test_variable_helper_uri_variables_returns_four_items() -> None:
    """Verifies VariableHelper.uri_variables returns four URI contract variables."""
    uri_variables = _when_building_uri_variables()
    _then_uri_variables_have_expected_length(uri_variables)


def test_prepare_contracts_serializes_contracts_to_dict_list() -> None:
    """Verifies prepare_contracts serializes Contract instances to dict payloads."""
    serialized_contracts = _when_preparing_contracts([_given_contract_instance()])
    _then_prepared_contracts_have_expected_shape(serialized_contracts)


def test_contract_enums_expose_expected_values() -> None:
    """Verifies ContractCardinality and VariableType expose expected values."""
    contract_cardinality, variable_type = _when_reading_enum_values()
    _then_enum_values_match(contract_cardinality, variable_type)


def test_contract_expectation_type_exposes_eight_members() -> None:
    """Verifies ContractExpectationType contains exactly eight members."""
    members = _when_reading_contract_expectation_members()
    _then_collection_has_length(members, 8)


def test_supported_language_exposes_fr_and_en_members() -> None:
    """Verifies SupportedLanguage contains exactly fr and en members."""
    members = _when_reading_supported_language_members()
    _then_collection_has_length(members, 2)


def test_contract_builder_mandatory_group_sets_all_group_keys() -> None:
    """Verifies mandatory_group sets shared mandatoryGroups across all grouped elements."""
    builder = _given_contract_builder_instance()
    elements = _when_building_mandatory_group(builder)
    _then_elements_have_shared_mandatory_groups(elements)

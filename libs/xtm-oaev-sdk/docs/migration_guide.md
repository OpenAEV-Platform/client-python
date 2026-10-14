# Migrating from pyoaev to the SDKs

This guide is for you if your collector or injector still pulls shared code out of
`pyoaev`: configuration, contracts, signatures, daemons, helpers, errors. That code has
moved into three SDKs, and `pyoaev` is back to its real job: the OpenAEV API client.

## Nothing breaks today

Every former `pyoaev` path still works. Touch one and it fires a `DeprecationWarning`
naming the new import, then hands you the same object as before. The classes that used
to build the API client are the exception: they come back as a thin subclass that still builds the API client for you.
Migrate at your own pace, one import at a time. The legacy paths only disappear in a
future `pyoaev` major release. The machinery is laid out in
[shim_strategy.md](shim_strategy.md).

## 1. Pick your dependencies

| You write | Depend on |
|---|---|
| a collector | `collectors-sdk` and `pyoaev` |
| an injector | `injectors-sdk` and `pyoaev` |
| shared code only (configuration, contracts, signatures) | `xtm-oaev-sdk` |

`collectors-sdk` and `injectors-sdk` drag `xtm-oaev-sdk` in on their own. Keep `pyoaev`
around for one thing: the API client (`OpenAEV`).

```toml
dependencies = [
    "pyoaev (>=…)",
    "collectors-sdk (>=0.1.0,<0.2.0)",   # or injectors-sdk
]
```

Until the SDKs land on PyPI, pull them straight from their repositories, exactly like
`pyoaev`'s CI does in `libs/sdk-requirements.txt`:

```
xtm-oaev-sdk @ git+https://github.com/OpenAEV-Platform/client-python.git@<ref>#subdirectory=libs/xtm-oaev-sdk
collectors-sdk @ git+https://github.com/OpenAEV-Platform/collectors.git@<ref>#subdirectory=libs/collectors-sdk
injectors-sdk @ git+https://github.com/OpenAEV-Platform/injectors.git@<ref>#subdirectory=libs/injectors-sdk
```

## 2. Find the legacy imports

Make the deprecation warnings fatal. Every one of them names its own replacement:

```bash
python -m pytest -W error::DeprecationWarning
python -W error::DeprecationWarning -c "from pyoaev.helpers import OpenAEVInjectorHelper"
# DeprecationWarning: Use 'from injectors_sdk import OpenAEVInjectorHelper' and pass api_client=OpenAEV(...) instead.
```

Importing `pyoaev` itself stays silent. Only the moved names speak up.

## 3. Change the imports

Import from the package root (`xtm_oaev_sdk`, `collectors_sdk`, `injectors_sdk`).
Always. Every name of `pyoaev` that moved is in the tables below, next to
every legacy module that exposed it.

### To xtm-oaev-sdk

| Legacy name | Legacy modules | New import |
|---|---|---|
| `AppLogger` | `pyoaev.utils` | `from xtm_oaev_sdk import AppLogger` |
| `AssetCategory` | `pyoaev`, `pyoaev.asset_types` | `from xtm_oaev_sdk import AssetCategory` |
| `AssetCriticality` | `pyoaev`, `pyoaev.asset_types` | `from xtm_oaev_sdk import AssetCriticality` |
| `AssetSubCategory` | `pyoaev`, `pyoaev.asset_types` | `from xtm_oaev_sdk import AssetSubCategory` |
| `BaseConfigModel` | `pyoaev`, `pyoaev.configuration`, `pyoaev.configuration.settings_loader` | `from xtm_oaev_sdk import BaseConfigModel` |
| `BaseDaemon` | `pyoaev.daemons`, `pyoaev.daemons.base_daemon`, `pyoaev.daemons.collector_daemon` | `from xtm_oaev_sdk import BaseDaemon` |
| `build_marker` | `pyoaev.signatures.ai_marker` | `from xtm_oaev_sdk import build_marker` |
| `build_network_configs` | `pyoaev`, `pyoaev.signatures`, `pyoaev.signatures.models` | `from xtm_oaev_sdk import build_network_configs` |
| `CloudInjectorConfig` | `pyoaev`, `pyoaev.signatures`, `pyoaev.signatures.models`, `pyoaev.signatures.signature_manager` | `from xtm_oaev_sdk import CloudInjectorConfig` |
| `CloudProvider` | `pyoaev`, `pyoaev.asset_types` | `from xtm_oaev_sdk import CloudProvider` |
| `ConfigLoaderCollector` | `pyoaev`, `pyoaev.configuration`, `pyoaev.configuration.settings_loader` | `from xtm_oaev_sdk import ConfigLoaderCollector` |
| `ConfigLoaderOAEV` | `pyoaev`, `pyoaev.configuration`, `pyoaev.configuration.settings_loader` | `from xtm_oaev_sdk import ConfigLoaderOAEV` |
| `Configuration` | `pyoaev`, `pyoaev.configuration`, `pyoaev.configuration.configuration`, `pyoaev.daemons.base_daemon`, `pyoaev.daemons.collector_daemon`, `pyoaev.helpers` | `from xtm_oaev_sdk import Configuration` |
| `ConfigurationError` | `pyoaev`, `pyoaev.exceptions`, `pyoaev.helpers` | `from xtm_oaev_sdk import ConfigurationError` |
| `ConfigurationHint` | `pyoaev.configuration.configuration` | `from xtm_oaev_sdk import ConfigurationHint` |
| `ConnectorConfigSchemaGenerator` | `pyoaev.configuration.configuration`, `pyoaev.configuration.connector_config_schema_generator` | `from xtm_oaev_sdk import ConnectorConfigSchemaGenerator` |
| `Contract` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import Contract` |
| `ContractAiTarget` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import ContractAiTarget` |
| `ContractAsset` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import ContractAsset` |
| `ContractAssetGroup` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import ContractAssetGroup` |
| `ContractAttachment` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import ContractAttachment` |
| `ContractBuilder` | `pyoaev`, `pyoaev.contracts`, `pyoaev.contracts.contract_builder` | `from xtm_oaev_sdk import ContractBuilder` |
| `ContractCardinality` | `pyoaev.contracts.contract_config`, `pyoaev.contracts.contract_utils`, `pyoaev.contracts.variable_helper` | `from xtm_oaev_sdk import ContractCardinality` |
| `ContractCardinalityElement` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import ContractCardinalityElement` |
| `ContractCheckbox` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import ContractCheckbox` |
| `ContractConfig` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import ContractConfig` |
| `ContractElement` | `pyoaev.contracts.contract_builder`, `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import ContractElement` |
| `ContractExpectations` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import ContractExpectations` |
| `ContractFieldKey` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import ContractFieldKey` |
| `ContractFieldType` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import ContractFieldType` |
| `ContractOutputElement` | `pyoaev.contracts.contract_builder`, `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import ContractOutputElement` |
| `ContractOutputType` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import ContractOutputType` |
| `ContractPayload` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import ContractPayload` |
| `ContractSelect` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import ContractSelect` |
| `ContractTeam` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import ContractTeam` |
| `ContractText` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import ContractText` |
| `ContractTextArea` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import ContractTextArea` |
| `ContractTuple` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import ContractTuple` |
| `ContractVariable` | `pyoaev.contracts.contract_config`, `pyoaev.contracts.contract_utils`, `pyoaev.contracts.variable_helper` | `from xtm_oaev_sdk import ContractVariable` |
| `copy_dict` | `pyoaev.utils` | `from xtm_oaev_sdk import copy_dict` |
| `CustomJsonFormatter` | `pyoaev.utils` | `from xtm_oaev_sdk import CustomJsonFormatter` |
| `data_to_temp_file` | `pyoaev.helpers` | `from xtm_oaev_sdk import data_to_temp_file` |
| `DictionarySource` | `pyoaev.configuration.configuration`, `pyoaev.configuration.sources` | `from xtm_oaev_sdk import DictionarySource` |
| `Domain` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import Domain` |
| `EncodedId` | `pyoaev.utils` | `from xtm_oaev_sdk import EncodedId` |
| `EnhancedJSONEncoder` | `pyoaev.utils` | `from xtm_oaev_sdk import EnhancedJSONEncoder` |
| `EnvironmentSource` | `pyoaev.configuration.configuration`, `pyoaev.configuration.sources` | `from xtm_oaev_sdk import EnvironmentSource` |
| `ExecutionDetails` | `pyoaev.signatures.models`, `pyoaev.signatures.signature_manager` | `from xtm_oaev_sdk import ExecutionDetails` |
| `ExecutionSignature` | `pyoaev.signatures.models`, `pyoaev.signatures.signature_manager` | `from xtm_oaev_sdk import ExecutionSignature` |
| `ExecutionStatus` | `pyoaev.signatures.models`, `pyoaev.signatures.types` | `from xtm_oaev_sdk import ExecutionStatus` |
| `Expectation` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import Expectation` |
| `ExpectationSignatureGroup` | `pyoaev`, `pyoaev.signatures`, `pyoaev.signatures.models`, `pyoaev.signatures.signature_manager` | `from xtm_oaev_sdk import ExpectationSignatureGroup` |
| `ExpectationType` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import ContractExpectationType` |
| `ExpectationType` | `pyoaev`, `pyoaev.signatures`, `pyoaev.signatures.models`, `pyoaev.signatures.types` | `from xtm_oaev_sdk import SignatureExpectationType` |
| `ExtraSignatureData` | `pyoaev`, `pyoaev.signatures`, `pyoaev.signatures.models`, `pyoaev.signatures.signature_manager` | `from xtm_oaev_sdk import ExtraSignatureData` |
| `FALSY` | `pyoaev.helpers` | `from xtm_oaev_sdk import is_falsy` |
| `InjectExecutionActions` | `pyoaev`, `pyoaev.signatures`, `pyoaev.signatures.models`, `pyoaev.signatures.types` | `from xtm_oaev_sdk import InjectExecutionActions` |
| `InjectorConfig` | `pyoaev.signatures`, `pyoaev.signatures.models` | `from xtm_oaev_sdk import InjectorConfig` |
| `is_falsy` | `pyoaev.configuration.configuration` | `from xtm_oaev_sdk import is_falsy` |
| `is_memory_certificate` | `pyoaev.helpers` | `from xtm_oaev_sdk import is_memory_certificate` |
| `is_truthy` | `pyoaev.configuration.configuration` | `from xtm_oaev_sdk import is_truthy` |
| `LinkedFieldModel` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import LinkedFieldModel` |
| `logger` | `pyoaev.daemons.base_daemon`, `pyoaev.utils` | `from xtm_oaev_sdk import logger` |
| `MatchTypes` | `pyoaev`, `pyoaev.apis.inject_expectation.model.expectation`, `pyoaev.signatures`, `pyoaev.signatures.signature_match`, `pyoaev.signatures.signature_type`, `pyoaev.signatures.types` | `from xtm_oaev_sdk import MatchTypes` |
| `NetworkInjectorConfig` | `pyoaev`, `pyoaev.signatures`, `pyoaev.signatures.models`, `pyoaev.signatures.signature_manager` | `from xtm_oaev_sdk import NetworkInjectorConfig` |
| `on_http_error` | `pyoaev.exceptions` | `from xtm_oaev_sdk import on_http_error` |
| `OpenAEVAuthenticationError` | `pyoaev`, `pyoaev.exceptions` | `from xtm_oaev_sdk import OpenAEVAuthenticationError` |
| `OpenAEVCreateError` | `pyoaev`, `pyoaev.exceptions` | `from xtm_oaev_sdk import OpenAEVCreateError` |
| `OpenAEVDeleteError` | `pyoaev`, `pyoaev.exceptions` | `from xtm_oaev_sdk import OpenAEVDeleteError` |
| `OpenAEVError` | `pyoaev.daemons.base_daemon`, `pyoaev.exceptions`, `pyoaev.signatures.signature_manager`, `pyoaev.signatures.signature_match` | `from xtm_oaev_sdk import OpenAEVError` |
| `OpenAEVGetError` | `pyoaev`, `pyoaev.exceptions` | `from xtm_oaev_sdk import OpenAEVGetError` |
| `OpenAEVHeadError` | `pyoaev`, `pyoaev.exceptions` | `from xtm_oaev_sdk import OpenAEVHeadError` |
| `OpenAEVHttpError` | `pyoaev`, `pyoaev.exceptions` | `from xtm_oaev_sdk import OpenAEVHttpError` |
| `OpenAEVListError` | `pyoaev`, `pyoaev.exceptions` | `from xtm_oaev_sdk import OpenAEVListError` |
| `OpenAEVParsingError` | `pyoaev`, `pyoaev.exceptions` | `from xtm_oaev_sdk import OpenAEVParsingError` |
| `OpenAEVUpdateError` | `pyoaev`, `pyoaev.exceptions` | `from xtm_oaev_sdk import OpenAEVUpdateError` |
| `PingAlive` | `pyoaev.daemons.collector_daemon`, `pyoaev.helpers`, `pyoaev.utils` | `from xtm_oaev_sdk import PingAlive` |
| `prepare_contracts` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import prepare_contracts` |
| `PrimitiveType` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import PrimitiveType` |
| `RedirectError` | `pyoaev`, `pyoaev.exceptions` | `from xtm_oaev_sdk import RedirectError` |
| `remove_none_from_dict` | `pyoaev.utils` | `from xtm_oaev_sdk import remove_none_from_dict` |
| `RequiredOptional` | `pyoaev.utils` | `from xtm_oaev_sdk import RequiredOptional` |
| `SecurityDomains` | `pyoaev.security_domain.types` | `from xtm_oaev_sdk import SecurityDomains` |
| `SecurityPlatformType` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import SecurityPlatformType` |
| `SettingsLoader` | `pyoaev`, `pyoaev.configuration`, `pyoaev.configuration.settings_loader` | `from xtm_oaev_sdk import SettingsLoader` |
| `setup_logging_config` | `pyoaev.utils` | `from xtm_oaev_sdk import setup_logging_config` |
| `SignatureCallbackPayload` | `pyoaev`, `pyoaev.signatures`, `pyoaev.signatures.models` | `from xtm_oaev_sdk import SignatureCallbackPayload` |
| `SignatureManager` | `pyoaev`, `pyoaev.signatures`, `pyoaev.signatures.signature_manager` | `from xtm_oaev_sdk import SignatureManager` |
| `SignatureMatch` | `pyoaev.signatures.signature_match`, `pyoaev.signatures.signature_type` | `from xtm_oaev_sdk import SignatureMatch` |
| `SignatureOutputStructure` | `pyoaev.signatures.models`, `pyoaev.signatures.signature_manager` | `from xtm_oaev_sdk import SignatureOutputStructure` |
| `SignaturePayload` | `pyoaev`, `pyoaev.signatures`, `pyoaev.signatures.models`, `pyoaev.signatures.signature_manager` | `from xtm_oaev_sdk import SignaturePayload` |
| `SignatureTarget` | `pyoaev`, `pyoaev.signatures`, `pyoaev.signatures.models`, `pyoaev.signatures.signature_manager` | `from xtm_oaev_sdk import SignatureTarget` |
| `SignatureTransmissionError` | `pyoaev`, `pyoaev.exceptions` | `from xtm_oaev_sdk import SignatureTransmissionError` |
| `SignatureType` | `pyoaev.apis.inject_expectation.model.expectation`, `pyoaev.signatures.signature_type` | `from xtm_oaev_sdk import SignatureType` |
| `SignatureTypes` | `pyoaev`, `pyoaev.apis.inject_expectation.model.expectation`, `pyoaev.signatures`, `pyoaev.signatures.signature_type`, `pyoaev.signatures.types` | `from xtm_oaev_sdk import SignatureTypes` |
| `SignatureValue` | `pyoaev`, `pyoaev.signatures`, `pyoaev.signatures.models`, `pyoaev.signatures.signature_manager` | `from xtm_oaev_sdk import SignatureValue` |
| `ssl_cert_chain` | `pyoaev.helpers` | `from xtm_oaev_sdk import ssl_cert_chain` |
| `ssl_verify_locations` | `pyoaev.helpers` | `from xtm_oaev_sdk import ssl_verify_locations` |
| `SupportedLanguage` | `pyoaev.contracts.contract_config` | `from xtm_oaev_sdk import SupportedLanguage` |
| `TargetSignatures` | `pyoaev`, `pyoaev.signatures`, `pyoaev.signatures.models`, `pyoaev.signatures.signature_manager` | `from xtm_oaev_sdk import TargetSignatures` |
| `ToolErrorInfo` | `pyoaev.signatures.models` | `from xtm_oaev_sdk import ToolErrorInfo` |
| `ToolOutput` | `pyoaev.signatures.models`, `pyoaev.signatures.signature_manager` | `from xtm_oaev_sdk import ToolOutput` |
| `ToolTimeoutInfo` | `pyoaev.signatures.models` | `from xtm_oaev_sdk import ToolTimeoutInfo` |
| `TRUTHY` | `pyoaev.helpers` | `from xtm_oaev_sdk import is_truthy` |
| `VariableHelper` | `pyoaev.contracts.contract_config`, `pyoaev.contracts.variable_helper` | `from xtm_oaev_sdk import VariableHelper` |
| `VariableType` | `pyoaev.contracts.contract_utils`, `pyoaev.contracts.variable_helper` | `from xtm_oaev_sdk import VariableType` |

### To collectors-sdk

| Legacy name | Legacy modules | New import |
|---|---|---|
| `CollectorDaemon` | `pyoaev.daemons`, `pyoaev.daemons.collector_daemon`, `pyoaev.helpers` | `from collectors_sdk import CollectorDaemon` |
| `DEFAULT_PERIOD_SECONDS` | `pyoaev.daemons.collector_daemon` | `from collectors_sdk import DEFAULT_PERIOD_SECONDS` |
| `DEFAULT_PLATFORM_TAG_COLOR` | `pyoaev.daemons.collector_daemon` | `from collectors_sdk import DEFAULT_PLATFORM_TAG_COLOR` |
| `DetectionExpectation` | `pyoaev.apis.inject_expectation.model`, `pyoaev.apis.inject_expectation.model.expectation` | `from collectors_sdk import DetectionExpectation` |
| `Expectation` | `pyoaev.apis.inject_expectation.model.expectation` | `from collectors_sdk import Expectation` |
| `ExpectationSignature` | `pyoaev.apis.inject_expectation.model.expectation` | `from collectors_sdk import ExpectationSignature` |
| `ExpectationTypeEnum` | `pyoaev.apis.inject_expectation.model`, `pyoaev.apis.inject_expectation.model.expectation` | `from collectors_sdk import ExpectationTypeEnum` |
| `OpenAEVCollectorHelper` | `pyoaev.helpers` | `from collectors_sdk import CollectorDaemon` |
| `OpenAEVDetectionHelper` | `pyoaev.helpers` | `from collectors_sdk import OpenAEVDetectionHelper` |
| `PreventionExpectation` | `pyoaev.apis.inject_expectation.model`, `pyoaev.apis.inject_expectation.model.expectation` | `from collectors_sdk import PreventionExpectation` |

### To injectors-sdk

| Legacy name | Legacy modules | New import |
|---|---|---|
| `create_mq_ssl_context` | `pyoaev.helpers` | `from injectors_sdk import create_mq_ssl_context` |
| `ListenQueue` | `pyoaev.helpers` | `from injectors_sdk import ListenQueue` |
| `OpenAEVConfigHelper` | `pyoaev.helpers` | `from injectors_sdk import OpenAEVConfigHelper` |
| `OpenAEVInjectorHelper` | `pyoaev.helpers` | `from injectors_sdk import OpenAEVInjectorHelper` |

### Without replacement

| Legacy name | Legacy modules | New import |
|---|---|---|
| `CHALLENGES_URI` | `pyoaev.contracts.variable_helper` | no replacement (see below) |
| `COMCHECK` | `pyoaev.contracts.variable_helper` | no replacement (see below) |
| `EXERCISE` | `pyoaev.contracts.variable_helper` | no replacement (see below) |
| `LESSONS_URI` | `pyoaev.contracts.variable_helper` | no replacement (see below) |
| `PLAYER_URI` | `pyoaev.contracts.variable_helper` | no replacement (see below) |
| `SCOREBOARD_URI` | `pyoaev.contracts.variable_helper` | no replacement (see below) |
| `TEAMS` | `pyoaev.contracts.variable_helper` | no replacement (see below) |
| `USER` | `pyoaev.contracts.variable_helper` | no replacement (see below) |

## 4. Inject the API client

The SDKs never build the API client. You build it, and you hand it over. Four legacy
classes used to build it themselves from the configuration (`openaev_url`,
`openaev_token`, `openaev_tenant_id`), and their legacy paths still do.

Collector:

```python
# before
from pyoaev.daemons import CollectorDaemon

CollectorDaemon(configuration=configuration, callback=collect, collector_type="openaev_my_collector")

# after
from pyoaev import OpenAEV
from collectors_sdk import CollectorDaemon

api = OpenAEV(
    url=configuration.get("openaev_url"),
    token=configuration.get("openaev_token"),
    tenant_id=configuration.get("openaev_tenant_id"),
)
CollectorDaemon(
    configuration=configuration,
    callback=collect,
    api_client=api,
    collector_type="openaev_my_collector",
)
```

`BaseDaemon` (`pyoaev.daemons` → `xtm_oaev_sdk`) plays by the same rule: same
`api_client=`.

Injector:

```python
# before
from pyoaev.helpers import OpenAEVInjectorHelper

helper = OpenAEVInjectorHelper(config, icon)

# after
from pyoaev import OpenAEV
from injectors_sdk import OpenAEVInjectorHelper

api = OpenAEV(
    url=config.get_conf("openaev_url"),
    token=config.get_conf("openaev_token"),
    tenant_id=config.get_conf("openaev_tenant_id"),
)
helper = OpenAEVInjectorHelper(config, icon, api_client=api)
```

Signature manager:

```python
# before
from pyoaev.signatures import SignatureManager

manager = SignatureManager(client, logger)

# after
from xtm_oaev_sdk import SignatureManager

manager = SignatureManager(transport=client.signature, logger=logger)
```

## Renamed names

| Legacy | New |
|---|---|
| `pyoaev.signatures.ExpectationType` | `xtm_oaev_sdk.SignatureExpectationType` |
| `pyoaev.contracts.contract_config.ExpectationType` | `xtm_oaev_sdk.ContractExpectationType` |
| `pyoaev.helpers.TRUTHY` / `FALSY` | `xtm_oaev_sdk.is_truthy` / `is_falsy` |
| `pyoaev.helpers.OpenAEVCollectorHelper` (already deprecated) | `collectors_sdk.CollectorDaemon` |

The constants of `pyoaev.contracts.variable_helper` (`USER`, `EXERCISE`, `TEAMS`,
`COMCHECK` and the `*_URI` ones) get no public replacement. Reach for the built-in
variables of `xtm_oaev_sdk.VariableHelper` instead.

## What stays in pyoaev

The API client, and everything wired around it: `OpenAEV`, `pyoaev.apis` (including
`inputs.search`), `pyoaev.backends`, `pyoaev.base`, `pyoaev.client`, `pyoaev.mixins`,
and `pyoaev.utils.get_content_type` / `response_content`. Nothing to migrate there.

## Things you may notice

- In tests, the legacy patch targets (`pyoaev.daemons.base_daemon.OpenAEV`,
  `pyoaev.helpers.OpenAEV`, `pyoaev.utils.PingAlive.start`…) keep biting as long as
  your code runs through the legacy paths. Once it imports from the SDKs, patch the
  names it actually looks up now.
- `from <package> import X` on a legacy package (for example `from pyoaev.signatures
  import SignatureManager`) fires the warning twice. Plain modules fire it once.
- An `AppLogger` built without a name, and a `SignatureManager` built without a logger,
  now log under the SDK module name, not the former `pyoaev` one.

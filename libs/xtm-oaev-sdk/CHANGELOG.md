# Changelog

Every notable change to xtm-oaev-sdk lands here. Every seam change too, with the new
version of its seam
([seam-changes-are-versioned-contract-changes](docs/tdr/seam-changes-are-versioned-contract-changes.tdr.md)).

## [Unreleased]

### Added

- `port_io`: the platform's own payloads, key for key, so injectors and collectors
  running without the platform read and write the same JSON. Injector side:
  `ExecutableInject` (the queue message, with `ExecutableInjection`,
  `ExecutableInjectorContract`, `EndpointTargetOutput`, `AgentOutput`,
  `AssetGroupSimple`), `InjectReceptionInput` and `InjectExecutionInput`. Collector
  side: `InjectExpectationOutput` (with `InjectExpectationSignature`,
  `InjectExpectationResult`), `InjectExpectationUpdateFromCollectorInput`,
  `InjectExpectationBulkUpdateInput`, `InjectExpectationTraceInput` and
  `InjectExpectationTraceBulkInsertInput`. Each model is written by hand from the
  platform DTO it mirrors, names that DTO in its docstring, and ships with a sample
  payload. Dates are kept as the platform wrote them, ISO text or epoch numbers.
  `PORT_IO_CONTRACT_VERSION` `1.1.0`.
- `daemons`: the dev options common to every daemon. `DevOptions` (seam model) and
  `dev_options(argv=None)` expose `--dev`, `--out`, `--record`, `--replay` and the dev
  help (`-h` / `--help`, only together with `--dev`); `dev_help()` describes them, and
  `dev_argument_parser(description=None, epilog=None)` returns a new parser holding
  them, which the injector and collector SDKs extend with their own options. They are
  read only under their full name, and flags the daemon does not own are left alone,
  since every daemon reads them, dev or not. The port gains
  `DaemonRuntimePort.dev_argument_parser`, `dev_options` and `dev_help`. Seam `1.1.0`.
- `daemons`: the dev sink, where a daemon in dev mode writes the calls the platform
  would have received. `dev_sink(out=None, secrets=(), keep=(), to_stderr=False)`
  checks each call against the payload the platform accepts on its path (a body it
  would reject raises `OpenAEVHttpError` with `response_code` 400, and nothing is
  written), redacts the secrets (`***`, JSON text redacted as JSON) except in the
  `keep` keys, and writes the calls as one JSON list, indented, keys in the payload's
  order: rewritten whole after each call in `out`, so the file is valid JSON at any
  time, or written once, on close, to stdout or stderr. It also writes the run's notes
  and refusals on stderr. `environment_secret_values(environ=None)` lists the values of
  the secret-named environment variables. Ports `DevSinkPort` and `DevSinkFactoryPort`.
  Seam `1.1.0`.
- `configuration`: `Configuration.secret_values()` returns the values that must never
  be written out, longest first: those of the keys whose name says they hold a secret
  (`*_token`, `*_secret`, `*_password`, `*_key`…) and every `SecretStr` of the settings
  model, wherever they were read from. Port `ConfigurationResolverPort.secret_values`.
  Seam `1.1.0`.

### Changed

- `port_io`: `ExecutionStatus` gains `ASSET_CLEARANCE_RESTRICTED`, a status the
  platform accepts. `PORT_IO_CONTRACT_VERSION` `1.1.0`.
- `daemons`: a daemon no longer exits with code 2 on a command-line flag it does not
  own. `--dump-config-schema` detection only passes that flag to its parser, so dev
  flags and the daemon's own flags can share the command line. Seam `1.1.0`.
- `configuration`: under `--dev`, a settings model no longer needs the platform URL
  and token. A last, lowest-priority source fills every `ConfigLoaderOAEV` section the
  configuration leaves out with an unreachable platform (`http://platform.openaev.invalid`);
  whatever the configuration gives still wins, and without `--dev` both stay required.
  Seam `1.1.0`.

## [0.1.0] - Unreleased

First version. The shared, client-free code of `pyoaev` 3.261014.1 moves out and into
this SDK. The former `pyoaev` paths keep working, each one firing a
`DeprecationWarning` ([migration guide](docs/migration_guide.md)).

### Added

- `common`: the `OpenAEVError` hierarchy, `AppLogger`, logging setup, JSON encoding,
  SSL helpers, asset and security-domain enums, and the `BaseClient`,
  `DaemonProtocol` and `AppLoggerProtocol` protocols. Seam `1.0.0`.
- `configuration`: `Configuration`, `ConfigurationHint`, `SettingsLoader`, the settings
  models, sources and schema generator. Seam `1.0.0`.
- `contracts`: `Contract`, `ContractBuilder`, `VariableHelper`, `prepare_contracts`,
  the contract elements and enums, and the credential references (`CredentialType`,
  `ContractReferencedCredential`, `build_single_referenced_credential_element`, from
  `pyoaev.credential`). Seam `1.0.0`.
- `signatures`: `SignatureManager`, `build_network_configs`, `build_marker`, the
  matching types and the inbound I/O models. Seam `1.0.0`.
- `port_io`: the wire models sent to the platform. `PORT_IO_CONTRACT_VERSION` `1.0.0`.
- `daemons`: `BaseDaemon` and `PingAlive`. Seam `1.0.0`.
- `deprecation` (new, not from `pyoaev`): `make_deprecated_getattr`, the PEP 562
  deprecation primitive. Seam `1.0.0`.

### Changed (compared with pyoaev)

- `ExpectationType` splits in two: `SignatureExpectationType` and
  `ContractExpectationType`.
- `BaseDaemon` and `SignatureManager` stop building the API client. Pass
  `api_client=` / `transport=` yourself.
- `requires-python` moves from `>=3.11` to `>=3.12`, the version `typing.override`
  actually needs. Released `pyoaev` already failed to import on 3.11.

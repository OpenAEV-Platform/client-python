# Changelog

Every notable change to xtm-oaev-sdk lands here. Every seam change too, with the new
version of its seam
([seam-changes-are-versioned-contract-changes](docs/tdr/seam-changes-are-versioned-contract-changes.tdr.md)).

## [0.1.0] - Unreleased

First version. The shared, client-free code of `pyoaev` 3.261014.1 moves out and into
this SDK. The former `pyoaev` paths keep working, each one firing a
`DeprecationWarning` ([migration guide](docs/migration_guide.md)).

### Added

- `common`: the `OpenAEVError` hierarchy, `on_http_error`, `AppLogger`, logging setup,
  JSON encoding, SSL helpers, asset and security-domain enums, and the `BaseClient`,
  `DaemonProtocol` and `AppLoggerProtocol` protocols. Seam `1.0.0`.
- `configuration`: `Configuration`, `ConfigurationHint`, `SettingsLoader`, the settings
  models, sources and schema generator. Seam `1.0.0`.
- `contracts`: `Contract`, `ContractBuilder`, `VariableHelper`, `prepare_contracts`,
  the contract elements and enums, and the credential references (`CredentialType`,
  `ContractReferencedCredential`, `build_single_referenced_credential_element`, from
  `pyoaev.credential`). Seam `1.0.0`.
- `signatures`: `SignatureManager`, `build_network_configs`, `build_marker`, the
  matching types and the inbound I/O models. Seam `1.0.0`, JSON schemas pinned.
- `port_io`: the wire models sent to the platform. `PORT_IO_CONTRACT_VERSION` `1.0.0`,
  JSON schemas pinned.
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

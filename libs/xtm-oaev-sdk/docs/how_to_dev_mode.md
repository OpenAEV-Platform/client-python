# How to run an injector or a collector without the platform (dev mode)

This guide is for you if you write or debug an injector or a collector and want to run it
**without an OpenAEV platform**: no registration, no RabbitMQ, no heartbeat, no call to the
platform. The daemon still does its real work (it runs the real tool, queries the real
security product), and everything it would have sent to the platform is written to one
readable JSON file instead.

Dev mode reads and writes the platform's **own payloads**, key for key. You feed it what
the platform would have sent, and you get back what the platform would have received.

## TL;DR

```bash
python -m shodan --dev --help                                  # every dev option
python -m shodan --dev --list-contracts                        # its contracts
python -m shodan --dev --new-inject "ip enum" > inject.json    # a message to edit
#   fill what stderr says is still to fill, then:
python -m shodan --dev --inject inject.json --out run.json     # run it
python -m my_collector --dev --expectations expectations.json --once --out run.json
python -m shodan --dev --inject inject.json --emit expectations --out injector.json \
  | python -m my_collector --dev --expectations - --once --out collector.json   # chain
python -m shodan --dev --inject inject.json --record shodan.tape.json   # record its outside calls
python -m shodan --dev --inject inject.json --replay shodan.tape.json   # then run offline
```

## 1. Before you start

**The SDKs.** Dev mode lives in `injectors_sdk.OpenAEVInjectorHelper` and
`collectors_sdk.CollectorDaemon`. Daemons that import these names from `pyoaev` get the
very same objects through the deprecation shims, so they get dev mode too, **as long as
their `pyoaev` ships the SDKs**. Check with `pip show pyoaev`: `Requires` must list
`xtm-oaev-sdk`, `injectors-sdk` and `collectors-sdk`.

**The configuration still loads first**, but under `--dev` it no longer needs the
platform: a `ConfigLoaderOAEV` section the configuration leaves out gets an unreachable
platform (`http://platform.openaev.invalid`). What your configuration gives still wins.
Without `--dev`, the platform URL and token stay required.

Without `--dev`, nothing changes: the daemon registers, pings and consumes exactly as
before. The one behavior shared by both modes: injectors send their signatures under the
**signature types** collectors match on (`start_date`, `target_ipv4_address`…), and
collectors read a legacy name as its type and drop an unknown type with a warning.

## 2. The flags

`--dev --help` (or `-h`) prints the common options and the daemon's own, then exits 0.
An injector shows:

```text
common options:
  --dev                 run without the platform
  -h, --help            show this help and exit
  --out PATH            where the calls the daemon would have sent go, as one JSON
                        list (default: stdout)
  --record PATH         record every outside call (HTTP, commands) and its answer
                        to PATH
  --replay PATH         answer every outside call from PATH, offline; a call it
                        does not hold fails

injector options:
  --inject PATH         the inject message to run, as the platform publishes it
  --timeout SECONDS     how long to wait for the inject to complete (default: 600)
  --emit expectations   also write on stdout the pending expectations collectors
                        would then get
  --dump-contracts      write the registration, contracts included, and exit
  --list-contracts      list the contracts it serves, and exit
  --new-inject CONTRACT write an inject message to edit for CONTRACT
```

A collector shows the common options and `--expectations PATH` and `--once`. Every daemon
reads these flags, dev or not, so they never act on what is not theirs: they are only read
under their **full name**, `-h` / `--help` only counts together with `--dev`, and any flag
they do not own is left alone. `--dump-config-schema` still works alongside them, and
still wins.

From Python: `xtm_oaev_sdk.dev_options()` returns the common options (`DevOptions`),
`injectors_sdk.injector_dev_options()` and `collectors_sdk.collector_dev_options()` the
role's (`InjectorDevOptions`, `CollectorDevOptions`), each with its `*_dev_help()`.

## 3. Run an injector

### Write the inject message

```bash
python -m shodan --dev --list-contracts
python -m shodan --dev --new-inject "ip enum" > inject.json
```

The contract is named by its id or by any piece of a label, whatever the case. A name
that matches no contract, or several, is refused with exit code 2 and the candidates
listed. On stderr, a guide to each field (type, when it is mandatory, value, choices, where
targets go), then what is still to fill. On stdout, a lean inject message with only the
keys you edit, prefilled the way the platform's inject form fills a new inject. An
`asset-groups` target type is switched to `manual`, else `assets`: only the platform can
resolve the assets of a group.

### Run it

```bash
python -m shodan --dev --inject inject.json --out run.json
echo $?    # 0 completed, 1 failed or never completed, 2 refused before running
```

`--inject` takes the JSON the platform publishes to the injector's queue
(`ExecutableInject`), from a file or `-` for stdin. A lean message is completed the way
the platform fills it: the contract from the injector's own (both contract id paths), an
inject id **derived from the message** (the same message writes the same calls at every
run), a title, and the content defaults under the content you gave. A whole message,
captured from a platform run, is handed over unchanged.

**Before anything runs**, the message is checked the way the platform checks it, and a
refusal says why on stderr and exits with code 2: it must be an inject message naming a
contract this injector serves, and its content must satisfy the contract by the
platform's own health-check rules (`ContractValidator`; a text field with a non-blank
default counts as set; targets the message carries count as set).

**The run ends** on the inject's `complete` callback, or after `--timeout` seconds without
one (exit 1, saying so). The exit code comes from the `complete` status: 1 for the
platform's failure family (`ERROR`, `COMMAND_NOT_FOUND`, `TIMEOUT`…), 0 otherwise.

**Calls only the platform can answer** (a document download, a target search, any manager
the stand-in does not offer) raise `xtm_oaev_sdk.NeedsPlatformError`, naming the call.

### What it writes

One JSON list, indented, keys in the platform payload's order, so it reads well and diffs
cleanly. With `--out`, it is rewritten after each call, so the file is valid JSON at any
time; without, it goes to stdout when the run ends.

```json
[
  {
    "method": "POST",
    "path": "/api/injects/execution/callback/5dca53ff-…",
    "body": {
      "execution_message": "Scan done",
      "execution_status": "SUCCESS",
      "execution_action": "complete"
    }
  }
]
```

Each body is checked against what the platform accepts (`InjectReceptionInput`,
`InjectExecutionInput`). A call the platform would reject is refused the way the platform
answers it: the injector gets an `OpenAEVHttpError` with `response_code` 400, and nothing
is written. `--dump-contracts` writes the registration (`POST /api/injectors`).

## 4. Run a collector

```bash
python -m my_collector --dev --expectations expectations.json --once --out run.json
```

`--expectations` takes exactly what the platform serves on its expectation endpoints: a
JSON **list** of `InjectExpectationOutput`, from a file or `-` for stdin. Capture a real
one with the collector's own id and token:

```bash
curl -s -H "Authorization: Bearer $OPENAEV_TOKEN" \
  "$OPENAEV_URL/api/injects/expectations/assets/$COLLECTOR_ID?expiration_time=360" \
  > expectations.json
```

It is served through `expectations_assets_for_source`, `detection_expectations_for_source`,
`prevention_expectations_for_source` and `collectors_sdk.expectations_models_for_source`.
An answered expectation leaves the feed, as on the platform. The updates, bulk updates and
traces are written like an injector's calls, checked against
`InjectExpectationUpdateFromCollectorInput`, `InjectExpectationBulkUpdateInput`,
`InjectExpectationTraceInput` and `InjectExpectationTraceBulkInsertInput`. A run without
`--expectations`, or with a file that is not a list of pending expectations, exits 2.
Registration still runs against a local stand-in that hands back ids and writes nothing;
any other manager raises `NeedsPlatformError`. Without `--once`, the cycle runs every
`collector_period` until you stop it.

## 5. Chain an injector into a collector

```bash
python -m my_injector --dev --inject inject.json --emit expectations --out injector.json \
  | python -m my_collector --dev --expectations - --once --out collector.json
```

`--emit expectations` makes the injector also write, **on stdout**, the pending
expectations the platform would then serve to collectors. Without `--out`, its calls go to
stderr, so stdout always carries the pending expectations alone. The signatures are read
from the execution callbacks the injector posted, the way the platform's
`SignatureOutputProcessor` reads them:

- the target is the agent (`agent_id` or `agent`), else the asset, else the asset group;
  a signature naming none is dropped;
- signatures attach to DETECTION and PREVENTION expectations only, and only to those the
  inject content declares;
- a signature reads its type and value from `signature_type`/`type` and
  `signature_value`/`value`, keeps scalars with text, and a type/value pair is kept once;
- without `expectation_expiration_time`, an expectation expires after 21600 seconds.

What the platform would have dropped is noted on stderr (`dev: …`). Dev mode has no
expectation store: every target a signature names is taken as a target of the inject.

## 6. Record the outside calls, replay them offline

```bash
python -m shodan --dev --inject inject.json --record shodan.tape.json --out run.json  # online, once
python -m shodan --dev --inject inject.json --replay shodan.tape.json --out run.json  # offline, any time
```

It works for collectors the same way (`--expectations … --once --record splunk.tape.json`).

| Calls | Through | On replay |
|---|---|---|
| HTTP and HTTPS | `requests`, urllib3, `urllib.request` (so most product SDKs) | answered from the tape; no socket opens |
| commands | `subprocess.run` | exit code, stdout and stderr from the tape; the command does not run |
| anything else | any other outbound connection | **fails** with `TapeMissError` |

**The tape** is one JSON document, meant to be committed and reviewed in a diff:

```json
{
  "tape_version": "1",
  "sdk_version": "0.1.0",
  "daemon": "Shodan",
  "recorded_at": "2026-11-10T08:00:00Z",
  "calls": [
    {
      "kind": "http",
      "request": {"method": "GET", "url": "https://api.shodan.io/shodan/host/1.2.3.4?key=***", "headers": [["X-Api-Key", "***"]]},
      "response": {"status": 200, "reason": "OK", "headers": [["Content-Type", "application/json"]], "body": {"json": {"ip_str": "1.2.3.4"}}}
    }
  ]
}
```

A JSON body is kept as JSON (`json`), other text as `text`, binary in `base64`. A
compressed answer is kept decompressed when readable, `decoded_from` naming its encoding,
and replays without its `Content-Encoding`. The tape is rewritten after each call, so it is
valid JSON even after a crash.

**On replay**, a call is found by its method, URL and body (a JSON body by value, however
it is spaced; a command by its argv and input). Identical calls get their answers in the
order recorded, then the last one again. A call the tape does not hold **fails** with
`TapeMissError` (a `ConnectionError`), naming it. A tape that is not JSON, of another tape
version, or holding a call the SDK does not model is refused, saying why (exit 2).

**Secrets stay off the tape**: the configuration's and the environment's secret values,
and whatever goes in a secret-named header, parameter or body field. Replay matches a call
whatever secret it carries, so a tape recorded with your key replays with any key, or
none. Before committing a tape, lint it:

```python
from xtm_oaev_sdk import lint_tape
lint_tape("shodan.tape.json", secrets=["my-real-key"])   # [] when clean
```

`--record` and `--replay` together are refused (exit 2). From Python, the same tape is
`xtm_oaev_sdk.CallTape(path, "record" | "replay", secrets=…, daemon=…)`, with `start()`
and `stop()`, or as a context manager.

## 7. Secrets stay out of the output

Before anything is written, dev mode replaces with `***` the values of the configuration
keys whose name says they hold a secret (`*_token`, `*_secret`, `*_password`, `*_key`…),
every `SecretStr` of the settings model (`Configuration.secret_values()`), and the values
of environment variables with such names (`environment_secret_values()`). Ids, statuses,
actions and dates are never rewritten. JSON text holding a secret is redacted as JSON.

## 8. The payload models

They live in `xtm_oaev_sdk`, are written by hand from the platform DTOs they mirror (each
model's docstring names its DTO source), and ship with a sample payload. What the platform
sends keeps the keys a model does not list; what a daemon sends refuses any key the
platform does not take. Dates are kept as the platform wrote them, ISO text or epoch.

| Model | Payload |
|---|---|
| `ExecutableInject` | the inject message on the injector queue |
| `InjectReceptionInput` | `POST /api/injects/execution/reception/{inject_id}` |
| `InjectExecutionInput` | `POST /api/injects/execution/callback/{inject_id}` |
| `InjectExpectationOutput` | one pending expectation |
| `InjectExpectationUpdateFromCollectorInput` | `PUT /api/injects/expectations/{expectation_id}` |
| `InjectExpectationBulkUpdateInput` | `PUT /api/injects/expectations/bulk` |
| `InjectExpectationTraceInput` | `POST /api/inject-expectations-traces` |
| `InjectExpectationTraceBulkInsertInput` | `POST /api/inject-expectations-traces/bulk` |

## 9. When it does not work

| You see | Why | Do |
|---|---|---|
| connection errors to `openaev_url` or RabbitMQ | no `--dev`: the daemon runs against the platform | add `--dev` |
| `dev: refused: …` and exit code 2 | the message, its contract, its content, the expectations or the tape failed the checks | read the reason; `--new-inject` shows what to fill |
| `NeedsPlatformError: … needs the platform` | a document download, a target search, or a manager the stand-in does not offer | give the targets as `assets`, not `assetGroups` |
| `dev: no complete callback … within … seconds`, exit 1 | the injector never posted `complete` | raise `--timeout`, or fix the injector |
| `TapeMissError: not on the replay tape: …` | the replayed run made a call the recording did not | record again |
| exit code 1, `complete` with `ERROR` | the injector failed for real (tool, API key, network) | read `execution_message` in the output |

## 10. Known limits

- **The tape** covers HTTP through `http.client` and commands through `subprocess.run`.
  Other clients (`httpx`, `aiohttp`, SMTP, `subprocess.Popen` directly) are not taped: on
  replay, their connections fail closed instead of reaching the network.
- **Signatures over 5 MiB** are written as one callback; the platform client splits them
  per target.
- **Dates** in the output differ between a run and its replay when the daemon writes the
  time it ran; compare those runs dates aside.

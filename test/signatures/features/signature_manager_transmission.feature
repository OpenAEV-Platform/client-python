Feature: SignatureManager signature transmission and container IP resolution
    As an injector using the OpenAEV client
    I want to send compiled signatures to the backend and resolve my container's IP
    So that inject results are recorded and IP-based signatures are accurate

  Background:
    Given a SignatureManager initialised with constructor SignatureManager(client, logger)

  Scenario Outline: HTTP 2xx response is treated as successful transmission
    Given a compiled post-execution payload for inject_id "inject-abc-001"
    And the backend responds with HTTP <status_code>
    When I call send_signatures for inject_id "inject-abc-001" with phase "execution_complete"
    Then send_signatures completes without raising an exception

    Examples:
      | status_code |
      |         200 |
      |         202 |

  Scenario: send_signatures posts to the inject callback with the agreed nested schema
    Given a compiled payload with 1 target, expectation_type "DETECTION", signature_type "public_ip", signature_value "203.0.113.5"
    And the backend responds with HTTP 200
    When I call send_signatures for inject_id "inject-abc-001" with phase "execution_complete"
    Then a POST request is sent to /injects/execution/callback/inject-abc-001
    And the POST request body contains signatures.targets as a list
    And signatures.targets[0].signature_values[0].expectation_type equals "DETECTION"
    And signatures.targets[0].signature_values[0].values[0].signature_type equals "public_ip"
    And signatures.targets[0].signature_values[0].values[0].signature_value equals "203.0.113.5"
    And signatures.targets[0] contains a signature_target key


  Scenario Outline: resolve_container_ip returns a valid IPv4 in each supported execution environment
    Given a SignatureManager running in a "<environment>" environment
    When I call resolve_container_ip
    Then the returned value is a non-empty valid IPv4 address string

    Examples:
      | environment |
      | Docker      |
      | Kubernetes  |
      | bare-metal  |


  Scenario: Payload schema groups signature values by expectation_type within each target
    Given a compiled payload for 1 target with signatures of expectation_type "DETECTION" and expectation_type "PREVENTION"
    And the backend responds with HTTP 200
    When I call send_signatures for inject_id "inject-abc-001" with phase "execution_complete"
    Then the POST request body nests signature values under separate expectation_type entries within signatures.targets[0].signature_values
    And the entry with expectation_type "DETECTION" contains only DETECTION signature values
    And the entry with expectation_type "PREVENTION" contains only PREVENTION signature values

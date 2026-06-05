Feature: SignatureManager transmission constraints
    As an injector using the OpenAEV client
    I want signature transmission to handle large payloads, transient errors, and client errors correctly
    So that signatures are reliably delivered even under adverse conditions

  Background:
    Given a SignatureManager initialised with constructor SignatureManager(client, logger)

  Scenario: Payload exceeding MAX_PAYLOAD_SIZE is auto-chunked with chunk metadata
    Given a compiled payload whose serialised size exceeds MAX_PAYLOAD_SIZE by at least a factor of 2
    And the backend responds with HTTP 200
    When I call send_signatures for inject_id "inject-abc-001" with phase "execution_complete"
    Then the payload is sent as multiple sequential POST requests to /injects/inject-abc-001/callback
    And each POST request body contains chunk_index as a 0-based integer
    And each POST request body contains total_chunks as a positive integer matching the total number of chunks sent
    And each POST request body contains only "signatures", "chunk_index" and "total_chunks" at the top level
    And the union of targets across all POST requests equals the original target set
    And no individual POST request body exceeds MAX_PAYLOAD_SIZE bytes

  Scenario: HTTP 5xx response triggers exponential backoff retry for up to 3 additional attempts
    Given a compiled post-execution payload for inject_id "inject-abc-001"
    And the backend responds with HTTP 503 on every attempt
    When I call send_signatures for inject_id "inject-abc-001" with phase "execution_complete"
    Then send_signatures sends a total of 4 POST requests to /injects/inject-abc-001/callback
    And a WARNING log message containing the retry attempt number is emitted before each of the 3 retry attempts
    And the wait before attempt 2 is 1 second
    And the wait before attempt 3 is 2 seconds
    And the wait before attempt 4 is 4 seconds
    And a SignatureTransmissionError is raised after all retries are exhausted

  Scenario: HTTP 4xx response raises an exception immediately with no retries and no sleep
    Given a compiled post-execution payload for inject_id "inject-abc-001"
    And the backend responds with HTTP 400 and body '{"error": "bad request"}'
    When I call send_signatures for inject_id "inject-abc-001" with phase "execution_complete"
    Then only 1 POST request is sent to /injects/inject-abc-001/callback
    And an ERROR log message containing status code 400 and the response body is emitted
    And an exception is raised immediately
    And no sleep or wait occurs before the exception is raised

  Scenario: resolve_container_ip returns unknown and emits exactly one warning when all strategies fail
    Given all IP resolution strategies are mocked to fail
    When I call resolve_container_ip
    Then the returned value is the string "unknown"
    And exactly 1 WARNING log message is emitted
    And no exception propagates from resolve_container_ip

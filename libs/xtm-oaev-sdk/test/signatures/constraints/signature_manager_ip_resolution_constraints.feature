Feature: SignatureManager IP resolution constraints

  Scenario: resolve_container_ip returns unknown and emits exactly one warning when all strategies fail
    Given all IP resolution strategies are mocked to fail
    When I call resolve_container_ip
    Then the returned value is the string "unknown"
    And exactly 1 WARNING log message is emitted
    And no exception propagates from resolve_container_ip

Feature: SignatureManager container IP resolution

  Scenario Outline: resolve_container_ip returns a valid IPv4 in each supported execution environment
    Given a SignatureManager running in a "<environment>" environment
    When I call resolve_container_ip
    Then the returned value is a non-empty valid IPv4 address string

    Examples:
      | environment |
      | Docker      |
      | Kubernetes  |
      | bare-metal  |

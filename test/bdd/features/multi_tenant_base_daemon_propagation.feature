Feature: Tenant propagation in BaseDaemon API client initialization

  Scenario Outline: BaseDaemon propagates tenant_id correctly from configuration
    Given a daemon configuration with <tenant_id>
    When the BaseDaemon is initialized
    Then the API client should be created with tenant_id "<expected_tenant_id>"

    Examples:
      | tenant_id                               | expected_tenant_id                     |
      | Missing tenant key                      | None                                   |
      | None                                    | None                                   |
      | 2cffad3a-0001-4078-b0e2-ef74274022c3    | 2cffad3a-0001-4078-b0e2-ef74274022c3   |
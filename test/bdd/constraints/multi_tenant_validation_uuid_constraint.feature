Feature: Tenant ID handling in OpenAEV configuration

  Scenario: tenant_id is not provided
    Given a configuration without tenant_id
    When the configuration is loaded
    Then tenant_id should be None


  Scenario: tenant_id is explicitly set to None
    Given a configuration with tenant_id set to None
    When the configuration is loaded
    Then tenant_id should be None


  Scenario Outline: tenant_id is invalid and should raise a validation error
    Given a configuration with tenant_id "<tenant_id>" invalid
    When the configuration is loaded
    Then a validation error should be raised

    Examples:
      | tenant_id           |
      | ChangeMe            |
      | ""                  |
      | 550-e29-41d-a71-446 |


  Scenario: tenant_id is a valid UUID
    Given a configuration with tenant_id "2cffad3a-0001-4078-b0e2-ef74274022c3"
    When the configuration is loaded
    Then tenant_id should be a valid UUID
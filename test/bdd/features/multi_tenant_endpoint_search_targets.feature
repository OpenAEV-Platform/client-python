Feature: searchTargets API routing with and without tenant_id

  Scenario Outline: searchTargets routing behavior
    Given an OpenAEV client with tenant_id "<tenant_id>"
    And a valid SearchPaginationInput
    When I call searchTargets on endpoint
    Then the request URL should be "<expected_url>"

    Examples:
      | tenant_id | expected_url |
      | None | url/api/endpoints/targets |
      | 2cffad3a-0001-4078-b0e2-ef74274022c3 | url/api/tenants/2cffad3a-0001-4078-b0e2-ef74274022c3/endpoints/targets |
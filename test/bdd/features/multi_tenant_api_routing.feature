Feature: Multi-tenant API routing in OpenAEV client

  Scenario: Full URL bypasses tenant routing
    Given an OpenAEV client with tenant_id "2cffad3a-0001-4078-b0e2-ef74274022c3"
    When I build the URL for "https://external.service/api/path"
    Then the resulting URL should be "https://external.service/api/path"

  Scenario Outline: Relative path routing behavior
    Given an OpenAEV client with tenant_id "<tenant_id>"
    When I build the URL for "/path"
    Then the resulting URL should be "<output>"

    Examples:
      | tenant_id                             | output                                                          |
      | None                                  | base_url/api/path                                               |
      | 2cffad3a-0001-4078-b0e2-ef74274022c3  | base_url/api/tenants/2cffad3a-0001-4078-b0e2-ef74274022c3/path  |


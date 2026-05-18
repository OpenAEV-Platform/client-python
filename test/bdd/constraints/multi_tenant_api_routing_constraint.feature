Feature: URL normalization in OpenAEV client

  Scenario Outline: URL normalization combines base_url and path correctly
    Given an OpenAEV client with base_url "<base_url>"
    When I build the URL for "<path>"
    Then the resulting URL should be "<expected>"

    Examples:
      | base_url    | path       | expected              |
      | base_url    | path       | base_url/api/path    |
      | base_url/   | /path      | base_url/api/path    |
      | base_url//  | //path     | base_url/api/path    |
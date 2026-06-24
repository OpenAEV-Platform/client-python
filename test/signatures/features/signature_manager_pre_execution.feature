Feature: SignatureManager pre-execution signature compilation
    As an injector using the OpenAEV client
    I want to compile category-specific pre-execution signatures
    So that each inject has a correct, typed signature payload before execution begins

  Background:
    Given a SignatureManager initialised with constructor SignatureManager(client, logger)

  Scenario: Network category returns required IP and timing fields and no cloud or query fields
    Given a NetworkInjectorConfig with target_ipv4="192.168.1.10"
    And the running container has a resolvable IPv4 address
    When I call build_execution_signatures with the config
    Then the returned dict contains source_ipv4 as a non-empty valid IPv4 address string
    And the returned dict contains start_time as a UTC ISO 8601 string
    And the returned dict contains target_ipv4 equal to "192.168.1.10"
    But the returned dict does not contain cloud_provider
    And the returned dict does not contain cloud_account_id
    And the returned dict does not contain cloud_region
    And the returned dict does not contain target_service
    And the returned dict does not contain query

  Scenario: Network hostname target returns hostname and no target_ipv4
    Given a NetworkInjectorConfig with target_hostname="target.example.com"
    And the running container has a resolvable IPv4 address
    When I call build_execution_signatures with the config
    Then the returned dict contains target_hostname equal to "target.example.com"
    And the returned dict contains source_ipv4 as a non-empty valid IPv4 address string
    But the returned dict does not contain target_ipv4

  Scenario: Cloud category returns required cloud identity fields and no IP fields
    Given a CloudInjectorConfig with cloud_provider="aws", cloud_account_id="123456789012", cloud_region="eu-west-1", and target_service="ec2"
    When I call build_execution_signatures with the config
    Then the returned dict contains cloud_provider equal to "aws"
    And the returned dict contains cloud_account_id equal to "123456789012"
    And the returned dict contains cloud_region equal to "eu-west-1"
    And the returned dict contains target_service equal to "ec2"
    And the returned dict contains start_time as a UTC ISO 8601 string
    But the returned dict does not contain source_ipv4
    And the returned dict does not contain source_ipv6
    And the returned dict does not contain target_ipv4
    And the returned dict does not contain target_ipv6

  Scenario Outline: Network multi-target returns one dict per target with a shared source IP
    Given a list of 3 NetworkInjectorConfig with target_ipv4 "10.0.0.1", "10.0.0.2", "10.0.0.3"
    And the running container has a resolvable IPv4 address "172.17.0.2"
    When I call build_execution_signatures with the config list
    Then the return value is a list of exactly 3 dicts
    And the dict at position <index> contains target_ipv4 equal to "<target_ip>"
    And the dict at position <index> contains source_ipv4 equal to "172.17.0.2"

    Examples:
      | index | target_ip |
      |     0 |  10.0.0.1 |
      |     1 |  10.0.0.2 |
      |     2 |  10.0.0.3 |

  Scenario: All network multi-target dicts share the same source_ipv4
    Given a list of 3 NetworkInjectorConfig built from default IPv4 targets
    And the running container has a resolvable IPv4 address
    When I call build_execution_signatures with the config list
    Then the return value is a list of 3 dicts
    And all 3 dicts contain the same source_ipv4 value

  Scenario Outline: Cloud multi-region returns one dict per region with a shared account ID
    Given a list of 3 CloudInjectorConfig with cloud_account_id="123456789012" and regions "us-east-1", "eu-west-1", "ap-southeast-1"
    When I call build_execution_signatures with the config list
    Then the return value is a list of exactly 3 dicts
    And the dict at position <index> contains cloud_region equal to "<region>"
    And the dict at position <index> contains cloud_account_id equal to "123456789012"

    Examples:
      | index | region         |
      |     0 | us-east-1      |
      |     1 | eu-west-1      |
      |     2 | ap-southeast-1 |

  Scenario: Builder classifies a mixed list of targets into typed configs
    Given a raw mixed target list "10.0.0.1", "2001:db8::1", "target.example.com"
    When I build network configs from the raw list
    Then the builder returns 3 NetworkInjectorConfig
    And the config at position 0 has target_ipv4 equal to "10.0.0.1"
    And the config at position 1 has target_ipv6 equal to "2001:db8::1"
    And the config at position 2 has target_hostname equal to "target.example.com"

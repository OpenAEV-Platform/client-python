Feature: SignatureManager pre-execution signature compilation
    As an injector using the OpenAEV client
    I want to compile category-specific pre-execution signatures
    So that each inject has a correct, typed signature payload before execution begins

    Background:
        Given a SignatureManager initialised with constructor SignatureManager(client, logger)

    Scenario: Network category returns required IP and timing fields and no cloud or query fields
        Given an inject_config with a single target asset having target_ipv4="192.168.1.10" and target_hostname="target.example.com"
        And the running container has a resolvable IPv4 address
        When I call compile_pre_execution_signatures with category="network"
        Then the returned dict contains source_ipv4 as a non-empty valid IPv4 address string
        And the returned dict contains start_time as a UTC ISO 8601 string
        And the returned dict contains target_ipv4 equal to "192.168.1.10"
        And the returned dict contains target_hostname equal to "target.example.com"
        But the returned dict does not contain cloud_provider
        And the returned dict does not contain cloud_account_id
        And the returned dict does not contain cloud_region
        And the returned dict does not contain target_service
        And the returned dict does not contain query

    Scenario: Cloud category returns required cloud identity fields and no IP fields
        Given an inject_config with cloud_provider="aws", cloud_account_id="123456789012", cloud_region="eu-west-1", and target_service="ec2"
        When I call compile_pre_execution_signatures with category="cloud"
        Then the returned dict contains cloud_provider equal to "aws"
        And the returned dict contains cloud_account_id equal to "123456789012"
        And the returned dict contains cloud_region equal to "eu-west-1"
        And the returned dict contains target_service equal to "ec2"
        And the returned dict contains start_time as a UTC ISO 8601 string
        But the returned dict does not contain source_ipv4
        And the returned dict does not contain source_ipv6
        And the returned dict does not contain target_ipv4
        And the returned dict does not contain target_ipv6

    Scenario: External category returns scan target fields and no source IP
        Given an inject_config with target_ipv4="203.0.113.5" and query="port:22 os:linux"
        When I call compile_pre_execution_signatures with category="external"
        Then the returned dict contains target_ipv4 equal to "203.0.113.5"
        And the returned dict contains query equal to "port:22 os:linux"
        And the returned dict contains start_time as a UTC ISO 8601 string
        But the returned dict does not contain source_ipv4

    Scenario Outline: Network multi-target returns one dict per target with a shared source IP
        Given an inject_config with 3 target assets having IPs "10.0.0.1", "10.0.0.2", "10.0.0.3"
        And the running container has a resolvable IPv4 address "172.17.0.2"
        When I call compile_pre_execution_signatures with category="network"
        Then the return value is a list of exactly 3 dicts
        And the dict at position <index> contains target_ipv4 equal to "<target_ip>"
        And the dict at position <index> contains source_ipv4 equal to "172.17.0.2"

        Examples:
            | index | target_ip  |
            | 0     | 10.0.0.1   |
            | 1     | 10.0.0.2   |
            | 2     | 10.0.0.3   |

    Scenario: All network multi-target dicts share the same source_ipv4
        Given an inject_config with 3 target assets and category="network"
        And the running container has a resolvable IPv4 address
        When I call compile_pre_execution_signatures with category="network"
        Then the return value is a list of 3 dicts
        And all 3 dicts contain the same source_ipv4 value

    Scenario Outline: Cloud multi-region returns one dict per region with a shared account ID
        Given an inject_config with cloud_account_id="123456789012" and 3 AWS regions "us-east-1", "eu-west-1", "ap-southeast-1"
        When I call compile_pre_execution_signatures with category="cloud"
        Then the return value is a list of exactly 3 dicts
        And the dict at position <index> contains cloud_region equal to "<region>"
        And the dict at position <index> contains cloud_account_id equal to "123456789012"

        Examples:
            | index | region          |
            | 0     | us-east-1       |
            | 1     | eu-west-1       |
            | 2     | ap-southeast-1  |


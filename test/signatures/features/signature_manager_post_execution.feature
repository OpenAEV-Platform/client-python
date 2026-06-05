Feature: SignatureManager post-execution signature compilation
    As an injector using the OpenAEV client
    I want to merge execution results into pre-execution signatures
    So that each inject has a complete signature record including outcome and timing

    Background:
        Given a SignatureManager initialised with constructor SignatureManager(client, logger)
        And a pre_signatures dict containing:
            | key             | value                    |
            | source_ipv4     | 172.17.0.2               |
            | target_ipv4     | 10.0.0.1                 |
            | target_hostname | host-a.internal          |
            | start_time      | 2024-06-26T06:00:00Z     |

    Scenario: Successful execution merges end_time and execution_status into pre-execution fields
        Given a tool_output indicating successful completion with no errors and no timeout
        When I call compile_post_execution_signatures with the pre_signatures dict and tool_output
        Then the returned dict contains every key-value pair from pre_signatures unchanged
        And the returned dict contains end_time as a UTC ISO 8601 string
        And end_time is chronologically greater than or equal to start_time "2024-06-26T06:00:00Z"
        And the returned dict contains execution_status equal to "success"


    Scenario: Multi-target pre-signatures merge into a list of post-signatures
        Given the pre_signatures is replaced by a list of 3 dicts each with a distinct target_ipv4
        And a tool_output indicating successful completion with no errors and no timeout
        When I call compile_post_execution_signatures with the pre_signatures dict and tool_output
        Then the returned value is a list of exactly 3 dicts
        And every dict in the returned list contains execution_status equal to "success"
        And every dict in the returned list contains end_time as a UTC ISO 8601 string
        And every dict in the returned list preserves its original target_ipv4 and source_ipv4 fields

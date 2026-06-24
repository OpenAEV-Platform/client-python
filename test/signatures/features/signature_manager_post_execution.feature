Feature: SignatureManager post-execution execution elements update
    As an injector using the OpenAEV client
    I want to update both execution signatures and execution details with execution results
    So that each inject has a complete execution record including outcome and timing

    Background:
        Given a SignatureManager initialised with constructor SignatureManager(client, logger)
        And a execution_signatures object containing:
            | key             | value                    |
            | source_ipv4     | 172.17.0.2               |
            | target_ipv4     | 10.0.0.1                 |
            | target_hostname | host-a.internal          |
            | start_time      | 2024-06-26T06:00:00Z     |
        And a execution_details object containing:
            | key             | value                    |
            | start_time      | 2024-06-26T06:00:00Z     |

    Scenario: Successful execution updates end_time and execution_status in execution signatures and execution details
        Given a tool_output indicating successful completion with no errors and no timeout
        When I call post_execution_updates with the execution_details, execution_signatures and tool_output
        Then the execution signature model contains every previous parameter unchanged
        And the end_time parameter in the execution signature model is a UTC ISO 8601 string
        And this end_time is chronologically greater than or equal to start_time "2024-06-26T06:00:00Z"
        And the execution details model contain every previous parameter pair unchanged
        And the end_time parameter in the execution details model is a datetime object
        And this end_time is chronologically greater than or equal to start_time "2024-06-26T06:00:00Z"
        And the execution_status parameter in the execution details model is equal to "success"
        And the execution_action parameter in the execution details model is equal to "complete"

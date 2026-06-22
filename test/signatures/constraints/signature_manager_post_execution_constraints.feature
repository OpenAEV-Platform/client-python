Feature: SignatureManager post-execution constraints
    As an injector using the OpenAEV client
    I want post-execution compilation to handle failure and timeout edge cases
    So that incomplete executions still produce valid signature records

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

    Scenario: Tool crash sets execution_status to failed and uses crash timestamp as end_time
        Given a tool_output containing error_info with exit_code=1 and crash_timestamp="2024-06-26T06:05:00Z"
	When I call post_execution_updates with the execution_details, execution_signatures and tool_output
        Then execution_status equals "failed"
        And end_time equals "2024-06-26T06:05:00Z"
	And the execution signature model contains every previous parameter unchanged
	And the execution details model contain every previous parameter pair unchanged

    Scenario: Timeout sets execution_status to timeout and includes available partial results
        Given a tool_output containing timeout_info with partial_results=["result-A", "result-B"]
	When I call post_execution_updates with the execution_details, execution_signatures and tool_output
        Then execution_status equals "timeout"
        And the returned dict contains the partial results ["result-A", "result-B"] from timeout_info
	And the execution signature model contains every previous parameter unchanged
	And the execution details model contain every previous parameter pair unchanged

    Scenario: Timeout with no partial results still sets execution_status to timeout
        Given a tool_output containing timeout_info with no partial results available
	When I call post_execution_updates with the execution_details, execution_signatures and tool_output
        Then execution_status equals "timeout"
	And the execution signature model contains every previous parameter unchanged
	And the execution details model contain every previous parameter pair unchanged

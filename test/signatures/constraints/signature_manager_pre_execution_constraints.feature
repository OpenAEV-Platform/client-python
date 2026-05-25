Feature: SignatureManager pre-execution constraints
    As an injector using the OpenAEV client
    I want pre-execution compilation to handle timing edge cases correctly
    So that signatures always reflect the actual moment of execution

    Background:
        Given a SignatureManager initialised with constructor SignatureManager(client, logger)

    Scenario: start_time is generated at method-call time not at class instantiation time
        Given a SignatureManager that was instantiated at timestamp T0
        And 5 seconds elapse after instantiation
        And an inject_config with a single network target
        When I call compile_pre_execution_signatures with category="network" at timestamp T1
        Then the start_time in the returned dict equals T1 within 1 second tolerance
        And start_time does not equal T0

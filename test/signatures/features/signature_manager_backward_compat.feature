Feature: SignatureManager backward compatibility with existing pyoaev consumers
    As a maintainer of the OpenAEV client library
    I want SignatureManager to integrate without breaking any existing code
    So that all current injectors continue to work unchanged after the merge

    Scenario: Injectors that do not call SignatureManager experience no behavioural change
        Given an injector that does not call any SignatureManager method
        When that injector executes its normal workflow
        Then its behaviour is identical to its behaviour before SignatureManager was introduced
        And no import errors, attribute errors, or unexpected exceptions occur

    Scenario: Existing public import paths in pyoaev remain unchanged
        Given the pyoaev package with SignatureManager merged
        When existing code imports InjectManager, SignatureType, SignatureTypes, SignatureMatch, or Expectation using their current import paths
        Then all imports resolve without error
        And all constructor signatures remain unchanged
        And all public method signatures remain unchanged

import unittest

from pyoaev.signatures.models import ExecutionDetails
from pyoaev.signatures.types import ExecutionStatus, InjectExecutionActions


class TestExecutionMessage(unittest.TestCase):
    def test_message_carries_the_status_on_timeout(self):
        details = ExecutionDetails(
            execution_action=InjectExecutionActions("data"),
            execution_status=ExecutionStatus.TIMEOUT,
        )
        self.assertEqual(
            details.execution_message,
            "Current action: data - Current status: TIMEOUT",
        )

    def test_message_carries_the_status_on_error(self):
        details = ExecutionDetails(
            execution_action=InjectExecutionActions("data"),
            execution_status=ExecutionStatus.ERROR,
        )
        self.assertEqual(
            details.execution_message,
            "Current action: data - Current status: ERROR",
        )

    def test_message_without_action_or_status_reads_unknown(self):
        details = ExecutionDetails()
        self.assertEqual(
            details.execution_message,
            "Current action: unknown - Current status: unknown",
        )

    def test_message_without_status_does_not_repeat_the_action(self):
        details = ExecutionDetails(execution_action=InjectExecutionActions("data"))
        self.assertEqual(
            details.execution_message,
            "Current action: data - Current status: unknown",
        )


if __name__ == "__main__":
    unittest.main()

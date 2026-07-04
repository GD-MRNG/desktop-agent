from unittest.mock import patch

from agent.approvals import request_approval


def test_request_approval_returns_true_when_confirmed():
    with patch("agent.approvals.Confirm.ask", return_value=True):
        assert request_approval("echo hello", ".") is True


def test_request_approval_returns_false_when_denied():
    with patch("agent.approvals.Confirm.ask", return_value=False):
        assert request_approval("rm -rf /", ".") is False


def test_request_approval_defaults_to_no():
    # Confirm.ask is patched with a real default=False to prove the caller
    # doesn't need to pass an explicit answer for the gate to be safe-by-default.
    with patch("agent.approvals.Confirm.ask") as mock_ask:
        mock_ask.return_value = False
        request_approval("echo hello", ".")
    _, kwargs = mock_ask.call_args
    assert kwargs.get("default") is False

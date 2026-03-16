from types import SimpleNamespace

from texase.submitted_input import (
    coerce_kvp_value,
    stop_and_notify_if_invalid_submission,
)


class DummySubmitted:
    def __init__(self, validation_result):
        self.validation_result = validation_result
        self.stopped = False

    def stop(self):
        self.stopped = True


def test_stop_and_notify_if_invalid_submission_invalid():
    submitted = DummySubmitted(
        SimpleNamespace(
            is_valid=False,
            failure_descriptions=["first error", "second error"],
        )
    )
    notifications = []

    def notify_error(message: str, title: str) -> None:
        notifications.append((message, title))

    was_stopped = stop_and_notify_if_invalid_submission(submitted, notify_error)

    assert was_stopped is True
    assert submitted.stopped is True
    assert notifications == [("first error\nsecond error", "Invalid input")]


def test_stop_and_notify_if_invalid_submission_valid():
    submitted = DummySubmitted(
        SimpleNamespace(
            is_valid=True,
            failure_descriptions=[],
        )
    )

    def notify_error(_: str, __: str) -> None:
        raise AssertionError("notify_error should not be called for valid input")

    was_stopped = stop_and_notify_if_invalid_submission(submitted, notify_error)

    assert was_stopped is False
    assert submitted.stopped is False


def test_stop_and_notify_if_invalid_submission_without_validation_result():
    submitted = DummySubmitted(None)

    def notify_error(_: str, __: str) -> None:
        raise AssertionError("notify_error should not be called when no validation result")

    was_stopped = stop_and_notify_if_invalid_submission(submitted, notify_error)

    assert was_stopped is False
    assert submitted.stopped is False


def test_coerce_kvp_value_pbc_is_uppercased():
    assert coerce_kvp_value("pbc", "tFt") == "TFT"


def test_coerce_kvp_value_converts_common_types():
    assert coerce_kvp_value("some_key", "42") == 42
    assert coerce_kvp_value("some_key", "3.14") == 3.14
    assert coerce_kvp_value("some_key", "true") is True
    assert coerce_kvp_value("some_key", "hello") == "hello"

import random
import pytest
from generator.retry import RetryError, RetryPolicy

def test_first_attempt_success_without_sleep() -> None:
    pauses: list[float] = []
    policy = RetryPolicy(
        max_attempts=3,
        base_delay=1.0,
        max_delay=10.0,
        jitter=0.0,
        sleep=pauses.append,
    )
    result = policy.execute(lambda: "success")
    assert result == "success"
    assert pauses == []

def test_retry_until_success() -> None:
    pauses: list[float] = []
    calls = 0
    def unstable_function() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ValueError("Temporary error")
        return "success"
    policy = RetryPolicy(
        max_attempts=3,
        base_delay=1.0,
        max_delay=10.0,
        jitter=0.0,
        sleep=pauses.append,
    )
    result = policy.execute(unstable_function)
    assert result == "success"
    assert calls == 3
    assert pauses == [1.0, 2.0]

def test_all_attempts_failed() -> None:
    pauses: list[float] = []
    def failing_function() -> None:
        raise ValueError("Original error")
    policy = RetryPolicy(
        max_attempts=3,
        base_delay=1.0,
        max_delay=10.0,
        jitter=0.0,
        sleep=pauses.append,
    )
    with pytest.raises(RetryError) as exc_info:
        policy.execute(failing_function)
    assert isinstance(exc_info.value.__cause__, ValueError)
    assert str(exc_info.value.__cause__) == "Original error"
    assert pauses == [1.0, 2.0]

def test_exponential_backoff_delays() -> None:
    pauses: list[float] = []
    def failing_function() -> None:
        raise ValueError("Error")
    policy = RetryPolicy(
        max_attempts=4,
        base_delay=1.0,
        max_delay=10.0,
        backoff_factor=2.0,
        jitter=0.0,
        sleep=pauses.append,
    )
    with pytest.raises(RetryError):
        policy.execute(failing_function)
    assert pauses == [1.0, 2.0, 4.0]

def test_delay_does_not_exceed_max_delay() -> None:
    pauses: list[float] = []
    def failing_function() -> None:
        raise ValueError("Error")
    policy = RetryPolicy(
        max_attempts=5,
        base_delay=1.0,
        max_delay=3.0,
        backoff_factor=2.0,
        jitter=0.0,
        sleep=pauses.append,
    )
    with pytest.raises(RetryError):
        policy.execute(failing_function)
    assert pauses == [1.0, 2.0, 3.0, 3.0]

def test_jitter_stays_within_expected_range() -> None:
    pauses: list[float] = []
    def failing_function() -> None:
        raise ValueError("Error")
    policy = RetryPolicy(
        max_attempts=2,
        base_delay=1.0,
        max_delay=10.0,
        jitter=0.1,
        sleep=pauses.append,
        rng=random.Random(42),
    )
    for _ in range(200):
        with pytest.raises(RetryError):
            policy.execute(failing_function)
    assert len(pauses) == 200
    assert all(0.9 <= delay <= 1.1 for delay in pauses)


def test_non_retryable_exception_propagates_immediately() -> None:
    pauses: list[float] = []
    calls = 0
    def failing_function() -> None:
        nonlocal calls
        calls += 1
        raise TypeError("Non-retryable error")
    policy = RetryPolicy(
        max_attempts=3,
        base_delay=1.0,
        max_delay=10.0,
        jitter=0.0,
        retry_on=(ValueError,),
        sleep=pauses.append,
    )
    with pytest.raises(TypeError, match="Non-retryable error"):
        policy.execute(failing_function)
    assert calls == 1
    assert pauses == []

def test_one_attempt_without_sleep() -> None:
    pauses: list[float] = []
    calls = 0
    def failing_function() -> None:
        nonlocal calls
        calls += 1
        raise ValueError("Error")
    policy = RetryPolicy(
        max_attempts=1,
        base_delay=1.0,
        max_delay=10.0,
        jitter=0.0,
        sleep=pauses.append,
    )
    with pytest.raises(RetryError):
        policy.execute(failing_function)
    assert calls == 1
    assert pauses == []

@pytest.mark.parametrize(
    ("kwargs", "error_message"),
    [
        ({"max_attempts": 0}, "max_attempts"),
        ({"base_delay": -1.0}, "base_delay"),
        ({"max_delay": 0.5}, "max_delay"),
        ({"backoff_factor": 0.5}, "backoff_factor"),
        ({"jitter": -0.1}, "jitter"),
        ({"jitter": 1.0}, "jitter"),
    ],
)

def test_invalid_parameters(
    kwargs: dict[str, object],
    error_message: str,
) -> None:
    params: dict[str, object] = {
        "max_attempts": 3,
        "base_delay": 1.0,
        "max_delay": 10.0,
    }
    params.update(kwargs)
    with pytest.raises(ValueError, match=error_message):
        RetryPolicy(**params)  # type: ignore[arg-type]

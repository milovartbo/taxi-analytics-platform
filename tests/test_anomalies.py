import random
import pytest

from generator.generation.anomalies import AnomalyPolicy, AnomalyKind

def test_probability_zero():
    policy = AnomalyPolicy(
        probability=0,
        strength=1.0,
        rng=random.Random(42)
    )
    assert policy.decide() is None

def test_probability_one():
    policy = AnomalyPolicy(
        probability=1,
        strength=1.0,
        rng=random.Random(42)
    )
    result = policy.decide()
    assert result is not None
    assert result in AnomalyKind

def test_all_anomaly_kinds():
    policy = AnomalyPolicy(
        probability=1,
        strength=1.0,
        rng=random.Random(42)
    )
    found = set()
    for _ in range(100):
        result=policy.decide()
        found.add(result)
    assert found == set(AnomalyKind)

def test_probability_distribution():
    policy = AnomalyPolicy(
        probability=0.05,
        strength=1.0,
        rng=random.Random(42)
    )
    anomalies_count=0
    for _ in range(20000):
        if policy.decide() is not None:
            anomalies_count+=1
    percentage = anomalies_count / 20000
    assert 0.04 <= percentage <= 0.06

def test_same_speed():
    policy1 = AnomalyPolicy(0.5, 1.0, random.Random(42))
    policy2 = AnomalyPolicy(0.5, 1.0, random.Random(42))
    results1 = [policy1.decide() for _ in range(20)]
    results2 = [policy2.decide() for _ in range(20)]
    assert results1 == results2

def test_strength_zero():
    with pytest.raises(ValueError):
        policy = AnomalyPolicy(
            probability=0,
            strength=0.0,
            rng=random.Random(42)
        )

def test_strength_property():
    policy = AnomalyPolicy(
        probability=0.5,
        strength=3.5,
        rng=random.Random(42)
    )
    assert policy.strength == 3.5
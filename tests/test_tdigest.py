import bisect
import json
import math
import random

import pytest

from tdigest import TDigest


def exact_quantile(sorted_data, q):
    idx = q * (len(sorted_data) - 1)
    lo = int(math.floor(idx))
    hi = min(lo + 1, len(sorted_data) - 1)
    return sorted_data[lo] + (sorted_data[hi] - sorted_data[lo]) * (idx - lo)


def test_empty():
    d = TDigest()
    assert math.isnan(d.quantile(0.5))
    assert math.isnan(d.cdf(0))
    assert math.isnan(d.min)
    assert d.count == 0
    assert len(d) == 0


def test_single_value():
    d = TDigest()
    d.update(42)
    for q in (0, 0.25, 0.5, 1):
        assert d.quantile(q) == 42
    assert d.cdf(41) == 0
    assert d.cdf(43) == 1


def test_small_exact():
    d = TDigest()
    d.batch_update([1, 2, 3, 4, 5])
    assert d.quantile(0) == 1
    assert d.quantile(1) == 5
    assert d.quantile(0.5) == 3


@pytest.mark.parametrize(
    "gen",
    [
        lambda r: r.random(),
        lambda r: r.gauss(0, 1),
        lambda r: r.expovariate(1.0),
        lambda r: r.lognormvariate(0, 1),
    ],
)
def test_quantile_accuracy(gen):
    r = random.Random(1234)
    data = [gen(r) for _ in range(100_000)]
    d = TDigest(compression=200)
    d.batch_update(data)
    data.sort()
    for q in (0.001, 0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99, 0.999):
        est = d.quantile(q)
        # Compare in rank space: the true rank of the estimate should be close to q,
        # with tighter bounds in the tails.
        actual_rank = bisect.bisect_left(data, est) / len(data)
        tolerance = 0.002 + 0.01 * min(q, 1 - q)
        assert abs(actual_rank - q) < tolerance, (q, est, exact_quantile(data, q))


def test_extremes_match_min_max():
    r = random.Random(7)
    d = TDigest()
    data = [r.gauss(10, 3) for _ in range(10_000)]
    d.batch_update(data)
    assert d.quantile(0) == min(data)
    assert d.quantile(1) == max(data)
    assert d.min == min(data)
    assert d.max == max(data)


def test_centroid_count_bounded():
    d = TDigest(compression=100)
    r = random.Random(0)
    d.batch_update(r.random() for _ in range(200_000))
    assert len(d) <= 100


def test_cdf_monotonic_and_inverse():
    r = random.Random(3)
    d = TDigest(compression=200)
    d.batch_update(r.gauss(0, 1) for _ in range(50_000))
    xs = [x / 10 for x in range(-40, 41)]
    cdfs = [d.cdf(x) for x in xs]
    assert all(a <= b for a, b in zip(cdfs, cdfs[1:]))
    for q in (0.05, 0.5, 0.95):
        assert abs(d.cdf(d.quantile(q)) - q) < 0.01


def test_quantile_monotonic():
    r = random.Random(5)
    d = TDigest()
    d.batch_update(r.expovariate(2) for _ in range(20_000))
    qs = [i / 1000 for i in range(1001)]
    vals = d.quantiles(qs)
    assert all(a <= b for a, b in zip(vals, vals[1:]))


def test_merge_matches_single():
    r = random.Random(11)
    data = [r.gauss(0, 1) for _ in range(40_000)]
    parts = [TDigest(200) for _ in range(4)]
    for i, x in enumerate(data):
        parts[i % 4].update(x)
    merged = TDigest(200)
    for p in parts:
        merged.merge(p)
    single = TDigest(200)
    single.batch_update(data)
    assert merged.count == single.count == len(data)
    for q in (0.01, 0.5, 0.99):
        assert abs(merged.quantile(q) - single.quantile(q)) < 0.05


def test_add_operator():
    a, b = TDigest(), TDigest()
    a.batch_update(range(0, 500))
    b.batch_update(range(500, 1000))
    c = a + b
    assert c.count == 1000
    assert c.min == 0 and c.max == 999
    assert abs(c.quantile(0.5) - 499.5) < 5


def test_weighted_updates():
    d = TDigest()
    d.update(1, w=9)
    d.update(100, w=1)
    assert d.count == 10
    assert d.quantile(0.5) < 50


def test_serialization_roundtrip():
    r = random.Random(9)
    d = TDigest(150)
    d.batch_update(r.random() for _ in range(10_000))
    blob = json.dumps(d.to_dict())
    d2 = TDigest.from_dict(json.loads(blob))
    assert d2.count == d.count
    for q in (0, 0.1, 0.5, 0.9, 1):
        assert d2.quantile(q) == pytest.approx(d.quantile(q))


def test_trimmed_mean():
    d = TDigest()
    d.batch_update(range(1, 1001))
    assert d.trimmed_mean(0, 1) == pytest.approx(500.5, rel=1e-6)
    assert d.trimmed_mean(0.25, 0.75) == pytest.approx(500.5, rel=0.01)


def test_invalid_inputs():
    d = TDigest()
    with pytest.raises(ValueError):
        d.update(float("nan"))
    with pytest.raises(ValueError):
        d.update(1, w=0)
    d.update(1)
    with pytest.raises(ValueError):
        d.quantile(1.5)
    with pytest.raises(ValueError):
        TDigest(compression=1)

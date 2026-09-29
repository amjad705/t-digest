# t-digest

A dependency-free Python implementation of the **merging t-digest** from
Dunning & Ertl, [*Computing Extremely Accurate Quantiles Using t-Digests*](https://arxiv.org/abs/1902.04023).

A t-digest summarises a stream of numbers with a small, bounded set of weighted
centroids. Centroids near the tails are kept tiny, so extreme quantiles (p99,
p99.9) stay accurate, and digests built on separate machines can be merged.

## Install

```bash
pip install .
```

## Usage

```python
from tdigest import TDigest

d = TDigest(compression=100)      # higher = more accurate, more memory
for latency_ms in stream:
    d.update(latency_ms)          # or d.update(x, w=weight)

d.quantile(0.99)                  # p99
d.percentile(50)                  # median
d.cdf(250)                        # fraction of values <= 250
d.trimmed_mean(0.05, 0.95)

# Merge digests (e.g. one per shard)
total = shard_a + shard_b         # new digest
shard_a.merge(shard_b)            # in place

# Serialise
import json
blob = json.dumps(d.to_dict())
d2 = TDigest.from_dict(json.loads(blob))
```

## API

| Method | Description |
| --- | --- |
| `update(x, w=1)` / `add` | Add a value with an optional positive weight |
| `batch_update(iterable, w=1)` | Add many values |
| `merge(other)` / `a + b` | Combine digests |
| `quantile(q)` / `percentile(p)` / `quantiles(qs)` | Value at quantile `q` in [0, 1] |
| `cdf(x)` | Estimated fraction of values <= `x` |
| `trimmed_mean(lo, hi)` | Mean of values between two quantiles |
| `count`, `min`, `max`, `len(d)` | Total weight, exact extremes, number of centroids |
| `centroids()` | Iterate `(mean, weight)` pairs |
| `to_dict()` / `from_dict()` | JSON-friendly serialisation |

## How it works

Incoming points go into a buffer. When the buffer fills (or on query), it is
sorted together with the existing centroids and merged greedily. A centroid may
grow only while it spans at most one unit of the k1 scale function

    k(q) = δ / (2π) · asin(2q − 1)

which forces small centroids near q = 0 and q = 1. Quantiles and the CDF
interpolate linearly between centroid centres, using the exact min and max at
the ends and treating single-point centroids as exact values.

On 1M lognormal samples with `compression=100` it keeps about 60 centroids,
ingests about 1.7M points/s in CPython, and has a rank error of about 1e-6 at
p0.1 and under 0.1% at the median.

## Tests

```bash
pip install pytest
python -m pytest
```

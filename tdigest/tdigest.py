"""A merging t-digest for streaming quantile estimation.

The t-digest (Dunning & Ertl, "Computing Extremely Accurate Quantiles Using
t-Digests") summarises a distribution with a small, bounded set of weighted
centroids. Centroids near the tails are kept small, so extreme quantiles
(p99, p99.9, ...) stay accurate while the middle is compressed harder.

This implementation follows the "merging" variant: incoming points are
buffered and periodically sorted and merged into the centroid list using the
k1 (arcsine) scale function.
"""

from __future__ import annotations

import math
from typing import Iterable, Iterator, List, Optional, Tuple

__all__ = ["TDigest", "Centroid"]

Centroid = Tuple[float, float]  # (mean, weight)


class TDigest:
    """Streaming quantile sketch.

    Args:
        compression: The delta parameter. Higher values keep more centroids
            and give more accurate results at the cost of memory. The number
            of retained centroids is bounded by roughly ``compression``.
            Typical values are 100 to 500.
    """

    def __init__(self, compression: float = 100.0) -> None:
        if compression < 10:
            raise ValueError("compression must be >= 10")
        self.compression = float(compression)
        self._means: List[float] = []
        self._weights: List[float] = []
        self._buffer: List[Centroid] = []
        self._buffer_limit = int(5 * compression)
        self._total = 0.0
        self._min = math.inf
        self._max = -math.inf

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def update(self, x: float, w: float = 1.0) -> None:
        """Add a value ``x`` with weight ``w``."""
        x = float(x)
        if math.isnan(x):
            raise ValueError("cannot add NaN to a t-digest")
        if w <= 0:
            raise ValueError("weight must be positive")
        self._buffer.append((x, float(w)))
        self._total += w
        if x < self._min:
            self._min = x
        if x > self._max:
            self._max = x
        if len(self._buffer) >= self._buffer_limit:
            self._compress()

    add = update

    def batch_update(self, values: Iterable[float], w: float = 1.0) -> None:
        """Add every value in ``values`` with the same weight ``w``."""
        for x in values:
            self.update(x, w)

    def merge(self, other: "TDigest") -> "TDigest":
        """Fold another digest into this one in place and return ``self``."""
        if other._total == 0:
            return self
        for m, w in other.centroids():
            self._buffer.append((m, w))
        self._total += other._total
        self._min = min(self._min, other._min)
        self._max = max(self._max, other._max)
        self._compress()
        return self

    def __add__(self, other: "TDigest") -> "TDigest":
        result = TDigest(max(self.compression, other.compression))
        result.merge(self)
        result.merge(other)
        return result

    # ------------------------------------------------------------------
    # Compression
    # ------------------------------------------------------------------

    def _k(self, q: float) -> float:
        return self.compression / (2 * math.pi) * math.asin(2 * q - 1)

    def _q_limit(self, q: float) -> float:
        """Largest quantile a centroid starting at ``q`` may extend to."""
        k = self._k(q) + 1
        if k >= self.compression / 4:
            return 1.0
        return (math.sin(k * 2 * math.pi / self.compression) + 1) / 2

    def _compress(self) -> None:
        if not self._buffer:
            return
        points = list(zip(self._means, self._weights))
        points.extend(self._buffer)
        self._buffer = []
        points.sort(key=lambda c: c[0])

        total = self._total
        means: List[float] = []
        weights: List[float] = []

        cur_mean, cur_w = points[0]
        w_so_far = 0.0
        q_limit = self._q_limit(0.0)
        for m, w in points[1:]:
            if (w_so_far + cur_w + w) / total <= q_limit:
                cur_w += w
                cur_mean += (m - cur_mean) * w / cur_w
            else:
                means.append(cur_mean)
                weights.append(cur_w)
                w_so_far += cur_w
                q_limit = self._q_limit(w_so_far / total)
                cur_mean, cur_w = m, w
        means.append(cur_mean)
        weights.append(cur_w)

        self._means = means
        self._weights = weights

    def compress(self) -> None:
        """Flush buffered points into the centroid list."""
        self._compress()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @property
    def count(self) -> float:
        """Total weight of all values added."""
        return self._total

    def __len__(self) -> int:
        self._compress()
        return len(self._means)

    @property
    def min(self) -> float:
        return self._min if self._total else math.nan

    @property
    def max(self) -> float:
        return self._max if self._total else math.nan

    def centroids(self) -> Iterator[Centroid]:
        """Yield ``(mean, weight)`` pairs in ascending order of mean."""
        self._compress()
        return iter(zip(self._means, self._weights))

    def quantile(self, q: float) -> float:
        """Estimate the value at quantile ``q`` (0 <= q <= 1)."""
        if not 0 <= q <= 1:
            raise ValueError("q must be in [0, 1]")
        self._compress()
        means, weights = self._means, self._weights
        n = len(means)
        if n == 0:
            return math.nan
        if n == 1:
            return means[0]

        total = self._total
        index = q * total

        # Left tail: interpolate between min and the first centroid.
        if index < 1:
            return self._min
        if weights[0] > 1 and index < weights[0] / 2:
            return self._min + (index - 1) / (weights[0] / 2 - 1) * (means[0] - self._min)

        # Right tail: interpolate between the last centroid and max.
        if index > total - 1:
            return self._max
        if weights[-1] > 1 and total - index <= weights[-1] / 2:
            return self._max - (total - index - 1) / (weights[-1] / 2 - 1) * (self._max - means[-1])

        w_so_far = weights[0] / 2
        for i in range(n - 1):
            dw = (weights[i] + weights[i + 1]) / 2
            if w_so_far + dw > index:
                left_unit = 0.0
                if weights[i] == 1:
                    if index - w_so_far < 0.5:
                        return means[i]
                    left_unit = 0.5
                right_unit = 0.0
                if weights[i + 1] == 1:
                    if w_so_far + dw - index <= 0.5:
                        return means[i + 1]
                    right_unit = 0.5
                z1 = index - w_so_far - left_unit
                z2 = w_so_far + dw - index - right_unit
                return _weighted_average(means[i], z2, means[i + 1], z1)
            w_so_far += dw

        # Between the last centroid's centre and max.
        z1 = index - w_so_far
        z2 = total - index
        return _weighted_average(means[-1], z2, self._max, z1)

    def percentile(self, p: float) -> float:
        """Estimate the value at percentile ``p`` (0 <= p <= 100)."""
        return self.quantile(p / 100.0)

    def quantiles(self, qs: Iterable[float]) -> List[float]:
        return [self.quantile(q) for q in qs]

    def cdf(self, x: float) -> float:
        """Estimate the fraction of values that are <= ``x``."""
        self._compress()
        means, weights = self._means, self._weights
        n = len(means)
        if n == 0:
            return math.nan
        if x < self._min:
            return 0.0
        if x > self._max:
            return 1.0
        if n == 1:
            span = self._max - self._min
            return 0.5 if span <= 0 else (x - self._min) / span

        total = self._total

        if x < means[0]:
            if means[0] - self._min > 0:
                if x == self._min:
                    return 0.5 / total
                return (1 + (x - self._min) / (means[0] - self._min) * (weights[0] / 2 - 1)) / total
            return 0.0

        if x > means[-1]:
            if self._max - means[-1] > 0:
                if x == self._max:
                    return 1 - 0.5 / total
                dq = (1 + (self._max - x) / (self._max - means[-1]) * (weights[-1] / 2 - 1)) / total
                return 1 - dq
            return 1.0

        w_so_far = 0.0
        i = 0
        while i < n - 1:
            if means[i] == x:
                dw = 0.0
                while i < n and means[i] == x:
                    dw += weights[i]
                    i += 1
                return (w_so_far + dw / 2) / total
            if means[i] <= x < means[i + 1]:
                dw = (weights[i] + weights[i + 1]) / 2
                if means[i + 1] - means[i] <= 0:
                    return (w_so_far + dw) / total
                left_excluded = right_excluded = 0.0
                if weights[i] == 1:
                    if weights[i + 1] == 1:
                        return (w_so_far + 1) / total
                    left_excluded = 0.5
                elif weights[i + 1] == 1:
                    right_excluded = 0.5
                base = w_so_far + weights[i] / 2 + left_excluded
                frac = (x - means[i]) / (means[i + 1] - means[i])
                return (base + (dw - left_excluded - right_excluded) * frac) / total
            w_so_far += weights[i]
            i += 1

        # x == means[-1]
        return 1 - weights[-1] / 2 / total

    def trimmed_mean(self, lo: float, hi: float) -> float:
        """Mean of values between quantiles ``lo`` and ``hi``."""
        if not 0 <= lo < hi <= 1:
            raise ValueError("need 0 <= lo < hi <= 1")
        self._compress()
        if not self._means:
            return math.nan
        lo_w, hi_w = lo * self._total, hi * self._total
        acc = acc_w = w_so_far = 0.0
        for m, w in zip(self._means, self._weights):
            start, end = w_so_far, w_so_far + w
            overlap = min(end, hi_w) - max(start, lo_w)
            if overlap > 0:
                acc += m * overlap
                acc_w += overlap
            w_so_far = end
        return acc / acc_w if acc_w else math.nan

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        self._compress()
        return {
            "compression": self.compression,
            "min": self._min if self._total else None,
            "max": self._max if self._total else None,
            "centroids": [[m, w] for m, w in zip(self._means, self._weights)],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TDigest":
        digest = cls(data["compression"])
        centroids = data.get("centroids", [])
        digest._means = [float(m) for m, _ in centroids]
        digest._weights = [float(w) for _, w in centroids]
        digest._total = sum(digest._weights)
        if digest._total:
            digest._min = float(data["min"])
            digest._max = float(data["max"])
        return digest

    def __repr__(self) -> str:
        return (
            f"TDigest(compression={self.compression:g}, count={self._total:g}, "
            f"centroids={len(self)})"
        )


def _weighted_average(x1: float, w1: float, x2: float, w2: float) -> float:
    lo, hi = (x1, x2) if x1 <= x2 else (x2, x1)
    value = (x1 * w1 + x2 * w2) / (w1 + w2)
    return max(lo, min(value, hi))

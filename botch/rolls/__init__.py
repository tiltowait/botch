"""Handle rolls for both game lines."""

from numpy.random import default_rng

from botch.rolls import parse
from botch.rolls.roll import Roll

_rng = default_rng()  # numpy's default RNG is PCG64 (superior to builtin)


def d10(count: int | None = None) -> int | list[int]:
    """Roll one or many d10s."""
    if count is None:
        return int(_rng.integers(1, 11))
    return list(map(int, _rng.integers(1, 11, count)))

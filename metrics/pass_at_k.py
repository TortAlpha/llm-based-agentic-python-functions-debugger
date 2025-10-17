import math
from typing import List, Dict, Any

def estimate_pass_at_k(
        samples: Dict[str, Any],
        k: int
) -> float:
    """
    Estimates pass@k of each problem and returns the average.

    Args:
        samples: Dict of states
        k: k in pass@k

    Returns:
        Average pass@k score
    """

    def estimator(n: int, c: int) -> float:
        if n - c < k:
            return 1.0
        return 1.0 - math.comb(n - c, k) / math.comb(n, k)

    return sum(estimator(n, c) for n, c in zip(num_samples, num_correct)) / len(num_samples)

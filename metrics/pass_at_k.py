from typing import List, Dict, Any

def estimate_pass_at_1(results: List[Dict[str, Any]]) -> float:
    """
    Calculate pass@1 metric: probability that code passes in a single attempt.

    pass@1 = (number of problems solved) / (total number of problems)

    A problem is considered solved if is_fixed=True, regardless of
    how many iterations or submissions it took.
    """
    if not results:
        return 0.0

    solved = sum(1 for result in results if result.get("is_fixed", False))
    total = len(results)

    return solved / total


# my interest
def estimate_first_submission_accuracy(results: List[Dict[str, Any]]) -> float:
    """
    Calculate first-submission accuracy: probability that the FIRST
    code submission passes tests.

    This is a stricter metric than pass@1.
    """
    if not results:
        return 0.0

    first_passed = sum(1 for result in results if result.get("first_pass", False))
    total = len(results)

    return first_passed / total
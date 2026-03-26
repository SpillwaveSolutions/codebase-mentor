"""Sample project: minimal Python for codebase-wizard testing."""


def calculate(a: int, b: int) -> dict:
    """Compute sum, difference, and product of two integers.

    Returns a dict with keys 'sum', 'diff', 'product'.
    """
    return {"sum": a + b, "diff": a - b, "product": a * b}

from kork.ast_printer import AstPrinter
from kork.examples import c_, format_examples, r_


def add_(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y


def test_format_examples() -> None:
    """Test format examples."""
    examples = [
        (
            "Add 1 and 2",
            r_(c_(add_, 1, 2)),
        ),
    ]

    formatted_examples = format_examples(
        language_name="meow",
        examples=examples,
        ast_printer=AstPrinter(),
    )

    assert formatted_examples == [
        (
            "Add 1 and 2",
            "<code>var result = add_(1, 2)</code>",
        ),
    ]

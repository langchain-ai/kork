"""Interface to specify kork examples easily."""
import abc
from typing import Any, Callable, List, Literal, Sequence, Tuple, Union

from kork import ast
from kork.ast_printer import AbstractAstPrinter
from kork.foreign_funcs import to_kork_function_call
from kork.utils import wrap_in_tag


def _add_result_variable(expr: ast.Expr) -> ast.Program:
    """Assembles a solution from a program."""
    stmt = ast.VarDecl(name="result", value=expr)
    return ast.Program(stmts=[stmt])


# PUBLIC API

# Use to denote different types of formatters for the input.
InputFormatter = Union[
    Literal["text_prefix"],
    Literal["triple_quotes"],
    Literal["markdown_text"],
    None,
    Callable[[str], str],
]


def format_text(text: str, input_formatter: InputFormatter = None) -> str:
    """An encoder for the input text.

    Args:
        text: the text to encode
        input_formatter: the formatter to use for the input
            * None: use for single sentences or single paragraphs, no formatting
            * triple_quotes: surround input with \"\"\", use for long text
            * text_prefix: same as triple_quote but with `TEXT: ` prefix
            * Callable: user provided function

    Returns:
        The encoded text if it was encoded
    """
    if input_formatter == "text_prefix":
        return 'Text: """\n' + text + '\n"""'
    elif input_formatter == "triple_quotes":
        return '"""\n' + text + '\n"""'
    elif input_formatter == "markdown_text":
        return "```text\n" + text + "\n```"
    elif input_formatter is None:
        return text
    else:
        raise NotImplementedError(
            f'No support for input encoding "{input_formatter}". '
            ' Use one of "long_text" or None.'
        )


# Alias to create a kork function call
def c_(name: Callable, *args: Any) -> ast.FunctionCall:
    """Create a kork function call."""
    return to_kork_function_call(name, *args)


# Alias to assign the expression to a variable called `result`
def r_(expr: ast.Expr) -> ast.Program:
    """Assign last program expression to a result variable."""
    return _add_result_variable(expr)


def format_examples(
    language_name: str,
    examples: Sequence[Tuple[str, ast.Program]],
    ast_printer: AbstractAstPrinter,
    input_formatter: InputFormatter = None,
) -> List[Tuple[str, str]]:
    """Format examples."""
    formatted_examples = []
    for example_input, desired_output in examples:
        formatted_input = format_text(example_input, input_formatter=input_formatter)
        formatted_examples.append(
            (
                formatted_input,
                wrap_in_tag("code", ast_printer.visit(desired_output)),
            )
        )

    return formatted_examples


class AbstractExampleRetriever(abc.ABC):
    """Abstract interface for an example retriever.

    An example interface must implement the `retrieve` method which
    returns a list of relevant examples based on the given query.
    """

    @abc.abstractmethod
    def retrieve(self, query: str) -> List[Tuple[str, str]]:
        """Retrieve examples."""


class SimpleExampleRetriever(AbstractExampleRetriever):
    """Simple example retriever.

    Simple example that returns the examples it was initialized with.

    Supports initialization from a list of programs.

    Example:

    .. code-block:: python

        from kork import SimpleExampleRetriever, AstPrinter, c_, r_

        simple_example_retriever = SimpleExampleRetriever.from_programs(
            language_name="kork",
            examples=[
                ("add 1 2", r_(c_(add, 1, 2))),
                ("add 1 2 3", r_(c_(add, 1, 2, 3))),
                ],
            ast_printer=AstPrinter(),
        )

        examples = simple_example_retriever.retrieve("add 1 2")
    """

    def __init__(
        self,
        examples: Sequence[Tuple[str, str]],
    ) -> None:
        """Initialize the retriever with a list of examples."""
        self._examples = examples

    def retrieve(self, query: str) -> List[Tuple[str, str]]:
        """Retrieve examples that best match the given query."""
        return list(self._examples)

    @classmethod
    def from_programs(
        cls,
        language_name: str,
        examples: Sequence[Tuple[str, ast.Program]],
        ast_printer: AbstractAstPrinter,
    ) -> "SimpleExampleRetriever":
        """Create a simple example retriever from programs.

        Args:
            language_name: The language name to use for the markdown code blocks.
            examples: A sequence of tuples of the form (query, desired program).
            ast_printer: The ast printer to use to format the desired output.

        Returns:
            A simple example retriever.
        """
        return cls(
            examples=format_examples(
                language_name=language_name,
                examples=examples,
                ast_printer=ast_printer,
            )
        )

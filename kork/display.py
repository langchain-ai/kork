"""Utils for displaying chain results in a notebook."""
import math
from html import escape
from typing import Any, Optional, Sequence, TypedDict, Union

from kork.chain import CodeResult


class HtmlResult(TypedDict):
    """A result that can be displayed in a notebook."""

    query: str
    errors: str
    raw: str
    code: str
    result: str
    expected: str
    correct: str


def as_html_dict(
    code_result: CodeResult,
    query: Optional[str] = None,
    expected_answer: Optional[Any] = None,
) -> HtmlResult:
    """Use to generate a dict that can be easily displayed in an IPython notebook."""
    from IPython.display import Code

    code = code_result["code"].strip()

    if code:
        _code = Code(data=code)._repr_html_().strip().replace("\n", "<br/>")
    else:
        _code = code

    env = code_result["environment"]

    result = env.variables.get("result", "") if env else ""

    if isinstance(expected_answer, (float, int)) and isinstance(result, (float, int)):
        correct = math.isclose(expected_answer, result)
    else:
        correct = bool(expected_answer == result)

    query = query or code_result.get("query", "")  # type: ignore

    return {
        "query": escape(str(query)),
        "errors": escape(str(code_result["errors"])),
        "raw": escape(str(code_result["raw"])).replace("\n", "<br/>"),
        "code": _code,
        "result": escape(str(result).strip()),
        "expected": escape(str(expected_answer)),
        "correct": "✅" if correct else "⛔",
    }


def display_html_results(
    html_results: Union[Sequence[HtmlResult], HtmlResult],
    columns: Optional[Sequence[str]] = None,
) -> Any:
    """Display a sequence of HTML results as a table."""
    import pandas as pd
    from IPython import display

    _results = html_results if isinstance(html_results, list) else [html_results]

    _columns = (
        columns
        if columns
        else ["query", "code", "result", "expected", "correct", "errors", "raw"]
    )

    df = pd.DataFrame(_results, columns=_columns)
    if "query" in df.columns:
        df["query"] = df["query"].str.wrap(30)
        df["query"] = df["query"].str.replace("\n", "<br/>")
    df = df.style.set_properties(**{"text-align": "left"})
    return display.HTML(df.to_html(escape=False))


def display_code_result(
    code_result: CodeResult,
    query: Optional[str] = None,
    expected_answer: Optional[Any] = None,
    columns: Optional[Sequence[str]] = None,
) -> Any:
    """Display a code result as a table."""
    return display_html_results(
        as_html_dict(code_result, query=query, expected_answer=expected_answer),
        columns=columns,
    )

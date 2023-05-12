"""Utils for displaying chain results in a notebook."""
import base64
import math
from html import escape
from io import BytesIO
from typing import Any, Optional, Sequence, TypedDict, Union

from kork.ast_printer import AstPrinter
from kork.chain import CodeResult
from kork.parser import parse

try:
    from PIL.Image import Image
except ImportError:
    Image = None


def image_base64(image: Image) -> str:
    """Get a base64 representation of an image."""
    with BytesIO() as buffer:
        image.save(buffer, "jpeg")
        return base64.b64encode(buffer.getvalue()).decode()


def as_img_tag(image: Image) -> str:
    """Get an HTML representation of an image."""
    return f'<img src="data:image/jpeg;base64,{image_base64(image)}">'


class HtmlResult(TypedDict):
    """A result that can be displayed in a notebook."""

    query: str
    errors: str
    raw: str
    code: str
    result: str
    expected: str
    correct: str


class _NoExpectedAnswer:
    """A sentinel class to indicate that there is no expected answer."""

    pass


NO_EXPECTED_ANSWER = _NoExpectedAnswer()


def as_html_dict(
    code_result: CodeResult,
    query: Optional[str] = None,
    expected_answer: Optional[Any] = None,
    result_key: str = "result",
    pretty_print: bool = True,
) -> HtmlResult:
    """Use to generate a dict that can be easily displayed in an IPython notebook."""
    from IPython import display as ipy_display

    code = code_result["code"].strip()

    if pretty_print:
        code = AstPrinter().visit(parse(code), pretty_print=True)
    else:
        code = code

    if code:
        _code = ipy_display.Code(data=code)._repr_html_().strip().replace("\n", "<br/>")
    else:
        _code = code

    env = code_result["environment"]

    result = env.variables.get(result_key, "") if env else ""

    if expected_answer is NO_EXPECTED_ANSWER:
        _correct = "N/A"
    else:
        if isinstance(expected_answer, (float, int)) and isinstance(
            result, (float, int)
        ):
            correct = math.isclose(expected_answer, result)
        else:
            correct = bool(expected_answer == result)
        _correct = "✅" if correct else "⛔"

    query = query or code_result.get("query", "")  # type: ignore

    if Image and isinstance(result, Image):
        _result = as_img_tag(result)
    else:
        _result = escape(str(result).strip())

    _expected = (
        "" if expected_answer is NO_EXPECTED_ANSWER else escape(str(expected_answer))
    )

    return {
        "query": escape(str(query)),
        "errors": escape(str(code_result["errors"])),
        "raw": escape(str(code_result["raw"])).replace("\n", "<br/>"),
        "code": _code,
        "result": _result,
        "expected": _expected,
        "correct": _correct,
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
        df["query"] = df["query"].str.wrap(40)
        df["query"] = df["query"].str.replace("\n", "<br/>")
    df = df.style.set_properties(**{"text-align": "left"})
    return display.HTML(df.to_html(escape=False, index=False))


def display_code_result(
    code_result: CodeResult,
    query: Optional[str] = None,
    expected_answer: Optional[Any] = NO_EXPECTED_ANSWER,
    columns: Optional[Sequence[str]] = None,
    result_key: str = "result",
) -> Any:
    """Display a code result as a table."""
    return display_html_results(
        as_html_dict(
            code_result,
            query=query,
            expected_answer=expected_answer,
            result_key=result_key,
        ),
        columns=columns,
    )

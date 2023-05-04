"""API to import foreign functions."""
import inspect
import sys
import types
import typing
from typing import Any, Callable, List, Mapping, Tuple, TypedDict

from kork import ast

PY_VERSION = (sys.version_info.major, sys.version_info.minor)


class FunctionInfo(TypedDict):
    """Information about a function."""

    name: str
    args: List[Tuple[str, Any, Any]]
    return_type: Any
    docstring: str


def _type_repr(obj: Any) -> str:
    """Return the repr() of an object, special-casing types (internal helper).

    If obj is a type, we return a shorter version than the default
    type.__repr__, based on the module and qualified name, which is
    typically enough to uniquely identify a type.  For everything
    else, we fall back on repr(obj).
    """
    if PY_VERSION >= (3, 9):
        # Ignoring type for passing mypy testing with Python 3.8
        if isinstance(obj, types.GenericAlias):  # type: ignore[attr-defined]
            return repr(obj)
    if isinstance(obj, type):
        if obj.__module__ == "builtins":
            return obj.__qualname__
        return f"{obj.__module__}.{obj.__qualname__}"
    if obj is ...:
        return "..."
    if isinstance(obj, types.FunctionType):
        return obj.__name__
    return repr(obj)


def _type_repr_wrapper(obj: Any) -> str:
    """A hack to remove all references to `typing.` in type strings.

    There's likely a much better solution, but this will do for prototyping.

    Args:
        obj (Any): The object to get the type string of.

    Returns:
        str: The type string of the object.
    """
    return _type_repr(obj).replace("typing.", "")


def _get_stringified_type(type_hints: Mapping[str, Any], arg_name: str) -> str:
    """Get string version of an argument type from a mapping of type hints.

    Args:
        type_hints (Mapping[str, Any]): Mapping of argument names to types.
        arg_name (str): Name of the argument or `return` for the return type.

    Returns:
        str: String representation of the type if it exists, otherwise Any.
    """
    if arg_name in type_hints:
        return _type_repr_wrapper(type_hints[arg_name])
    else:
        return "Any"


def _get_function_info(func: Callable) -> FunctionInfo:
    """Extract information about a function.

    Args:
        func (callable): The function to get information about.

    Returns:
        A dictionary with the following keys:
            - name: The name of the function.
            - args: A list of tuples containing the name and type of each argument.
            - return_type: The type of the value returned by the function.
            - docstring: The docstring of the function.
    """
    # Get the name of the function
    name = func.__name__

    try:
        # Get information about the function's arguments
        type_hints = typing.get_type_hints(func)
    except ValueError:
        type_hints = {}

    try:
        signature = inspect.signature(func)
        args = []
        for arg_name, param in signature.parameters.items():
            arg_type = _get_stringified_type(type_hints, arg_name)
            arg_default = (
                param.default if param.default != inspect.Parameter.empty else None
            )
            args.append((arg_name, arg_type, arg_default))

        # Get the return type of the function
        return_type = _get_stringified_type(type_hints, "return")
    except ValueError:  # TODO: Exception is too broad, limit to correct scope
        return_type = "Any"
        args = []

    # Get the docstring of the function
    docstring = func.__doc__

    # Construct and return a dictionary with the function information
    return {
        "name": name,
        "args": args,
        "return_type": return_type,
        "docstring": docstring.strip() if docstring else "",
    }


def _convert_to_kork_expr(value: Any) -> ast.Expr:
    """Convert mixed-expression value to a kork expression.

    This function converts a potentially mixed python, kork expression
    into a pure kork expression.

    Args:
        value (Any): The value to convert.

    Returns:
        An `kork` expression.
    """
    if isinstance(value, ast.Expr):
        # If it's already a kork expression, return as is
        return value
    elif isinstance(value, (int, float, bool, type(None), str)):
        return ast.Literal(value=value)
    elif isinstance(value, (list, tuple)):
        return ast.List_(elements=[_convert_to_kork_expr(v) for v in value])
    else:
        raise ValueError(f"Cannot convert {value} to an `kork` expression.")


# PUBLIC API


def to_extern_func_def(func: Callable) -> ast.ExternFunctionDef:
    """Convert a python function to a kork external function definition."""
    func_info = _get_function_info(func)
    params = [
        ast.Param(name=arg_name, type_=arg_type)
        for arg_name, arg_type, _ in func_info["args"]
    ]
    return ast.ExternFunctionDef(
        name=func_info["name"],
        params=ast.ParamList(params=params),
        return_type=func_info["return_type"],
        implementation=func,
        doc_string=func_info["docstring"],
    )


def to_kork_function_call(func: Callable, *args: Any) -> ast.FunctionCall:
    """Convert a python function call to a kork function call."""
    return ast.FunctionCall(
        name=func.__name__,
        args=[_convert_to_kork_expr(arg) for arg in args],
    )

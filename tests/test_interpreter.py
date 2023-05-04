from typing import Any

import pytest

from kork import ast
from kork.ast_printer import AstPrinter
from kork.environment import Environment
from kork.exceptions import KorkRunTimeException
from kork.interpreter import run_interpreter

# TODO: Determine why mypy is not recognizing the import.
from kork.parser import parse  # type: ignore[attr-defined]


def set_up_environment() -> Environment:
    """Prepopulate an environment with some symbols."""
    environment = Environment(
        parent=None,
        variables={},
    )
    environment.set_symbol(
        "add",
        ast.ExternFunctionDef(
            name="add",
            params=ast.ParamList(
                params=[
                    ast.Param(name="a", type_="number"),
                    ast.Param(name="b", type_="number"),
                ]
            ),
            return_type="number",
        ).add_implementation(lambda a, b: a + b),
    )
    environment.set_symbol(
        "time",
        ast.ExternFunctionDef(
            name="time",
            params=ast.ParamList(params=[]),
            return_type="number",
        ).add_implementation(lambda: 1.0),
    )
    return environment


@pytest.mark.parametrize(
    "code, value",
    [
        # Int
        ("var x = 1", 1),
        # None
        ("var x = null", None),
        # Scientific
        ("var x = 1e2", 100),
        ("var x = 1E2", 100),
        ("var x = 1E-2", 0.01),
        # String
        ('var x = "hello"', "hello"),
        # Float
        ("var x = 5.0", 5.0),
        ("var x = 5.0 + 2", 7.0),
        ("var x = 5\nvar x = 2", 2.0),
        ("var x = 5;var x = 2", 2.0),
        ("var x = add(1,2)", 3.0),
        ("var x = time()", 1.0),
        # Add
        ("var x = 1 + 1", 2),
        # Subtract
        ("var x = 2 - 3", -1),
        # Unary minus
        ("var x = -3", -3),
        # Divide
        ("var x = 6 / 3", 2),
        # Multiply
        ("var x = 2 * 3", 6),
        # Operator precedence
        ("var x = 1 + 3 * 3", 10),
        # Grouping
        ("var x = (1 + 1) * 3", 6),
        # List
        ('var x = [1.0,2,"3"]', [1.0, 2, "3"]),
        # Variable declaration and assignment
        ("var x = 1\nx=2", 2),
        # Comments
        ("var x = 1 # comment", 1),
        ("var x = 1 // Also a comment", 1),
        # Sum with identifiers
        ("var x = 2\nvar x = 1 + x", 3),
        ("var x = 2\nvar x = 1 / x", 0.5),
        ("var y = 1\nvar z = 2\nvar x = y + z", 3),
        ("var y = 1\nvar z = 2\nvar x = y * z", 2),
        # Add binary operators
        ("var x = 1 + 1", 2),
        ("var x = 1 - 1", 0),
        ("var x = 1 * 3", 3),
        ("var x = 8 / 2", 4),
        ("var x = 9 % 3", 0),
        ("var x = 9 % 5", 4),
        # unary rule
        ("var x = --3", 3),
        # Take powers
        ("var x = 2 ** 4", 16),
        ("var x = 2 ^ 4", 16),
        ("var x = 2 ^ -1", 0.5),
        ("var x = 2 ^ -add(2, 2)", 1 / 16),
        ("var x = 2 ^ +add(2, 2)", 16),
        ("var y = 3; var x = 2 ^ y", 8),
        ("var y = 3; var z = 2; var x = z ^ y", 8),
        ("var y = 3; var z = 2; var x = z ** y", 8),
        # Add binary operators involving primary and function call
        ("var z = 2\nvar x = 1 + add(z, z)", 5),
        # Add binary operators involving function calls
        ("var z = 2\nvar x = add(z, z) * add(z, z)", 16),
        # Repeat tests but with semi-colons
        # Sum with identifiers
        ("var x = 2; x = 1 + x;", 3),
        ("var x = 2; x = 1 / x;", 0.5),
        ("var y = 1; z = 2; x = y + z;", 3),
        ("var y = 1; z = 2; x = y * z;", 2),
        # Add binary operators involving primary and function call
        ("var z = 2; x = 1 + add(z, z);", 5),
        # Add binary operators involving function calls
        ("var z = 2; x = add(z, z) * add(z, z);", 16),
    ],
)
def test_interpreter(code: str, value: Any) -> None:
    """Run program and verify value of `x` symbol is as expected."""
    result = run_interpreter(code, environment=set_up_environment())
    assert result["environment"].get_symbol("x") == value


def test_interpreter_extern_func_declaration() -> None:
    """Test that an extern function declaration is added to the environment."""
    result = run_interpreter("extern fn meow(x : int, y:int) -> int")
    env = result["environment"]
    extern_fn_declaration = env.get_symbol("meow")
    assert isinstance(extern_fn_declaration, ast.ExternFunctionDef)

    # Verify that the function cannot be called.
    result = run_interpreter("meow(1,2)", environment=env)
    assert isinstance(result["errors"][0], KorkRunTimeException)

    env.set_symbol("meow", extern_fn_declaration.add_implementation(lambda x, y: x + y))

    result = run_interpreter("var x = meow(1,2)", environment=env)
    assert result["environment"].get_symbol("x") == 3


def test_cannot_invoke_undefined_variable() -> None:
    """Test exception is raised when referencing an undefined variable."""
    result = run_interpreter("var x = y")
    assert isinstance(result["errors"][0], KorkRunTimeException)


def test_function_definition() -> None:
    """Test unimplemented features raise exception."""
    result = run_interpreter("def fn meow(x : int, y:int) -> int {}")
    assert isinstance(result["errors"][0], KorkRunTimeException)


def test_function_invocation() -> None:
    """Test unimplemented features raise exception."""
    environment = Environment(parent=None, variables={})
    environment.set_symbol(
        "meow",
        ast.FunctionDef(
            name="meow",
            body=[],
            params=ast.ParamList(
                params=[
                    ast.Param(name="a", type_="number"),
                    ast.Param(name="b", type_="number"),
                ]
            ),
            return_type="number",
        ),
    )

    result = run_interpreter("var x = meow(1,2)", environment=environment)

    run_interpreter("fn meow(x : int, y:int) -> int {}\nmeow(1,2)")
    assert isinstance(result["errors"][0], KorkRunTimeException)


@pytest.mark.parametrize(
    "code, expected",
    [
        ("var x = 5", "var x = 5"),
        ("var x = 5\t\t\t\nadd(2,3  )", "var x = 5\nadd(2, 3)"),
        # Verify whitespace insensitivity
        ("extern fn add(x : int, y:int)->int", "extern fn add(x: int, y: int) -> int"),
        (
            "extern fn add  (x : int, y:int) -> int",
            "extern fn add(x: int, y: int) -> int",
        ),
        ("fn add(x : int, y:int) -> int {}", "fn add(x: int, y: int) -> int {\n}"),
        ('var x = ["a", [], 1, 2.0, null]', 'var x = ["a", [], 1, 2.0, null]'),
        ("var x = []; var z = 1;", "var x = []\nvar z = 1"),
    ],
)
def test_ast_parsing_and_printing(code: str, expected: str) -> None:
    """Test parsing of code into an AST and then printing it back as code."""
    program = parse(code)
    assert AstPrinter().visit(program) == expected

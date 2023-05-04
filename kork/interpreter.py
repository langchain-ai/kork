from typing import Any, Optional, Sequence, TypedDict, Union

from lark.exceptions import LarkError

from kork import ast
from kork.environment import Environment
from kork.exceptions import KorkRunTimeException

# TODO: Determine why mypy is not recognizing the import.
from kork.parser import parse  # type: ignore[attr-defined]


class Interpreter(ast.Visitor):
    """Kork's default interpreter."""

    def __init__(self, program: ast.Program, environment: Environment) -> None:
        """Initialize the interpreter."""
        self.program = program
        self.environment = environment
        self.last_expression_value: Any = None

    def intepret(self) -> None:
        """Interpret the program."""
        self.program.accept(self)

    def visit_program(self, program: ast.Program) -> None:
        """Visit a program."""
        for stmt in program.stmts:
            stmt.accept(self)

    def visit_extern_function_def(
        self, extern_function_def: ast.ExternFunctionDef
    ) -> None:
        """Visit an external function definition."""
        self.environment.variables[extern_function_def.name] = extern_function_def

    def visit_function_call(self, call: ast.FunctionCall) -> Any:
        """Visit a function call."""
        function = self.environment.get_symbol(call.name)
        args = [arg.accept(self) for arg in call.args]
        if isinstance(function, ast.ExternFunctionDef):
            if function.implementation is None:
                raise KorkRunTimeException("External function has not been linked yet.")
            try:
                return function.implementation(*args)
            except Exception as e:
                raise KorkRunTimeException(
                    "Encountered an exception while invoking an external function "
                    f"`{call.name}` with arguments: `{args}`."
                    f"Details: {e}"
                )
        elif isinstance(function, ast.FunctionDef):
            raise KorkRunTimeException("Function definition is unimplemented.")
        else:
            raise KorkRunTimeException(f"Cannot call {call.name}.")

    def visit_function_def(self, function_def: ast.FunctionDef) -> None:
        """Visit a function definition."""
        self.environment.variables[function_def.name] = function_def

    def visit_variable(self, variable: ast.Variable) -> Any:
        """Visit a variable."""
        return self.environment.get_symbol(variable.name)

    def visit_var_decl(self, var_decl: ast.VarDecl) -> None:
        """Visit a variable declaration."""
        self.environment.variables[var_decl.name] = var_decl.value.accept(self)

    def visit_unary(self, unary: ast.Unary) -> Any:
        """Visit a unary expression."""
        operator = unary.operator
        right = unary.right.accept(self)
        if operator == "-":
            return -right
        elif operator == "+":
            return right
        else:
            raise ValueError(f"Unknown operator {operator}.")

    def visit_binary(self, binary: ast.Binary) -> Any:
        """Visit a binary expression."""
        left = binary.left.accept(self)
        right = binary.right.accept(self)
        operator = binary.operator
        if operator == "+":
            return left + right
        elif operator == "-":
            return left - right
        elif operator == "*":
            return left * right
        elif operator == "/":
            return left / right
        elif operator == "**":
            return left**right
        elif operator == "%":
            return left % right
        elif (
            operator == "^"
        ):  # Please note that we do not follow python convention here
            return left**right  # Duplicating `**` operator
        else:
            raise ValueError(f"Unknown operator {operator}.")

    def visit_grouping(self, grouping: ast.Grouping) -> Any:
        """Visit a grouping."""
        return grouping.expr.accept(self)

    def visit_assign(self, assign: ast.Assign) -> None:
        """Visit an assignment."""
        self.environment.variables[assign.name] = assign.value.accept(self)

    def visit_literal(self, literal: ast.Literal) -> Union[int, float, bool, str, None]:
        """Visit a number."""
        return literal.value

    def visit_list_(self, list_: ast.List_) -> list:
        """Visit a list."""
        return [element.accept(self) for element in list_.elements]


# PUBLIC API


class InterpreterResult(TypedDict):
    """Use this to return the result of the interpreter."""

    environment: Environment
    errors: Sequence[Exception]


def run_interpreter(
    code: str, environment: Optional[Environment] = None
) -> InterpreterResult:
    """Run the interpreter with the given code.

    Args:
        code: The code to run
        environment: The environment to run the code in

    Returns:
        the final environment after running the code (this will likely change)
    """
    # TODO(Eugene): May want to refactor to avoid cloning here without introducing
    #                mutability associated bugs.
    environment = (
        environment.clone() if environment else Environment(parent=None, variables={})
    )
    try:
        program = parse(code)
        interpreter = Interpreter(program, environment)
        interpreter.intepret()
    except (
        LarkError,
        KorkRunTimeException,
        ValueError,
        ZeroDivisionError,
        TypeError,
    ) as e:
        return InterpreterResult(
            environment=environment,
            errors=[e],
        )

    return InterpreterResult(
        environment=interpreter.environment,
        errors=[],
    )

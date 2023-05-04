import abc
from typing import Union

from kork import ast


class AbstractAstPrinter(ast.Visitor, abc.ABC):
    @abc.abstractmethod
    def visit(self, element: Union[ast.Stmt, ast.Expr]) -> str:
        """Entry-point for printing the AST."""


class AstPrinter(AbstractAstPrinter):
    """Default AST Printer implementation."""

    def visit(self, element: Union[ast.Stmt, ast.Expr]) -> str:
        """Entry-point for printing the AST."""
        return element.accept(self)

    def visit_program(self, program: ast.Program) -> str:
        """Print a program."""
        return "\n".join(stmt.accept(self) for stmt in program.stmts)

    def visit_extern_function_def(
        self, extern_function_def: ast.ExternFunctionDef
    ) -> str:
        """Print an extern function definition."""
        code = [
            f"extern fn {extern_function_def.name}",
            "(",
            extern_function_def.params.accept(self),
            ")",
            " -> ",
            extern_function_def.return_type,
        ]

        if extern_function_def.doc_string:
            # TODO: This is hacky for prototyping, will need to have a better
            # way to represent the doc string.
            doc_string = extern_function_def.doc_string.strip().split("\n")[0]
            code.append(f" // {doc_string}")

        return "".join(code)

    def visit_function_call(self, call: ast.FunctionCall) -> str:
        """Print a function call."""
        return f"{call.name}({', '.join(arg.accept(self) for arg in call.args)})"

    def visit_function_def(self, function_def: ast.FunctionDef) -> str:
        """Print a function definition."""
        signature = [
            f"fn {function_def.name}",
            "(",
            function_def.params.accept(self),
            ")",
            " -> ",
            function_def.return_type,
        ]

        code = [" {"]
        for stmt in function_def.body:
            code.append(stmt.accept(self))
        code.append("}")
        return "".join(signature) + "\n".join(code)

    def visit_variable(self, variable: ast.Variable) -> str:
        """Print a variable."""
        return variable.name

    def visit_var_decl(self, var_decl: ast.VarDecl) -> str:
        """Print a variable declaration."""
        return f"var {var_decl.name} = {var_decl.value.accept(self)}"

    def visit_assign(self, assign: ast.Assign) -> str:
        """Print an assignment."""
        return f"{assign.name} = {assign.value.accept(self)}"

    def visit_literal(self, literal: ast.Literal) -> str:
        """Print a literal."""
        value = literal.value
        if isinstance(value, type(None)):
            return "null"
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, (float, int)):
            return str(value)
        else:
            raise AssertionError(f"Unknown literal type: {type(value)}")

    def visit_param_list(self, param_list: ast.ParamList) -> str:
        """Print a parameter list."""
        return ", ".join(param.accept(self) for param in param_list.params)

    def visit_param(self, param: ast.Param) -> str:
        """Print a parameter."""
        return f"{param.name}: {param.type_}"

    def visit_list_(self, list_: ast.List_) -> str:
        """Print a list."""
        return f"[{', '.join(element.accept(self) for element in list_.elements)}]"

    def visit_unary(self, unary: ast.Unary) -> str:
        """Visit a unary expression."""
        return f"{unary.operator}{unary.right.accept(self)}"

    def visit_grouping(self, grouping: ast.Grouping) -> str:
        return f"({grouping.expr.accept(self)})"

    def visit_binary(self, binary: ast.Binary) -> str:
        """Print a binary expression."""
        return (
            f"{binary.left.accept(self)} "
            f"{binary.operator} {binary.right.accept(self)}"
        )

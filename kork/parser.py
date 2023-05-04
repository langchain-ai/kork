# type:ignore[no-untyped-def]
"""Kork's default AST parser.

Kork uses Lark to parse the AST. The grammar follows closely
the one used in Crafting Interpreters for the Lox Programming Language.

https://craftinginterpreters.com/appendix-i.html#expressions

The grammar and parser were clobbered together in a few hours of work.

If you deeply care about language design, please forgive any transgressions,
and feel free to help improve the grammar/parser/interpreter.
"""
from typing import cast

from lark import Lark, Transformer, v_args

from kork import ast

GRAMMAR = """
    program: statement+

    statement: function_decl
              | extern_function_decl
              | var_decl
              | expr

    function_decl: "fn" CNAME "(" [params] ")" "->" type block
    extern_function_decl: "extern" "fn" CNAME "(" [params] ")" "->" type
    var_decl: ("let" | "const" | "var") CNAME "=" expr [";"]
    params: param ("," param)*
    param: CNAME ":" type
    type: CNAME
    
    block: "{" [statement+] "}"
    
    ?expr: assignment
    
    ?assignment: CNAME "=" expr [";"] -> variable_assign
        | term
        
    !?term: term "+" factor -> binary
        | term "-" factor -> binary
        | factor
        
    !?factor: factor "*" unary -> binary
        | factor "/" unary -> binary
        | factor "%" unary -> binary
        | unary
        
    !?unary: "-" unary -> unary_r
        | "+" unary -> unary_r
        | power
        
    !?power: call "**" unary -> binary
        | call "^" unary -> binary
        | call
    
    ?call: CNAME "(" [args] ")" -> function_call
        | primary
    
    ?primary: numbers
        | list
        | string
        | "true" -> true
        | "false" -> false
        | "null" -> null
        | "(" expr ")" -> group
        | CNAME -> identifier
        
    ?numbers: SIGNED_NUMBER ("E"|"e") SIGNED_NUMBER -> scientific
        | SIGNED_NUMBER -> number
        
    args: expr ("," expr)*
    string: ESCAPED_STRING
    list: "[" [args] "]"

    %import common.CNAME
    %import common.SIGNED_NUMBER
    %import common.ESCAPED_STRING
    %import common.WS
    %ignore WS
    %ignore /#.*/
    %ignore /\/\/.*/
"""


# mypy: ignore-errors


@v_args(inline=True)
class AstParser(Transformer):
    """An ast parser for the given language."""

    def program(self, *items) -> ast.Program:
        """Create a program from the given statements."""
        return ast.Program(stmts=items)

    def function_decl(self, name, params, return_type, block) -> ast.FunctionDef:
        """Function declaration from the given name, params, return type and block."""
        return ast.FunctionDef(
            name=str(name),
            params=params,
            return_type=return_type,
            body=block,
        )

    def extern_function_decl(self, name, params, return_type) -> ast.ExternFunctionDef:
        """Extern function declaration from the given name, params and return type."""
        return ast.ExternFunctionDef(
            name=str(name),
            params=params or ast.ParamList(params=[]),
            return_type=return_type,
        )

    def statement(self, item) -> ast.Stmt:
        """Create a statement from the given item."""
        return item

    def var_decl(self, name, value) -> ast.VarDecl:
        """Variable declaration from the given name and value."""
        return ast.VarDecl(
            name=str(name),
            value=value,
        )

    def params(self, *items) -> ast.ParamList:
        """Create a param list from the given items."""
        return ast.ParamList(params=items or [])

    def unary_r(self, operator, right) -> ast.Unary:
        """Create a unary from the given operator and left."""
        op = str(operator)
        if op not in {"+", "-"}:
            raise ValueError(f"Unknown operator: {op}.")
        return ast.Unary(operator=str(operator), right=right)

    def binary(self, left, operator, right) -> ast.Binary:
        """Create a binary from the given left, operator and right."""
        op = str(operator)
        if op not in {"+", "-", "*", "/", "**", "//", "%", "^"}:
            raise ValueError(f"Unknown operator: {op}.")
        return ast.Binary(left=left, operator=str(operator), right=right)

    def param(self, name, type_) -> ast.Param:
        """Create a param from the given name and type."""
        return ast.Param(
            name=str(name),
            type_=type_,
        )

    def type(self, name):
        """Create a type from the given name."""
        return str(name)

    def block(self, *statements):
        """Create a block from the given statements."""
        return statements or []

    def group(self, expr) -> ast.Grouping:
        """Create a group from the given expression."""
        return ast.Grouping(expr=expr)

    def function_call(self, name, args) -> ast.FunctionCall:
        """Create a function call from the given name and args."""
        return ast.FunctionCall(name=str(name), args=args or [])

    def identifier(self, name) -> ast.Variable:
        """Create a variable reference from the given name."""
        return ast.Variable(
            name=str(name),
        )

    def variable_assign(self, name, value) -> ast.Assign:
        """Create a variable assignment from the given name and value."""
        return ast.Assign(
            name=str(name),
            value=value,
        )

    def expr(self, item) -> ast.Expr:
        """Create an expression from the given item."""
        return item

    def args(self, *items):
        """Create an argument list for a function from the given items."""
        return items or []

    def list(self, items) -> ast.List_:
        """Create a list literal from the given items."""
        return ast.List_(
            elements=items or [],
        )

    def true(self) -> ast.Literal:
        """Create a true literal."""
        return ast.Literal(value=True)

    def false(self) -> ast.Literal:
        """Create a false literal."""
        return ast.Literal(value=False)

    def null(self) -> ast.Literal:
        """Create a null literal."""
        return ast.Literal(value=None)

    def number(self, item) -> ast.Literal:
        try:
            return ast.Literal(value=int(item))
        except ValueError:
            return ast.Literal(value=float(item))

    def scientific(self, coefficient, exponent) -> ast.Literal:
        return ast.Literal(value=coefficient * 10**exponent)

    def string(self, item) -> ast.Literal:
        return ast.Literal(
            value=str(item[1:-1]),
        )


ast_parser = Lark(GRAMMAR, parser="lalr", transformer=AstParser(), start="program")

# PUBLIC API


def parse(source: str) -> ast.Program:
    """Parse the given source code into an AST."""
    return cast(ast.Program, ast_parser.parse(source))

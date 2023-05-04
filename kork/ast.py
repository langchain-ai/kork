"""The AST for the language.

The AST is a bit messy right now in terms of what's a statement vs. an expression,
and will likely need to be cleaned up a bit in the near future.
"""
from __future__ import annotations

import abc
import dataclasses
from typing import Any, Callable, Optional, Sequence, TypeVar, Union

T = TypeVar("T")


class Visitor(abc.ABC):
    """Abstract visitor interface."""


def _to_snake_case(name: str) -> str:
    """Convert a name into snake_case."""
    snake_case = ""
    for i, char in enumerate(name):
        if char.isupper() and i != 0:
            snake_case += "_" + char.lower()
        else:
            snake_case += char.lower()
    return snake_case


@dataclasses.dataclass(frozen=True)
class Expr(abc.ABC):
    """Abstract expression."""

    def accept(self, visitor: Visitor) -> Any:
        """Accept implementation for a visitor."""
        return getattr(visitor, f"visit_{_to_snake_case(self.__class__.__name__)}")(
            self
        )


@dataclasses.dataclass(frozen=True)
class Literal(Expr):
    """A literal expression."""

    value: Union[float, int, bool, None, str]


@dataclasses.dataclass(frozen=True)
class Grouping(Expr):
    """A grouping expression."""

    expr: Expr


@dataclasses.dataclass(frozen=True)
class Unary(Expr):
    """A unary expression."""

    operator: str
    right: Expr


@dataclasses.dataclass(frozen=True)
class Binary(Expr):
    """A binary expression."""

    left: Expr
    operator: str
    right: Expr


@dataclasses.dataclass(frozen=True)
class Assign(Expr):
    """Assignment statement for a variable."""

    name: str
    value: Expr


@dataclasses.dataclass(frozen=True)
class Variable(Expr):
    """Variable reference."""

    name: str


@dataclasses.dataclass(frozen=True)
class List_(Expr):
    """List literal."""

    elements: Sequence[Expr]


@dataclasses.dataclass(frozen=True)
class Stmt(abc.ABC):
    """Abstract statement."""

    def accept(self, visitor: Visitor) -> Any:
        """Accept implementation for a visitor."""
        return getattr(visitor, f"visit_{_to_snake_case(self.__class__.__name__)}")(
            self
        )


@dataclasses.dataclass(frozen=True)
class Param(Stmt):
    """Represent a function parameter."""

    name: str
    type_: str


@dataclasses.dataclass(frozen=True)
class ParamList(Stmt):
    """Represent a list of function parameters."""

    params: Sequence[Param]


@dataclasses.dataclass(frozen=True)
class FunctionDef(Stmt):
    """Represent a function definition with an implementation."""

    name: str
    params: ParamList
    body: Sequence[Union[Stmt, Expr]]
    # This is just an annotation so it's a string.
    return_type: str


@dataclasses.dataclass(frozen=True)
class ExternFunctionDef(Stmt):
    """External function definition."""

    name: str
    params: ParamList
    # This is just an annotation so it's a string.
    return_type: str
    implementation: Optional[Callable] = None
    doc_string: str = ""

    def add_implementation(self, implementation: Callable) -> "ExternFunctionDef":
        """Add an implementation to an external function definition."""
        if self.implementation is not None:
            raise ValueError("Cannot add implementation to an already implemented func")
        return ExternFunctionDef(
            name=self.name,
            params=self.params,
            return_type=self.return_type,
            implementation=implementation,
        )


@dataclasses.dataclass(frozen=True)
class FunctionCall(Expr):
    """Represent a function call."""

    name: str  # Name of function being invoked
    args: Sequence[Expr]  # Arguments to the function call


@dataclasses.dataclass(frozen=True)
class VarDecl(Stmt):
    """Represent a variable declaration."""

    name: str  # Name of variable
    value: Expr  # Expression to assign to the variable


@dataclasses.dataclass(frozen=True)
class Program(Stmt):
    """Represent a program."""

    stmts: Sequence[Union[Stmt, Expr]]

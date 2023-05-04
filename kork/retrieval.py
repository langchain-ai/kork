"""Logic that attempts to surface the most relevant information for writing code."""
from __future__ import annotations

import abc
import dataclasses
from typing import Callable, Sequence, Union

from kork import ast
from kork.foreign_funcs import to_extern_func_def


@dataclasses.dataclass(frozen=True)
class AbstractContextRetriever(abc.ABC):
    """Abstract interface for retrieving programming context."""

    @abc.abstractmethod
    def retrieve(self, query: str) -> Sequence[ast.ExternFunctionDef]:
        """Retrieve the external function definitions."""


FuncLike = Union[ast.ExternFunctionDef, Callable]


@dataclasses.dataclass(frozen=True)
class SimpleContextRetriever(AbstractContextRetriever):
    """Retrieve information as was provided without any filtering or re-ranking."""

    external_functions: Sequence[ast.ExternFunctionDef] = tuple()

    def __post_init__(self) -> None:
        """Validate the external functions."""
        for func in self.external_functions:
            if not isinstance(func, ast.ExternFunctionDef):
                raise ValueError(
                    "SimpleRetriever only accepts ExternFunctionDef objects in "
                    f"the external_functions list. Got: {func}"
                )

    def retrieve(self, query: str) -> Sequence[ast.ExternFunctionDef]:
        """Retrieve the external function definitions."""
        return self.external_functions

    @classmethod
    def from_functions(cls, mixed_funcs: Sequence[FuncLike]) -> SimpleContextRetriever:
        """Create a simple retrieval from a sequence of functions.

        Args:
            mixed_funcs: A sequence of functions or external function definitions.

        Returns:
            A simple retriever.
        """

        external_functions = []

        for func in mixed_funcs:
            if isinstance(func, ast.ExternFunctionDef):
                external_functions.append(func)
            else:
                external_functions.append(to_extern_func_def(func))

        return cls(external_functions=external_functions)

from __future__ import annotations

import copy
import dataclasses
from dataclasses import field
from typing import Any, Dict, List, Mapping, Optional, Sequence

from kork import ast
from kork.exceptions import KorkRunTimeException


@dataclasses.dataclass
class Environment:
    """Environment for storing variables and function definitions."""

    parent: Optional[Environment] = None
    variables: Dict[str, Any] = field(default_factory=dict)

    def get_symbol(self, name: str) -> Any:
        """Get a symbol from the environment.

        Args:
            name: symbol name to lookup

        Returns:
            SymbolValue for the given symbol if it exists, otherwise raises an error
        """
        if name in self.variables:
            return self.variables[name]
        elif self.parent:
            return self.parent.get_symbol(name)
        else:
            raise KorkRunTimeException(f"Variable `{name}` not found")

    def set_symbol(self, name: str, value: Any) -> Any:
        """Set a symbol in the environment."""
        # TODO: We need to determine whether want the variable to be
        #       declared prior to be being set.
        #       At the moment, this allows for `x = 1` without having to declare the
        #       variable.
        self.variables[name] = value
        return value

    def clone(self) -> Environment:
        """Clone a root level environment, with deep copy on variables.

        Cloning functionality is provided because the environment is
        a mutable variable.

        Biggest danger is mutating the variables dict which the caller
        may retain a reference to.

        TODO(Eugene): Refactor to make this less dangerous.
        """
        if self.parent is not None:
            raise AssertionError("Cannot clone an environment with a parent.")
        return Environment(parent=None, variables=copy.deepcopy(self.variables))

    def list_external_functions(self) -> List[ast.ExternFunctionDef]:
        """Get a list of the externally defined foreign functions."""
        return [
            func
            for func in self.variables.values()
            if isinstance(func, ast.ExternFunctionDef)
        ]


def create_environment(
    extern_function_defs: Sequence[ast.ExternFunctionDef],
    external_variables: Optional[Mapping[str, Any]] = None,
) -> Environment:
    """Create a new environment with pre-populated state."""
    variables: Dict[str, Any] = {func.name: func for func in extern_function_defs}
    environment = Environment(parent=None, variables=variables)

    if external_variables:
        for name, value in external_variables.items():
            # At the moment, let's not clone the variable so that it can be
            # mutated if the goal is to do mutation.
            environment.set_symbol(name, value)
    return environment

import pytest

from kork import ast
from kork.environment import Environment
from kork.exceptions import KorkRunTimeException


def test_accessing_variables() -> None:
    """Test the instantiation of the environment."""
    env = Environment()

    with pytest.raises(KorkRunTimeException):
        env.get_symbol("x")

    env.set_symbol("x", 1)
    assert env.get_symbol("x") == 1


def test_clone() -> None:
    """Test env cloning."""
    env = Environment()
    env.set_symbol("x", 1)
    new_env = env.clone()
    env.set_symbol("y", 2)
    new_env.set_symbol("z", 3)

    assert env.variables == {"x": 1, "y": 2}
    assert new_env.variables == {"x": 1, "z": 3}


def test_list_external_functions() -> None:
    """Test list external functions."""
    env = Environment()
    assert env.list_external_functions() == []
    func = ast.ExternFunctionDef(
        name="foo", params=ast.ParamList([]), return_type="Any"
    )
    env.set_symbol("foo", func)
    assert env.list_external_functions() == [func]

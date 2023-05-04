from kork.ast import _to_snake_case


def test_snake_case() -> None:
    assert _to_snake_case("Number") == "number"
    assert _to_snake_case("NumberWoof") == "number_woof"

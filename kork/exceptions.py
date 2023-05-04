"""Definitions for custom Kork exceptions."""


class KorkException(Exception):
    """Generic Kork exception."""


class LLMParseException(KorkException):
    """Failed to parse LLM output."""


class KorkSyntaxException(KorkException):
    """Exceptions raised during syntax parsing."""


class KorkInterpreterException(KorkException):
    """Exceptions raised during interpretation."""


class KorkRunTimeException(KorkInterpreterException):
    """An exception that is raised during Kork interpreter runtime."""

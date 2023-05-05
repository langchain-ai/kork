# Introduction 

`Kork` is an *experimental* [Langchain chain](https://python.langchain.com/en/latest/modules/chains.html) that can write and execute code safely.

`Kork` **cannot** write *arbitrary* code. If that's what you need, save yourself some time and use [docker](https://www.docker.com/) and a real programming language.

`Kork` does not aim implement a fully functional programming language, but to make it
easier to get an LLM to code that is *safe* and *useful* for a *constrained* problem
domain.

A calculator powered by natural language is one example of a constrained problem domain.

The main feature of the `Kork` programming language and interpreter is that it does not have any features. To do useful things with `Kork` a user specifies  *foreign functions* that can be called from the `Kork` interpreter by the chain. The chain uses an LLM to translate a user query into a `Kork` program, which is then executed by a `Kork` interpreter.

## Safety

Nothing is bulletproof when humans are involved.

* Don't do silly things like exposing `eval` as a foreign function.
* If a foreign function allocates memory, the LLM could ask for more memory than is available crashing the process.
* Think carefully about whether the LLM could behave maliciously before trusting its output.

## Quality

The short version: No benchmarks yet!

The long version: Quality of generated programs depends on many factors.

You can experiment with tweaking the prompt (e.g., explain the syntax of the language), changing the foreign function retriever (e.g., retrieve the most relevant foreign functions based on the user query), or providing examples in the form of (query, expected program).

The prompt, examples and syntax of the language can trip up the LLM to assume
it's programming in a specific language (e.g., typescript or python) and assume
that it can use language features that are not supported by `Kork` or to import
libraries that are not available.

## Limitations

- The `Kork` language and interpreter are limited to *function invocation*, *variable declaration* and
  *basic arithmetic* (no function declaration, loops etc.)
- Only supporting `int`, `float`, `str`, `type(None)`, `bool` types. No support for `lists` or `object` types.
- Very limited type annotations.

## Future Work

Let us know if you're interested in contributing or have ideas for improvements!

- Allow enabling/disabling language features
- Allow changing underlying language syntax
- Add support for objects
- Add other language features (e.g., loops)
- Provide foreign function retriever implementations based on similarity to user query

## Compatibility

`Kork` is tested against python 3.8, 3.9, 3.10, 3.11.

## Installation

```sh
pip install kork
```

## 🙏 Appreciation

* [Lark](https://github.com/lark-parser/lark) -- For making it easy to define a grammar and parse it!
* [Bob Nystrom](https://github.com/munificent) -- For writing [Crafting Interpreters](https://www.craftinginterpreters.com/)!

## © Contributing

If you have any ideas or feature requests, please open an issue and share!

See [CONTRIBUTING.md](https://github.com/langchain-ai/kork/blob/main/CONTRIBUTING.md) for more information.

## 🎶 Why the name?

Fast to type and maybe sufficiently unique.


```{toctree}
:maxdepth: 2
:caption: Contents

introduction
language
ast
examples
prompt
retrievers
```

```{toctree}
:caption: Examples
calculator
query_analyzer
```

```{toctree}
:maxdepth: 2
:caption: Advanced
api
```

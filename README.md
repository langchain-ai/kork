[![Unit Tests](https://github.com/langchain-ai/kork/actions/workflows/test.yml/badge.svg?branch=main&event=push)](https://github.com/langchain-ai/kork/actions/workflows/test.yml)

# Kork ![alt The Parrot](assets/parrot.png)

`Kork` is an *experimental* [Langchain chain](https://python.langchain.com/en/latest/modules/chains.html) that makes it easy to create natural language based APIs powered by LLMs.

## Main Features

1. Assemble a natural language API from a set of python functions.
2. Generate a prompt based on the user query that helps the LLM to generate a **correct** program.
3. Execute the program generated by the LLM **safely**.

## How

`Kork` defines its own tiny programming language that is limited to variable declarations, function invocations and arithmetic operations. 

The `Kork` chain takes a user query, translates it into a program, and executes it using its interpreter.

Because the `Kork` language is limited to invocations of pre-specified functions, any
generated programs by the LLM are relatively safe to execute.

*No loops, no conditionals, no file access, no network access, no arbitrary code execution. WHAT?!*

The ability to invoke custom functions goes a long way in terms of the kinds of programs that can be written! (You can always add a `write_to_file` function!)

## Limitations

- `Kork` **cannot write arbitrary** code. If that's what you need, save yourself some time and use [docker](https://www.docker.com/) and a real programming language.

- The `Kork` language and interpreter are limited to *function invocation*, *variable declaration* and
  *basic arithmetic* (no function declaration, loops etc.)
- Only supporting `int`, `float`, `str`, `type(None)`, `bool` types. No support for `lists` or `object` types.
- Very limited type annotations.

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

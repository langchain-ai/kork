# Contributing to Kork

Thanks for your interest in contributing to Kork!

If you have ideas or features you would like to see implemented feel free to
open an issue and let me know.

PRs are welcome, but before starting to work on a substantial PR, please file
an issue to discuss the design and the code change. 

## Setting up for development

The package uses [poetry](https://python-poetry.org/) together with
[poethepoet](https://github.com/nat-n/poethepoet).

### Install dependencies

```shell

poetry install --with dev,test
```

### List tasks

```shell
poe
```

### autoformat

```shell
poe autoformat
```

### test

```shell
poe test
```

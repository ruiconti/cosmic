# Architectural Patterns


### Virtual environment

It is advisable to run this project under a specific environment running Python 3.7+

### Dependencies

`poetry` is being used to manage dependencies efficiently. Therefore, it's as simple as

```bash
$ poetry install
```

### Migrations

In order to update database to recent changes on declared metadata, we're using `alembic`. By doing

```bash
alembic upgrade head
```

You should be able to reach most-recent state


### Tests

TDD is being employed so in order to run and test implementations, abstracted to `Makefile`:

```bash
$ make test
```

This is a self-study of the book Cosmic Python: Architectural Patterns.

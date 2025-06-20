# Architecture of ReqSnake

This file defines the architecture of `ReqSnake`.

## Overview

It shall be possible to use the `ReqSnake` application both interactively (via CLI) and via a Python API.
This can be useful both for extending `ReqSnake` and for tests.

## Testing

Apart from unit testing, there shall also exist test scenarios which check the behaviour of the entire `ReqSnake` when used on a specific set of Markdown files.

Tests shall create a test folder via `tempfile`, add the Markdown documentation and run a set of `ReqSnake` commands (using the Python API). Then, the tests shall check if the Python API require expected outputs and if the `requirements.lock` file has been properly changed (or has not, depending on the scenario).

## Example Workflow

1. Create a test folder
2. Add Markdown files with requirements
3. Run `reqsnake.py init` (via Python API)
4. Check the generated `requirements.lock`
5. Run `reqsnake.py init` again

# Architecture

This file defines the architecture of `require.py`.

## Modularity

It shall be possible to use the `require.py` application both interactively (via CLI) and via a Python API.
This can be useful both for extending `require.py` and for tests.

### Testing

Apart from unit testing, there shall also exist test scenarios which check the behaviour of the entire `require.py` when used on a specific set of Markdown files.

Tests shall create a test folder via `tempfile`, add the Markdown documentation and run a set of `require.py` commands (using the Python API). Then, the tests shall check if the Python API require expected outputs and if the `requirements.lock` file has been properly changed (or has not, depending on the test).
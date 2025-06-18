# Architecture

This file defines the architecture of `require.py`.

## Modularity

It shall be possible to use the `require.py` application both interactively (via CLI) and via a Python API.
This can be useful both for extending `require.py` and for tests.

### Testing

Apart from unit testing, there shall also exist test scenarios which check the behaviour of the entire `require.py` when used on a specific set of Markdown files.

Tests shall create a test folder via `tempfile`, add the Markdown documentation and run a set of `require.py` commands (using the Python API). Then, the tests shall check if the Python API require expected outputs and if the `requirements.lock` file has been properly changed (or has not, depending on the test).

#### Example tests

**Checking if `requirements.lock` is not created again**

1. Create a new folder
2. Create some requirements in Markdown files
3. Run `require.py init` (via Python API)
4. Check if `requirements.lock` has been generated
5. Run `require.py init` again
6. Check if an error is returned

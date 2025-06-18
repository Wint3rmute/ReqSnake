# Requirements Status Report

## Summary

- **Total requirements:** 42
- **Completed:** 3/42 (7.1%)
- **Critical requirements:** 4
- **Critical completed:** 2/4 (50.0%)

## Requirements by File

### /home/wint3rmute/require.py/reqs.md
- **Completed:** 1/2 (50.0%)

- ⏳ **REQ-1**: The first requirement.
- ✅ ⚠️ **REQ-1**: The system shall support user authentication. _(children: REQ-0)_

### /home/wint3rmute/require.py/requirements/REQ-CLI.md
- **Completed:** 2/10 (20.0%)

- ✅ ⚠️ **REQ-CLI-1**: The tool shall provide a command-line interface (CLI) for managing requirements.
- ✅ **REQ-CLI-2**: The CLI shall support the commands: init, check, lock, and status.
- ⏳ **REQ-CLI-3**: The CLI shall print the Markdown files being scanned during operations.
- ⏳ **REQ-CLI-4**: When the user runs `require.py lock` and the requirements have not changed since the last lock, the CLI shall print a message indicating that the lockfile is already up-to-date (e.g., "requirements.lock is already up-to-date."). Only print the "requirements.lock updated" message if the lockfile was actually changed.
- ⏳ **REQ-CLI-5**: When displaying changed requirements with `require.py check`, the application shall display the path to the file containing each requiremement which has undergone any kind of change
- ⏳ **REQ-CLI-6**: The CLI shall provide a `status` command that displays completion status of requirements.
- ⏳ **REQ-CLI-7**: The `status` command shall display total requirements count, completed requirements count and percentage, and critical requirements status.
- ⏳ **REQ-CLI-8**: The `status` command shall group requirements by source file and show completion status for each file.
- ⏳ **REQ-CLI-9**: The `status` command shall display hierarchical completion status showing parent-child relationships with visual indicators.
- ⏳ **REQ-CLI-10**: The CLI shall provide a command to generate a Markdown file containing the status of all currently defined requirements, relying solely on the requirements.lock file. The output shall be suitable for inclusion in documentation or reports.

### /home/wint3rmute/require.py/requirements/REQ-CORE.md
- **Completed:** 0/6 (0.0%)

- ⏳ ⚠️ **REQ-CORE-1**: The tool shall parse requirements from Markdown files using blockquote syntax.
- ⏳ **REQ-CORE-2**: Each requirement shall have a unique ID, description, and may have critical, child, and completed attributes.
- ⏳ **REQ-CORE-3**: The tool shall store requirements in a requirements.lock file in JSON format.
- ⏳ **REQ-CORE-4**: The tool shall provide a Python API for core operations (init, check, lock).
- ⏳ **REQ-CORE-5**: Child relationships shall be described with a "child-of" key. Example: "child-of REQ-123"
- ⏳ **REQ-CORE-6**: Each requirement shall be in a form of "<STRING>-<NUMBER>". Where NUMBER is an integer.

### /home/wint3rmute/require.py/requirements/REQ-PARSER.md
- **Completed:** 0/19 (0.0%)

- ⏳ **REQ-PARSER-1**: The parser shall extract requirements from Markdown blockquotes with high accuracy.
- ⏳ **REQ-PARSER-2**: The parser shall raise an error if a requirement ID is duplicated in the scanned files.
- ⏳ **REQ-PARSER-3**: The parser shall support the 'critical', 'child', and 'completed' attributes in the blockquote format.
- ⏳ **REQ-PARSER-4**: The parser shall ignore non-blockquote content in Markdown files.
- ⏳ **REQ-PARSER-5**: The parser shall be dependency-free and use only the Python standard library.
- ⏳ **REQ-PARSER-6**: The parser shall handle blockquotes with only an ID or only a description by ignoring them.
- ⏳ **REQ-PARSER-7**: The parser shall ignore extra blank lines or whitespace within blockquotes.
- ⏳ **REQ-PARSER-8**: The parser shall treat attribute keywords (e.g., 'critical', 'child', 'completed') case-insensitively and ignore leading/trailing spaces.
- ⏳ **REQ-PARSER-9**: The parser shall allow multiple 'child:' lines per requirement.
- ⏳ **REQ-PARSER-99**: The parser shall raise errors on duplicated 'child:' lines per requirement.
- ⏳ **REQ-PARSER-10**: The parser shall raise errors on unknown attributes in requirement definitions.
- ⏳ **REQ-PARSER-11**: The parser shall treat requirement IDs as case-sensitive and not allow IDs with only case differences.
- ⏳ **REQ-PARSER-12**: The parser shall handle blockquotes with inconsistent use of '>' by only considering lines that start with '>'.
- ⏳ **REQ-PARSER-13**: The parser shall ignore Markdown formatting inside blockquotes.
- ⏳ **REQ-PARSER-14**: The parser shall ignore blockquotes that span multiple paragraphs (i.e., with blank lines in between).
- ⏳ **REQ-PARSER-15**: The parser shall raise an error if a circular child relationship is detected.
- ⏳ **REQ-PARSER-16**: The parser shall support requirements and attributes containing Unicode characters.
- ⏳ **REQ-PARSER-17**: The parser shall ignore blockquotes that are commented out in Markdown (e.g., inside ).
- ⏳ **REQ-PARSER-18**: The parser shall handle files with mixed line endings and leading/trailing whitespace.

### /home/wint3rmute/require.py/requirements/REQ-TEST.md
- **Completed:** 0/4 (0.0%)

- ⏳ ⚠️ **REQ-TEST-1**: The tool shall provide unit tests for the Markdown parser.
- ⏳ **REQ-TEST-2**: The tool shall provide integration tests that use the Python API to simulate CLI operations in temporary directories.
- ⏳ **REQ-TEST-3**: Integration tests shall verify that requirements.lock is updated when Markdown files are changed.
- ⏳ **REQ-TEST-4**: Integration tests shall verify that duplicate requirement IDs raise an error.

### unknown.md
- **Completed:** 0/1 (0.0%)

- ⏳ **REQ-2**: The system shall store user credentials securely.

## Hierarchical Status

- ⏳ **REQ-1**: The first requirement.
- ✅ ⚠️ **REQ-1**: The system shall support user authentication. _(children: REQ-0)_
  - ❓ **REQ-0**: (not found)
- ⏳ **REQ-2**: The system shall store user credentials securely.
- ✅ ⚠️ **REQ-CLI-1**: The tool shall provide a command-line interface (CLI) for managing requirements.
- ⏳ **REQ-CLI-10**: The CLI shall provide a command to generate a Markdown file containing the status of all currently defined requirements, relying solely on the requirements.lock file. The output shall be suitable for inclusion in documentation or reports.
- ✅ **REQ-CLI-2**: The CLI shall support the commands: init, check, lock, and status.
- ⏳ **REQ-CLI-3**: The CLI shall print the Markdown files being scanned during operations.
- ⏳ **REQ-CLI-4**: When the user runs `require.py lock` and the requirements have not changed since the last lock, the CLI shall print a message indicating that the lockfile is already up-to-date (e.g., "requirements.lock is already up-to-date."). Only print the "requirements.lock updated" message if the lockfile was actually changed.
- ⏳ **REQ-CLI-5**: When displaying changed requirements with `require.py check`, the application shall display the path to the file containing each requiremement which has undergone any kind of change
- ⏳ **REQ-CLI-6**: The CLI shall provide a `status` command that displays completion status of requirements.
- ⏳ **REQ-CLI-7**: The `status` command shall display total requirements count, completed requirements count and percentage, and critical requirements status.
- ⏳ **REQ-CLI-8**: The `status` command shall group requirements by source file and show completion status for each file.
- ⏳ **REQ-CLI-9**: The `status` command shall display hierarchical completion status showing parent-child relationships with visual indicators.
- ⏳ ⚠️ **REQ-CORE-1**: The tool shall parse requirements from Markdown files using blockquote syntax.
- ⏳ **REQ-CORE-2**: Each requirement shall have a unique ID, description, and may have critical, child, and completed attributes.
- ⏳ **REQ-CORE-3**: The tool shall store requirements in a requirements.lock file in JSON format.
- ⏳ **REQ-CORE-4**: The tool shall provide a Python API for core operations (init, check, lock).
- ⏳ **REQ-CORE-5**: Child relationships shall be described with a "child-of" key. Example: "child-of REQ-123"
- ⏳ **REQ-CORE-6**: Each requirement shall be in a form of "<STRING>-<NUMBER>". Where NUMBER is an integer.
- ⏳ **REQ-PARSER-1**: The parser shall extract requirements from Markdown blockquotes with high accuracy.
- ⏳ **REQ-PARSER-10**: The parser shall raise errors on unknown attributes in requirement definitions.
- ⏳ **REQ-PARSER-11**: The parser shall treat requirement IDs as case-sensitive and not allow IDs with only case differences.
- ⏳ **REQ-PARSER-12**: The parser shall handle blockquotes with inconsistent use of '>' by only considering lines that start with '>'.
- ⏳ **REQ-PARSER-13**: The parser shall ignore Markdown formatting inside blockquotes.
- ⏳ **REQ-PARSER-14**: The parser shall ignore blockquotes that span multiple paragraphs (i.e., with blank lines in between).
- ⏳ **REQ-PARSER-15**: The parser shall raise an error if a circular child relationship is detected.
- ⏳ **REQ-PARSER-16**: The parser shall support requirements and attributes containing Unicode characters.
- ⏳ **REQ-PARSER-17**: The parser shall ignore blockquotes that are commented out in Markdown (e.g., inside ).
- ⏳ **REQ-PARSER-18**: The parser shall handle files with mixed line endings and leading/trailing whitespace.
- ⏳ **REQ-PARSER-2**: The parser shall raise an error if a requirement ID is duplicated in the scanned files.
- ⏳ **REQ-PARSER-3**: The parser shall support the 'critical', 'child', and 'completed' attributes in the blockquote format.
- ⏳ **REQ-PARSER-4**: The parser shall ignore non-blockquote content in Markdown files.
- ⏳ **REQ-PARSER-5**: The parser shall be dependency-free and use only the Python standard library.
- ⏳ **REQ-PARSER-6**: The parser shall handle blockquotes with only an ID or only a description by ignoring them.
- ⏳ **REQ-PARSER-7**: The parser shall ignore extra blank lines or whitespace within blockquotes.
- ⏳ **REQ-PARSER-8**: The parser shall treat attribute keywords (e.g., 'critical', 'child', 'completed') case-insensitively and ignore leading/trailing spaces.
- ⏳ **REQ-PARSER-9**: The parser shall allow multiple 'child:' lines per requirement.
- ⏳ **REQ-PARSER-99**: The parser shall raise errors on duplicated 'child:' lines per requirement.
- ⏳ ⚠️ **REQ-TEST-1**: The tool shall provide unit tests for the Markdown parser.
- ⏳ **REQ-TEST-2**: The tool shall provide integration tests that use the Python API to simulate CLI operations in temporary directories.
- ⏳ **REQ-TEST-3**: Integration tests shall verify that requirements.lock is updated when Markdown files are changed.
- ⏳ **REQ-TEST-4**: Integration tests shall verify that duplicate requirement IDs raise an error.

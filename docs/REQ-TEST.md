> REQ-TEST-1
> The parser shall provide unit tests for the Markdown parser.
> critical
> child-of: REQ-CORE-1
> child-of: REQ-PARSER-1

> REQ-TEST-2
> The application code shall provide integration tests that use the Python API to simulate MkDocs plugin operations in temporary directories.
> child-of: REQ-CORE-1

> REQ-TEST-3
> Integration tests shall verify that reqsnake.lock is updated when Markdown files are changed.
> child-of: REQ-CORE-1

> REQ-TEST-4
> Integration tests shall verify that duplicate requirement IDs raise an error.
> child-of: REQ-CORE-1 
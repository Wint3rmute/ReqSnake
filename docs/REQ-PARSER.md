# Markdown Parser

> REQ-PARSER-0
>
> A valid requirement is a blockquote with unique requirement ID as the first line in the form of `STRING-NUMBER`, requirement description as a second line and additional fields as lines below.
>
> critical
>
> child-of: REQ-PARSER-1

> REQ-PARSER-1
>
> The Markdown parser shall extract requirements from Markdown blockquotes compliant with the specified format.
>
> child-of: REQ-CORE-1
>
> critical

> REQ-PARSER-2
>
> The parser shall raise an error if a requirement ID is duplicated in the scanned files.
>
> child-of: REQ-PARSER-0

> REQ-PARSER-3
> The parser shall support the 'critical', 'child', and 'completed' attributes in the blockquote format.
> child-of: REQ-CORE-2

> REQ-PARSER-4
>
> Child relationships shall be described with a "child-of" key. Example: "child-of REQ-123"
>
> child-of: REQ-CORE-3

> REQ-PARSER-5
> The parser shall be dependency-free and use only the Python standard library.
> child-of: REQ-PARSER-1

Todo: this should be changed to raise errors instead?

> REQ-PARSER-6
> The parser shall handle blockquotes with only an ID or only a description by ignoring them.
> child-of: REQ-PARSER-1

> REQ-PARSER-7
> The parser shall ignore extra blank lines or whitespace within blockquotes.
> child-of: REQ-CORE-1

> REQ-PARSER-8
> The parser shall treat attribute keywords (e.g., 'critical', 'child-of', 'completed') case-insensitively and ignore leading/trailing spaces.
> child-of: REQ-PARSER-0

> REQ-PARSER-9
> The parser shall allow multiple 'child-of:' lines per requirement, allowing linking a requirement to multiple parents.
> child-of: REQ-CORE-2

> REQ-PARSER-10
> The parser shall raise errors on unknown attributes in requirement definitions.
> child-of: REQ-PARSER-0

> REQ-PARSER-11
> The parser shall treat requirement IDs as case-sensitive and not allow IDs with only case differences.
> child-of: REQ-PARSER-1

> REQ-PARSER-12
> The parser shall handle blockquotes with inconsistent use of '>' by only considering lines that start with '>'.
> child-of: REQ-CORE-1

> REQ-PARSER-13
> The parser shall ignore Markdown formatting inside blockquotes.
> child-of: REQ-PARSER-1

> REQ-PARSER-14
> The parser shall ignore blockquotes that span multiple paragraphs (i.e., with blank lines in between).
> child-of: REQ-PARSER-1

> REQ-PARSER-16
> The parser shall support requirements and attributes containing Unicode characters.
> child-of: REQ-CORE-1

> REQ-PARSER-17
> The parser shall ignore blockquotes that are commented out in Markdown comment blocks.
> child-of: REQ-CORE-1

> REQ-PARSER-18
> The parser shall handle files with mixed line endings and leading/trailing whitespace.
> child-of: REQ-CORE-1

> REQ-PARSER-19
> The parser shall raise errors on duplicated 'child-of:' lines per requirement.
> child-of: REQ-CORE-2

> REQ-PARSER-20
> ReqSnake shall allow for specification of filesystem paths to be ignored during requirements scanning. A file `.requirementsignore` shall be used to specify the list of filesystem paths to ignore, similar to how .gitignore works.
> child-of: REQ-CORE-1

> REQ-PARSER-21
> The parser shall ignore non-blockquote content in Markdown files.
> child-of: REQ-PARSER-1

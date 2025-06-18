> REQ-PARSER-1
> The parser shall extract requirements from Markdown blockquotes with high accuracy.
> child: REQ-CORE-1

> REQ-PARSER-2
> The parser shall raise an error if a requirement ID is duplicated in the scanned files.
> child: REQ-CORE-2

> REQ-PARSER-3
> The parser shall support the 'critical', 'child', and 'completed' attributes in the blockquote format.
> child: REQ-CORE-2

> REQ-PARSER-4
> The parser shall ignore non-blockquote content in Markdown files.
> child: REQ-CORE-1

> REQ-PARSER-5
> The parser shall be dependency-free and use only the Python standard library.
> child: REQ-CORE-1

> REQ-PARSER-6
> The parser shall handle blockquotes with only an ID or only a description by ignoring them.
> child: REQ-CORE-1

> REQ-PARSER-7
> The parser shall ignore extra blank lines or whitespace within blockquotes.
> child: REQ-CORE-1

> REQ-PARSER-8
> The parser shall treat attribute keywords (e.g., 'critical', 'child', 'completed') case-insensitively and ignore leading/trailing spaces.
> child: REQ-CORE-2

> REQ-PARSER-9
> The parser shall allow multiple 'child:' lines per requirement and ignore duplicate child IDs.
> child: REQ-CORE-2

> REQ-PARSER-10
> The parser shall ignore unknown attributes in blockquotes.
> child: REQ-CORE-2

> REQ-PARSER-11
> The parser shall treat requirement IDs as case-sensitive and not allow IDs with only case differences.
> child: REQ-CORE-2

> REQ-PARSER-12
> The parser shall handle blockquotes with inconsistent use of '>' by only considering lines that start with '>'.
> child: REQ-CORE-1

> REQ-PARSER-13
> The parser shall ignore Markdown formatting inside blockquotes.
> child: REQ-CORE-1

> REQ-PARSER-14
> The parser shall ignore blockquotes that span multiple paragraphs (i.e., with blank lines in between).
> child: REQ-CORE-1

> REQ-PARSER-15
> The parser shall raise an error if a circular child relationship is detected.
> child: REQ-CORE-2

> REQ-PARSER-16
> The parser shall support requirements and attributes containing Unicode characters.
> child: REQ-CORE-1

> REQ-PARSER-17
> The parser shall ignore blockquotes that are commented out in Markdown (e.g., inside <!-- ... -->).
> child: REQ-CORE-1

> REQ-PARSER-18
> The parser shall handle files with mixed line endings and leading/trailing whitespace.
> child: REQ-CORE-1 
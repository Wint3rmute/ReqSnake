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
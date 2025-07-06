# Requirements

This directory stores the requirements of ReqSnake. I figured that I should track the requirements of ReqSnake with ReqSnake, using anything else would make me look like a hypocrite!

- This file - core requirements
- [REQ-PARSER.md](./REQ-PARSER.md) - Markdown parser requirements
- [REQ-OUTPUT.md](./REQ-OUTPUT.md) - Output generation and MkDocs plugin requirements
- [REQ-TEST.md](./REQ-TEST.md) - Requirements regarding testing of ReqSnake

## ReqSnake - core requirements

> REQ-CORE-1
>
> ReqSnake shall parse requirements from MkDocs Markdown files using blockquote syntax.
>
> critical

> REQ-CORE-2
> A valid requirement is a blockquote with unique requirement ID as the first line, requirement description as a second line and additional fields as lines below.
> critical

> REQ-CORE-3
> Each requirement ID shall be in a form of "<STRING>-<NUMBER>". Where NUMBER is an integer.
> child-of REQ-CORE-2
> critical

> REQ-PARSER-1
> The Markdown parser shall extract requirements from Markdown blockquotes compliant with the specified format.
> child-of: REQ-CORE-1
> child-of: REQ-CORE-2
> child-of: REQ-CORE-3

> REQ-CORE-4
> The tool shall provide a MkDocs plugin interface for managing requirements.
> critical

> REQ-CORE-5
> Child relationships shall be described with a "child-of" key. Example: "child-of REQ-123"
> critical

> REQ-CORE-7
> A requirement can only be marked as completed once all of its child requirements have been marked as completed
> critical

> REQ-CORE-8
> The core operations shall be independent from MkDocs' library.
> critical

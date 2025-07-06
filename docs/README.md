# Overview

This directory stores the requirements of ReqSnake. I figured that I should track the requirements of ReqSnake with ReqSnake, using anything else would make me look like a hypocrite!

- This file - core requirements
- [REQ-PARSER.md](./REQ-PARSER.md) - Markdown parser requirements
- [REQ-OUTPUT.md](./REQ-OUTPUT.md) - Output generation and MkDocs plugin requirements
- [REQ-TEST.md](./REQ-TEST.md) - Requirements regarding testing of ReqSnake

## ReqSnake - core requirements

> REQ-CORE-0
>
> ReqSnake shall allow the user to manage & trace requirements.
>
> critical

> REQ-CORE-1
>
> ReqSnake shall parse requirements from Markdown files.
>
> critical
>
> child-of: REQ-CORE-0

> REQ-CORE-2
>
> ReqSnake shall integrate with MkDocs, acting as an MkDocs plugin.
>
> critical
>
> child-of: REQ-CORE-0

> REQ-PARSER-1
> The Markdown parser shall extract requirements from Markdown blockquotes compliant with the specified format.
>
> child-of: REQ-CORE-1

> critical

> REQ-CORE-5
>
> The tool shall allow the user to define child relationships
>
> critical
>
> child-of: REQ-CORE-0

> REQ-CORE-7
>
> A requirement can only be marked as completed once all of its child requirements have been marked as completed
>
> critical
>
> child-of: REQ-CORE-0

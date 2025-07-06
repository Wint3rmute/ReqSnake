# 🐍 ReqSnake

Turn your MkDocs documentation into a powerful requirements management system!
ReqSnake extracts, validates, and visualizes project requirements directly from
your existing Markdown files.

Full introduction available in [GitHub README](https://github.com/Wint3rmute/ReqSnake).

## Overview

This directory stores the requirements of ReqSnake. I figured that I should track the requirements of ReqSnake with ReqSnake, using anything else would make me look like a hypocrite!

- This file - core requirements
- [REQ-PARSER.md](./REQ-PARSER.md) - Markdown parser requirements
- [REQ-OUTPUT.md](./REQ-OUTPUT.md) - Output generation and MkDocs plugin requirements
- [REQ-CHECKS.md](./REQ-CHECKS.md) - Requirements regarding checking/validating requirements
- [REQ-TEST.md](./REQ-TEST.md) - Requirements regarding testing of ReqSnake

## Core requirements

Also called L0 requirements in some jargons. Here are
high-level requirements about ReqSnake. The requirements below
are the first thing to read when learning about how ReqSnake
should work. They are all marked as `critical` and form the
roots of the requirements hierarchy:

> REQ-CORE-0
>
> ReqSnake shall allow the user to manage & trace requirements.
>
> critical

---

> REQ-CORE-1
>
> ReqSnake shall parse requirements from Markdown files.
>
> critical
>
> child-of: REQ-CORE-0

---

> REQ-CORE-2
>
> ReqSnake shall integrate with MkDocs as a plugin.
>
> critical
>
> child-of: REQ-CORE-0

---

> REQ-CORE-3
>
> ReqSnake allow the user to define parent-child relationships between requirements.
>
> critical
>
> child-of: REQ-CORE-0

---

> REQ-CORE-4
>
> A requirement can only be marked as completed once all of its child requirements have been marked as completed
>
> critical
>
> child-of: REQ-CORE-0
>
> child-of: REQ-CORE-3

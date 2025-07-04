# Requirements

This directory stores the requirements of ReqSnake. I figured that I should track the requirements of ReqSnake with ReqSnake, using anything else would make me look like a hypocrite!

- This file - core requirements
- [REQ-CLI.md](./REQ-CLI.md) - CLI interface requirements
- [REQ-PARSER.md](./REQ-PARSER.md) - Markdown parser requirements
- [REQ-OUTPUT.md](./REQ-OUTPUT.md) - Output formats requirements
- [REQ-TEST.md](./REQ-TEST.md) - Requirements regarding testing of ReqSnake

## ReqSnake - core requirements

(first 2 core requirements are defined in [README.md](../README.md)).

> REQ-CORE-4
> The tool shall provide a command-line interface (CLI) for managing requirements.
> critical

> REQ-CORE-5
> Child relationships shall be described with a "child-of" key. Example: "child-of REQ-123"
> critical

> REQ-CORE-7
> A requirement can only be marked as completed once all of its child requirements have been marked as completed
> critical

> REQ-CORE-8
> The tool shall provide a CLI Python API for core operations.
> critical

> REQ-CORE-9
> The tool shall store requirements in a reqsnake.lock file in JSON format. The file shall be used to compare differences when making changes to requirements.
> critical
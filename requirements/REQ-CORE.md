> REQ-CORE-1
> The tool shall parse requirements from Markdown files using blockquote syntax.
> critical

> REQ-CORE-2
> Each requirement shall have a unique ID, description, and may have critical, child, and completed attributes.
> critical

> REQ-CORE-3
> The tool shall store requirements in a reqsnake.lock file in JSON format. The file shall be used to compare differences when making changes to requirements.
> critical

> REQ-CORE-4
> The tool shall provide a command-line interface (CLI) for managing requirements.
> critical

> REQ-CORE-5
> Child relationships shall be described with a "child-of" key. Example: "child-of REQ-123"
> critical

> REQ-CORE-6
> Each requirement shall be in a form of "<STRING>-<NUMBER>". Where NUMBER is an integer.
> critical

> REQ-CORE-7
> A requirement can only be marked as completed once all of its child requirements have been marked as completed
> critical

> REQ-CORE-8
> The tool shall provide a CLI Python API for core operations. 
> critical

> REQ-CORE-9
> The tool shall provide tools for visualisation of the current state of requirements.
> critical

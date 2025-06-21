# 🐍 ReqSnake

ReqSnake is a dead-simple Python script for tracking requirements defined in a set of Markdown documents.

![Image containing requirements status report and a requirements diagram](./docs/demo.jpg)

## 📄 But what is a requirement?

Citing [Wikipedia](https://en.wikipedia.org/wiki/Requirements_management):

> In engineering, a requirement is a condition that must be satisfied for the output of a work effort to be acceptable. It is an explicit, objective, clear and often quantitative description of a condition to be satisfied by a material, design, product, or service.

Proper specification of requirements is a critical field in Systems Engineering, especially when coordinating large interdisciplinary projects.

## 🤔 Why a script to track them?

We, programmers, like to be smart about the tools we use. We dislike huge, GUI-based programs, hogging our CPU or bloating our experience with dozens of popups. "We like to keep things simple", we say to ourselves.

Well, you can't solve documentation only using a bunch of Markdown documents! You need a bit more than that.

And don't get me wrong, there's a ton of amazing Markdown tooling around there:

- 📚 MkDocs
- 🗒️ Joplin
- 🏗️ Hugo
- 🦄 Zola
- ✨ You name it!

However, in my engineering niche, I found a piece missing - ability to manage system requirements within my Markdown documentation.

## 🏢 What exists already?

Huge, proprietary programs like:

- [IBM DOORS](https://www.ibm.com/docs/en/engineering-lifecycle-management-suite/doors/9.7.0?topic=overview-doors)
- [Enterprise architect](https://sparxsystems.com/)
- [Jama Software](https://www.jamasoftware.com/)

### 🐍 How is `ReqSnake` better?

- It is a simple Python CLI
    - No dependencies
    - No strings attached
- It lets you manage dependencies/ via Markdown
    - **Simple blockquote-based syntax for defining requirements, no need to butcher your existing documents**
- It is smart about change tracking
    - ...yeah we just commit a lockfile to `git`
    - `reqsnake.lock` file is used for change detection
    - It can warn you about deleting important dependencies
- Want extra functionality? Extend ReqSnake by using its Pythonic API instead of the CLI

## ✍️ Requirements Syntax Example

Requirements are defined in Markdown blockquotes, one per requirement. Supported attributes:

- `critical` — marks a requirement as critical
- `child-of` — specifies a parent relationship (no cycles allowed)
- `completed` — marks a requirement as completed

Example:

```
> REQ-1
> The system shall support user authentication.
> critical
> child-of: REQ-0
> completed

> REQ-2
> The system shall store user credentials securely.
```

## 🚀 Features

- **No dependencies:** Only the Python standard library is used.
- **Blockquote-based Markdown syntax:** Human-readable, easy to edit.
- **Requirements hierarchy:** Use `child-of` to define relationships.
- **Change tracking:** Uses a `reqsnake.lock` file for precise diffing.
- **CLI commands:**
    - `reqsnake.py init` — scan Markdown files and generate `reqsnake.lock`.
    - `reqsnake.py check` — compare the lockfile to Markdown requirements. Shows which file each changed requirement comes from.
    - `reqsnake.py lock` — update the lockfile. Idempotent: only updates if needed.
- **Validation workflow:** All changes are validated with `./check.sh` (runs tests, type checks, and linter).
- **Google-style docstrings and modern Python:** All code is documented and type-annotated.

## ⚡ Quick Start example

- `reqsnake.py init` — initialize ReqSnake in the current working directory
    - This will scan the existing directory for Markdown files and generate a `reqsnake.lock`
- `reqsnake.py check` — will read the current `reqsnake.lock` file and check if it is up-to-date with the requirements defined in the Markdown documentation in your working directory.
    - If there are changes, the difference between `reqsnake.lock` file and the currently defined requirements will be displayed, including the file path for each changed requirement.
- `reqsnake.py lock` — will update the `reqsnake.lock` file to reflect the currently defined requirements in your Markdown files. If nothing has changed, the lockfile is left untouched.

## ⭐ Additional reading

- [ARCHITECTURE.md](./ARCHITECTURE.md) for how I structure the code
- [NOTES.md](./NOTES.md) for my working notes

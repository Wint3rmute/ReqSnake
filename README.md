# 🐍 ReqSnake

ReqSnake is a dead-simple Python script for tracking requirements defined in a set of Markdown documents.

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

However, in my engineering niche, I found a piece missing - possibility to manage system requirements using a markdown-friendly syntax.

## 🏢 What exists already?

Huge, proprietary programs like:

- IBM DOORS 
- Enterprise architect

### 🐍 How is `ReqSnake` better?

- It is a simple Python script
    - No dependencies
    - No strings attached
- It lets you manage dependencies via Markdown
    - **Markdown syntax to define a requirement is blockquote-based and well-defined**
- It is smart about change tracking
    - It simply uses `git`
    - It keeps a `requirements.lock` file for more fine-grained change detection
    - It can warn you about deleting important dependencies

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
- **Change tracking:** Uses a `requirements.lock` file for precise diffing.
- **CLI commands:**
    - `reqsnake.py init` — scan Markdown files and generate `requirements.lock`.
    - `reqsnake.py check` — compare the lockfile to Markdown requirements. Shows which file each changed requirement comes from.
    - `reqsnake.py lock` — update the lockfile. Idempotent: only updates if needed.
- **Validation workflow:** All changes are validated with `./check.sh` (runs tests, type checks, and linter).
- **Google-style docstrings and modern Python:** All code is documented and type-annotated.

## ⚡ Quick Start example

- `reqsnake.py init` — initialize ReqSnake in the current working directory
    - This will scan the existing directory for Markdown files and generate a `requirements.lock`
- `reqsnake.py check` — will read the current `requirements.lock` file and check if it is up-to-date with the requirements defined in the Markdown documentation in your working directory.
    - If there are changes, the difference between `requirements.lock` file and the currently defined requirements will be displayed, including the file path for each changed requirement.
- `reqsnake.py lock` — will update the `requirements.lock` file to reflect the currently defined requirements in your Markdown files. If nothing has changed, the lockfile is left untouched.

## ❓ Questions to be asked

- How to mark requirements so that it is human-readable and markdown-friendly?
    - Use blockquotes and IDs like `ABC-123`
    - For example, when making a plane:
        - `MECH-123` would be a requirement for the mechanical team
        - `AVIO-15` would be something for avionics
        - `SW-33` would be on-board software for the plane
- How to generate a lockfile with all defined requirements at a given point in time?
    - This is done with `reqsnake.py init` and produces a JSON file
- How to mark some requirements as `critical`, so that `reqsnake.py` throws an error if they are ever removed?
    - Add `critical` as an attribute in the blockquote
- How to mark some requirements as children of other requirements?
    - Use `child-of` attributes (no cycles allowed)
- How to mark requirements as `completed`?
    - Add `completed` as an attribute in the blockquote
- How to track completion status of requirements and their child requirements?
    - Use the `completed` attribute and the hierarchy features


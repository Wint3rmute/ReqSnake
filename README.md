# 🐍 ReqSnake

ReqSnake is a dead-simple Python script for tracking requirements defined in a set of Markdown documents.

![Image containing requirements status report and a requirements diagram](./docs/demo.jpg)
<i style="text-align: center;">Screenshot of requirements status report and requirements diagram, generate by SnakeReq.</i>

## 📄 But what is a requirement?

Citing [Wikipedia](https://en.wikipedia.org/wiki/Requirements_management):

> In engineering, a requirement is a condition that must be satisfied
> for the output of a work effort to be acceptable. It is an explicit,
> objective, clear and often quantitative description of a condition
> to be satisfied by a material, design, product, or service.

Proper specification of requirements is a critical field in Systems
Engineering, especially when coordinating interdisciplinary projects.

### 🤔 Why track requirements?

Requirements define what you should deliver as a result of your
project. They are usually broken down into smaller sub-requirements,
which are tackled by teams/engineers and delivered separately.
Requirements management tools help you manage the process of breaking
down requirements and trace how the completion of sub-requirements
results in completion of high-level project goals.

If you're completely new to requirements management, think about them like
[User Stories](https://en.wikipedia.org/wiki/User_story), but more formalized
and with dependencies. A dependency tree to be specific!

## ✍️ Requirements Syntax in ReqSnake

Suppose you have existing project documentation in Markdown, a loose set of
notes, or something like a MkDocs website. Open up your docs and start defining
requirements as Markdown blockquotes in any file you see fit. Example:

```
> REQ-CORE-1
> ReqSnake shall parse requirements from Markdown files using blockquote syntax.
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
```

That's all you have to do to start working with ReqSnake! Simply extend your
existing Markdown documentation with requirements definition and start tracing
what you're building.

From now on, ReqSnake will:

- Check dependencies of requirements before letting you mark them as completed
- Report errors when attempting to complete a requirement with uncompleted child dependencies
- Raise errors upon encountering duplicate requirement IDs
- Generate reports showing the status of requirements and their dependencies
- Help you review the changes you've made to dependencies

## ⚡ Installation & quick-start guide

```bash
# Download ReqSnake from this GitHub repo
wget https://raw.githubusercontent.com/Wint3rmute/ReqSnake/refs/heads/main/reqsnake.py

# Make the file executable for convenience
chmod +x reqsnake.py

# Initialize ReqSnake:
#   - Scan Markdown files in your working directory
#   - Read all defined requirements
#   - Save them into `reqsnake.lock`
./reqsnake.py init
```

Go ahead and write some requirements now. Once you have them, write:

```bash
# Check the correctnes and display changes made to the requirements
./reqsnake.py check

# Snapshot the current version of requirements to `reqsnake.lock`
./reqsnake.py lock

# Display the completion status of defined requirements
./reqsnake.py status

# Generate a Markdown report with the status of your requirements
./reqsnake.py status-markdown
# ^ Tip: add this into your static site generation process!
```

## 💎 Value Proposition

Between small, one-person projects and huge corporate enterprise-grade
software, there's a large niche of medium-sized projects. They may be done by a
sigle team or by a small/medium company. Across such projects, Markdown is a
widely used tool, mostly for documentation. There's a ton of amazing Markdown
tooling around:

- 📚 [MkDocs](https://www.mkdocs.org/)
- 🗒️ [Joplin](https://joplinapp.org/)
- 🏗️ [Hugo](https://gohugo.io/)
- 🦄 [Zola](https://www.getzola.org/)
- ✨ You name it!

However, I found a piece missing - ability to manage project requirements
within my Markdown documentation!

### 🏢 What software exists currently?

Huge, expensive, proprietary programs like:

- [IBM DOORS](https://www.ibm.com/docs/en/engineering-lifecycle-management-suite/doors/9.7.0?topic=overview-doors)
- [Enterprise architect](https://sparxsystems.com/)
- [Jama Software](https://www.jamasoftware.com/)

### 🐍 How is `ReqSnake` better?

- It's free and open-source
- Core functionality is provided by a simple CLI application
  - No dependencies
  - No strings attached
- It fits into your existing workflow
  - Simple blockquote-based syntax for defining requirements
  - No need to butcher your existing documents
  - No need to migrate into a proprietary system
  - You own your documentation

Want extra functionality? Extend ReqSnake by using its Pythonic API instead of the CLI:

```python
from reqsnake import reqsnake_lock

requirements = reqsnake_lock().requirements
for requirement in requirements:
  print("Processing", requirement.req_id)
  # Do anything you want here
```

## 📖 Examples

ReqSnake's requirements are managed by ReqSnake! See the [requirements directory](./requirements/).

ReqSnake's dependency status, generated by ReqSnake: [requirements-status.md](./requirements-status.md).

## 🚀 Features

- **No dependencies:** Only the Python standard library is used.
- **Blockquote-based Markdown syntax:** Human-readable, easy to edit.
- **Requirements hierarchy:** Use `child-of` to define relationships.
- **Change tracking:** Uses a `reqsnake.lock` file for precise diffing.
- **Reasonably fast:** A stress test parsing 10'000 requirements takes ~700ms on my machine
  - The application should easily scale to thousands of requirements
- **CLI commands:**
  - `reqsnake.py init` — scan Markdown files and generate `reqsnake.lock`.
  - `reqsnake.py check` — compare the lockfile to Markdown requirements. Shows which file each changed requirement comes from.
  - `reqsnake.py lock` — update the lockfile. Idempotent: only updates if needed.

## ⭐ Additional reading

- [ARCHITECTURE.md](./ARCHITECTURE.md) for how I structure the code
- [NOTES.md](./NOTES.md) for my working notes

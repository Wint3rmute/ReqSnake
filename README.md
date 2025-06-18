# Require.py

Require.py is a dead-simple Python script for tracking requirements defined in a set of Markdown documents.

## But what is a requirement?

Citing Wikipedia:

> In engineering, a requirement is a condition that must be satisfied for the output of a work effort to be acceptable. It is an explicit, objective, clear and often quantitative description of a condition to be satisfied by a material, design, product, or service.

Proper specification of requirements is a critical field in Systems Engineering, especially when coordinating large interdisciplinary projects.

## Why a script to track them?

We, programmers, like to be smart about the tools we use. We dislike huge, GUI-based programs, hogging our CPU or bloating our experience with dozens of popups. "We like to keep things simple", we say to ourselves.

Well, you can't solve documentation only using a bunch of Markdown documents! You need a bit more than that.

And don't get me wrong, there's a ton of amazing Markdown tooling around there:

- MkDocs
- Joplin
- Hugo
- Zola
- You name it!

However, in my engineering niche, I found a piece missing - possibility to manage system requirements using a markdown-friendly syntax.

## What exists already?

Huge, proprietary programs like:

- IBM DOORS 
- Enterprise architect

### How is `require.py` better?

- It is a simple Python script
    - No dependencies
    - No strings attached
- It lets you manage dependencies via Markdown
    - Markdown syntax to define a dependency is yet to be defined
- It is smart about change tracking
    - It simply uses `git`
    - It keeps a `requirements.lock` file for more fine-grained change detection
    - It can warn you about deleting important dependencies

## Quick Start example

- `require.py init` - initialize `require.py` in the current working directory
    - This will scan the existing directory for Markdown files and generate a `requirements.lock`
- `require.py check` - will read the current `requirements.lock` file and check if it is up-to-date with the requirements defined in the Markdown documentation in your working directory.
    - If there are changes, the difference between `requirements.lock` file and the currently defined requirements will be displayed
- `require.py lock` - will update the `requirements.lock` file to reflect the currently defined requirements in your Markdown files

## Questions to be asked

- How to mark requirements so that it is human-readable and markdown-friendly?
    - I want requirements to be named like `ABC-123`
    - A bunch of numbers + a number
    - For example, when making a plane:
        - `MECH-123` would be a requirement for the mechanical team
        - `AVIO-15` would be something for avionics
        - `SW-33` would be on-board software for the plane
- How to generate a lockfile with all defined requirements at a given point in time?
    - This should be a JSON file
- I want to mark some requirements as `critical`, so that `require.py` throws an error if they are ever removed
- I want to mark some requirements as children of other requirements
    - No cycles are allowed
- I want to mark requirements as `completed`
- I want to track completion status of requirements and their child requirements


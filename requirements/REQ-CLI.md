> REQ-CLI-1
> The tool shall provide a command-line interface (CLI) for managing requirements.
> critical

> REQ-CLI-2
> The CLI shall support the commands: init, check, and lock.

> REQ-CLI-3
> The CLI shall print the Markdown files being scanned during operations.

> REQ-CLI-LOCK-IDEMPOTENT
> When the user runs `require.py lock` and the requirements have not changed since the last lock, the CLI shall print a message indicating that the lockfile is already up-to-date (e.g., "requirements.lock is already up-to-date."). Only print the "requirements.lock updated" message if the lockfile was actually changed. 
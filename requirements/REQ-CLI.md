> REQ-CLI-1
> The CLI shall support the commands: init, check, lock, and status.
> child-of: REQ-CORE-4

> REQ-CLI-2
> The CLI shall print the Markdown files being scanned during operations.
> child-of: REQ-CLI-1

> REQ-CLI-3
> When the user runs `reqsnake.py lock` and the requirements have not changed since the last lock, the CLI shall print a message indicating that the lockfile is already up-to-date (e.g., "requirements.lock is already up-to-date."). Only print the "requirements.lock updated" message if the lockfile was actually changed.
> child-of: REQ-CLI-1

> REQ-CLI-4
> When displaying changed requirements with `reqsnake.py check`, the application shall display the path to the file containing each requiremement which has undergone any kind of change
> child-of: REQ-CLI-1

> REQ-CLI-5
> The application shall allow for specification of filesystem paths to be ignored during requirements scanning. A file `.requirementsignore` shall be used to specify the list of filesystem paths to ignore, similar to how .gitignore works

> REQ-CLI-6
> The CLI shall provide a `status` command that displays completion status of requirements.
> child-of: REQ-CLI-2
> child-of: REQ-CORE-9

> REQ-CLI-7
> The `status` command shall display total requirements count, completed requirements count and percentage, and critical requirements status.
> child-of: REQ-CLI-6

> REQ-CLI-8
> The `status` command shall group requirements by source file and show completion status for each file.
> child-of: REQ-CLI-6

> REQ-CLI-9
> The `status` command shall display hierarchical completion status showing parent-child relationships with visual indicators.
> child-of: REQ-CLI-6

> REQ-OUTPUT-1
> The CLI shall provide a command to generate a Markdown file containing the status of all currently defined requirements, relying solely on the requirements.lock file. The output shall be suitable for inclusion in documentation or reports.
> child-of: REQ-CORE-9

> REQ-OUTPUT-2
> The tool shall provide a command to generate a Graphviz diagram (in dot format) representing the requirements hierarchy, using the requirements.lock file as input. The output shall be suitable for visualization tools and similar in spirit to the status-md command. 
> child-of: REQ-CORE-9

> REQ-OUTPUT-3
> The requirements.lock file shall contain the version of application which generated it.
> child-of: REQ-CORE-3
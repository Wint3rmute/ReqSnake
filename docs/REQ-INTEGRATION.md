# MkDocs Integration

Requirements which define how ReqSnake shall integrate with MkDocs to ensure
modularity and clean architecture.

> REQ-INTEGRATION-1
>
> ReqSnake be implemented according to MkDocs best practices regarding plugin development.
>
> child-of: REQ-CORE-2

MkDocs has a great [guide to installing, using and creating MkDocs
Plugins](https://www.mkdocs.org/dev-guide/plugins/). SnakeReq shall be
compliant with this guide.

---

> REQ-INTEGRATION-2
>
> The core operations performed by SnakeReq shall be independent from MkDocs' library.
>
> child-of: REQ-INTEGRATION-1

This requirement ensures that MkDocs-specific logic will not be mixed together
with ReqSnake's domain logic. This will make ReqSnake resilient to any changes
which might happen in MkDocs. If there ever comes a time when ReqSnake needs to
migrate to a different documentation system, architectural decisions stemming
from this requirement will make the migration easier.

---

> REQ-INTEGRATION-3
>
> ReqSnake shall provide error handling according to MkDocs best practices.
>
> child-of: REQ-INTEGRATION-1

Python Exceptions which don't follow MkDocs plugin developer guidelines will
display large stack traces, unfriendly to the user. Compliance with MkDocs'
guides will improve UX.

> REQ-INTEGRATION-4
>
> ReqSnake shall raise "mkdocs.exceptions.PluginError" upon errors
>
> child-of: REQ-INTEGRATION-3

---

> REQ-INTEGRATION-5
>
> ReqSnake shall provide logging according to MkDocs best practices.
>
> child-of: REQ-INTEGRATION-1

TODO: implement.

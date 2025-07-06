Requirements defining how ReqSnake will validate parsed requirements
definition, prior to any further processing. As as start, parent requirement
for all of the checks:

> REQ-CHECKS-0
>
> ReqSnake shall run checks (validation) of parsed requirements prior to further processing.
>
> child-of: REQ-CORE-0

As the `child-of` requirements allow `child->parent` linking, ReqSnake shall
detect when a non-existing parent requirement is used:

> REQ-CHECKS-1
>
> ReqSnake shall raise errors when attempting to link a requirement to a non-existing parent.
>
> child-of: REQ-CHECKS-0

Any kind of linking brings danger of cyclical relationships and endless loops.
ReqSnake shall detect dependency cycles and raise errors immediately:

> REQ-CHECKS-2
>
> ReqSnake shall raise an error if a circular child relationship is detected.
>
> child-of: REQ-CHECKS-0

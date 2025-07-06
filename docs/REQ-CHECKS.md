> REQ-CHECKS-0
>
> ReqSnake shall run checks (validation) of parsed requirements prior to further processing.
>
> child-of: REQ-CORE-0

> REQ-CHECKS-1
>
> ReqSnake shall raise errors when attempting to link a requirement to a non-existing parent.
>
> child-of: REQ-CHECKS-0

> REQ-CHECKS-2
>
> ReqSnake shall raise an error if a circular child relationship is detected.
>
> child-of: REQ-CHECKS-0

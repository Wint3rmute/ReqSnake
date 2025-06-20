# Notes

## ❓ Questions yet to be answered

- How to mark some requirements as `critical`, so that `reqsnake.py` throws an error if they are ever removed?
    - Add `critical` as an attribute in the blockquote
- How to mark some requirements as children of other requirements?
    - Use `child-of` attributes (no cycles allowed)
- How to mark requirements as `completed`?
    - Add `completed` as an attribute in the blockquote
- How to track completion status of requirements and their child requirements?
    - Use the `completed` attribute and the hierarchy features

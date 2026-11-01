# Python Type Hints and Data Structures

Python type hints document the expected types of variables, function parameters, and return values. They are not enforced by the Python runtime by default, but static type checkers and frameworks can use them.

## Lists and dictionaries

Use `list[str]` to describe a list of strings and `dict[str, int]` to describe a dictionary with string keys and integer values. For older Python versions, the typing module provides `List` and `Dict`.

## Optional values

Use `str | None` in modern Python to indicate a value may be a string or None. The older equivalent is `Optional[str]`. A default value of None does not automatically make a field optional in every validation framework; field requiredness depends on the model declaration and default.

## TypedDict

`TypedDict` defines the expected keys and value types of a dictionary. It is useful for describing state objects passed between nodes in a workflow. `total=False` makes keys optional.

## Dataclasses

The `dataclasses` module can generate methods such as `__init__` and `__repr__` for classes that primarily store data. Use the `@dataclass` decorator and annotate fields with types.

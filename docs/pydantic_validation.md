# Pydantic Model Validation

Pydantic validates data using Python type annotations. Models commonly inherit from `BaseModel`.

## Defining a model

A model can declare fields such as `name: str` and `age: int`. When a model is created from input data, Pydantic parses and validates the values. Invalid data raises a `ValidationError` containing details about the fields that failed validation.

## Field constraints

Use `Field` to add constraints and metadata. For example, `Field(min_length=1, max_length=100)` constrains a string length. Numeric fields can use `gt`, `ge`, `lt`, and `le` constraints.

## Optional fields and defaults

In Pydantic v2, `nickname: str | None` without a default is required but accepts None. `nickname: str | None = None` is not required and defaults to None. A field with a concrete default is also not required in input.

## Serialization

Use `model_dump()` to convert a model to a Python dictionary. Use `model_dump_json()` to serialize it as JSON. `model_validate()` validates a Python object against a model, while `model_validate_json()` validates JSON input.

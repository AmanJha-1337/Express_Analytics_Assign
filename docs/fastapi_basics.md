# FastAPI Basics

FastAPI is a Python web framework for building APIs with standard Python type hints. It is built on Starlette for web handling and Pydantic for data validation.

## Creating an application

Create an instance with `app = FastAPI()`. A path operation is declared with decorators such as `@app.get("/")` or `@app.post("/items")`. The decorated function handles requests for that path and HTTP method.

## Request validation

FastAPI uses Pydantic models to validate request bodies. Define a class that inherits from `pydantic.BaseModel`, then use it as a function parameter. FastAPI parses JSON, validates fields, and returns a structured validation error when the input is invalid.

## Interactive API documentation

FastAPI automatically provides Swagger UI at `/docs` and ReDoc at `/redoc`. The OpenAPI schema is available at `/openapi.json`. These pages are generated from route definitions, type annotations, and Pydantic models.

## File uploads

Use `UploadFile` and `File` from FastAPI to receive uploaded files. For multiple files, declare a list of `UploadFile` values. File upload requests use multipart form data, so install `python-multipart`. `UploadFile` uses a spooled file and is suitable for larger files than reading the entire request body into memory.

## Dependency injection

Use `Depends` to declare dependencies. FastAPI calls the dependency and injects its result into the path operation. Dependencies can be used for database sessions, authentication, and shared logic.

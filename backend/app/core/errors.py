from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError


class FieldError(dict[str, Any]):
    def __init__(self, field: str, message: str) -> None:
        super().__init__(field=field, message=message)


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        field_errors: list[dict[str, Any]] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.field_errors = field_errors or []


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(code="not_found", message=message, status_code=status.HTTP_404_NOT_FOUND)


def _envelope(code: str, message: str, field_errors: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"detail": {"code": code, "message": message, "field_errors": field_errors or []}}


def _pydantic_field_errors(exc: ValidationError | RequestValidationError) -> list[dict[str, Any]]:
    field_errors: list[dict[str, Any]] = []
    for error in exc.errors():
        loc = ".".join(str(part) for part in error["loc"] if part not in ("body",))
        field_errors.append({"field": loc, "message": error["msg"]})
    return field_errors


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.code, exc.message, exc.field_errors),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_envelope("validation_error", "Request validation failed", _pydantic_field_errors(exc)),
        )

    @app.exception_handler(ValidationError)
    async def handle_pydantic_validation_error(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_envelope("validation_error", "Validation failed", _pydantic_field_errors(exc)),
        )

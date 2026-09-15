from typing import Annotated, Any

from fastapi import Query
from pydantic import BeforeValidator


def blank_to_none(value: Any) -> Any:
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


OptionalIntQuery = Annotated[
    int | None,
    BeforeValidator(blank_to_none),
    Query(),
]

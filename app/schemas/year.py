from pydantic import BaseModel


class YearsResponse(BaseModel):
    years: list[int]

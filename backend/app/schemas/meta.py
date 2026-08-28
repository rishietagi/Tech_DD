from pydantic import BaseModel


class EnumOption(BaseModel):
    value: str
    label: str


class EnumsResponse(BaseModel):
    enums: dict[str, list[EnumOption]]

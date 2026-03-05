from pydantic import BaseModel, ConfigDict, Field


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str


class CompanyUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=255)

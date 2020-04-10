from pydantic import BaseModel, Field


class Error(BaseModel):
    detail: str = Field(..., description='The detail of a HTTPException')
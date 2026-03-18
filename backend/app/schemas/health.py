from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str


class DetailedHealthResponse(BaseModel):
    status: str
    database: str
    redis: str
    version: str

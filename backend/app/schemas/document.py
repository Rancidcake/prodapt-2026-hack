from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    title: str
    filename: str
    chunk_count: int

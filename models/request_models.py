from pydantic import BaseModel
from typing import Optional

class QueryRequest(BaseModel):
    guest_name: Optional[str]
    query: str

class SearchRequest(BaseModel):
    filename: str  # The original filename (or partial) to search for
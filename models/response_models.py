from pydantic import BaseModel

class UploadResponse(BaseModel):
    message: str
    session_id: str

class QueryResponse(BaseModel):
    answer: str

class DeleteSessionResponse(BaseModel):
    message: str
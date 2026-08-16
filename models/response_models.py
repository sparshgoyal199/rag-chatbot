from pydantic import BaseModel
from datetime import datetime
 
class UploadResponse(BaseModel):
    message: str
    session_id: str

class QueryResponse(BaseModel):
    answer: str

class DeleteSessionResponse(BaseModel):
    message: str

class UploadResponse(BaseModel):
    id: int
    filename: str
    pdf_summary: str
    upload_date: datetime
    pdf_url: str
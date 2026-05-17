from fastapi import APIRouter
from pipeline.rag_pipeline import RAGPipeline
from fastapi import UploadFile,File
from typing import Annotated
from models.response_models import UploadResponse
upload_router = APIRouter() 

@upload_router.post("/upload")
def upload_document(file: Annotated[UploadFile, File(description="A file read as UploadFile")]):
    upload_object = RAGPipeline()
    session_id = upload_object.ingest_document(file=file)
    return UploadResponse(message="Document uploaded and ingested successfully.", session_id="12346")
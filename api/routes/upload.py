from fastapi import APIRouter
from pipeline.rag_pipeline import RAGPipeline
from fastapi import UploadFile,File
from typing import Annotated
from models.response_models import UploadResponse
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

upload_router = APIRouter() 

@upload_router.post("/upload")
def upload_document(file: Annotated[UploadFile, File(description="A file read as UploadFile")]):
    try:
        upload_object = RAGPipeline()
        return StreamingResponse(
            upload_object.ingest_document(file),
            media_type="text/event-stream"
        )
        # session_id = upload_object.ingest_document(file=file)
        # yield session_id
        #return UploadResponse(message="Document uploaded and ingested successfully.", session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=405, detail=f"Error occurred while uploading document: {str(e)}")
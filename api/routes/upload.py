from fastapi import APIRouter, Depends
from fastapi import UploadFile,File
from typing import Annotated
from dependencies import get_current_user
from fastapi import HTTPException
import traceback
from pipeline.ingest_workflow import ingestion_workflow

upload_router = APIRouter() 

@upload_router.post("/upload")
async def upload_document(file: Annotated[UploadFile, File(description="A file read as UploadFile")], current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user["id"]
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        initial_state = {"file": file, "user_id": user_id}
        final_state = await ingestion_workflow.ainvoke(initial_state)
        return "Document Uploaded Successfully"
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=405, detail=f"Error occurred while uploading document: {str(e)}")
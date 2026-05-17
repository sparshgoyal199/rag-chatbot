from fastapi import APIRouter
from pipeline.rag_pipeline import RAGPipeline
from models.response_models import DeleteSessionResponse
session_router = APIRouter()

@session_router.delete("/session/{session_id}")
def delete_session(session_id: str):
    session_object = RAGPipeline()
    session_object.delete_session(session_id=session_id)
    return DeleteSessionResponse(message="Session deleted successfully.")
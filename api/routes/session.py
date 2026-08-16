from fastapi import APIRouter
from pipeline.rag_pipeline import RAGPipeline
from models.response_models import DeleteSessionResponse
session_router = APIRouter()

@session_router.post("/session/{session_id}")
async def delete_session(session_id: str):
    session_object = RAGPipeline()
    await session_object.delete_session(session_id=session_id)
    return DeleteSessionResponse(message="Session deleted successfully.")
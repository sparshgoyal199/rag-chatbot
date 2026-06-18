from fastapi import APIRouter
from pipeline.rag_pipeline import RAGPipeline
from models.request_models import QueryRequest
from models.response_models import QueryResponse
query_router = APIRouter()

@query_router.post("/query")
async def query_document(query: QueryRequest):
    try:
        query_object = RAGPipeline()
        query_response = await query_object.query_document(session_id=query.session_id, query=query.query)
        return query_response
    except Exception as e:
        print(e)
from fastapi import APIRouter
from pipeline.rag_pipeline import RAGPipeline
from models.request_models import QueryRequest
from models.response_models import QueryResponse
query_router = APIRouter()

@query_router.post("/query")
def query_document(query: QueryRequest):
    query_object = RAGPipeline()
    query_response = query_object.query_document(session_id=query.session_id, query=query.query)
    return QueryResponse(answer=query_response[0], source=query_response.source[1])

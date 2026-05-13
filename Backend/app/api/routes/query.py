from fastapi import APIRouter

query_router = APIRouter()

query_router.post("/query")
def query():
    pass
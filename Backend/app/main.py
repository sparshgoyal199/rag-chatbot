from fastapi import FastAPI
from .api.routes.session import session_router
from .api.routes.query import query_router
from .api.routes.upload import upload_router

app = FastAPI()

app.include_router(session_router)
app.include_router(query_router)
app.include_router(upload_router)
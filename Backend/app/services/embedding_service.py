from core.embedding_models import bge_model
import math 

def generate_chunks_embeddings(chunks: list[dict]):
    chunks_embeddings = []
    for chunk in chunks:
        content = chunk.get("content", "")
        embedding = bge_model.encode(content)
        embedding.tolist()
        chunks_embeddings.append(embedding)
    return chunks_embeddings

def generate_query_embeddings(query:str):
    pass

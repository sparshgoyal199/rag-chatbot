from fastapi import UploadFile
from services.embedding_service import generate_chunks_embeddings, generate_query_embeddings
from utils.helpers import generate_session
from services.document_service import parse_document
from services.chunk_service import create_chunks
from services.vector_service import store_vectors
from services.retrieval_service import response_generator, retrieve_relevant_chunks
from services.vector_service import delete_collection


class RAGPipeline:
    
    def ingest_document(self, file: UploadFile):
        session_id = generate_session()
        structured_doc = parse_document(file)
        chunks_payload, avg_doc_length = create_chunks(structured_doc)
        embedded_chunks = generate_chunks_embeddings(chunks_payload)
        store_vectors(session_id, chunks_payload, embedded_chunks, avg_doc_length)
        return session_id
    
    def query_document(self, session_id: str, query: str):
        embedded_query = generate_query_embeddings(query)
        relevant_chunks_payload = retrieve_relevant_chunks(session_id, embedded_query, query)
        response = response_generator(query, relevant_chunks_payload)
        return response

    def delete_session(self, session_id: str):
        delete_collection(session_id)
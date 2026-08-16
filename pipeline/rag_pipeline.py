from fastapi import UploadFile
from services.embedding_service import generate_embeddings
from utils.helpers import generate_pdf_id
from services.document_service import parse_document
from services.chunk_service import create_chunks
from services.vector_service import store_vectors
from services.retrieval_service import response_generator, retrieve_relevant_chunks
from services.vector_service import delete_collection
import json


class RAGPipeline:
    
    async def ingest_document(self, file: UploadFile):
        try:
            session_id = generate_pdf_id()

            yield f"data: {json.dumps({
                'type': 'updates',
                'stage': 'modal',
                'message': 'Modal server started.'
            })}\n\n"

            structured_doc = await parse_document(file)

            yield f"data: {json.dumps({
                'type': 'updates',
                'stage': 'parsing',
                'message': 'PDF parsed successfully.'
            })}\n\n"

            chunks_payload, avg_doc_length = create_chunks(structured_doc)

            yield f"data: {json.dumps({
                'type': 'updates',
                'stage': 'chunking',
                'message': 'Chunks created successfully.'
            })}\n\n"

            embedded_chunks = await generate_embeddings(
                query=None,
                chunks=chunks_payload,
            )

            yield f"data: {json.dumps({
                'type': 'updates',
                'stage': 'embedding',
                'message': 'Embeddings generated successfully.'
            })}\n\n"

            store_vectors(
                session_id,
                chunks_payload,
                embedded_chunks,
                avg_doc_length,
            )

            yield f"data: {json.dumps({
                'type': 'updates',
                'stage': 'vector_store',
                'message': 'Vectors stored successfully.'
            })}\n\n"

            yield f"data: {json.dumps({
                'type': 'completed',
                'stage': 'completed',
                'session_id': session_id,
                'message': 'Document ingestion completed successfully.'
            })}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({
                'type': 'error',
                'stage': 'error',
                'message': str(e)
            })}\n\n"
    
    async def query_document(self, session_id: str, query: str):
        embedded_query = await generate_embeddings(query=query,chunks=None)
        relevant_chunks_payload = await retrieve_relevant_chunks(session_id, embedded_query, query)
        response = await response_generator(query, relevant_chunks_payload)
        return response

    async def delete_session(self, session_id: str):
        await delete_collection(session_id)
def retrieve_relevant_chunks(session_id: str, embedded_query: list[float], original_query: str):
    # will use vector_service for actually querying the db, it will not have its own logic of querying the db
    # It will only have logic of hybrid_search, and BM25 sparse vector
    pass

def response_generator(query: str, relevant_chunks: list[dict]):
    pass

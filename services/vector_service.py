from qdrant_client import QdrantClient, models
from core.qdrant import client
import uuid
from fastapi import HTTPException
def exist_collection(session_id: str) -> bool:
    try:
        client.get_collection(session_id)
        return True
    except Exception as e:
        print(f"Collection {session_id} does not exist: {e}")
        return False

def create_collection(session_id: str):
    client.create_collection(
        collection_name=session_id,
        vectors_config={
            "content_dense_vector": models.VectorParams(size=384, 
            distance=models.Distance.DOT,
            hnsw_config=models.HnswConfigDiff(
                m=32,
                ef_construct=128,
                full_scan_threshold=100
            ),
            quantization_config=models.ScalarQuantization(
                scalar=models.ScalarQuantizationConfig(type=models.ScalarType.INT8, always_ram=True, quantile=0.99)
                # Remaining values will get be scaled better from this quantile thing except outlier, they will surely get distorted    
                # jitna mai quantile ki value km kronga, usse unn quantile value ki asli scaled na hone par, unko galat dimension assign ho jaaeygi - that means effect is that we are some distorting the dimensions of the vector
            ),
            on_disk=True
            )
        },
        sparse_vectors_config={
            "heading_sparse_vector": models.SparseVectorParams(index=models.SparseIndexParams(on_disk=False),modifier=models.Modifier.IDF)
        },
    )

def store_vectors(session_id: str, chunks: list[dict], vectors: list[list[float]], avg_doc_length: float):
    if not exist_collection(session_id):
        create_collection(session_id)
    points = build_points(chunks, vectors, avg_doc_length)
    client.upsert(
        collection_name=session_id,
        points=points
    )
    print("Vectors stored successfully in collection:", session_id)
    # Code to store vectors in the collection would go here

def build_points(chunks_payload: list[dict], vectors: list[list[float]], avg_doc_length: float) -> list[models.PointStruct]:
    points=[
        models.PointStruct(
            id=uuid.uuid4().hex,
            vector={
                "content_dense_vector": vector,
                "heading_sparse_vector": models.Document(
                    text=payload["heading"] or "",
                    options={"language": "english", "avg_len": avg_doc_length},
                    model="Qdrant/bm25",
                ),
            },
            payload={"heading": payload["heading"], "content": payload["content"], "page_no": payload["page_no"], "filename": payload["filename"]},
        )
        for payload,vector in zip(chunks_payload, vectors)
        ]
    return points

def delete_collection(session_id: str):
    if exist_collection(session_id):
        client.delete_collection(session_id)
        print(f"Collection {session_id} deleted successfully.")
    else:
        print(f"Collection {session_id} does not exist. No deletion performed.")

def retrieve_results(session_id: str, prefetch: list[models.Prefetch]):
    if not exist_collection(session_id):
        raise HTTPException(status_code=403, detail=f"Session {session_id} not found.Please reupload the document and try again.")
    
    results = client.query_points(
        collection_name=session_id,
        prefetch=prefetch,
        query=models.RrfQuery(rrf=models.Rrf(weights=[1.5, 1.0])),
        search_params=models.SearchParams(
            quantization=models.QuantizationSearchParams(rescore=False)
        ),
        with_payload=True,
        limit=5,
    )
    return results


from qdrant_client import QdrantClient, models

client.create_collection(
    collection_name="CC_book",
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

import uuid

client.upsert(
    collection_name="CC_book",
    points=[
        models.PointStruct(
            id=uuid.uuid4().hex,
            vector={
                "content_dense_vector": doc["vector"],
                "heading_sparse_vector": models.Document(
                    text=doc["properties"]["Heading"] or "",
                    options={"language": "english"},
                    model="Qdrant/bm25",
                ),
            },
            payload={"Heading": doc["properties"]["Heading"], "Content": doc["properties"]["Content"], "Page_no": doc["properties"]["Page_No"], "Filename": doc["properties"]["Filename"]},
        )
        for doc in minilm_data_objects
    ]
)
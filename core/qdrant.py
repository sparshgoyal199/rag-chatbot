from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Document
from dotenv import load_dotenv
import os

load_dotenv()

# connect to Qdrant Cloud
client = AsyncQdrantClient(
    url="https://9ad67d77-0546-4231-abd6-778771474b21.sa-east-1-0.aws.cloud.qdrant.io",
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=60,
    cloud_inference=True
)
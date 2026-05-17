from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Document
from dotenv import load_dotenv
import os

load_dotenv()

# connect to Qdrant Cloud
client = QdrantClient(
    url="https://9ad67d77-0546-4231-abd6-778771474b21.sa-east-1-0.aws.cloud.qdrant.io",
    api_key=os.getenv("QDRANT_API_KEY"),
    cloud_inference=True
)
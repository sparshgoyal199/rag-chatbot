from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer

MAX_TOKENS = 500  # set to a small number for illustrative purposes

tokenizer = HuggingFaceTokenizer(
    tokenizer=AutoTokenizer.from_pretrained("BAAI/bge-small-en-v1.5"),
    max_tokens=MAX_TOKENS,  # optional, by default derived from `tokenizer` for HF case
)

from sentence_transformers import SentenceTransformer
bge_model = SentenceTransformer('BAAI/bge-small-en-v1.5')
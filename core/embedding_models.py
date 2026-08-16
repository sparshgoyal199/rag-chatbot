from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer
import modal
import os

MAX_TOKENS = 500
#MAX_TOKENS = 800

tokenizer = HuggingFaceTokenizer(
    tokenizer=AutoTokenizer.from_pretrained("Qwen/Qwen3-Embedding-8B"),
    max_tokens=MAX_TOKENS,
)


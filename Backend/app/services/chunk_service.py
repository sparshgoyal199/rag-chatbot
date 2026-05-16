from cv2 import threshold
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer
from docling.chunking import HybridChunker, HierarchicalChunker
from docling_core.transforms.chunker.hierarchical_chunker import (
    ChunkingDocSerializer,
    ChunkingSerializerProvider,
    TripletTableSerializer
)
from docling_core.transforms.serializer.markdown import MarkdownParams
from core.embedding_models import tokenizer
from docling.datamodel.document import ConversionResult

class MDTableSerializerProvider(ChunkingSerializerProvider):
    def get_serializer(self, doc):
        return ChunkingDocSerializer(
            doc=doc,
            params=MarkdownParams(
                image_placeholder="<!-- image -->"
            ),
        )

def generate_chunks_payload(chunks: list[dict]) -> list[dict]:
    min_chunk_length = 100
    chunks_payload = []
    for idx, chunk in enumerate(chunks):
        text = chunk.text.strip()

        # Step 1: Filter small chunks
        if len(text) <= min_chunk_length:
            continue
        
        # Step 3: Extract heading
        heading = None
        if hasattr(chunk.meta, "headings") and chunk.meta.headings:
            heading = chunk.meta.headings[0]

        # Step 4: Extract doc_items info (page_no + reference)
        page_no = None

        if chunk.meta.doc_items:
            first_item = chunk.meta.doc_items[0]

            # page number
            if first_item.prov:
                page_no = first_item.prov[0].page_no

        filename = None
        if chunk.meta.origin and chunk.meta.origin.filename:
            filename = chunk.meta.origin.filename

        # Step 5: Build dictionary
        properties = {
            "heading": heading,
            "content": text,
            "page_no": page_no,
            "filename": filename
        }
        chunks_payload.append(properties)
    return chunks_payload

def create_chunks(structured_doc: ConversionResult) -> list[dict]:
    chunker = HybridChunker(
        tokenizer=tokenizer,
        serializer_provider=MDTableSerializerProvider(),
        merge_peers=True,  # optional, defaults to True
    )
    chunk_iter = chunker.chunk(dl_doc=structured_doc)
    chunks = list(chunk_iter)
    chunks_payload = generate_chunks_payload(chunks)
    return chunks_payload
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

# MODEL_ID = "BAAI/bge-small-en-v1.5"

# image = modal.Image.debian_slim().pip_install(
#     "torch==2.6.0",
#     "sentence-transformers==3.4.1",
#     "fastapi[standard]",
#     "docling==2.75.0",
#     "docling-core==2.66.0",
#     "docling-ibm-models==3.11.0",
#     "docling-parse==5.4.0"
# )

# app = modal.App("embeddings-generator", image=image)

# GPU_CONFIG = "A10G"
# CACHE_DIR = "/cache"
# cache_vol = modal.Volume.from_name("hf-hub-cache", create_if_missing=True)


# @app.cls(
#     gpu=GPU_CONFIG,
#     volumes={CACHE_DIR: cache_vol},
#     scaledown_window=60 * 30,
#     timeout=60 * 30,
# )

# @modal.concurrent(max_inputs=15)
# class EmbeddingModel:

#     @modal.enter()
#     def setup(self):
#         from sentence_transformers import SentenceTransformer
#         self.model = SentenceTransformer(
#             MODEL_ID,
#             cache_folder=CACHE_DIR,
#         )
        
#         os.environ["HF_HOME"] = CACHE_DIR
#         os.environ["DOCLING_CACHE_DIR"] = CACHE_DIR
#         from docling.datamodel.base_models import InputFormat
#         from docling.datamodel.pipeline_options import (
#             PdfPipelineOptions
#         )
#         from docling.document_converter import DocumentConverter, PdfFormatOption
#         from docling.datamodel.layout_model_specs import DOCLING_LAYOUT_HERON
#         from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions

#         pipeline_options = PdfPipelineOptions()
#         pipeline_options.accelerator_options = AcceleratorOptions(
#             num_threads=4,   # safe default, CPU threads for pre/post processing
#             device=AcceleratorDevice.CUDA
#         )
#         pipeline_options.do_ocr = False  
#         pipeline_options.layout_options.model_spec = DOCLING_LAYOUT_HERON
#         pipeline_options.do_table_structure = False
#         pipeline_options.table_structure_options.do_cell_matching = False
#         pipeline_options.generate_page_images = False
#         pipeline_options.generate_picture_images = False
#         pipeline_options.do_formula_enrichment = False
#         pipeline_options.do_code_enrichment = False
#         pipeline_options.do_picture_description = False
#         pipeline_options.do_picture_classification = False
#         pipeline_options.generate_parsed_pages = False

#         doc_converter = DocumentConverter(
#             allowed_formats=[InputFormat.PDF],
#             format_options={
#                 InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
#             }
#         )

#         doc_converter.initialize_pipeline(InputFormat.PDF)
#         self.docling_obj = doc_converter

#     def _encode_query(self, query: str) -> list[float]:
#         return self.model.encode(query, normalize_embeddings=True).tolist()

#     def _encode_chunks(self, chunks: list[dict]) -> list[list[float]]:
#         texts = [chunk.get("content", "") for chunk in chunks]
#         return self.model.encode(texts, normalize_embeddings=True).tolist()

#     def _parse_pdf(self, filename,file_bytes):
#         from io import BytesIO
#         from docling_core.types.io import DocumentStream
#         file_stream = BytesIO(file_bytes)
#         docling_input_obj = DocumentStream(name=filename, stream=file_stream)
#         structured_doc = self.docling_obj.convert(docling_input_obj)
#         return {"docling_document":structured_doc.document.export_to_dict()}

#     @modal.method()
#     def embed_chunks(self, chunks: list[dict]) -> list[list[float]]:
#         return self._encode_chunks(chunks)

#     @modal.method()
#     def embed_query(self, query: str) -> list[float]:
#         return self._encode_query(query)
    
#     @modal.method()
#     def parsing_pdf(self,filename,file_bytes):
#         return self._parse_pdf(filename,file_bytes)

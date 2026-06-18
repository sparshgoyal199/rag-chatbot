from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.layout_model_specs import DOCLING_LAYOUT_HERON

def document_converter_configurations():
    pipeline_options = PdfPipelineOptions()

    pipeline_options.do_ocr = False  

    pipeline_options.layout_options.model_spec = DOCLING_LAYOUT_HERON

    pipeline_options.do_table_structure = False
    pipeline_options.table_structure_options.do_cell_matching = False

    pipeline_options.generate_page_images = False
    pipeline_options.generate_picture_images = False

    pipeline_options.do_formula_enrichment = False
    pipeline_options.do_code_enrichment = False
    pipeline_options.do_picture_description = False
    pipeline_options.do_picture_classification = False

    pipeline_options.generate_parsed_pages = False


    doc_converter = DocumentConverter(
        allowed_formats=[InputFormat.PDF],
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    doc_converter.initialize_pipeline(InputFormat.PDF)
    return doc_converter

doc_converter = document_converter_configurations()
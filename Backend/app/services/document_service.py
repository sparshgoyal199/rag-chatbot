import logging
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    ThreadedPdfPipelineOptions,
    TableFormerMode,
    PdfPipelineOptions
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.layout_model_specs import DOCLING_LAYOUT_HERON, DOCLING_LAYOUT_HERON_101, DOCLING_LAYOUT_EGRET_MEDIUM, DOCLING_LAYOUT_V2, LAYOUTLMV3_BASE
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

# Configure accelerator options for GPU


_log = logging.getLogger(__name__)

# Faster rendering
IMAGE_RESOLUTION_SCALE = 2.0

input_doc_path = r"C:\Users\hp\OneDrive\Desktop\rag_bot\middle_10_pages.pdf"


def main():
    logging.basicConfig(level=logging.INFO)

    # Use threaded options (important)
    pipeline_options = PdfPipelineOptions()

    # ---------- OCR ----------
    pipeline_options.do_ocr = False  

    # ---------- Layout ----------
    pipeline_options.layout_options.model_spec = DOCLING_LAYOUT_HERON

    pipeline_options.do_table_structure = False
    pipeline_options.table_structure_options.do_cell_matching = False
    #pipeline_options.table_structure_options.mode = TableFormerMode.FAST

    # ---------- Images (disable for speed) ----------
    #pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
    pipeline_options.generate_page_images = False
    pipeline_options.generate_picture_images = False
    # ---------- Disable enrichment (prevents heavy backend loading) ----------
    pipeline_options.do_formula_enrichment = False
    pipeline_options.do_code_enrichment = False
    pipeline_options.do_picture_description = False
    pipeline_options.do_picture_classification = False

    # ---------- Memory optimization ----------
    pipeline_options.generate_parsed_pages = False

    # ---------- Thread tuning (optional speed boost) ----------

    # Create converter
    doc_converter = DocumentConverter(
        allowed_formats=[InputFormat.PDF],
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    return doc_converter

doc_converter = main()

#Load all the necessary models and initialize the pipeline (important to do this before processing documents to avoid loading models during processing which can cause timeouts)
import time
start_time = time.time()
doc_converter.initialize_pipeline(InputFormat.PDF)
init_runtime = time.time() - start_time
_log.info(f"Pipeline initialized in {init_runtime:.2f} seconds.")


# Process document
start_time = time.time()
conv_res = doc_converter.convert(input_doc_path)

import logging
from collections import Counter
from docling_core.types.doc import DocItemLabel, SectionHeaderItem

log = logging.getLogger(__name__)

def find_repeating_headers(doc, min_repeat: int = 4) -> set:
    """
    Collect all SECTION_HEADER texts that appear multiple times
    — these are likely running page headers.
    """
    header_texts = []
    for item, _ in doc.iterate_items():
        if item.label == DocItemLabel.SECTION_HEADER:
            header_texts.append(item.text.strip())

    counts = Counter(header_texts)
    return {text for text, count in counts.items() if count >= min_repeat}

def is_false_page_header(item, doc, repeating_headers: set, threshold: float = 0.08) -> bool:
    """Check if an item is a false page header (repeated text or at top of page)."""
    if item.text.strip() in repeating_headers:
        return True
    for prov in item.prov:
        page = doc.pages.get(prov.page_no)
        if page is None:
            continue
        if prov.bbox.t >= page.size.height * (1 - threshold):
            return True
    return False

def remove_false_headers_from_doc(doc, repeating_headers: set, threshold: float = 0.08):
    """
    Removes false page headers from the docling document.
    Re-parents their children to the preceding real heading before deleting.
    """

    # ── Step 1: Identify all false headers ──────────────────────────────────
    false_headers = []
    false_header_refs = set()

    for item, _ in doc.iterate_items():
        if item.label == DocItemLabel.SECTION_HEADER:
            if is_false_page_header(item, doc, repeating_headers, threshold):
                false_headers.append(item)
                false_header_refs.add(item.self_ref)
                log.info(f"Flagged for removal → '{item.text.strip()}'")

    if not false_headers:
        log.info("No false headers found to remove.")
        return doc

    # ── Step 2: Re-parent children of each false header ─────────────────────
    for header in false_headers:
        if not header.children:
            continue # no children to re-parent, skip

        # Find the parent node of this false header
        parent_node = header.parent.resolve(doc=doc)

        # Find the index of this false header among its parent's children
        header_ref = header.get_ref()
        header_index = None
        for i, child_ref in enumerate(parent_node.children):
            if child_ref.cref == header_ref.cref:
                header_index = i
                break

        if header_index is None:
            log.warning(f"Could not find header '{header.text.strip()}' in parent's children, skipping re-parent.")
            continue

        # Walk backwards through siblings to find the nearest real heading
        real_heading = None
        for i in range(header_index - 1, -1, -1):
            sibling = parent_node.children[i].resolve(doc)
            if (isinstance(sibling, SectionHeaderItem)
                    and sibling.self_ref not in false_header_refs):
                real_heading = sibling
                break

        if real_heading:
            # Move each child of the false header to the real heading
            for child_ref in list(header.children): # copy list since _move_subtree modifies it
                child = child_ref.resolve(doc)
                doc._move_subtree(old_subroot=child, new_subroot=real_heading)
            log.info(f"Re-parented children of '{header.text.strip()}' → under '{real_heading.text.strip()}'")
        else:
            # No preceding real heading found — shift children up to the parent level
            log.info(f"No preceding heading found for '{header.text.strip()}', shifting children up.")
            doc._shift_up(old_subroot=header)
            # _shift_up already removes the header from its parent's children,
            # so we should NOT delete it again via delete_items.
            # Remove it from our false_headers list to avoid double-removal.
            false_header_refs.discard(header.self_ref)

    # ── Step 3: Delete the now-childless false headers ──────────────────────
    # Only delete headers that weren't already removed by _shift_up
    headers_to_delete = [h for h in false_headers if h.self_ref in false_header_refs]
    if headers_to_delete:
        doc.delete_items(node_items=headers_to_delete)

    log.info(f"Successfully removed {len(false_headers)} false header(s) from document.")
    return doc

from docling_core.types.doc import DocItemLabel
from collections import Counter
def find_repeating_headers(doc, min_repeat: int = 4) -> set:
    """
    Collect all SECTION_HEADER texts that appear on
    multiple pages — these are likely running page headers.
    """
    header_texts = []

    for item, _ in doc.iterate_items():
        if item.label == DocItemLabel.SECTION_HEADER:
            header_texts.append(item.text.strip())

    counts = Counter(header_texts)
    repeating = {text for text, count in counts.items() if count >= min_repeat}


    return repeating

repeating_headers = find_repeating_headers(conv_res_Reference_1, min_repeat=4)

# Step 2: Remove them directly from the doc object
doc = remove_false_headers_from_doc(conv_res_Reference_1, repeating_headers, threshold=0.08)

def validate_docling_document(doc):
    """
    Full cross-reference consistency check for DoclingDocument.
    Run this before passing to HybridChunker.
    """
    errors = []

    # --- Step 1: Build ground truth index maps ---
    # self_ref must match actual position
    for i, item in enumerate(doc.texts):
        expected = f"#/texts/{i}"
        if item.self_ref != expected:
            errors.append(f"doc.texts[{i}].self_ref='{item.self_ref}' expected '{expected}'")

    for i, item in enumerate(doc.tables):
        expected = f"#/tables/{i}"
        if item.self_ref != expected:
            errors.append(f"doc.tables[{i}].self_ref='{item.self_ref}' expected '{expected}'")

    for i, item in enumerate(doc.groups):
        expected = f"#/groups/{i}"
        if item.self_ref != expected:
            errors.append(f"doc.groups[{i}].self_ref='{item.self_ref}' expected '{expected}'")

    # --- Step 2: Build resolution lookup ---
    ref_map = {}
    for i, item in enumerate(doc.texts):
        ref_map[f"#/texts/{i}"] = item
    for i, item in enumerate(doc.tables):
        ref_map[f"#/tables/{i}"] = item
    for i, item in enumerate(doc.pictures):
        ref_map[f"#/pictures/{i}"] = item
    for i, item in enumerate(doc.groups):
        ref_map[f"#/groups/{i}"] = item
    ref_map["#/body"] = doc.body
    ref_map["#/furniture"] = doc.furniture

    def check_ref(ref_str, context):
        if ref_str not in ref_map:
            errors.append(f"Dangling ref '{ref_str}' in {context}")
            return False
        return True

    # --- Step 3: Walk every node's .children and .parent ---
    all_nodes = (
        [(f"#/texts/{i}", item) for i, item in enumerate(doc.texts)]
        + [(f"#/tables/{i}", item) for i, item in enumerate(doc.tables)]
        + [(f"#/pictures/{i}", item) for i, item in enumerate(doc.pictures)]
        + [(f"#/groups/{i}", item) for i, item in enumerate(doc.groups)]
        + [("#/body", doc.body), ("#/furniture", doc.furniture)]
    )

    for own_ref, node in all_nodes:
        # Check parent pointer is resolvable
        if node.parent is not None:
            parent_cref = node.parent.cref
            if check_ref(parent_cref, f"{own_ref}.parent"):
                # Check that parent actually lists this node as child
                parent_node = ref_map[parent_cref]
                child_crefs = [c.cref for c in parent_node.children]
                if own_ref not in child_crefs:
                    errors.append(
                        f"{own_ref}.parent='{parent_cref}' but parent does NOT list {own_ref} in .children"
                    )

        # Check all children are resolvable
        for child_ref in node.children:
            if check_ref(child_ref.cref, f"{own_ref}.children"):
                # Check child's parent points back
                child_node = ref_map[child_ref.cref]
                if child_node.parent is None or child_node.parent.cref != own_ref:
                    errors.append(
                        f"{own_ref}.children has '{child_ref.cref}' but its .parent='{getattr(child_node.parent, 'cref', None)}'"
                    )

    # --- Step 4: Detect items in doc.texts not reachable from body tree ---
    reachable = set()
    def walk(node):
        reachable.add(node.self_ref)
        for child_ref in node.children:
            if child_ref.cref in ref_map:
                walk(ref_map[child_ref.cref])
    walk(doc.body)

    for i, item in enumerate(doc.texts):
        if item.self_ref not in reachable:
            errors.append(f"doc.texts[{i}] (self_ref='{item.self_ref}') is UNREACHABLE from doc.body")

    if errors:
        print(f"❌ Found {len(errors)} consistency error(s):")
        for e in errors:
            print(f"  - {e}")
    else:
        print("✅ DoclingDocument is consistent.")

    return errors

print(validate_docling_document(doc))
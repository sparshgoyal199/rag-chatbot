# Docling Technical Report: Assembly Stage (Layout-Only Configuration)

When Docling operates with **only the layout model enabled** (no OCR, no Table Structure Extraction, no vision-language models), the system relies purely on bounding boxes, basic text heuristics, and rule-based reading order mapping to produce the final `DoclingDocument`.

Here is the exact code-level behavior of the pipeline during this configuration.

## 1. Execution Flow

The full call chain from layout completion to the final `DoclingDocument` is:

1. `docling.pipeline.base_pipeline.BasePipeline.execute()`
2. `↳ StandardPdfPipeline._build_document()` (spawns multithreaded stages)
3. `  ↳ PageAssembleModel.__call__()` (process layout clusters per page into intermediate elements)
4. `↳ StandardPdfPipeline._assemble_document()` (flattens features across the entire doc)
5. `  ↳ ReadingOrderModel.__call__()` (sorts nodes and constructs target document)
6. `    ↳ ReadingOrderPredictor.predict_reading_order()` (calculates sorting algorithm)
7. `    ↳ ReadingOrderModel._readingorder_elements_to_docling_doc()` (final document conversion)
8. `↳ BasePipeline._enrich_document()` (no-op since enrichment options are False)

## 2. Assembly Mechanism

The transformation of Layout predictions into structured elements happens natively inside [docling/models/stages/page_assemble/page_assemble_model.py](file:///c:/Users/hp/OneDrive/Desktop/rag_learning_materials/docling/docling/models/stages/page_assemble/page_assemble_model.py).

**Transformation Logic (`PageAssembleModel.__call__`)**:
The pipeline iterates over every `cluster` inside `page.predictions.layout.clusters`. Based on `cluster.label`, it parses the layout cells into an intermediate data structure:
- **Texts** (`LayoutModel.TEXT_ELEM_LABELS`): Text lines are joined and sanitized via `self.sanitize_text()`. It forms a `TextElement`.
- **Tables** (`LayoutModel.TABLE_LABELS`): Since `page.predictions.tablestructure` is missing (disabled), it hits a fallback branch:
  ```python
  if not tbl:  # fallback: add table without structure
      tbl = Table(label=cluster.label, id=cluster.id, text="", otsl_seq=[], 
                  table_cells=[], cluster=cluster, page_no=page.page_no)
  ```
- **Figures** (`LayoutModel.FIGURE_LABEL`): Since figure classification is disabled, it forms an empty shell:
  ```python
  if not fig:  # fallback: add figure without classification
      fig = FigureElement(label=cluster.label, id=cluster.id, text="", 
                          data=None, cluster=cluster, page_no=page.page_no)
  ```

All these elements are saved individually per page in `page.assembled = AssembledUnit(elements=..., headers=..., body=...)`.

## 3. Models vs Algorithms

In a Layout-only configuration, the Assembly stage is **100% algorithm (rule-based)**. No Machine Learning or Deep Learning models are actively invoked during Assembly.

- [PageAssembleModel](file:///c:/Users/hp/OneDrive/Desktop/rag_learning_materials/docling/docling/models/stages/page_assemble/page_assemble_model.py#30-157): Exclusively relies on if/else logic mapping labels to Python dataclasses (`TextElement`, [Table](file:///c:/Users/hp/OneDrive/Desktop/rag_learning_materials/docling/docling/datamodel/pipeline_options.py#76-91), etc.).
- [ReadingOrderModel](file:///c:/Users/hp/OneDrive/Desktop/rag_learning_materials/docling/docling/models/stages/reading_order/readingorder_model.py#42-432): Uses `ReadingOrderPredictor` which belongs to `docling_ibm_models.reading_order.reading_order_rb` (`rb` stands for rule-based). It does not load any `.onnx` or `.safetensors` files.

## 4. Reading Order Resolution

Since only layout bounding boxes are available, reading order is determined geometrically.

[ReadingOrderModel](file:///c:/Users/hp/OneDrive/Desktop/rag_learning_materials/docling/docling/models/stages/reading_order/readingorder_model.py#42-432) (located in [docling/models/stages/reading_order/readingorder_model.py](file:///c:/Users/hp/OneDrive/Desktop/rag_learning_materials/docling/docling/models/stages/reading_order/readingorder_model.py)) converts the intermediate `PageElement` items into `ReadingOrderPageElement` nodes (which possess `l, r, b, t` spatial properties) and feeds them into the structural algorithm:

```python
sorted_elements = self.ro_model.predict_reading_order(page_elements)
el_to_captions_mapping = self.ro_model.predict_to_captions(sorted_elements)
```
The `ReadingOrderPredictor` executes a heuristic sorting pipeline:
- It typically assesses vertical overlaps, columnar grouping, and text indentation to sort bounding boxes top-down, left-to-right (common XY-cut algorithms).
- It infers `el_merges_mapping` (combining broken paragraph fragments based on margin distances).
- It associates figure labels and tables to adjacent caption text based on proximity thresholding (`predict_to_captions`).

## 5. Post-processing Pipeline

The final step in [execute()](file:///c:/Users/hp/OneDrive/Desktop/rag_learning_materials/docling/docling/pipeline/base_pipeline.py#64-94) is `self._enrich_document(conv_res)`.

**What is skipped?**
Because the pipeline options (e.g., `do_picture_classification = False`, `do_code_enrichment = False`) are turned off, the `self.enrichment_pipe` models like `DocumentPictureClassifier` or `CodeFormulaVlmModel` evaluate their `self.enabled` flag as `False`. They simply bypass the execution loop yielding nothing.

**What still runs?**
The only mapping rules that still run aggressively are spatial heuristic bindings (e.g. Footnote and Caption binding inside [ReadingOrderModel](file:///c:/Users/hp/OneDrive/Desktop/rag_learning_materials/docling/docling/models/stages/reading_order/readingorder_model.py#42-432)).
- Figures still get bound to text chunks that look like captions via geometric proximity.

## 6. End-to-End Example

**Input**: A Page with 3 Layout clusters: `Title` (Top), `Paragraph` (Middle), [Table](file:///c:/Users/hp/OneDrive/Desktop/rag_learning_materials/docling/docling/datamodel/pipeline_options.py#76-91) (Bottom bounding box).

1. **Layout Output**:
   - `cluster 1`: {label: 'title', bbox: [100, 800, 500, 850]}
   - `cluster 2`: {label: 'text',  bbox: [100, 600, 500, 750]}
   - `cluster 3`: {label: 'table', bbox: [100, 200, 500, 500]}

2. **Intermediate Assembly ([PageAssembleModel](file:///c:/Users/hp/OneDrive/Desktop/rag_learning_materials/docling/docling/models/stages/page_assemble/page_assemble_model.py#30-157))**:
   Flattens into `PageElement` objects:
   - `TextElement`(id=1, label="title", text="Docling Report")
   - `TextElement`(id=2, label="text", text="This is a minimal pipeline.")
   - [Table](file:///c:/Users/hp/OneDrive/Desktop/rag_learning_materials/docling/docling/datamodel/pipeline_options.py#76-91)(id=3, label="table", num_cols=0, num_rows=0, table_cells=[])

3. **Reading Order ([ReadingOrderModel](file:///c:/Users/hp/OneDrive/Desktop/rag_learning_materials/docling/docling/models/stages/reading_order/readingorder_model.py#42-432))**:
   - Spatially orders [1, 2, 3] from top to bottom.
   - Detects `cluster 3` is an empty table with no cells (since `do_table_structure` is disabled).
   
4. **Final `DoclingDocument`**:
   The [_readingorder_elements_to_docling_doc](file:///c:/Users/hp/OneDrive/Desktop/rag_learning_materials/docling/docling/models/stages/reading_order/readingorder_model.py#122-328) iterates the sorted list:
   - Appends a standard Title node.
   - Appends a standard Paragraph node.
   - For the empty table it encounters the rule:
     ```python
     # If no structure, make an empty 1x1 fallback with zero contents
     if element.num_rows == 0 and element.num_cols == 0:
         tbl_data = TableData(num_rows=0, num_cols=0, table_cells=[])
     ```
   - Spits out a generic `DoclingDocument` with nodes `[HeadingItem, TextItem, TableItem (empty)]`.

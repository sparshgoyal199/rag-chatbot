# Docling Layout & Text Extraction Report

This report details the step-by-step process of how Docling's document conversion pipeline (specifically the PDF backend and Layout Model) processes a single PDF page containing:
- 1 Main Heading
- 2 Titles (Subheadings)
- 2 Main Paragraphs

The focus is strictly on how text and bounding boxes are detected and extracted from start to finish.

---

## Step 1: Document Ingestion & PDF Parsing (The Backend)

When the PDF is passed to Docling's `DocumentConverter`, the first component that interacts with it is the **PDF Backend** (usually powered by `pypdfium2`).

1. **Native Text Cell Extraction**: The backend reads the raw PDF data stream. Because the document is a standard PDF (not a scanned image), the text is stored programmatically. 
2. **Character & Line Grouping**: The backend extracts every individual character along with its exact spatial coordinates (bounding box). It groups these characters into raw "text cells" or "words" based on spacing.
3. **Result of Step 1**: At this stage, Docling has a collection of text strings and their precise bounding boxes on the page. However, it *does not yet know* the semantic meaning of these text cells (i.e., it doesn't know which text is the heading, title, or paragraph).

## Step 2: Page Image Rendering

Simultaneously, the PDF backend renders the entire PDF page into a high-resolution bitmap image. This image representation is necessary because the Layout Model is an AI vision model that "looks" at the page just like a human would to understand its visual structure.

## Step 3: Layout Model Inference (The Vision Model)

The rendered page image is fed into Docling's **Layout Predictor** (typically an object detection model like RT-DETR).

1. **Visual Object Detection**: The model scans the visual features of the page (font sizes, negative space, bolding, block shapes).
2. **Bounding Box Prediction**: The model predicts bounding boxes around visual clusters of text and classifies them into semantic categories.
3. **Result for our specific page**: The model will output exactly 5 layout predictions:
   - **`Title`**: 1 bounding box tightly wrapping the Main Heading.
   - **`Section-header`**: 2 separate bounding boxes wrapping the two Titles.
   - **`Text`**: 2 separate bounding boxes wrapping the two Main Paragraphs.

*Note: The Layout Model only predicts bounding boxes and labels (e.g., "This rectangular area is a Paragraph"). It does NOT read the text.*

## Step 4: Assembly & Intersection (Merging Backend and Model)

Now, Docling must bridge the gap between the semantic boxes found by the Layout Model and the raw text cells found by the PDF Backend. This happens in the **Assembly Stage**.

1. **Geometric Matching**: The assembler takes the 5 layout bounding boxes and overlays them onto the raw PDF text cells.
2. **Intersection Calculation**: It calculates the geometric overlap (Intersection over Union - IoU) or containment score. It checks: *"Which raw text cells fall inside this Layout bounding box?"*
   - The text cells forming the large heading will fall inside the Layout Model's `Title` box.
   - The text cells forming the paragraphs will fall precisely inside the Layout Model's `Text` boxes.
3. **Text Assignment**: The text from the PDF cells is assigned to the corresponding layout object. 

## Step 5: Reading Order Resolution

With the 5 semantic blocks fully populated with text and bounding boxes, Docling applies a **Reading Order** algorithm. 
- It sorts the bounding boxes based on two-dimensional coordinates (typically top-to-bottom, left-to-right).
- It generates a sequential flow: Main Heading → Title 1 → Paragraph 1 → Title 2 → Paragraph 2.

## Summary of the Final Output

The final exported `DoclingDocument` will contain an ordered list of elements. Each element will have:
1. **Label**: Identified by the Layout Model (e.g., `Title`, `Section-header`, `Text`).
2. **Bounding Box**: The exact spatial coordinates `[x0, y0, x1, y1]` on the page, refined by the assembly stage.
3. **Text**: The exact string of text natively extracted by the PDF backend, guaranteeing 100% text accuracy without needing OCR.

### Why this dual approach?
By relying on the PDF backend for text and the Layout Vision Model for bounding boxes, Docling avoids the slow speed and hallucination risks of OCR, while achieving near-human semantic understanding of the page structure.

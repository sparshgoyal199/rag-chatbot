minilm_data_objects = []
threshold = 100
import math

for idx, chunk in enumerate(chunks):
    text = chunk.text.strip()

    # Step 1: Filter small chunks
    if len(text) <= threshold:
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
        "Heading": heading,
        "Content": text,
        "Page_No": page_no,
        "Filename": filename
    }

    normalized_vector = minilm_model.encode(text)  # Convert numpy array to list for JSON serialization
    print(math.sqrt(sum(x*x for x in normalized_vector)))
    minilm_data_object = {
        "properties": properties,
        "vector": normalized_vector
    }
    minilm_data_objects.append(minilm_data_object)

print("Total data objects:", len(minilm_data_objects))
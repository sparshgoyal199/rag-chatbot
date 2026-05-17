from qdrant_client import models
from services.vector_service import retrieve_results
from core.llm import groq_client
import json

def prompt_formatter(query: str, 
                     formatted_chunks: str) -> str:

    SYSTEM_PROMPT = """
        You are an intelligent retrieval-augmented generation (RAG) assistant.

        Your task is to answer the user's query ONLY using the provided context items.

        ---

        INSTRUCTIONS:

        1. Read all context items carefully before answering.
        2. Use ONLY the information available in the provided context. Do NOT invent, assume, or hallucinate any information.
        3. If the answer cannot be fully derived from the context, explicitly state that.
        4. Combine information across multiple context items when needed to produce a complete answer.

        ---

        RESPONSE FORMAT:

        - Structure the answer professionally. Use paragraphs, bullet points, or a mix — whichever suits the nature of the question.
        - Simple factual questions → concise paragraph.
        - Explanatory or multi-part questions → bullet points or numbered steps, with a brief lead-in sentence.
        - Avoid unnecessary verbosity, but never sacrifice completeness for brevity.

        ---

        CITATION RULES (very important):

        - Embed citations inline within the answer using the format: [p. X], where X is the page number.
        - Do NOT mention filenames anywhere in the answer.
        - Do NOT place a citation after every sentence. Citations should appear at the level of a complete idea or claim — typically at the end of a paragraph, or at the end of a bullet point that contains a distinct factual claim.
        - If multiple consecutive bullet points all draw from the same page, cite only once at the end of the last point in that group, or note it in a natural way.
        - If a paragraph or section synthesizes information from multiple pages, cite all relevant pages together at the end: [p. 4, p. 11].
        - Never stack citations redundantly. Once a page has been cited for a point, do not re-cite it for the same point in different words.
        - Citations must feel like natural scholarly inline references — not noise appended to every line.

        ---

        OUTPUT FORMAT:

        Return ONLY a JSON object in the following structure:

        {
            "answer": "Your complete, well-structured answer with inline citations like [p. X] placed at the right level of granularity."
        }

        ---

        EXAMPLES:

        Query: What is attention in transformer models?

        Response:
        {
            "answer": "Attention is a mechanism that allows a model to weigh the relevance of different parts of an input sequence when producing each output token. Rather than compressing the entire input into a single fixed vector, attention lets the model dynamically focus on the most relevant tokens at each step [p. 34].\n\nThere are several key properties of attention:\n- It operates across all token pairs simultaneously, making it parallelizable.\n- Scaled dot-product attention divides scores by the square root of the key dimension to prevent gradient saturation.\n- Multi-head attention runs several attention operations in parallel, each learning different relational patterns [p. 36]."
        }

        Query: What are the causes of overfitting?

        Response:
        {
            "answer": "Overfitting occurs when a model learns the training data too closely, capturing noise rather than the underlying pattern. This results in poor generalization to unseen data.\n\nCommon causes include:\n- **Insufficient training data**: With too few examples, the model memorizes rather than generalizes [p. 58].\n- **Excessive model complexity**: A model with too many parameters relative to the data size can fit noise [p. 60].\n- **Lack of regularization**: Without techniques like dropout or weight decay, the model is unconstrained in how it fits the data [p. 61]."
        }
        """

    messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    },
    {
        "role": "user",
        "content": f"""
        Context:
        {formatted_chunks}

        Question:
        {query}
        """
            }
        ]

    return messages

def format_retrieved_chunks(relevant_chunks_payload: list[dict]) -> str:
    formatted_chunks = ""
    for idx,chunk in enumerate(relevant_chunks_payload):
        formatted_chunks += f"[chunk {idx}]\n"
        formatted_chunks += f"heading: {chunk['heading']}\n"
        formatted_chunks += f"content: {chunk['content']}\n"
        formatted_chunks += f"page_no: {chunk['page_no']}\n"
        formatted_chunks += f"filename: {chunk['filename']}\n\n"
    return formatted_chunks

def retrieve__llm_response(prompt: list[dict]) -> str:
    # This function will call the mistral api to get the response for the given prompt
    response = groq_client.chat.completions.create(
        messages=prompt,
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        )
    return response.choices[0].message.content

def retrieve_relevant_chunks(session_id: str, embedded_query: list[float], original_query: str):
    # will use vector_service for actually querying the db, it will not have its own logic of querying the db
    # It will only have logic of hybrid_search, and BM25 sparse vector
    result_payload = []
    prefetch = [
        models.Prefetch(
            query=embedded_query,
            using="content_dense_vector",
            limit=20,
        ),
        models.Prefetch(
            query=models.Document(text=original_query, model="Qdrant/bm25"),
            using="heading_sparse_vector",
            limit=20,
        ),
    ]

    results = retrieve_results(session_id, prefetch)
    for resp in results.points:
        result_payload.append({
            "heading": resp.payload.get("heading", ""),
            "content": resp.payload.get("content", ""),
            "page_no": resp.payload.get("page_no", ""),
            "filename": resp.payload.get("filename", "")
        })
    return result_payload

def response_generator(query: str, relevant_chunks_payload: list[dict]):
    formatted_chunks = format_retrieved_chunks(relevant_chunks_payload)
    prompt = prompt_formatter(query, formatted_chunks)
    llm_response = retrieve__llm_response(prompt)
    return llm_response
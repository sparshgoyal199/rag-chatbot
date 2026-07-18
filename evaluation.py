import os
import sys
import asyncio
import json
from unittest.mock import MagicMock

# Mock the missing legacy vertexai path before importing ragas to avoid package version issues
sys.modules['langchain_community.chat_models.vertexai'] = MagicMock()

from dotenv import load_dotenv
# Load .env file relative to this script directory
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, ".env"))

# Import RAG system services
from services.embedding_service import generate_embeddings
from services.retrieval_service import retrieve_relevant_chunks, response_generator

# Import Ragas and LangChain evaluation dependencies
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
from langchain_openai import ChatOpenAI
from langchain_core.embeddings import Embeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

# 1. Custom Langchain Embeddings wrapper for your Qwen model hosted on Modal.com
class QwenModalEmbeddings(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        chunks = [{"content": text} for text in texts]
        return generate_embeddings(query=None, chunks=chunks)

    def embed_query(self, text: str) -> list[float]:
        return generate_embeddings(query=text, chunks=None)


# 2. Hardcoded evaluation dataset questions & ground truths from 'progit-en.1084.pdf'
EVALUATION_DATA = [
    {
        "question": "What are the rules and syntax for patterns in a .gitignore file?",
        "ground_truth": "Blank lines or lines starting with '#' are ignored. Standard glob patterns work and will be applied recursively throughout the entire working tree. An asterisk '*' matches zero or more characters. [abc] matches any character inside the brackets. A question mark '?' matches a single character. Brackets enclosing characters separated by a hyphen (e.g., [0-9]) match any character in that range. You can use two asterisks '**' to match nested directories (e.g., a/**/z). A leading slash '/' avoids recursive matching (e.g., /TODO only ignores the TODO file in the current directory). A trailing slash '/' specifies a directory (e.g., build/). An exclamation mark '!' negates a pattern."
    },
    {
        "question": "What is a topic branch in Git, and when is it useful?",
        "ground_truth": "A topic branch is a short-lived branch created and used for a single particular feature or related work. It is useful in projects of any size to isolate work on a specific feature, allowing developers to try out ideas, make changes, and discard them easily if they don't work, without cluttering the main line of development or other branches."
    },
    {
        "question": "What is progressive-stability branching (or long-running branches)?",
        "ground_truth": "Progressive-stability branching involves maintaining multiple long-running branches that represent different levels of stability (e.g., master/main, develop/next, proposed/pu). Commits move or graduate to a more stable branch (silo) only when they are fully tested and stable. This is especially helpful in large or complex projects to ensure that the main branch always contains stable, release-ready code."
    },
    {
        "question": "What does the git diff command show?",
        "ground_truth": "The git diff command shows the exact lines added and removed in files. Running git diff by itself compares the working directory with the staging area, showing what changes have been made but not yet staged. Running git diff --staged or git diff --cached compares the staging area with the last commit, showing what has been staged and is ready to be committed."
    },
    {
        "question": "What are the first-time setup options for Git identity?",
        "ground_truth": "When installing Git for the first time, you should set your user name and email address. This is important because every Git commit uses this information, and it is immutably baked into the commits you create. You can set them using the commands: git config --global user.name 'John Doe' and git config --global user.email johndoe@example.com. The --global option means Git will always use this information for anything you do on that system."
    }
]

# Hardcoded session ID corresponding to the ingested 'progit-en.1084.pdf' in Qdrant
DEFAULT_SESSION_ID = "2704766c6a054f929a76559683350d6a"


async def query_rag_system(session_id: str, query: str):
    """
    Invokes the custom RAG chatbot backend:
    - Generates query embeddings via Qwen Modal model.
    - Retrieves the relevant chunks from Qdrant.
    - Generates the LLM response.
    - Captures both the retrieved context chunk texts and the final generated answer text.
    """
    # Generate query embeddings
    embedded_query = generate_embeddings(query=query, chunks=None)
    
    # Retrieve relevant chunks (payload items)
    relevant_chunks = retrieve_relevant_chunks(session_id, embedded_query, query)
    context_texts = [chunk.get("content", "").strip() for chunk in relevant_chunks]
    
    # Generate streaming response
    response = await response_generator(query, relevant_chunks)
    
    # Consume the StreamingResponse to capture the complete text answer
    full_answer = ""
    async for chunk in response.body_iterator:
        if chunk.startswith("data: "):
            try:
                data = json.loads(chunk[6:].strip())
                delta = data.get("delta", "")
                if delta != "done":
                    full_answer += delta
            except Exception:
                pass
                
    return full_answer.strip(), context_texts


async def run_evaluation(session_id: str = DEFAULT_SESSION_ID):
    """
    Runs the full RAG queries, populates the evaluation dataset, and evaluates it using Ragas.
    """
    print(f"--- Starting RAG Queries using Session ID: {session_id} ---")
    
    questions = []
    ground_truth = []
    generated_answer = []
    contexts = []
    
    for idx, item in enumerate(EVALUATION_DATA):
        q = item["question"]
        gt = item["ground_truth"]
        print(f"Querying [{idx + 1}/{len(EVALUATION_DATA)}]: '{q}'")
        
        answer, retrieved_contexts = await query_rag_system(session_id, q)
        
        questions.append(q)
        ground_truth.append(gt)
        generated_answer.append(answer)
        contexts.append(retrieved_contexts)
        
    print("\n--- RAG Queries Completed ---")
    
    # Build evaluation dataset dictionary
    eval_dict = {
        "questions": questions,
        "ground_truth": ground_truth,
        "generated_answer": generated_answer,
        "contexts": contexts
    }
    
    # Format dataset for Ragas framework (which expects specific keys 'question', 'answer', 'contexts', 'ground_truth')
    ragas_dataset = Dataset.from_dict({
        "question": questions,
        "answer": generated_answer,
        "contexts": contexts,
        "ground_truth": ground_truth
    })
    
    print("\n--- Initializing Ragas Evaluation ---")
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        print("ERROR: GROQ_API_KEY environment variable not found in .env")
        return eval_dict, None
        
    # Set up LLM pointing to your Groq API
    eval_llm = ChatOpenAI(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        api_key=groq_api_key,
        base_url="https://api.groq.com/openai/v1"
    )
    
    # Set up custom Qwen Embeddings
    embeddings = QwenModalEmbeddings()
    
    ragas_llm = LangchainLLMWrapper(eval_llm)
    ragas_embeddings = LangchainEmbeddingsWrapper(embeddings)
    
    # Select standard Ragas metrics for evaluation
    metrics = [
        faithfulness,
        answer_relevancy,
        context_recall,
        context_precision
    ]
    
    # Override LLMs and Embeddings for all metrics
    for metric in metrics:
        metric.llm = ragas_llm
        if hasattr(metric, "embeddings"):
            metric.embeddings = ragas_embeddings
            
    print("Evaluating metrics (faithfulness, answer_relevancy, context_recall, context_precision)...")
    eval_result = evaluate(
        dataset=ragas_dataset,
        metrics=metrics,
        llm=ragas_llm,
        embeddings=ragas_embeddings
    )
    
    import math
    print("\n================ RAGAS EVALUATION METRICS ================")
    for metric in metrics:
        metric_name = metric.name
        try:
            scores = eval_result[metric_name]
            if isinstance(scores, list):
                valid_scores = [s for s in scores if s is not None and not (isinstance(s, float) and math.isnan(s))]
                avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
            else:
                avg_score = scores
            print(f"- {metric_name}: {avg_score:.4f}")
        except Exception as e:
            print(f"- {metric_name}: N/A (Error: {e})")
    print("==========================================================")
    
    return eval_dict, eval_result


def get_evaluation_results(session_id: str = DEFAULT_SESSION_ID):
    """
    Synchronous helper to run the evaluation and return the evaluation dictionary.
    """
    eval_dict, _ = asyncio.run(run_evaluation(session_id))
    return eval_dict


if __name__ == "__main__":
    # If run directly as a script, execute the full evaluation
    asyncio.run(run_evaluation())

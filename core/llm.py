from mistralai.client import Mistral
from dotenv import load_dotenv
import os
from groq import AsyncGroq
from langchain_groq import ChatGroq

load_dotenv()  # Load environment variables from .env file

groq_client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
)
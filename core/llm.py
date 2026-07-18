from mistralai.client import Mistral
from dotenv import load_dotenv
import os
from groq import AsyncGroq

load_dotenv()  # Load environment variables from .env file
# MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
# mistral_client = Mistral(api_key=MISTRAL_API_KEY)

groq_client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])
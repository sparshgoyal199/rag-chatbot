from core.llm import groq_client
stream_response = groq_client.chat.completions.create(
        messages=[
    {
        "role": "system",
        "content": "You are an intelligent AI"
    },
    {
        "role": "user",
        "content": "Give me the five days holiday plan to GOA"
            }
        ],
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        stream=True
        )

for chunk in stream_response:
    print(chunk)
import os
import instructor

# Choose the appropriate import based on your API:
from langchain_google_genai import ChatGoogleGenerativeAI

# config = {
#     "model": "gemini-2.5-flash",
#     "embedding_model": "gemini-embedding-001",
#     "temperature": 0,
#     "max_tokens": None,
#     "top_p": 0.8,
#     "google_api_key": os.environ.get("gemini_api_key"),
# }

def get_llm(model_name="gemini-2.5-flash",api_key=None):
    if not api_key:
        api_key = os.environ.get("gemini_api_key2")
    llm = ChatGoogleGenerativeAI(
        model=model_name, google_api_key=api_key, temperature=0
    )
    return llm

# if __name__ == "__main__":
#     client = get_client()
#     result = client.chat.completions.create(
#         response_model=typing.List,
#         messages=[{"role": "user", "content": document_text}],
#     )

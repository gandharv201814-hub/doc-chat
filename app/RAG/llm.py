import requests

def generate_answer(question, chunks):

    context = "\n\n".join(chunk["chunk"] for chunk in chunks)

    prompt = f"""
Answer the question using only the context.

Context:
{context}

Question:
{question}

Give a concise answer.
"""
    response = requests.post(
        "http://host.docker.internal:11434/api/generate",
        json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        }
    )

    return response.json()["response"]
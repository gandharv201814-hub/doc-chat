from sentence_transformers import SentenceTransformer
model = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5")

def create_embeddings(chunks):
    embeddings = model.encode(chunks)
    return embeddings
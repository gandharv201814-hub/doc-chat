import faiss
import numpy as np
import os
import pickle

VECTOR_DIR = "data/vector_store"

INDEX_PATH = os.path.join(VECTOR_DIR, "index.faiss")
METADATA_PATH = os.path.join(VECTOR_DIR, "metadata.pkl")

index = None
chunks = []
doc_ids = []
file_names = []
chunk_positions = []

def load_vector_store():
    global index, chunks, doc_ids, file_names, chunk_positions

    os.makedirs(VECTOR_DIR, exist_ok=True)

    if os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH):

        index = faiss.read_index(INDEX_PATH)

        with open(METADATA_PATH, "rb") as f:
            metadata = pickle.load(f)

        chunks = metadata["chunks"]
        doc_ids = metadata["doc_ids"]
        file_names = metadata["file_names"]
        chunk_positions = metadata["chunk_positions"]

        print(
            f"Loaded FAISS index: {index.ntotal} vectors"
        )


def save_vector_store():
    os.makedirs(VECTOR_DIR, exist_ok=True)

    if index is not None:
        faiss.write_index(index, INDEX_PATH)

    metadata = {
        "chunks": chunks,
        "doc_ids": doc_ids,
        "file_names": file_names,
        "chunk_positions": chunk_positions
    }

    with open(METADATA_PATH, "wb") as f:
        pickle.dump(metadata, f)


def add_embeddings(
    embeddings,
    new_chunks,
    doc_id,
    file_name
):
    global index, chunks, doc_ids
    global file_names, chunk_positions

    embeddings = np.array(
        embeddings,
        dtype="float32"
    )

    if index is None:

        index = faiss.IndexFlatL2(
            embeddings.shape[1]
        )

    index.add(embeddings)

    chunks.extend(new_chunks)

    doc_ids.extend([doc_id] * len(new_chunks))

    file_names.extend([file_name] * len(new_chunks))

    for i in range(len(new_chunks)):
        chunk_positions.append(i)

    save_vector_store()

def search(query_embedding,k=5,doc_id=None):

    if index is None or index.ntotal == 0:
        raise RuntimeError(
            "Vector store is empty. Upload a document first."
        )

    query_embedding = np.array([query_embedding],dtype="float32")

    distances, indices = index.search(query_embedding,index.ntotal)

    results = []

    for distance, index_number in zip(distances[0],indices[0]):
        if index_number < 0:
            continue
        if (doc_id and doc_ids[index_number] != doc_id):
            continue

        score = 1 / (1 + distance)

        results.append({
            "chunk": chunks[index_number],
            "score": float(score),
            "citation": {
                "document":
                    file_names[index_number],
                "chunk":
                    chunk_positions[index_number]
            }
        })

        if len(results) >= k:
            break

    return results

load_vector_store()
# Doc Chat

A lightweight document question-answering service built with FastAPI, local Sentence Transformers embeddings, FAISS, SQLite, and an optional local LLM through Ollama.

## Features

* Upload `.txt` and `.md` documents
* Configurable chunk size and overlap
* Local open-source embeddings
* FAISS vector retrieval
* Document-level filtering with `doc_id`
* Top-k retrieval with similarity scores and citations
* SQLite document and question history
* Retrieval evaluation with Hit@1, Hit@3, and Hit@5
* Local LLM answer synthesis through Ollama
* Minimal HTML frontend
* Docker support

## Project Structure

```text
DOC-CHAT/
├── app/
│   ├── RAG/
│   │   ├── chunking.py
│   │   ├── embeddings.py
│   │   ├── ingestion.py
│   │   ├── llm.py
│   │   └── vector_store.py
│   ├── db/
│   │   ├── database.py
│   │   └── models.py
│   ├── config.py
│   └── main.py
├── frontend/
├── sample_docs/
├── test/
├── .env.example
├── .gitignore
├── Dockerfile
└── requirements.txt
```

## Setup

### Local

```bash
git clone https://github.com/gandharv201814-hub/doc-chat.git
cd doc-chat

python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

Create `.env` from `.env.example`:

```env
CHUNK_SIZE=800
CHUNK_OVERLAP=150
DEFAULT_K=5
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## Configuration

The following values are configurable through `.env`:

| Variable        | Default | Description                        |
| --------------- | ------: | ---------------------------------- |
| `CHUNK_SIZE`    |   `800` | Maximum chunk size                 |
| `CHUNK_OVERLAP` |   `150` | Overlap between chunks             |
| `DEFAULT_K`     |     `5` | Default number of retrieved chunks |

## API Endpoints

### Health

```bash
curl http://127.0.0.1:8000/health
```

### Upload Document

```bash
curl -X POST http://127.0.0.1:8000/documents ^
  -F "file=@sample_docs/python_theory_introduction.txt"
```

Returns a `doc_id` and chunk count.

### List Documents

```bash
curl http://127.0.0.1:8000/documents
```

### Ask for Retrieved Chunks

```bash
curl -X POST http://127.0.0.1:8000/ask ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"What are the two types of loops in Python?\",\"doc_id\":\"YOUR_DOC_ID\",\"k\":5}"
```

Returns the most relevant chunks with scores and citations.

### Generate an Answer

```bash
curl -X POST http://127.0.0.1:8000/answer ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"What are the two types of loops in Python?\",\"doc_id\":\"YOUR_DOC_ID\",\"k\":5}"
```

Returns the generated answer and retrieved source chunks.

### Question History

```bash
curl "http://127.0.0.1:8000/history?limit=10&offset=0"
```

Returns recent questions, targeted document IDs, latency, and timestamps.

## Design Decisions

### Chunking

The document chunker splits text by paragraph boundaries and combines paragraphs until the configured chunk size is reached. Configurable overlap is added between consecutive chunks to preserve context across boundaries.

### Embeddings

The project uses the local open-source model:

```text
nomic-ai/nomic-embed-text-v1.5
```

This keeps the core retrieval path offline and avoids paid embedding APIs.

### Vector Store

FAISS was selected because it is lightweight, fast for local similarity search, and requires no external vector database service. Chunk text, document IDs, filenames, and chunk positions are stored as metadata alongside the index.

### Database

SQLite stores document metadata and question history. This keeps the service simple and self-contained.

## Retrieval Evaluation

The evaluation dataset contains 10 questions mapped to expected answer chunks across three sample documents.

Current results:

| Metric | Result |
| ------ | -----: |
| Hit@1  |    50% |
| Hit@3  |    80% |
| Hit@5  |    90% |

Run the evaluation with:

```bash
pytest -s test/test_evaluation.py
```

## Retrieval Failure Analysis

Retrieval can fail when a question is phrased very differently from the wording in the document, because semantic similarity may rank another chunk higher. Questions whose answers span multiple chunks can also fail when only one of the required chunks is retrieved. Chunk boundaries can further split related information and reduce the amount of useful context in a single retrieved passage. A concrete improvement would be adding a reranking stage after FAISS retrieval so the initial candidates are rescored with a stronger relevance model. Another option would be hybrid keyword plus vector retrieval, followed by the same Hit@K evaluation to determine whether it improves over the current vector-only baseline.

## Testing

The project includes automated API tests covering core error and health cases, plus the retrieval evaluation suite.

Run:

```bash
pytest
```

## Docker

Build the image:

```bash
docker build -t doc-chat .
```

Run:

```powershell
docker run -p 8000:8000 `
  -v "${PWD}/docchat.db:/app/docchat.db" `
  -v "${PWD}/data:/app/data" `
  --add-host=host.docker.internal:host-gateway `
  doc-chat
```

Open:

```text
http://localhost:8000
```

The Docker setup uses a CPU-only PyTorch installation for the local embedding stack. If Ollama is used for answer synthesis, the service can connect to Ollama running on the host through `host.docker.internal`.

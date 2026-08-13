import uuid
import time
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.db.database import Base, SessionLocal, engine
from app.db.models import Document, QuestionHistory
from app.RAG.chunking import chunk_text
from app.RAG.embeddings import create_embeddings
from app.RAG.ingestion import read_document
from app.RAG.vector_store import add_embeddings ,search
from app.RAG.llm import generate_answer
from app.config import settings

Base.metadata.create_all(bind=engine)
DEFAULT_K = settings.default_k

app = FastAPI(
    title="Doc Chat",
    description="Offline document retrieval and question answering service",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def frontend():
    return FileResponse("frontend/index.html")

class AskRequest(BaseModel):
    question: str
    doc_id: str | None = None
    k: int = DEFAULT_K

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/documents")
async def upload_document(file: UploadFile = File(...)):
    try:
        text = await read_document(file)

        chunks = chunk_text(text)

        if not chunks:
            raise ValueError("The document contains no usable text.")
        
        doc_id = str(uuid.uuid4())

        embeddings = create_embeddings(chunks)

        add_embeddings(embeddings,chunks,doc_id,file.filename)

        db = SessionLocal()

        document = Document(doc_id=doc_id,filename=file.filename,chunk_count=len(chunks))

        db.add(document)
        db.commit()
        db.close()

        return {"doc_id": doc_id,"chunk_count": len(chunks)}

    except ValueError as e:
        raise HTTPException(status_code=400,detail=str(e))

@app.get("/documents")
def get_documents():

    db = SessionLocal()

    documents = db.query(Document).all()

    result = []

    for document in documents:
        result.append({
            "doc_id": document.doc_id,
            "name": document.filename,
            "chunk_count": document.chunk_count,
            "upload_time": document.uploaded_at.isoformat() + "Z"
        })

    db.close()

    return {
        "documents": result
    }

@app.post("/ask")
def ask(request: AskRequest):

    if not request.question.strip():
        raise HTTPException(status_code=400,detail="Question cannot be empty")

    db = SessionLocal()

    if request.doc_id:
        document = db.query(Document).filter(
            Document.doc_id == request.doc_id
        ).first()

        if not document:
            db.close()
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

    start_time = time.time()

    query_embedding = create_embeddings([request.question])[0]

    results = search(query_embedding,request.k,request.doc_id)

    latency = (time.time() - start_time) * 1000

    history = QuestionHistory(
        question=request.question,
        doc_id=request.doc_id,
        latency_ms=latency
    )

    db.add(history)
    db.commit()
    db.close()

    return {
        "question": request.question,
        "results": results
    }

@app.get("/history")
def get_history(limit: int = 10, offset: int = 0):

    db = SessionLocal()

    history = db.query(QuestionHistory).order_by(
        QuestionHistory.created_at.desc()).offset(offset).limit(limit).all()

    result = []

    for item in history:
        result.append({
            "question": item.question,
            "doc_id": item.doc_id,
            "latency_ms": item.latency_ms,
            "created_at": item.created_at.isoformat() + "Z"
        })

    db.close()

    return {
        "history": result
    }

@app.post("/answer")
def answer(request: AskRequest):

    start_time = time.time()

    query_embedding = create_embeddings([request.question])[0]

    results = search(query_embedding,request.k,request.doc_id)

    answer = generate_answer(request.question,results)

    latency = (time.time() - start_time) * 1000

    db = SessionLocal()

    history = QuestionHistory(question=request.question,doc_id=request.doc_id,latency_ms=latency)

    db.add(history)
    db.commit()
    db.close()

    return {
        "question": request.question,
        "answer": answer,
        "results": results
    }
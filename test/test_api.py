from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_empty_question():
    response = client.post(
        "/ask",
        json={
            "question": ""
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Question cannot be empty"

def test_invalid_doc_id():
    response = client.post(
        "/ask",
        json={
            "question": "what is python",
            "doc_id": "invalid-doc-id"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"
def test_unsupported_file_type():
    response = client.post(
        "/documents",
        files={
            "file": (
                "test.pdf",
                b"This is a test file",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]
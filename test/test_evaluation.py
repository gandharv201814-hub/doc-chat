import requests


questions = [
    {
        "question": "What are the two types of loops in Python?",
        "doc_id": "65274484-e15c-45e8-aea5-2b7176ecc004",
        "expected_chunk": 18
    },
    {
        "question": "What is a tuple in Python, and can its values be changed after creation?",
        "doc_id": "65274484-e15c-45e8-aea5-2b7176ecc004",
        "expected_chunk": 20
    },
    {
        "question": "What is the Zen Python?",
        "doc_id": "65274484-e15c-45e8-aea5-2b7176ecc004",
        "expected_chunk": 5
    },
    {
        "question": "What is machine learning?",
        "doc_id": "1bead131-45b3-45b7-95c0-8b740a240764",
        "expected_chunk": 0
    },
    {
        "question": "What is supervised learning?",
        "doc_id": "1bead131-45b3-45b7-95c0-8b740a240764",
        "expected_chunk": 4
    },
    {
        "question": "What is reinforcement learning?",
        "doc_id": "1bead131-45b3-45b7-95c0-8b740a240764",
        "expected_chunk": 6
    },
    {
        "question": "What is RAG?",
        "doc_id": "be82db2e-92ea-488c-8ba1-28a7de78ca1b",
        "expected_chunk": 0
    },
    {
        "question": "How does the retrieval stage work in RAG?",
        "doc_id": "be82db2e-92ea-488c-8ba1-28a7de78ca1b",
        "expected_chunk": 4
    },
    {
        "question": "What is semantic chunking in RAG?",
        "doc_id": "be82db2e-92ea-488c-8ba1-28a7de78ca1b",
        "expected_chunk": 11
    },
    {
        "question": "Why is a vector database used in RAG?",
        "doc_id": "be82db2e-92ea-488c-8ba1-28a7de78ca1b",
        "expected_chunk": 5
    }
]


def test_retrieval():

    hit_1 = 0
    hit_3 = 0
    hit_5 = 0

    for item in questions:

        response = requests.post(
            "http://127.0.0.1:8000/ask",
            json={
                "question": item["question"],
                "doc_id": item["doc_id"],
                "k": 5
            }
        )

        assert response.status_code == 200

        results = response.json()["results"]

        chunks = []

        for result in results:
            chunks.append(result["citation"]["chunk"])

        expected = item["expected_chunk"]

        if expected in chunks[:1]:
            hit_1 += 1

        if expected in chunks[:3]:
            hit_3 += 1

        if expected in chunks[:5]:
            hit_5 += 1

        print()
        print("Question:", item["question"])
        print("Expected chunk:", expected)
        print("Retrieved chunks:", chunks)

    total = len(questions)

    print()
    print("========== FINAL RESULTS ==========")
    print("Total questions:", total)
    print("Hit@1:", hit_1 / total)
    print("Hit@3:", hit_3 / total)
    print("Hit@5:", hit_5 / total)
import re
from app.config import settings
CHUNK_SIZE = settings.chunk_size
CHUNK_OVERLAP = settings.chunk_overlap

def chunk_text(text: str) -> list[str]:
    if not text.strip():
        return []
    paragraphs = re.split(r"\n\s*\n", text.strip())
    chunks = []
    current_chunk = ""
    for paragraph in paragraphs:
        paragraph = paragraph.strip()

        if not paragraph:
            continue

        if len(current_chunk) + len(paragraph) + 1 <= CHUNK_SIZE:
            current_chunk += paragraph + "\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())

            overlap = current_chunk[-CHUNK_OVERLAP:]

            current_chunk = overlap + paragraph + "\n"

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
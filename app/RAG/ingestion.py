from fastapi import UploadFile
ALLOWED_EXTENSIONS = {".txt", ".md"}
async def read_document(file: UploadFile) -> str:
    filename = file.filename or ""

    extension = "." + filename.split(".")[-1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            "Unsupported file type. Only .txt and .md files are allowed."
        )

    content = await file.read()

    if not content:
        raise ValueError("The uploaded file is empty.")

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("The file must be UTF-8 encoded.")

    if not text.strip():
        raise ValueError("The uploaded file is empty.")

    return text
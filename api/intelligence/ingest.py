"""
File ingestion pipeline: extract → chunk → embed → store in Qdrant
"""
import os
import hashlib
import uuid
from typing import List, Tuple
from pathlib import Path

import httpx
from config import get_settings


def extract_text(file_path: str, content_type: str = None) -> str:
    """Extract text from various file types"""
    ext = Path(file_path).suffix.lower()

    if ext == ".txt" or ext == ".md":
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    elif ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception as e:
            return f"[PDF extraction error: {e}]"

    elif ext == ".docx":
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            return f"[DOCX extraction error: {e}]"

    elif ext == ".csv":
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            return df.to_markdown(index=False)
        except Exception as e:
            return f"[CSV extraction error: {e}]"

    elif ext in [".xlsx", ".xls"]:
        try:
            import pandas as pd
            df = pd.read_excel(file_path)
            return df.to_markdown(index=False)
        except Exception as e:
            return f"[Excel extraction error: {e}]"

    else:
        # Try reading as text
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except:
            return f"[Unsupported file type: {ext}]"


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[Tuple[int, str]]:
    """Split text into overlapping chunks by approximate token count.
    Returns list of (chunk_index, chunk_text) tuples."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        tokens = enc.encode(text)
    except:
        # Fallback: approximate 1 token ≈ 4 chars
        words = text.split()
        tokens = words
        chunk_size = chunk_size * 4  # adjust for word-based chunking

    chunks = []
    start = 0
    idx = 0

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]

        try:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            chunk_text = enc.decode(chunk_tokens)
        except:
            chunk_text = " ".join(chunk_tokens)

        chunks.append((idx, chunk_text))
        idx += 1
        start += chunk_size - overlap

    return chunks


async def embed_text(text: str) -> List[float]:
    """Generate embedding via OpenRouter / OpenAI compatible endpoint"""
    settings = get_settings()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/embeddings",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": settings.embedding_model,
                "input": text
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]


async def embed_batch(texts: List[str]) -> List[List[float]]:
    """Embed multiple texts (batched for efficiency, with single-embed fallback)"""
    settings = get_settings()

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.embedding_model,
                    "input": texts
                }
            )
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]
    except Exception:
        # Fallback: embed one at a time
        embeddings = []
        for text in texts:
            emb = await embed_text(text)
            embeddings.append(emb)
        return embeddings


def file_hash(file_path: str) -> str:
    """Generate SHA-256 hash of file"""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

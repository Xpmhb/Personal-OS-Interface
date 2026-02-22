from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from pydantic import BaseModel
from typing import Optional, List
import uuid
import os
import logging

from config import get_settings
from intelligence.ingest import extract_text, chunk_text, embed_batch, file_hash

router = APIRouter()
logger = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    query: str
    agent_id: Optional[str] = None
    namespace: Optional[str] = "default"
    limit: int = 5


class PermissionGrant(BaseModel):
    agent_id: str
    resource_type: str
    resource_id: str
    permission: str = "read"


async def _ingest_file(file_id: str, file_path: str, namespace: str):
    """Background task: extract, chunk, embed, store in Qdrant"""
    from database import SessionLocal
    from models import File as FileModel, FileChunk
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct, VectorParams, Distance

    settings = get_settings()
    db = SessionLocal()

    try:
        # Update status
        db_file = db.query(FileModel).filter(FileModel.id == file_id).first()
        if not db_file:
            return
        db_file.status = "processing"
        db.commit()

        # Extract text
        logger.info(f"Extracting text from {file_path}")
        text = extract_text(file_path)
        if not text or text.startswith("["):
            db_file.status = "error"
            db.commit()
            return

        # Chunk
        logger.info(f"Chunking text ({len(text)} chars)")
        chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        logger.info(f"Generated {len(chunks)} chunks")

        # Embed (batch)
        chunk_texts = [c[1] for c in chunks]

        # Process in batches of 20
        all_embeddings = []
        for i in range(0, len(chunk_texts), 20):
            batch = chunk_texts[i:i + 20]
            embeddings = await embed_batch(batch)
            all_embeddings.extend(embeddings)

        # Setup Qdrant collection
        client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
        collections = [c.name for c in client.get_collections().collections]

        if settings.qdrant_collection not in collections:
            client.create_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=VectorParams(
                    size=settings.embedding_dimensions,
                    distance=Distance.COSINE
                )
            )

        # Store chunks in DB + Qdrant
        points = []
        for (chunk_idx, chunk_text_content), embedding in zip(chunks, all_embeddings):
            chunk_id = str(uuid.uuid4())

            # DB record
            db_chunk = FileChunk(
                id=chunk_id,
                file_id=file_id,
                chunk_index=chunk_idx,
                chunk_text=chunk_text_content,
                token_count=len(chunk_text_content.split()),
                embedding_id=chunk_id
            )
            db.add(db_chunk)

            # Qdrant point (use UUID hex for Qdrant compatibility)
            points.append(PointStruct(
                id=chunk_id.replace("-", ""),
                vector=embedding,
                payload={
                    "file_id": str(file_id),
                    "chunk_id": chunk_id,
                    "namespace": namespace,
                    "filename": db_file.filename,
                    "chunk_index": chunk_idx,
                    "chunk_text": chunk_text_content[:500],
                }
            ))

        # Upsert to Qdrant
        if points:
            client.upsert(
                collection_name=settings.qdrant_collection,
                points=points
            )

        # Update file status
        db_file.status = "indexed"
        db_file.hash = file_hash(file_path)
        db.commit()

        logger.info(f"File {file_id} indexed: {len(chunks)} chunks")

    except Exception as e:
        logger.error(f"Ingestion error for {file_id}: {e}")
        try:
            db_file = db.query(FileModel).filter(FileModel.id == file_id).first()
            if db_file:
                db_file.status = "error"
                db.commit()
        except:
            pass
    finally:
        db.close()


@router.post("/files/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    namespace: str = Form("default"),
    db: Session = Depends(get_db)
):
    """Upload a file for indexing"""
    from models import File as FileModel

    settings = get_settings()

    # Create upload directory
    file_id = str(uuid.uuid4())
    upload_path = os.path.join(settings.upload_dir, file_id)
    os.makedirs(upload_path, exist_ok=True)

    # Save file
    file_path = os.path.join(upload_path, file.filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Create DB record
    db_file = FileModel(
        id=file_id,
        filename=file.filename,
        content_type=file.content_type,
        size_bytes=len(content),
        storage_path=file_path,
        namespace=namespace,
        status="uploaded"
    )
    db.add(db_file)
    db.commit()

    # Queue background ingestion
    background_tasks.add_task(_ingest_file, file_id, file_path, namespace)

    return {
        "file_id": file_id,
        "filename": file.filename,
        "size_bytes": len(content),
        "namespace": namespace,
        "status": "uploaded",
        "message": "File uploaded. Ingestion started in background."
    }


@router.get("/files")
def list_files(namespace: str = None, db: Session = Depends(get_db)):
    """List all uploaded files"""
    from models import File as FileModel

    query = db.query(FileModel).order_by(FileModel.uploaded_at.desc())
    if namespace:
        query = query.filter(FileModel.namespace == namespace)

    files = query.all()
    return [
        {
            "id": str(f.id),
            "filename": f.filename,
            "content_type": f.content_type,
            "size_bytes": f.size_bytes,
            "namespace": f.namespace,
            "status": f.status,
            "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None
        }
        for f in files
    ]


@router.get("/files/{file_id}/status")
def get_file_status(file_id: str, db: Session = Depends(get_db)):
    """Get file indexing status"""
    from models import File as FileModel, FileChunk

    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    chunk_count = db.query(FileChunk).filter(FileChunk.file_id == file_id).count()

    return {
        "file_id": str(file.id),
        "filename": file.filename,
        "status": file.status,
        "chunks_indexed": chunk_count,
        "namespace": file.namespace
    }


@router.post("/search")
async def search(request: SearchRequest, db: Session = Depends(get_db)):
    """Permission-aware vector search"""
    from intelligence.retrieval import search_with_permissions

    if not request.agent_id:
        raise HTTPException(status_code=400, detail="agent_id required for search")

    results = await search_with_permissions(
        db=db,
        agent_id=request.agent_id,
        query=request.query,
        namespace=request.namespace,
        limit=request.limit
    )

    return {
        "query": request.query,
        "agent_id": request.agent_id,
        "results": results,
        "count": len(results)
    }


@router.post("/permissions/grant")
def grant_perm(request: PermissionGrant, db: Session = Depends(get_db)):
    """Grant an agent permission to access a resource"""
    from intelligence.retrieval import grant_permission

    perm = grant_permission(
        db=db,
        agent_id=request.agent_id,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        permission=request.permission
    )
    return {"status": "granted", "permission_id": str(perm.id)}

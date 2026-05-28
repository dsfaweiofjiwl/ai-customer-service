import os
from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
import aiofiles

from src.rag import rag_engine

KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge")
router = APIRouter(prefix="/admin/kb")


@router.get("/list")
async def list_files():
    files = []
    if os.path.isdir(KNOWLEDGE_DIR):
        for fname in sorted(os.listdir(KNOWLEDGE_DIR)):
            if fname.endswith((".md", ".json", ".txt")):
                fpath = os.path.join(KNOWLEDGE_DIR, fname)
                size = os.path.getsize(fpath)
                files.append({"name": fname, "size": size})
    chunks_count = len(rag_engine.chunks)
    return JSONResponse({"files": files, "total_chunks": chunks_count})


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith((".md", ".json", ".txt")):
        return JSONResponse({"error": "仅支持 .md / .json / .txt 文件"}, status_code=400)

    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
    fpath = os.path.join(KNOWLEDGE_DIR, file.filename)
    content = await file.read()
    async with aiofiles.open(fpath, "wb") as f:
        await f.write(content)

    rag_engine.load_knowledge_dir(KNOWLEDGE_DIR)
    return JSONResponse({"ok": True, "filename": file.filename, "total_chunks": len(rag_engine.chunks)})


@router.delete("/{filename}")
async def delete_file(filename: str):
    fpath = os.path.join(KNOWLEDGE_DIR, filename)
    if not os.path.exists(fpath):
        return JSONResponse({"error": "文件不存在"}, status_code=404)
    os.remove(fpath)
    rag_engine.load_knowledge_dir(KNOWLEDGE_DIR)
    return JSONResponse({"ok": True, "total_chunks": len(rag_engine.chunks)})

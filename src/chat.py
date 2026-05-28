import json
import time
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
from src.session import session_store
from src.rag import rag_engine
from src.llm import chat_stream
from src.prompts import SYSTEM_PROMPT

router = APIRouter()


@router.get("/sessions")
async def list_sessions():
    return JSONResponse(session_store.get_all())


@router.post("/sessions/new")
async def new_session():
    import uuid
    sid = str(uuid.uuid4())
    session_store.get_or_create(sid)
    return JSONResponse({"session_id": sid})


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    session_store.clear(session_id)
    return JSONResponse({"ok": True})


@router.post("/chat")
async def chat(request: Request):
    body = await request.json()
    user_message = body.get("message", "").strip()
    session_id = body.get("session_id", "").strip() or None

    if not user_message:
        return StreamingResponse(
            _empty_stream("请输入您的问题"),
            media_type="text/event-stream",
        )

    session = session_store.get_or_create(session_id)
    session.last_active = time.time()

    # Auto-set title from first user message
    if not session.title:
        session.title = user_message[:20] + ("..." if len(user_message) > 20 else "")

    # RAG search
    sources = rag_engine.search(user_message, top_k=3)
    raw_context = "\n\n".join([s[0] for s in sources]) if sources else "暂无相关参考资料"
    context = _strip_md(raw_context)
    source_labels = [s[1] for s in sources]

    # Build messages
    system_content = SYSTEM_PROMPT.format(context=context)
    messages = [{"role": "system", "content": system_content}]
    messages.extend(session.get_history())
    messages.append({"role": "user", "content": user_message})

    session.add("user", user_message)

    async def event_stream():
        full_reply = ""
        try:
            async for token in chat_stream(messages):
                clean = token.replace('*', '')
                full_reply += clean
                yield f"data: {json.dumps({'type': 'token', 'content': clean}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
            if source_labels:
                yield f"data: {json.dumps({'type': 'sources', 'sources': source_labels}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"

        session.add("assistant", full_reply)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Session-Id": session.session_id,
        },
    )


def _strip_md(text: str) -> str:
    import re
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # **bold** → bold
    text = re.sub(r'^#{1,6} ', '', text, flags=re.MULTILINE)  # ## heading → heading
    text = re.sub(r'^[-*] ', '', text, flags=re.MULTILINE)  # - list → list
    return text


async def _empty_stream(msg: str):
    yield f"data: {json.dumps({'type': 'token', 'content': msg}, ensure_ascii=False)}\n\n"
    yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

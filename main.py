from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import httpx

import database

# ---- Config ----
# Ollama runs locally, free, no API key needed
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2:1b"  # change if you pulled a different model

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

database.init_db()


class ChatRequest(BaseModel):
    message: str


@app.get("/api/history")
async def history():
    return {"history": database.get_history()}


@app.delete("/api/history")
async def clear():
    database.clear_history()
    return {"status": "cleared"}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    # load past messages from DB so the model has context
    past_messages = database.get_history()
    messages = past_messages + [{"role": "user", "content": req.message}]

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(OLLAMA_URL, json=payload)
    except httpx.ConnectError:
        raise HTTPException(
            500,
            "Ollama is not running. Start it first: open the Ollama app, "
            "or run 'ollama serve' in a terminal.",
        )

    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text)

    data = r.json()
    reply_text = data.get("message", {}).get("content", "")

    # save both sides of the conversation
    database.save_message("user", req.message)
    database.save_message("assistant", reply_text)

    return {"reply": reply_text}


# Serve frontend static files (index.html, style.css, script.js)
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

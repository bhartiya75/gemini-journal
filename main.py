"""Personal Gemini Journal — secure, authenticated journaling with Gemini.

Gen AI Academy APAC C3 Ideathon entry.

Security posture (see constitution.md):
- Every /api route requires a verified Firebase ID token (no anonymous access).
- Firestore paths are always rooted at users/{uid} — cross-user reads are
  structurally impossible, not merely filtered.
- The Gemini API key is fetched from Google Cloud Secret Manager at startup;
  it is never hardcoded, logged, or sent to the client.
- The browser only ever holds the public Firebase client key and the user's
  own ID token.
"""

import os
import logging
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import google.auth.transport.requests
from google.oauth2 import id_token as google_id_token

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("journal")

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "genai-academy-c3-357d")
SECRET_NAME = os.environ.get("GEMINI_SECRET", "gemini-api-key")
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

MAX_TURNS = 20          # conversation turns sent to the model
MAX_MESSAGE_CHARS = 4000
REFLECTION_ENTRIES = 14  # journal entries analyzed by Reflections

SYSTEM_DIRECTIVES = (
    "You are the Personal Gemini Journal assistant — a warm, thoughtful "
    "journaling companion. Help the user brainstorm, reflect, and untangle "
    "their day. Ask one gentle follow-up question when it helps. Keep "
    "replies under 120 words. Never request or repeat passwords, API keys, "
    "or payment details. If the user reports intent to harm themselves or "
    "others, respond with care and suggest professional support resources."
)


def _load_gemini_key() -> str | None:
    """Fetch the Gemini API key from Secret Manager (never from env/code)."""
    try:
        from google.cloud import secretmanager

        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{PROJECT_ID}/secrets/{SECRET_NAME}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        key = response.payload.data.decode().strip()
        log.info("Gemini API key loaded from Secret Manager.")
        return key or None
    except Exception as err:  # noqa: BLE001 — degrade to Vertex ADC
        log.warning("Secret Manager key unavailable (%s); using Vertex ADC.", type(err).__name__)
        return None


def _make_genai_client():
    from google import genai

    key = _load_gemini_key()
    if key:
        return genai.Client(api_key=key)
    # Fallback: Vertex AI with the runtime service account (no key at all).
    return genai.Client(vertexai=True, project=PROJECT_ID, location="us-central1")


genai_client = _make_genai_client()

from google.cloud import firestore  # noqa: E402

db = firestore.Client(project=PROJECT_ID)

app = FastAPI(title="Personal Gemini Journal")

_token_request = google.auth.transport.requests.Request()


def current_uid(request: Request) -> str:
    """Verify the Firebase ID token and return the caller's uid."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token.")
    token = header.removeprefix("Bearer ").strip()
    try:
        claims = google_id_token.verify_firebase_token(
            token, _token_request, audience=PROJECT_ID
        )
    except Exception as err:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="Invalid or expired token.") from err
    uid = claims.get("sub") or claims.get("user_id")
    if not uid:
        raise HTTPException(status_code=401, detail="Token has no subject.")
    return uid


def _user_root(uid: str):
    return db.collection("users").document(uid)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)


@app.post("/api/chat")
def chat(payload: ChatIn, uid: str = Depends(current_uid)):
    """One multi-turn exchange; history is loaded from the user's own doc tree."""
    convo = _user_root(uid).collection("conversation")
    history = [
        d.to_dict()
        for d in convo.order_by("ts", direction=firestore.Query.DESCENDING)
        .limit(MAX_TURNS)
        .stream()
    ][::-1]

    from google.genai import types as gt

    contents = [
        gt.Content(role=t["role"], parts=[gt.Part(text=t["text"])])
        for t in history
        if t.get("role") in ("user", "model") and t.get("text")
    ]
    contents.append(gt.Content(role="user", parts=[gt.Part(text=payload.message)]))

    try:
        result = genai_client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=gt.GenerateContentConfig(system_instruction=SYSTEM_DIRECTIVES),
        )
        reply = (result.text or "").strip() or "I'm here — tell me more?"
    except Exception as err:  # noqa: BLE001
        log.error("Gemini call failed: %s", type(err).__name__)
        raise HTTPException(status_code=502, detail="The journal assistant is unavailable right now.")

    batch = db.batch()
    batch.set(convo.document(), {"role": "user", "text": payload.message, "ts": _now()})
    batch.set(convo.document(), {"role": "model", "text": reply, "ts": _now()})
    batch.commit()
    return {"reply": reply}


@app.post("/api/save")
def save_entry(uid: str = Depends(current_uid)):
    """Summarize the current conversation into a journal entry, then clear it."""
    convo = _user_root(uid).collection("conversation")
    turns = [
        d.to_dict()
        for d in convo.order_by("ts", direction=firestore.Query.ASCENDING).stream()
    ]
    if not turns:
        raise HTTPException(status_code=400, detail="Nothing to save yet — chat first.")

    transcript = "\n".join(f"{t['role']}: {t['text']}" for t in turns)
    prompt = (
        "Summarize this journaling conversation as JSON with keys: "
        '"summary" (2-3 sentences, second person), "mood" (one word), '
        '"themes" (array of 1-3 short lowercase tags). Transcript:\n' + transcript
    )
    try:
        result = genai_client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        import json

        data = json.loads(result.text)
    except Exception:  # noqa: BLE001
        data = {"summary": transcript[:400], "mood": "reflective", "themes": ["journal"]}

    entry = {
        "summary": str(data.get("summary", ""))[:1500],
        "mood": str(data.get("mood", "reflective"))[:40],
        "themes": [str(t)[:40] for t in data.get("themes", [])][:3],
        "turns": len(turns),
        "ts": _now(),
    }
    _user_root(uid).collection("entries").document().set(entry)
    for doc in convo.stream():
        doc.reference.delete()
    entry["ts"] = entry["ts"].isoformat()
    return {"entry": entry}


@app.get("/api/entries")
def list_entries(uid: str = Depends(current_uid)):
    docs = (
        _user_root(uid)
        .collection("entries")
        .order_by("ts", direction=firestore.Query.DESCENDING)
        .limit(30)
        .stream()
    )
    out = []
    for d in docs:
        e = d.to_dict()
        e["ts"] = e["ts"].isoformat() if e.get("ts") else None
        out.append(e)
    return {"entries": out}


@app.get("/api/reflections")
def reflections(uid: str = Depends(current_uid)):
    """Unique feature: cross-entry themes, mood trend, and a weekly insight."""
    docs = (
        _user_root(uid)
        .collection("entries")
        .order_by("ts", direction=firestore.Query.DESCENDING)
        .limit(REFLECTION_ENTRIES)
        .stream()
    )
    entries = [d.to_dict() for d in docs]
    if len(entries) < 2:
        return {"ready": False, "needed": 2 - len(entries)}

    digest = "\n".join(
        f"- [{e['ts'].date() if e.get('ts') else '?'}] mood={e.get('mood')} "
        f"themes={','.join(e.get('themes', []))} :: {e.get('summary', '')}"
        for e in entries
    )
    prompt = (
        "You are a reflective-insight engine. Given these dated journal entry "
        "summaries (newest first), return JSON with keys: "
        '"themes" (array of the 3 most recurring themes with a short reason each, '
        'as objects {"theme","reason"}), '
        '"mood_trend" (one sentence describing the mood direction over time), '
        '"insight" (one caring, specific observation the writer may not have '
        "noticed, max 50 words). Entries:\n" + digest
    )
    try:
        result = genai_client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        import json

        data = json.loads(result.text)
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=502, detail="Reflections unavailable right now.")
    data["ready"] = True
    data["entries_analyzed"] = len(entries)
    return data


@app.get("/healthz")
def health():
    return {"ok": True}


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index():
    return FileResponse("static/index.html")

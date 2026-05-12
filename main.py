import json
import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import run_agent
from tools import load_stocks

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "data" / "users.json"

app = FastAPI(title="JetKobi API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS = {}


def load_users():
    with USERS_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_session(token: str):
    session = SESSIONS.get(token)
    if not session:
        raise HTTPException(status_code=401, detail="Oturum bulunamadı. Lütfen tekrar giriş yapın.")
    return session

def welcome_message(user: dict):
    if user["role"] == "KOBİ":
        return f"Hoş geldin {user['name']}! Sabah raporunu hazırlamamı ister misin?"
    return f"Merhaba {user['name']}! Sipariş durumunu öğrenmek için sipariş numaranı yazabilirsin."

class LoginData(BaseModel):
    username: str
    password: str

class Message(BaseModel):
    message: str
    token: str

@app.get("/", response_class=HTMLResponse)
def index():
    with (BASE_DIR / "templates" / "index.html").open("r", encoding="utf-8") as f:
        return f.read()

@app.post("/login")
def login(data: LoginData):
    users = load_users()
    user = users.get(data.username)
    if user and user["password"] == data.password:
        token = secrets.token_urlsafe(32)
        SESSIONS[token] = {
            "username": data.username,
            "role": user["role"],
            "name": user["name"],
            "history": [
                {"role": "assistant", "content": welcome_message(user)}
            ],
        }
        return {"status": "success", "role": user["role"], "name": user["name"], "token": token}
    raise HTTPException(status_code=401, detail="Hatalı kullanıcı adı veya şifre")

@app.post("/chat")
def chat(body: Message):
    user_info = get_session(body.token)
    response = run_agent(
        body.message,
        user_role=user_info["role"],
        username=user_info["username"],
        history=user_info.get("history", []),
    )
    user_info.setdefault("history", []).append({"role": "user", "content": body.message})
    user_info["history"].append({"role": "assistant", "content": response})
    user_info["history"] = user_info["history"][-12:]
    return {"response": response}

@app.get("/stocks")
def stocks(token: str):
    user_info = get_session(token)
    if user_info["role"] != "KOBİ":
        raise HTTPException(status_code=403, detail="Bu veriye erişim yetkiniz bulunmuyor.")
    return load_stocks()

@app.get("/health")
def health():
    return {"status": "ok", "service": "JetKobi"}

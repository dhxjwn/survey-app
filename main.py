from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import sqlite3
import os
import secrets
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# =========================
# 資料庫設定
# =========================

DB_PATH = os.environ.get("DB_PATH", "database.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            department TEXT,
            age INTEGER,
            future_state TEXT,
            emotion_impact TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# =========================
# Admin Basic Auth 設定
# =========================

security = HTTPBasic()

ADMIN_USER = "admin"
ADMIN_PASS = "12345"  # ⚠️ 部署前記得改密碼

def require_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = secrets.compare_digest(credentials.username, ADMIN_USER)
    correct_pass = secrets.compare_digest(credentials.password, ADMIN_PASS)

    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True

# =========================
# 前台問卷頁
# =========================

@app.get("/", response_class=HTMLResponse)
def form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

# =========================
# 提交表單
# =========================

@app.post("/submit")
def submit(
    name: str = Form(...),
    department: str = Form(...),
    age: int = Form(...),
    future_state: str = Form(...),
    emotion_impact: str = Form(...)
):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        INSERT INTO responses
        (name, department, age, future_state, emotion_impact, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name,
        department,
        age,
        future_state,
        emotion_impact,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    return RedirectResponse("/success", status_code=303)

# =========================
# 成功頁
# =========================

@app.get("/success", response_class=HTMLResponse)
def success(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})

# =========================
# 後台管理頁（有密碼）
# =========================

@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request, _: bool = Depends(require_admin)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM responses ORDER BY created_at DESC")
    data = c.fetchall()
    conn.close()

    return templates.TemplateResponse("admin.html", {"request": request, "data": data})
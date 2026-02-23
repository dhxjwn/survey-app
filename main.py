from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "database.db")

app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(APP_DIR, "templates"))

security = HTTPBasic()


# -------- DB helpers --------
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS survey (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                age INTEGER NOT NULL,
                future TEXT NOT NULL,
                emotion TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


@app.on_event("startup")
def on_startup():
    init_db()


# -------- Auth (Admin) --------
def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> bool:
    admin_user = os.getenv("ADMIN_USER", "")
    admin_pass = os.getenv("ADMIN_PASS", "")

    # 沒設定就不放行（避免你忘了設，結果 admin 裸奔）
    if not admin_user or not admin_pass:
        raise HTTPException(status_code=500, detail="ADMIN_USER/ADMIN_PASS not set")

    ok_user = secrets.compare_digest(credentials.username, admin_user)
    ok_pass = secrets.compare_digest(credentials.password, admin_pass)

    if not (ok_user and ok_pass):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True


# -------- Routes --------
@app.get("/", response_class=HTMLResponse)
@app.get("/form", response_class=HTMLResponse)
def form_page(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})


@app.post("/submit")
def submit(
    request: Request,
    name: str = Form(...),
    department: str = Form(...),
    age: int = Form(...),
    future: str = Form(...),
    emotion: str = Form(...),
):
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO survey (name, department, age, future, emotion, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, department, age, future, emotion, created_at),
        )
        conn.commit()

    return RedirectResponse(url="/success", status_code=303)


@app.get("/success", response_class=HTMLResponse)
def success_page(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, _ok: bool = Depends(require_admin)):
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM survey").fetchone()["c"]

        dept_counts = conn.execute(
            """
            SELECT department, COUNT(*) AS cnt
            FROM survey
            GROUP BY department
            ORDER BY cnt DESC, department ASC
            """
        ).fetchall()

        recent = conn.execute(
            """
            SELECT id, name, department, age, future, emotion, created_at
            FROM survey
            ORDER BY id DESC
            LIMIT 20
            """
        ).fetchall()

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "total": total,
            "dept_counts": dept_counts,
            "recent": recent,
        },
    )


# Render health check friendly
@app.get("/healthz")
def healthz():
    return {"ok": True}
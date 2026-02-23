import os
import secrets
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from db import SessionLocal, engine, Base
from models import Survey

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ✅ 啟動時自動建表（Postgres/SQLite 都可）
Base.metadata.create_all(bind=engine)

def now_tw():
    return datetime.now(ZoneInfo("Asia/Taipei"))

def basic_auth_ok(request: Request) -> bool:
    """
    Basic Auth: 用 Render 環境變數 ADMIN_USER / ADMIN_PASS 控制
    """
    admin_user = os.getenv("ADMIN_USER")
    admin_pass = os.getenv("ADMIN_PASS")

    # 沒設定就直接擋，避免 /admin 裸奔
    if not admin_user or not admin_pass:
        return False

    auth = request.headers.get("authorization") or ""
    if not auth.lower().startswith("basic "):
        return False

    import base64
    try:
        b64 = auth.split(" ", 1)[1].strip()
        decoded = base64.b64decode(b64).decode("utf-8")
        user, pw = decoded.split(":", 1)
    except Exception:
        return False

    # 用 secrets.compare_digest 避免簡單 timing attack
    return secrets.compare_digest(user, admin_user) and secrets.compare_digest(pw, admin_pass)


@app.get("/", response_class=HTMLResponse)
@app.get("/form", response_class=HTMLResponse)
def form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})


@app.post("/submit")
def submit(
    name: str = Form(...),
    department: str = Form(...),
    age: int = Form(...),
    future: str = Form(...),
    emotion: str = Form(...),
):
    db = SessionLocal()
    try:
        row = Survey(
            name=name,
            department=department,
            age=age,
            future=future,
            emotion=emotion,
            time=now_tw(),  # ✅ 時間用台灣時區
        )
        db.add(row)
        db.commit()
    finally:
        db.close()

    return RedirectResponse(url="/success", status_code=303)


@app.get("/success", response_class=HTMLResponse)
def success(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request):
    # ✅ Basic Auth 保護
    if not basic_auth_ok(request):
        # 這個 header 會讓瀏覽器跳出帳密視窗
        return HTMLResponse(
            content='{"detail":"Unauthorized"}',
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="admin"'},
        )

    db = SessionLocal()
    try:
        total = db.query(Survey).count()  # ✅ 真正總筆數
        rows = db.query(Survey).order_by(Survey.id.desc()).limit(20).all()
    finally:
        db.close()

    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "rows": rows, "total": total},
    )


# （可選）健康檢查：Render/你自己測試用
@app.get("/healthz")
def healthz():
    return {"ok": True}
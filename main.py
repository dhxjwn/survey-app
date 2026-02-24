from sqlalchemy import func
import os
import secrets
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from db import SessionLocal, engine, Base
from models import SurveyV2

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

    q1_future_state: str = Form(...),
    q2_emotion_impact: str = Form(...),
    q3_obstacles: list[str] = Form(...),  # 多選
    q4_solution: str = Form(...),
    q5_help_channel: str = Form(...),
    q6_avoid: str = Form(...),
    q7_prefer: str = Form(...),
):
    db = SessionLocal()
    try:
        row = SurveyV2(
            name=name,
            department=department,
            age=age,
            q1_future_state=q1_future_state,
            q2_emotion_impact=q2_emotion_impact,
            q3_obstacles=",".join(q3_obstacles),
            q4_solution=q4_solution,
            q5_help_channel=q5_help_channel,
            q6_avoid=q6_avoid,
            q7_prefer=q7_prefer,
            time=now_tw(),
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
    db = SessionLocal()
    try:
        total = db.query(func.count(SurveyV2.id)).scalar() or 0

        rows = (
            db.query(SurveyV2)
            .order_by(SurveyV2.id.desc())
            .limit(20)
            .all()
        )

        dept_stats = (
            db.query(Survey.department, func.count(Survey.id))
            .group_by(Survey.department)
            .order_by(func.count(Survey.id).desc())
            .all()
        )
        # 轉成 template 好用的格式
        dept_stats = [{"department": d, "count": c} for d, c in dept_stats]

    finally:
        db.close()

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "total": total,
            "rows": rows,
            "dept_stats": dept_stats,
        },
    )

# （可選）健康檢查：Render/你自己測試用
@app.get("/healthz")
def healthz():
    return {"ok": True}
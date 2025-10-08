import json
from fastapi import APIRouter, Request, Form, BackgroundTasks
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from services.student_service import process_register

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse("students.html", {"request": request, "error": "ホーム画面から<br>ログインしてください🙇", "data": {"students": []}})

@router.post("/register", response_class=HTMLResponse)
async def register_post(
    request: Request,
    background: BackgroundTasks,
    index: int = Form(...),
    late: str = Form(None),
    homework: str = Form(None),
    concentration: str = Form(None),
    understanding: str = Form(None),
    today_homework: str = Form(None),
    students: str = Form(...),
    user_id: str = Form(None),
    password: str = Form(None),
):
    print("****** スクレポ登録開始 ******")

    user_id = user_id or request.session.get("user_id")
    password = password or request.session.get("password")
    if not user_id or not password:
        return templates.TemplateResponse("students.html", {"request": request, "error": "ログイン情報が不足しています🥺", "data": {"students": []}})
    request.session["user_id"] = user_id
    request.session["password"] = password

    try:
        students_data = json.loads((students or "").replace("'", '"'))
    except json.JSONDecodeError:
        return templates.TemplateResponse("students.html", {"request": request, "error": "生徒情報の形式が不正です🥺", "data": {"students": []}})

    sukurepo_data = {
        "index": index,
        f"content_{index}": (await request.form()).get(f"content_{index}"),
        "late": late, "homework": homework, "concentration": concentration, "understanding": understanding, "today_homework": today_homework,
    }

    # 非同期で登録
    background.add_task(process_register, user_id, password, students_data, sukurepo_data)

    # 画面更新用のフィルタリング
    class_start_time = ""
    name = ""
    for s in students_data:
        if s["index"] == index:
            class_start_time = s["class_start_time"]; name = s["name"]; break

    filtered = {"students": [s for s in students_data if not (s["class_start_time"] == class_start_time and s["name"] == name)]}
    if filtered["students"]:
        return templates.TemplateResponse("students.html", {"request": request, "user_id": user_id, "data": filtered})
    else:
        return templates.TemplateResponse("students.html", {"request": request, "user_id": user_id, "error": "全て入力済みです！<br>お疲れ様でした🚀", "data": {"students": []}})

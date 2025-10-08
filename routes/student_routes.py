import datetime
from fastapi import APIRouter, Request, Form
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from services.student_service import process_students

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/students", response_class=HTMLResponse)
async def students_get(request: Request):
    return templates.TemplateResponse(
        "students.html",
        {"request": request, "error": "ホーム画面から<br>ログインしてください🙇", "data": {"students": []}},
    )

@router.post("/students", response_class=HTMLResponse)
async def students_post(
    request: Request,
    user_id: str = Form(None),
    password: str = Form(None),
):
    print("****** 生徒情報取得開始 ******")
    start_time = datetime.datetime.now()

    user_id = user_id or request.session.get("user_id")
    password = password or request.session.get("password")
    if not user_id or not password:
        return templates.TemplateResponse("students.html", {"request": request, "error": "ログイン情報が不足しています🥺", "data": {"students": []}})

    request.session["user_id"] = user_id
    request.session["password"] = password

    print(f"生徒情報の処理実行: {datetime.datetime.now() - start_time}")
    result = await process_students(user_id, password)
    print(f"生徒情報の処理終了: {datetime.datetime.now() - start_time}")

    if result is None:
        return templates.TemplateResponse("students.html", {"request": request, "error": "もう一度試してください🙇", "data": {"students": []}})
    if isinstance(result, Exception):
        return templates.TemplateResponse("students.html", {"request": request, "error": "授業はありません💤", "data": {"students": []}})

    print("****** 生徒情報取得終了 ******")
    if result["students"]:
        return templates.TemplateResponse("students.html", {"request": request, "user_id": user_id, "data": result})
    else:
        return templates.TemplateResponse("students.html", {"request": request, "user_id": user_id, "error": "全て入力済みです！<br>お疲れ様でした🚀", "data": {"students": []}})

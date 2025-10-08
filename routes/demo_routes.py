from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/demo", response_class=HTMLResponse)
async def demo(request: Request):
    students = {"students": [
        {
            "index": 1001,
            "class_start_time": "17:30",
            "name": "山本 太郎",
            "subject": "数学",
            "key1": 1001,
            "key2": 1001,
            "key3": 1001,
        },
        {
            "index": 1002,
            "class_start_time": "17:30",
            "name": "山田 花子",
            "subject": "国語",
            "key1": 1002,
            "key2": 1002,
            "key3": 1002,
        },
        {
            "index": 1003,
            "class_start_time": "17:30",
            "name": "佐藤 次郎",
            "subject": "社会",
            "key1": 1003,
            "key2": 1003,
            "key3": 1003,
        },
        {
            "index": 1004,
            "class_start_time": "19:00",
            "name": "鈴木 三郎",
            "subject": "理科",
            "key1": 1004,
            "key2": 1004,
            "key3": 1004,
        },
    ]}
    return templates.TemplateResponse("demo_students.html", {"request": request, "data": students})

@router.get("/demo_register", response_class=HTMLResponse)
async def demo_register_get(request: Request):
    return templates.TemplateResponse(
        "demo_students.html",
        {"request": request, "error": "ホーム画面から<br>ログインしてください🙇", "data": {"students": []}},
    )

@router.post("/demo_register", response_class=HTMLResponse)
async def demo_register_post(request: Request):
    form = await request.form()

    students_json = (form.get("students") or "").replace("'", '"')
    import json
    try:
        students_data = json.loads(students_json)
    except Exception:
        return templates.TemplateResponse("demo_students.html", {"request": request, "error": "生徒情報の形式が不正です🥺", "data": {"students": []}})

    index_str = form.get("index")
    if not index_str:
        return templates.TemplateResponse("demo_students.html", {"request": request, "error": "インデックスが指定されていません🥺", "data": {"students": []}})
    try:
        index = int(index_str)
    except ValueError:
        return templates.TemplateResponse("demo_students.html", {"request": request, "error": "無効なインデックスです🥺", "data": {"students": []}})

    class_start_time = ""
    name = ""
    for s in students_data:
        if s["index"] == index:
            class_start_time = s["class_start_time"]; name = s["name"]; break

    filtered = {"students": [s for s in students_data if not (s["class_start_time"] == class_start_time and s["name"] == name)]}
    if filtered["students"]:
        return templates.TemplateResponse("demo_students.html", {"request": request, "data": filtered})
    else:
        return templates.TemplateResponse("demo_students.html", {"request": request, "error": "全て入力済みです！<br>お疲れ様でした🚀", "data": {"students": []}})

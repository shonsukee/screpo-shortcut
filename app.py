import os
import sentry_sdk
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from routes.student_routes import router as student_router
from routes.register_routes import router as register_router
from routes.demo_routes import router as demo_router

load_dotenv()

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    send_default_pii=True,
)

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set. Set it in your environment/.env for production.")

middleware = [
    Middleware(SessionMiddleware, secret_key=SECRET_KEY, same_site="lax", https_only=True, session_cookie="session")
]

app = FastAPI(middleware=middleware)

# static / templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ルータ登録
app.include_router(student_router)
app.include_router(register_router)
app.include_router(demo_router)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "error": "ログインして生徒情報を<br>取得してください<a href='/demo'>🕵️‍♀️</a>",
            "data": {"students": []},
            "user_id": request.session.get("user_id", ""),
        },
    )

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}, 200

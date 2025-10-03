import os
from dotenv import load_dotenv
from flask import Flask, render_template
from werkzeug.middleware.proxy_fix import ProxyFix  # 追加
from routes.student_routes import student_bp
from routes.register_routes import register_bp
from routes.demo_routes import demo_bp

load_dotenv()

app = Flask(__name__)

# --- セキュリティ／設定 ---
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set. Set it in your environment/.env for production.")

app.config['SECRET_KEY'] = SECRET_KEY
app.config['SESSION_COOKIE_NAME'] = os.getenv('SESSION_COOKIE_NAME', 'session')
app.config.update(
    SESSION_COOKIE_SECURE=True,      # HTTPSのみ
    SESSION_COOKIE_SAMESITE="Lax",
)

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

app.register_blueprint(student_bp)
app.register_blueprint(register_bp)
app.register_blueprint(demo_bp)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html',
                           error="ログインして生徒情報を<br>取得してください<a href='/demo'>🕵️‍♀️</a>",
                           data={"students": []})

@app.get("/healthz")
def healthz():
    return {"status": "ok"}, 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)

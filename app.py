import os
from dotenv import load_dotenv
from flask import Flask, render_template
from routes.student_routes import student_bp
from routes.register_routes import register_bp
from routes.demo_routes import demo_bp

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SESSION_COOKIE_NAME'] = os.getenv('SESSION_COOKIE_NAME')

# ブループリントの登録
app.register_blueprint(student_bp)
app.register_blueprint(register_bp)
app.register_blueprint(demo_bp)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', error="ログインして生徒情報を<br>取得してください<a href='/demo'>🕵️‍♀️</a>", data={ "students": [] })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
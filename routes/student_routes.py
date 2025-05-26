from flask import Blueprint, render_template, request, session
from services.student_service import process_students
import datetime

student_bp = Blueprint('student', __name__)

@student_bp.route('/students', methods=['GET', 'POST'])
def students():
    if request.method == 'GET':
        return render_template('students.html', error="ホーム画面から<br>ログインしてください🙇", data={ "students": [] })

    elif request.method == 'POST':
        print("****** 生徒情報取得開始 ******")
        start_time = datetime.datetime.now()

        # ユーザIDとパスワードを取得
        user_id = request.form.get('user_id') or session.get('user_id')
        password = request.form.get('password') or session.get('password')
        if not user_id or not password:
            return render_template('students.html', error="ログイン情報が不足しています🥺", data={ "students": [] })
        session['user_id'] = user_id
        session['password'] = password

        # 生徒情報取得をキューイング
        print(f"生徒情報の処理実行: {datetime.datetime.now() - start_time}")
        result = process_students(user_id, password)
        print(f"生徒情報の処理終了: {datetime.datetime.now() - start_time}")

        if result is None:
            return render_template('students.html', error="もう一度試してください🙇", data={ "students": [] })
        if isinstance(result, Exception):
            return render_template('students.html', error="授業はありません💤", data={ "students": [] })

        print("****** 生徒情報取得終了 ******")
        # 生徒情報が取得できた場合
        if len(result["students"]) > 0:
            return render_template('students.html', user_id=user_id, data=result)
        else:
            return render_template('students.html', user_id=user_id, error="全て入力済みです！<br>お疲れ様でした🚀", data={"students": []})
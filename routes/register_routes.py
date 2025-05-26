from flask import Blueprint, render_template, request, session
from services.student_service import process_register
import json
import threading

register_bp = Blueprint('register', __name__)

@register_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('students.html', error="ホーム画面から<br>ログインしてください🙇", data={ "students": [] })

    elif request.method == 'POST':
        print("****** スクレポ登録開始 ******")

        # ユーザIDとパスワードを取得
        user_id = request.form.get('user_id') or session.get('user_id')
        password = request.form.get('password') or session.get('password')
        if not user_id or not password:
            return render_template('students.html', error="ログイン情報が不足しています🥺", data={ "students": [] })
        session['user_id'] = user_id
        session['password'] = password

        # インデックスの取得と検証
        index_str = request.form.get('index')
        if not index_str:
            return render_template('students.html', error="インデックスが指定されていません🥺", data={ "students": [] })
        try:
            index = int(index_str)
        except ValueError:
            return render_template('students.html', error="無効なインデックスです🥺", data={ "students": [] })

        sukurepo_data = {
            "index": index,
            f"content_{index}": request.form.get(f'content_{index}'),
            "late": request.form.get('late'),
            "homework": request.form.get('homework'),
            "concentration": request.form.get('concentration'),
            "understanding": request.form.get('understanding'),
            "today_homework": request.form.get('today_homework'),
        }

        # 生徒情報を取得
        students_json = request.form.get('students')
        if not students_json:
            return render_template('students.html', error="生徒情報が取得できませんでした🥺", data={ "students": [] })
        
        students_json = students_json.replace("'", '"')
        try:
            students_data = json.loads(students_json)
        except json.JSONDecodeError:
            return render_template('students.html', error="生徒情報の形式が不正です🥺", data={ "students": [] })

        thread = threading.Thread(target=process_register, args=[user_id, password, students_data, sukurepo_data], daemon=True)
        thread.start()

        class_start_time = ""
        name = ""
        for student in students_data:
            if student['index'] == index:
                class_start_time = student['class_start_time']
                name = student['name']
                break

        filtered_students = {"students": [student for student in students_data if not (student["class_start_time"] == class_start_time and student["name"] == name)]}
        if len(filtered_students["students"]) > 0:
            return render_template('students.html', user_id=user_id, data=filtered_students)
        else:
            return render_template('students.html', user_id=user_id, error="全て入力済みです！<br>お疲れ様でした🚀", data={"students": []})
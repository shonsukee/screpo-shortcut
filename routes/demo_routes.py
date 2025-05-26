from flask import Blueprint, render_template, request
import json

demo_bp = Blueprint('demo', __name__)

@demo_bp.route('/demo', methods=['GET'])
def demo():
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

    return render_template('demo_students.html', data=students)

@demo_bp.route('/demo_register', methods=['GET', 'POST'])
def demo_register():
    if request.method == 'GET':
        return render_template('demo_students.html', error="ホーム画面から<br>ログインしてください🙇", data={ "students": [] })

    elif request.method == 'POST':
        print("****** スクレポ[デモ]登録開始 ******")

        # 生徒情報を取得
        students_json = request.form.get('students')
        if not students_json:
            return render_template('demo_students.html', error="生徒情報が取得できませんでした🥺", data={ "students": [] })
        
        students_json = students_json.replace("'", '"')
        try:
            students_data = json.loads(students_json)
        except json.JSONDecodeError:
            return render_template('demo_students.html', error="生徒情報の形式が不正です🥺", data={ "students": [] })

        # インデックスの取得と検証
        index_str = request.form.get('index')
        if not index_str:
            return render_template('demo_students.html', error="インデックスが指定されていません🥺", data={ "students": [] })
        try:
            index = int(index_str)
        except ValueError:
            return render_template('demo_students.html', error="無効なインデックスです🥺", data={ "students": [] })

        class_start_time = ""
        name = ""
        for student in students_data:
            if student['index'] == index:
                class_start_time = student['class_start_time']
                name = student['name']
                break

        filtered_students = {"students": [student for student in students_data if not (student["class_start_time"] == class_start_time and student["name"] == name)]}
        if len(filtered_students["students"]) > 0:
            return render_template('demo_students.html', data=filtered_students)
        else:
            return render_template('demo_students.html', error="全て入力済みです！<br>お疲れ様でした🚀", data={"students": []})
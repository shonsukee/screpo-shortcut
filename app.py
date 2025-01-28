from flask import Flask, render_template, request
import json
import datetime
import lxml.html
from threading import Thread
from urllib.request import urlopen
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tempfile import mkdtemp
import shutil

app = Flask(__name__)

login_url = "https://sukurepo.azurewebsites.net/teachers_report/T_report_login"
target_url = "https://sukurepo.azurewebsites.net/teachers_report/t_menu"
day_schedule_url = "https://sukurepo.azurewebsites.net/teachers_report/t_daySchedule"

def init():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    temp_dir = mkdtemp()
    options.add_argument(f"--user-data-dir={temp_dir}")
    return webdriver.Chrome(options=options), temp_dir

def login(driver, user_id, password):
    print("---------------------------------")
    start_time = datetime.datetime.now()
    # 要素全体から検索
    driver.get(login_url)
    driver.find_element(By.NAME,"id").send_keys(user_id)
    driver.find_element(By.NAME,"pass").send_keys(password)
    driver.find_element(By.ID,"LOGIN_SUBMIT_BUTTON").click()
    end_time = datetime.datetime.now()
    print("全体: ", end_time-start_time)

    # JSで実行
    driver.get(login_url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "id")))
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "pass")))
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "LOGIN_SUBMIT_BUTTON")))
    end_timejs = datetime.datetime.now()
    print("JS before: ", end_timejs-start_time)

    script = f"""
        document.getElementsByName('id').value = '{user_id}';
        document.getElementsByName('pass').value = '{password}';
        document.getElementById('LOGIN_SUBMIT_BUTTON').click();
    """
    driver.execute_script(script)
    end_time1 = datetime.datetime.now()
    print("JS: ", end_time1-end_timejs)

# スクレポを登録
def register_screpo(user_id, password, students, index, content):
    try:
        driver, temp_dir = init()
        tree = lxml.html.parse(urlopen(day_schedule_url))
        html_text = lxml.html.tostring(tree, encoding="utf-8").decode()

        # 1. タイムアウトしている場合はログインする
        if "セッション タイムアウト" in html_text:
            login(driver, user_id, password)

        # TODO: ここで登録処理
        # driver.get(day_schedule_url + index)
        script = f"""
            document.getElementsByName('content').value = '{content}';
            document.getElementById('SUBMIT_BUTTON').click();
        """
        driver.execute_script(script)
    except Exception:
        print("エラー発生")

    finally:
        if 'driver' in locals():
            driver.quit()
        shutil.rmtree(temp_dir)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', error="ログインを行って生徒情報を取得してください", data={ "students": [] })

# 生徒情報の取得
@app.route('/students', methods=['POST'])
def students():
    start_time = datetime.datetime.now()

    # ユーザIDとパスワードを取得
    user_id = request.form.get('user_id')
    password = request.form.get('password')

    try:
        driver, temp_dir = init()
        tree = lxml.html.parse(urlopen(day_schedule_url))
        html_text = lxml.html.tostring(tree, encoding="utf-8").decode()

        # 1. タイムアウトしている場合はログインする
        if "セッション タイムアウト" in html_text:
            login(driver, user_id, password)
            print(f"再ログインの時間: {datetime.datetime.now() - start_time}")

        # 2. 生徒情報ページへ遷移
        driver.get(day_schedule_url)
        print(f"getした時間: {datetime.datetime.now() - start_time}")

        # 3. 生徒情報を取得
        # TODO: 変更！

        students = {
            "students": [
                {
                    "index": 1,
                    "class_start_time": "17:30",
                    "name": "清水大河",
                    "content": "生徒Aのスクレポですわ",
                    "subject": "数学"
                },
                {
                    "index": 2,
                    "class_start_time": "17:30",
                    "name": "佐藤寿也",
                    "content": "",
                    "subject": "英語"
                },
                {
                    "index": 3,
                    "class_start_time": "17:30",
                    "name": "茂野吾郎",
                    "content": "生徒Cのスクレポですわ",
                    "subject": "理科"
                },
                {
                    "index": 4,
                    "class_start_time": "19:00",
                    "name": "清水大河",
                    "content": "生徒Aのスクレポですわ2",
                    "subject": "数学"
                }
            ]
        }

        print(f"全体の時間: ", datetime.datetime.now() - start_time)
        # 担当生徒がいる場合
        if len(students) > 0:
            return render_template('index.html', user_id=user_id, password=password, data=students)
        # 担当生徒がいない場合
        else:
            return render_template('index.html', user_id=user_id, password=password, data={ "students": [] })

    except Exception as e:
        print("例外が発生しました:", str(e))
        return render_template('index.html', user_id=user_id, password=password, error="ユーザIDもしくはパスワードが違います", data={ "students": [] })

    finally:
        if 'driver' in locals():
            driver.quit()
        shutil.rmtree(temp_dir)

# スクレポの自動登録
@app.route('/register', methods=['POST'])
def register():
    user_id = request.form.get('user_id')
    password = request.form.get('password')

    # 生徒名，開始時間，スクレポ内容を取得
    students_json = request.form.get('students').replace("'", '"')
    students = json.loads(students_json)
    index = int(request.form.get('index'))
    content = request.form.get(f'content_{index}')
    class_start_time = ""
    name = ""
    for student in students:
        if student['index'] == index:
            class_start_time = student['class_start_time']
            name = student['name']
            break

    thread = Thread(target=lambda: register_screpo(user_id, password, students, index, content))
    thread.start()

    # 登録済みの生徒をフィルタリング
    students = {
        "students": [
            student for student in students
            if not (student["class_start_time"] == class_start_time and student["name"] == name)
        ]
    }

    if len(students) > 0:
        return render_template('index.html', user_id=user_id, password=password, data=students)
    else:
        return render_template('index.html', user_id=user_id, password=password, data={ "students": [] })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)

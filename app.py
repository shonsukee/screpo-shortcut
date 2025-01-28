from flask import Flask, render_template, request
import json
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tempfile import mkdtemp

app = Flask(__name__)

login_url = "https://sukurepo.azurewebsites.net/teachers_report/T_report_login"
target_url = "https://sukurepo.azurewebsites.net/teachers_report/t_menu"
day_schedule_url = "https://sukurepo.azurewebsites.net/teachers_report/t_daySchedule"

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', error="ログインを行って生徒情報を取得してください", data={ "students": [] })

# 生徒情報の取得
@app.route('/students', methods=['POST'])
def students():
    def login(driver, user_id, password):
        driver.get(login_url)
        driver.find_element(By.NAME,"id").send_keys(user_id)
        driver.find_element(By.NAME,"pass").send_keys(password)
        driver.find_element(By.ID,"LOGIN_SUBMIT_BUTTON").click()

    # ユーザIDとパスワードを取得
    user_id = request.form.get('user_id')
    password = request.form.get('password')

    # ドライバーオプション
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    temp_dir = mkdtemp()
    options.add_argument(f"--user-data-dir={temp_dir}")

    # 1. ログインする
    try:
        start_time = datetime.datetime.now()
        driver = webdriver.Chrome(options=options)
        login(driver, user_id, password)
        end_time = datetime.datetime.now()
        print(f"ログインまでの時間{end_time - start_time}")

        # 1-1. セッションタイムアウト時は再度ログインする
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "MAIN_MENU_TABLE"))
        )
        start_time = datetime.datetime.now()
        page_source = driver.page_source
        if "セッション タイムアウト" in page_source:
            login(driver, user_id, password)
            end_time = datetime.datetime.now()
            print(f"タイムアウト復活までの時間{end_time - start_time}")

    except Exception as e:
        print("例外が発生しました:", str(e))
        if 'driver' in locals():
            driver.quit()
        return render_template('index.html', user_id=user_id, password=password, error="ユーザIDもしくはパスワードが違います", data={ "students": [] })

    start_time = datetime.datetime.now()
    # 2. 生徒情報ページへ遷移
    driver.find_element(By.XPATH, "//input[@value='本日の授業']").click()
    end_time = datetime.datetime.now()
    print(f"本日の授業の時間{end_time - start_time}")

    # 3. 生徒情報を取得
    # TODO: 変更！
    start_time = datetime.datetime.now()
    message_element = driver.find_element(By.CSS_SELECTOR, "label[for='schedule']")
    print(f"スクレイピングしたメッセージ: {message_element.text}")
    end_time = datetime.datetime.now()
    print(f"スクレイピングまでの時間{end_time - start_time}")

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
    driver.quit()

    # 担当生徒がいる場合
    if len(students) > 0:
        return render_template('index.html', user_id=user_id, password=password, data=students)
    # 担当生徒がいない場合
    else:
        return render_template('index.html', user_id=user_id, password=password, data={ "students": [] })

# スクレポの自動登録
@app.route('/register', methods=['POST'])
def register():
    # 生徒名，開始時間，スクレポ内容を取得
    students_json = request.form.get('students').replace("'", '"')
    students = json.loads(students_json)

    index = int(request.form.get('index'))
    class_start_time = ""
    name = ""

    for student in students:
        if student['index'] == index:
            class_start_time = student['class_start_time']
            name = student['name']
            break

    content = request.form.get(f'content_{index}')
    user_id = request.form.get('user_id')
    password = request.form.get('password')

    # ドライバーオプション
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # 1. ログインする
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(login_url)
        driver.find_element(By.NAME,"id").send_keys(user_id)
        driver.find_element(By.NAME,"pass").send_keys(password)
        driver.find_element(By.ID,"LOGIN_SUBMIT_BUTTON").click()

        # 1-1. セッションタイムアウト時は再度ログインする
        WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.ID, "MAIN_MENU_TABLE"))
        )
        page_source = driver.page_source
        if "セッション タイムアウト" in page_source:
            driver.get(login_url)
            driver.find_element(By.NAME,"id").send_keys(user_id)
            driver.find_element(By.NAME,"pass").send_keys(password)
            driver.find_element(By.ID,"LOGIN_SUBMIT_BUTTON").click()

    except Exception:
        driver.quit()
        return render_template('index.html', user_id=user_id, password=password, error="ユーザIDもしくはパスワードが違います", data={ "students": [] })

    # 2. 入力済みである生徒名と時間を基に，記入ページを開く
    # TODO: 生徒ページの判別
    params = {
        'start_time': class_start_time,
        'name': name
    }
    # schedule_url = f"{day_schedule_url}?{urlencode(params)}"
    schedule_url = f"{day_schedule_url}"
    driver.get(schedule_url)

    # 3. 講師が入力したスクレポ情報を書き込む
    # TODO: テキストボックスと登録ボタンの要素特定
    # driver.find_element(By.NAME, "生徒スクレポのテキストボックスNameかIDなど").send_keys(content)
    # driver.find_element(By.ID,"登録ボタンのIDに要変更！").click()
    driver.quit()

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

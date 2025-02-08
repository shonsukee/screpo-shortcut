import os
import json
import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, session
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from tempfile import mkdtemp
import fcntl
import threading

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SESSION_COOKIE_NAME'] = os.getenv('SESSION_COOKIE_NAME')

# スクレポURL
LOGIN_URL = "https://sukurepo.azurewebsites.net/teachers_report/T_report_login"
DAY_SCHEDULE_URL = "https://sukurepo.azurewebsites.net/teachers_report/t_daySchedule"

# ブラウザの初期化
LOCK_FILE = '/tmp/chrome-user-data.lock'
BROWSER_INSTANCE = None
BROWSER_ACCESS_LOCK = threading.Lock()

def acquire_lock(lock_file):
    fd = open(lock_file, 'w')
    fcntl.flock(fd, fcntl.LOCK_EX)
    return fd

def release_lock(fd):
    fcntl.flock(fd, fcntl.LOCK_UN)
    fd.close()

# WARNING: ブラウザの初期化
def init_browser():
    print("!!!!!!!!ブラウザの初期化!!!!!!!!")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.images": 2,
        "javascript.enabled": False
    })
    temp_dir = mkdtemp()
    options.add_argument(f"--user-data-dir={temp_dir}")

    return webdriver.Chrome(options=options)

# ブラウザがNoneの場合のみ実行
def reset_browser_instance():
    global BROWSER_INSTANCE

    lock_fd = acquire_lock(LOCK_FILE)
    try:
        if BROWSER_INSTANCE is not None:
            BROWSER_INSTANCE.quit()
        BROWSER_INSTANCE = init_browser()
    finally:
        release_lock(lock_fd)
    return BROWSER_INSTANCE

# ブラウザの共通インスタンスを取得
def get_browser_instance():
    global BROWSER_INSTANCE

    if BROWSER_INSTANCE is None:
        BROWSER_INSTANCE = reset_browser_instance()

    return BROWSER_INSTANCE

# 生徒情報の取得
def process_students(user_id, password):
    with BROWSER_ACCESS_LOCK:
        try:
            driver = get_browser_instance()
            driver = login(driver, user_id, password)
            if isinstance(driver, Exception):
                return

            # 生徒一覧情報を取得
            driver.get(DAY_SCHEDULE_URL)

            WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".slist_table"))
            )
            students = {"students": []}
            rows = driver.find_elements(By.XPATH, "//tr[@class='slist']")
            if len(rows) == 0:
                return students

            del rows[0]
            search_keys = driver.execute_script("return Serch_Key;")
            search_key_pairs = [item.split() for item in search_keys]

            for index, row in enumerate(rows):
                td_elements = row.find_elements(By.TAG_NAME, "td")
                search_key_pair = search_key_pairs[index]
                if len(td_elements) >= 4 and len(search_key_pair) >= 2 and td_elements[6].text == "未入力":
                    search_key1 = search_key_pair[0]
                    search_key2 = search_key_pair[1]
                    class_start_time = td_elements[2].text.split('～')[0]
                    student_name = td_elements[3].text
                    subject = td_elements[5].text
                    students["students"].append({
                        "index": index + 1,
                        "class_start_time": class_start_time,
                        "name": student_name,
                        "subject": subject,
                        "key1": search_key1,
                        "key2": search_key2,
                        "key3": 1,
                    })
            return students
        except TimeoutException as e:
            print("授業がありませんでした...", type(e).__name__)
            return e
        except Exception as e:
            print("例外が発生しました:",  type(e).__name__, str(e))
            return e

# ログイン処理
def login(driver, user_id, password):
    try:
        print("---------- login開始 --------------")
        start_time = datetime.datetime.now()
        print(f"ログイン開始: {start_time}")

        # NOTE: 5秒程度かかる
        driver.get(LOGIN_URL)

        WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.NAME, "id")))
        WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.NAME, "pass")))
        WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.ID, "LOGIN_SUBMIT_BUTTON")))
        print(f"ログイン項目待機: {datetime.datetime.now() - start_time}")

        # JSで実行
        driver.find_element(By.ID, "id").send_keys(user_id)
        driver.find_element(By.ID, "pass").send_keys(password)
        driver.find_element(By.ID, "LOGIN_SUBMIT_BUTTON").click()
        WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.ID, "BUTTON_SIZE")))
        print(f"ログイン実行: {datetime.datetime.now() - start_time}")

        print("---------- login終了 --------------")
        return driver

    except TimeoutException as e:
        print("ログイン画面がタイムアウトしました...", type(e).__name__)
        return e

    except Exception as e:
        print("ログインエラーが発生しました: ", type(e).__name__, str(e))
        return e

# スクレポを登録
def process_register(user_id, password, students, index, content):
    with BROWSER_ACCESS_LOCK:
        try:
            start_time = datetime.datetime.now()

            # 1. ログイン処理
            driver = get_browser_instance()
            driver = login(driver, user_id, password)
            if isinstance(driver, Exception):
                return

            # 2. 生徒一覧ページへ遷移
            driver.get(DAY_SCHEDULE_URL)

            # 3. 生徒個別ページへ遷移
            key1, key2, key3 = next(
                ((s["key1"], s["key2"], s["key3"]) for s in students if s["index"] == index),
                (1, 1, 1)
            )
            xpath = f'//button[contains(@onclick, "grid_click( {key1}, {key2}, {key3} );")]'
            button = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            driver.execute_script("arguments[0].scrollIntoView();", button)
            WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            button.click()
            print("生徒個別ページへ遷移", datetime.datetime.now()-start_time)

            # 4. スクレポ記入
            WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.ID, "com_teacher"))
            )
            # テキストを記入
            textarea = driver.find_element(By.XPATH, "//textarea[@id='com_teacher']")
            textarea.clear()
            textarea.send_keys(content)
            print("テキスト入力", datetime.datetime.now()-start_time)

            # 登録ボタン押下
            register_button = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, "//li[@class='ui-block-d']/a"))
            )
            driver.execute_script("arguments[0].scrollIntoView();", register_button)
            register_button.click()
            print("登録ボタン押下", datetime.datetime.now()-start_time)

            # 確認ボタン押下
            WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.ID, "dialog1"))
            )
            confirm_button = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@id='dialog1']//button[text()='はい']"))
            )
            driver.execute_script("arguments[0].scrollIntoView();", confirm_button)
            confirm_button.click()
            print("確認ボタン押下", datetime.datetime.now()-start_time)

        except TimeoutException as e:
            print("授業がありませんでした...", type(e).__name__)

        except Exception as e:
            print("エラー発生", type(e).__name__, str(e))

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', error="ログインして生徒情報を<br>取得してください🕵️‍♀️", data={ "students": [] })

# 生徒情報の取得
@app.route('/students', methods=['GET', 'POST'])
def students():
    if request.method == 'GET':
        return render_template('index.html', error="ログインして生徒情報を<br>取得してください🕵️‍♀️", data={ "students": [] })

    elif request.method == 'POST':
        start_time = datetime.datetime.now()

        # ユーザIDとパスワードを取得
        user_id = request.form.get('user_id') or session.get('user_id')
        password = request.form.get('password') or session.get('password')
        if not user_id or not password:
            return render_template('index.html', error="ログイン情報が不足しています🥺", data={ "students": [] })
        session['user_id'] = user_id
        session['password'] = password

        # 生徒情報取得をキューイング
        print(f"生徒情報の処理実行: {datetime.datetime.now() - start_time}")
        result = process_students(user_id, password)
        print(f"生徒情報の処理終了: {datetime.datetime.now() - start_time}")

        if isinstance(result, Exception):
            return render_template('index.html', error="授業はありません💤", data={ "students": [] })

        # 生徒情報が取得できた場合
        if len(result["students"]) > 0:
            return render_template('index.html', user_id=user_id, data=result)
        else:
            return render_template('index.html', user_id=user_id, error="全て入力済みです！<br>お疲れ様でした🚀", data={"students": []})


# スクレポの自動登録
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('index.html', error="ログインして生徒情報を<br>取得してください🕵️‍♀️", data={ "students": [] })

    elif request.method == 'POST':
        # ユーザIDとパスワードを取得
        user_id = request.form.get('user_id') or session.get('user_id')
        password = request.form.get('password') or session.get('password')
        if not user_id or not password:
            return render_template('index.html', error="ログイン情報が不足しています🥺", data={ "students": [] })
        session['user_id'] = user_id
        session['password'] = password

        # スクレポ内容を取得
        index = int(request.form.get('index'))
        content = request.form.get(f'content_{index}')

        # 生徒情報を取得
        students_json = request.form.get('students').replace("'", '"')
        students_data = json.loads(students_json)
        class_start_time = ""
        name = ""
        for student in students_data:
            if student['index'] == index:
                class_start_time = student['class_start_time']
                name = student['name']
                break

        thread = threading.Thread(target=process_register, args=[user_id, password, students_data, index, content], daemon=True)
        thread.start()
        filtered_students = {"students": [student for student in students_data if not (student["class_start_time"] == class_start_time and student["name"] == name)]}
        if len(filtered_students["students"]) > 0:
            return render_template('index.html', user_id=user_id, data=filtered_students)
        else:
            return render_template('index.html', user_id=user_id, error="全て入力済みです！<br>お疲れ様でした🚀", data={"students": []})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)

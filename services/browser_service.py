from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from tempfile import mkdtemp
from utils.lock_utils import acquire_lock, release_lock, LOCK_FILE
import datetime

# スクレポURL
LOGIN_URL = "https://sukurepo.azurewebsites.net/teachers_report/T_report_login"

# ブラウザの初期化
BROWSER_INSTANCE = None

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

def get_browser_instance():
    global BROWSER_INSTANCE

    if BROWSER_INSTANCE is None:
        BROWSER_INSTANCE = reset_browser_instance()

    return BROWSER_INSTANCE

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

def logout(driver):
    try:
        print("---------- logout開始 --------------")
        start_time = datetime.datetime.now()
        print(f"ログアウト開始: {start_time}")

        # クッキーを削除
        driver.delete_all_cookies()

        print(f"クッキー削除完了: {datetime.datetime.now() - start_time}")
        print("---------- logout終了 --------------")
        return True

    except Exception as e:
        print("ログアウトエラーが発生しました: ", type(e).__name__, str(e))
        return False
import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from services.browser_service import get_browser_instance, login, logout
from utils.lock_utils import BROWSER_ACCESS_LOCK

# スクレポURL
DAY_SCHEDULE_URL = "https://sukurepo.azurewebsites.net/teachers_report/t_daySchedule"

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
        finally:
            logout(driver)

def process_register(user_id, password, students_data, sukurepo_data):
    with BROWSER_ACCESS_LOCK:
        try:
            start_time = datetime.datetime.now()

            # 入力を取得
            index = sukurepo_data['index']
            content = sukurepo_data[f'content_{index}']
            late = sukurepo_data['late']
            homework = sukurepo_data['homework']
            concentration = sukurepo_data['concentration']
            understanding = sukurepo_data['understanding']
            today_homework = sukurepo_data['today_homework']

            # 1. ログイン処理
            driver = get_browser_instance()
            driver = login(driver, user_id, password)
            if isinstance(driver, Exception):
                return

            # 2. 生徒一覧ページへ遷移
            driver.get(DAY_SCHEDULE_URL)

            # 3. 生徒個別ページへ遷移
            key1, key2, key3 = next(
                ((s["key1"], s["key2"], s["key3"]) for s in students_data if s["index"] == index),
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

            # 追加情報処理
            ## 遅刻有の場合
            if late != "0":
                late_button = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[@id='delay_group']//label"))
                )
                late_button.click()

            ## 宿題をやっていない場合
            if homework != "3":
                id = int(homework)
                key = ['buttonB2', 'button_A2', 'button_B1']

                homework_button = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, f"//*[@id='homework_group']//*[@id='{key[id]}']//label"))
                )
                homework_button.click()

            ## 集中力
            if concentration != "2":
                key = ['E', 'D', 'C', 'B', 'A']
                button_id = "button_" + key[int(concentration)]

                concentration_button = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, f"//*[@id='concentration_group']//*[@id='{button_id}']//label"))
                )
                concentration_button.click()

            ## 理解度
            if understanding != "2":
                key = ['E', 'D', 'C', 'B', 'A']
                button_id = "button_" + key[int(understanding)]

                understanding_button = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, f"//*[@id='knowledge_group']//*[@id='{button_id}']//label"))
                )
                understanding_button.click()

            ## 本日の宿題がない場合
            if today_homework != "1":
                today_homework_button = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="todays_homework_group"]//*[@id="button_B"]//label'))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", today_homework_button)
                driver.execute_script("arguments[0].click();", today_homework_button)

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
            print("****** スクレポ登録終了 ******")

        except TimeoutException as e:
            print("****** 授業がありませんでした ******", type(e).__name__)

        except Exception as e:
            print("****** エラー発生 ******", type(e).__name__, str(e))

        finally:
            logout(driver)
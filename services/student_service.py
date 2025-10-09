import datetime
from playwright.async_api import TimeoutError as PwTimeout
from services.browser_service import get_browser_instance, login, logout
from utils.lock_utils import BROWSER_ACCESS_LOCK

DAY_SCHEDULE_URL = "https://sukurepo.azurewebsites.net/teachers_report/t_daySchedule"

async def process_students(user_id, password):
    async with BROWSER_ACCESS_LOCK:
        browser = await get_browser_instance()

    context = await browser.new_context(java_script_enabled=True)
    page = None
    try:
        page_or_exc = await login(context, user_id, password)
        if isinstance(page_or_exc, Exception):
            await context.close()
            return
        page = page_or_exc

        # 生徒一覧
        await page.goto(DAY_SCHEDULE_URL, wait_until="domcontentloaded", timeout=3000)

        # テーブルが出るまで待機
        await page.locator(".slist_table").wait_for(timeout=3000)

        # 行を収集
        rows = page.locator("//tr[@class='slist']")
        count = await rows.count()
        students = {"students": []}
        if count == 0:
            await context.close()
            return students

        # JS 変数 Serch_Key を拾う
        search_keys = await page.evaluate("() => window.Serch_Key")
        search_key_pairs = [item.split() for item in search_keys] if search_keys else []

        # 2行目以降抽出
        for i in range(1, count):
            row = rows.nth(i)
            tds = row.locator("td")
            # 必要な列を読む
            t0 = await tds.nth(2).inner_text()   # 時刻
            t1 = await tds.nth(3).inner_text()   # 氏名
            t2 = await tds.nth(5).inner_text()   # 教科
            status = await tds.nth(6).inner_text()

            if i-1 < len(search_key_pairs) and status.strip() == "未入力":
                key1, key2 = search_key_pairs[i-1][:2]
                class_start_time = t0.split('～')[0]
                students["students"].append({
                    "index": i,
                    "class_start_time": class_start_time,
                    "name": t1.strip(),
                    "subject": t2.strip(),
                    "key1": key1,
                    "key2": key2,
                    "key3": 1,
                })
        return students

    except PwTimeout as e:
        print("授業がありませんでした...", type(e).__name__)
        raise e
    except Exception as e:
        print("例外が発生しました:", type(e).__name__, str(e))
        raise e
    finally:
        await logout(context)
        await context.close()

async def process_register(user_id, password, students_data, sukurepo_data):
    async with BROWSER_ACCESS_LOCK:
        browser = await get_browser_instance()

    context = await browser.new_context(java_script_enabled=True)
    page = None
    try:
        start_time = datetime.datetime.now()

        index = sukurepo_data["index"]
        content = sukurepo_data.get(f"content_{index}", "")
        late = sukurepo_data.get("late", "0")
        homework = sukurepo_data.get("homework", "3")
        concentration = sukurepo_data.get("concentration", "2")
        understanding = sukurepo_data.get("understanding", "2")
        today_homework = sukurepo_data.get("today_homework", "1")

        page_or_exc = await login(context, user_id, password)
        if isinstance(page_or_exc, Exception):
            await context.close()
            return
        page = page_or_exc

        await page.goto(DAY_SCHEDULE_URL, wait_until="domcontentloaded", timeout=10000)

        key1, key2, key3 = next(
            ((s["key1"], s["key2"], s["key3"]) for s in students_data if s["index"] == index),
            (1, 1, 1)
        )
        # ボタン押下
        xpath = f'//button[contains(@onclick, "grid_click( {key1}, {key2}, {key3} );")]'
        btn = page.locator(xpath)
        await btn.scroll_into_view_if_needed()
        await btn.wait_for(state="visible", timeout=5000)
        await btn.click()
        print("生徒個別ページへ遷移", datetime.datetime.now()-start_time)

        # スクレポ記入
        await page.locator("#com_teacher").wait_for(timeout=5000)
        ta = page.locator("#com_teacher")
        await ta.fill("")
        await ta.type(content or "")
        print("テキスト入力", datetime.datetime.now()-start_time)

        # 追加情報
        ## 遅刻有の場合
        if late != "0":
            await page.locator("//*[@id='delay_group']//label").first.click()
        ## 宿題をやっていない場合
        if homework != "3":
            hid = int(homework)
            key = ['buttonB2', 'button_A2', 'button_B1']
            await page.locator(f"//*[@id='homework_group']//*[@id='{key[hid]}']//label").click()
        ## 集中力
        if concentration != "2":
            key = ['E', 'D', 'C', 'B', 'A']
            btn_id = "button_" + key[int(concentration)]
            await page.locator(f"//*[@id='concentration_group']//*[@id='{btn_id}']//label").click()

        ## 理解度
        if understanding != "2":
            key = ['E', 'D', 'C', 'B', 'A']
            btn_id = "button_" + key[int(understanding)]
            await page.locator(f"//*[@id='knowledge_group']//*[@id='{btn_id}']//label").click()

        ## 本日の宿題がない場合
        if today_homework != "1":
            th = page.locator('//*[@id="todays_homework_group"]//*[@id="button_B"]//label')
            await th.scroll_into_view_if_needed()
            await th.click()

        # 登録ボタン押下
        reg = page.locator("//li[@class='ui-block-d']/a")
        await reg.scroll_into_view_if_needed()
        await reg.click()
        print("登録ボタン押下", datetime.datetime.now()-start_time)

        # 確認ボタン押下
        await page.locator("#dialog1").wait_for(timeout=5000)
        ok = page.locator("//div[@id='dialog1']//button[text()='はい']")
        await ok.scroll_into_view_if_needed()
        await ok.click()
        print("確認ボタン押下", datetime.datetime.now()-start_time)
        print("****** スクレポ登録終了 ******")

    except PwTimeout as e:
        print("****** 授業がありませんでした ******", type(e).__name__)
    except Exception as e:
        print("****** エラー発生 ******", type(e).__name__, str(e))
        raise e
    finally:
        await logout(context)
        await context.close()

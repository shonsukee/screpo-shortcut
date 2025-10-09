import datetime
from playwright.async_api import async_playwright, TimeoutError as PwTimeout
from utils.lock_utils import BROWSER_ACCESS_LOCK

LOGIN_URL = "https://sukurepo.azurewebsites.net/teachers_report/T_report_login"

_playwright = None
_browser = None

async def _ensure_browser():
    global _playwright, _browser
    async with BROWSER_ACCESS_LOCK:
        if _playwright is None:
            _playwright = await async_playwright().start()
        if _browser is None:
            _browser = await _playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-extensions",
                ],
            )
    return _browser

async def get_browser_instance():
    return await _ensure_browser()

async def login(context, user_id: str, password: str):
    try:
        print("---------- login開始 --------------")
        start_time = datetime.datetime.now()
        page = await context.new_page()

        await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=10000)

        await page.locator("[name='id']").wait_for(timeout=5000)
        await page.locator("[name='pass']").wait_for(timeout=5000)
        await page.locator("#LOGIN_SUBMIT_BUTTON").wait_for(state="attached", timeout=5000)
        print(f"ログイン項目待機: {datetime.datetime.now() - start_time}")

        await page.fill("#id", user_id)
        await page.fill("#pass", password)
        await page.click("#LOGIN_SUBMIT_BUTTON")

        # ログイン後はメニューURLの遷移を待つ
        await page.wait_for_url("**/teachers_report/t_menu", timeout=10000)

        # IDが重複しているためvalueで絞る
        await page.locator("input#BUTTON_SIZE[value='本日の授業']").wait_for(timeout=5000)

        print(f"ログイン実行: {datetime.datetime.now() - start_time}")
        print("---------- login終了 --------------")
        return page

    except PwTimeout as e:
        print("ログイン画面がタイムアウトしました...", type(e).__name__)
        raise e
    except Exception as e:
        print("ログインエラーが発生しました: ", type(e).__name__, str(e))
        raise e

async def logout(context):
    """
    Cookie/Storage を消す
    """
    try:
        print("---------- logout開始 --------------")
        await context.close()
        print("---------- logout終了 --------------")
        return True
    except Exception as e:
        print("ログアウトエラーが発生しました: ", type(e).__name__, str(e))
        raise False
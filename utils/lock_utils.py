import asyncio

# Playwright のブラウザ操作を直列化したい箇所で使うロック
BROWSER_ACCESS_LOCK = asyncio.Lock()

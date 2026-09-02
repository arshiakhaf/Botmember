"""ربات فروشگاهی تلگرام — نقطه ورود برنامه.

دو حالت اجرا:
  1) Polling (پیش‌فرض): مناسب اجرای محلی — python main.py
  2) Webhook: مناسب هاست‌های رایگان (Render/Koyeb) — فقط کافی است
     WEBHOOK_URL را تنظیم کنید (در Render خودکار از RENDER_EXTERNAL_URL می‌آید).
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

import config
import store
from handlers import admin, user

logger = logging.getLogger(__name__)


async def health(request: web.Request) -> web.Response:
    """نقطه بررسی سلامت برای Render/Koyeb و سرویس‌های keep-alive."""
    return web.json_response({"ok": True})


def build_webhook_app(bot: Bot, dp: Dispatcher) -> web.Application:
    """ساخت اپلیکیشن aiohttp برای حالت وب‌هوک."""
    webhook_url = config.WEBHOOK_URL.rstrip("/") + config.WEBHOOK_PATH

    async def on_startup(bot: Bot) -> None:
        await bot.set_webhook(webhook_url, drop_pending_updates=True)
        logger.info("Webhook set to %s", webhook_url)

    async def on_shutdown(bot: Bot) -> None:
        await bot.delete_webhook()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    app.router.add_get("/", health)
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=config.WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    return app


def run_webhook(bot: Bot, dp: Dispatcher) -> None:
    app = build_webhook_app(bot, dp)
    web.run_app(app, host="0.0.0.0", port=config.PORT)


async def run_polling(bot: Bot, dp: Dispatcher) -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if not config.BOT_TOKEN:
        print("❌ BOT_TOKEN در .env تنظیم نشده است.")
        return

    store.ensure_seed_products()

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(user.router)
    dp.include_router(admin.router)

    if config.WEBHOOK_URL:
        logger.info("حالت Webhook با آدرس %s", config.WEBHOOK_URL)
        run_webhook(bot, dp)
    else:
        logger.info("حالت Polling")
        asyncio.run(run_polling(bot, dp))


if __name__ == "__main__":
    main()

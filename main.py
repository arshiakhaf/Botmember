"""ربات فروشگاهی تلگرام — نقطه ورود برنامه.

نمونه‌ای کامل برای تحویل پروژه دانشگاهی:
انتخاب کالا ← سبد خرید ← نمایش شماره کارت ← واریز ← آپلود رسید ← تأیید ادمین.
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import config
import store
from handlers import admin, user


async def main():
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

    print("[bot] در حال راه‌اندازی...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

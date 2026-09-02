"""لاگین کردن حساب یوزربات و ذخیره سشن.

قبل از اجرا، API_ID و API_HASH را در فایل .env وارد کنید
(از https://my.telegram.org بخش API development).

استفاده:
    python setup_account.py
    python setup_account.py +989123456789
"""
import asyncio
import sys

from telethon import TelegramClient

from config import API_HASH, API_ID, SESSION_NAME


async def main():
    if not API_ID or not API_HASH:
        print("ابتدا API_ID و API_HASH را در فایل .env وارد کنید.")
        print("از https://my.telegram.org بخش API development بگیرید.")
        return

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    phone = sys.argv[1] if len(sys.argv) > 1 else None
    await client.start(phone=phone)

    me = await client.get_me()
    print(f"\n✅ لاگین موفق: {me.first_name} (@{me.username}) | id={me.id}")
    print("می‌توانید این آی‌دی را در .env کنار ADMIN_IDS قرار دهید.")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

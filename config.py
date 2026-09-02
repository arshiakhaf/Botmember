"""تنظیمات ربات — از فایل .env خوانده می‌شود."""
import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# اطلاعات کارت برای واریز
CARD_NUMBER = os.getenv("CARD_NUMBER", "6037-9970-1234-5678").strip()
CARD_HOLDER = os.getenv("CARD_HOLDER", "نام صاحب کارت").strip()

# پشتیبانی
SUPPORT = os.getenv("SUPPORT", "@support").strip()


def _parse_ids(raw: str) -> set:
    """تبدیل '123, 456' به مجموعه‌ای از عددها (پشتیبانی از ممیز فارسی)."""
    if not raw:
        return set()
    ids = set()
    for part in raw.replace("،", ",").split(","):
        part = part.strip()
        if part.lstrip("-").isdigit():
            ids.add(int(part))
    return ids


# آی‌دی عددی ادمین‌های مجاز (برای دسترسی به پنل /admin)
ADMIN_IDS = _parse_ids(os.getenv("ADMIN_IDS", ""))

"""خواندن تنظیمات از فایل .env"""
import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
API_ID = int(os.getenv("API_ID", "0") or 0)
API_HASH = os.getenv("API_HASH", "").strip()
SESSION_NAME = os.getenv("SESSION_NAME", "account").strip()
DEFAULT_COUNTRY_CODE = os.getenv("DEFAULT_COUNTRY_CODE", "98").strip()


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


ADMIN_IDS = _parse_ids(os.getenv("ADMIN_IDS", ""))

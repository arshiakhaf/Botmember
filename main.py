"""ربات تلگرامی اضافه‌کننده عضو با شماره موبایل.

- ربات (توکن BotFather) = پنل مدیریت / دریافت دستورها از ادمین.
- یوزربات (Telethon) = حساب کاربری واقعی که عملیات اضافه کردن را انجام می‌دهد.

قبل از اجرا:
    1) .env را تنظیم کنید (توکن + API_ID/API_HASH از my.telegram.org).
    2) python setup_account.py را اجرا کنید تا حساب یوزربات لاگین شود.
    3) python main.py را اجرا کنید.

⚠️ فقط مخاطبانی را اضافه کنید که رضایت دارند؛ اضافه کردن بدون رضایت
برخلاف قوانین تلگرام است و به محدودیت/مسدود شدن حساب می‌انجامد.
"""
import asyncio
import json
import os

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from telethon import TelegramClient

import config
from adder import add_phone

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
router = Router()

# یوزربات فقط وقتی ساخته می‌شود که API_ID/API_HASH تنظیم شده باشند
userbot = (
    TelegramClient(config.SESSION_NAME, config.API_ID, config.API_HASH)
    if config.API_ID and config.API_HASH
    else None
)

STATE_FILE = os.path.join("data", "state.json")
ADD_DELAY_SECONDS = 2  # فاصله بین هر اضافه کردن برای جلوگیری از فلود

owner_id = 0
userbot_ready = False


# ---------- ذخیره مقصد ----------
def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ---------- کنترل دسترسی ----------
def is_admin(user_id: int) -> bool:
    if user_id == owner_id:
        return True
    if user_id in config.ADMIN_IDS:
        return True
    # اگر هنوز هیچ ادمینی مشخص نیست، دسترسی آزاد است (فقط تا قبل از لاگین یوزربات)
    if not config.ADMIN_IDS and owner_id == 0:
        return True
    return False


async def ensure_admin(m: Message) -> bool:
    if not is_admin(m.from_user.id):
        await m.answer("⛔️ شما اجازه استفاده از این ربات را ندارید.")
        return False
    return True


# ---------- دستورها ----------
HELP_TEXT = (
    "📖 راهنما:\n\n"
    "/target <آیدی> — انتخاب گروه/کانال مقصد\n"
    "/add <شماره> — اضافه کردن یک عضو\n"
    "/addmany <شماره‌ها> — اضافه کردن چند عضو (جدا با کاما یا خط جدید)\n"
    "/status — وضعیت اتصال یوزربات\n"
    "/help — همین راهنما\n\n"
    "نمونه:\n"
    "/target @mychannel\n"
    "/add 09123456789\n"
    "/addmany 09123456789\n"
    "09011112222"
)


@router.message(CommandStart())
async def cmd_start(m: Message):
    await m.answer(
        "سلام 👋 ربات اضافه‌کننده عضو با شماره موبایل\n\n" + HELP_TEXT
    )


@router.message(Command("help"))
async def cmd_help(m: Message):
    await m.answer(HELP_TEXT)


@router.message(Command("target"))
async def cmd_target(m: Message):
    if not await ensure_admin(m):
        return
    arg = m.text.split(maxsplit=1)
    if len(arg) < 2:
        await m.answer("استفاده: /target @channel یا /target -1001234567890")
        return
    target = arg[1].strip()

    # اگر یوزربات متصل است، صحت آیدی را هم بررسی می‌کنیم
    if userbot_ready and userbot is not None:
        try:
            entity = await userbot.get_entity(target)
            kind = "گروه" if getattr(entity, "megagroup", False) else (
                "کانال" if getattr(entity, "broadcast", False) else "گروه"
            )
            note = f" ({kind})"
        except Exception:
            note = " (⚠️ بررسی نشد؛ مطمئن شوید یوزربات عضو آن است)"
    else:
        note = ""

    state = load_state()
    state.setdefault(str(m.from_user.id), {})["target"] = target
    save_state(state)
    await m.answer(f"✅ مقصد ذخیره شد: {target}{note}")


@router.message(Command("status"))
async def cmd_status(m: Message):
    if userbot_ready and userbot is not None:
        me = await userbot.get_me()
        await m.answer(
            f"✅ یوزربات متصل است.\nحساب: {me.first_name} (@{me.username})\nid: {me.id}"
        )
    else:
        await m.answer(
            "⛔️ حساب یوزربات متصل نیست.\n\n"
            "۱) API_ID و API_HASH را در .env وارد کنید\n"
            "۲) `python setup_account.py` را اجرا کنید\n"
            "۳) دوباره `python main.py` را اجرا کنید"
        )


async def _run_add(m: Message, phone: str, target: str):
    if userbot is None or not userbot_ready:
        await m.answer(
            "⛔️ حساب یوزربات متصل نیست. اول API_ID/API_HASH را تنظیم و "
            "`python setup_account.py` را اجرا کنید."
        )
        return
    status = await m.answer("⏳ در حال اضافه کردن...")
    ok, text = await add_phone(userbot, phone, target)
    await status.edit_text(text)


@router.message(Command("add"))
async def cmd_add(m: Message):
    if not await ensure_admin(m):
        return
    arg = m.text.split(maxsplit=1)
    if len(arg) < 2:
        await m.answer("استفاده: /add 09123456789")
        return
    state = load_state()
    target = state.get(str(m.from_user.id), {}).get("target")
    if not target:
        await m.answer("اول مقصد را با /target مشخص کنید.")
        return
    await _run_add(m, arg[1].strip(), target)


@router.message(Command("addmany"))
async def cmd_addmany(m: Message):
    if not await ensure_admin(m):
        return
    arg = m.text.split(maxsplit=1)
    if len(arg) < 2:
        await m.answer(
            "استفاده:\n/addmany 09123456789\n09011112222\n\n"
            "یا با کاما: /addmany 0912..., 0913..."
        )
        return
    state = load_state()
    target = state.get(str(m.from_user.id), {}).get("target")
    if not target:
        await m.answer("اول مقصد را با /target مشخص کنید.")
        return
    if userbot is None or not userbot_ready:
        await m.answer(
            "⛔️ حساب یوزربات متصل نیست. اول `python setup_account.py` را اجرا کنید."
        )
        return

    raw = arg[1].strip()
    phones = [p.strip() for p in raw.replace("،", ",").replace("\n", ",").split(",") if p.strip()]
    if not phones:
        await m.answer("شماره‌ای یافت نشد.")
        return

    progress = await m.answer(f"⏳ در حال اضافه کردن {len(phones)} شماره...")
    lines = []
    for p in phones:
        ok, text = await add_phone(userbot, p, target)
        lines.append(text)
        await asyncio.sleep(ADD_DELAY_SECONDS)
    await progress.edit_text("\n".join(lines))


# ---------- اجرا ----------
async def main():
    global userbot_ready, owner_id

    if not config.BOT_TOKEN:
        print("❌ BOT_TOKEN در .env تنظیم نشده است.")
        return

    # اتصال یوزربات (اختیاری — ربات بدون آن هم بالا می‌آید)
    if config.API_ID and config.API_HASH:
        try:
            await userbot.connect()
            if await userbot.is_user_authorized():
                userbot_ready = True
                me = await userbot.get_me()
                owner_id = me.id
                print(f"[userbot] متصل: {me.first_name} (id={me.id})")
            else:
                print("[userbot] سشن معتبری پیدا نشد. برای فعال شدن /add، "
                      "`python setup_account.py` را اجرا کنید.")
                await userbot.disconnect()
        except Exception as e:
            print(f"[userbot] خطای اتصال: {e}")
            userbot_ready = False
    else:
        print("[userbot] API_ID/API_HASH تنظیم نشده؛ فقط پنل مدیریت فعال است.")

    dp.include_router(router)
    print("[bot] در حال اجرا...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

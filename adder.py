"""منطق اضافه کردن عضو با شماره موبایل (یوزربات / Telethon).

نکته مهم: اضافه کردن کاربر با شماره فقط برای کسانی ممکن است که در تنظیمات
حریم خصوصی تلگرام اجازه داده باشند. تلگرام هرگونه اسپم را محدود/مسدود می‌کند.
این ابزار را فقط برای مخاطبانی استفاده کنید که رضایت دارند.
"""
import asyncio

from telethon import functions, types
from telethon.errors import (
    ChannelPrivateError,
    ChatAdminRequiredError,
    ChatWriteForbiddenError,
    FloodWaitError,
    PeerFloodError,
    UserAlreadyParticipantError,
    UserChannelsTooMuchError,
    UserPrivacyRestrictedError,
)

FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"
EN_DIGITS = "0123456789"
_DIGIT_TABLE = str.maketrans(FA_DIGITS + AR_DIGITS, EN_DIGITS + EN_DIGITS)


def normalize_phone(raw, country_code="98"):
    """شماره را به فرمت بین‌المللی «+98...» تبدیل می‌کند (پشتیبانی از اعداد فارسی/عربی)."""
    if raw is None:
        return None
    s = str(raw).strip().translate(_DIGIT_TABLE)
    digits = "".join(ch for ch in s if ch.isdigit())
    if not digits:
        return None
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("0"):
        digits = country_code + digits[1:]
    elif not digits.startswith(country_code) and len(digits) == 10:
        digits = country_code + digits
    return "+" + digits


async def resolve_user_by_phone(client, phone):
    """شماره را import می‌کند و کاربر تلگرام مربوطه را برمی‌گرداند (یا None)."""
    normalized = normalize_phone(phone)
    if not normalized:
        return None
    contact = types.InputPhoneContact(
        client_id=0, phone=normalized, first_name="Contact", last_name=""
    )
    result = await client(functions.contacts.ImportContactsRequest([contact]))
    for user in result.users:
        if getattr(user, "phone", None) == normalized:
            return user
    return None


async def _add(client, user, entity):
    """اضافه کردن کاربر به گروه ساده / سوپرگروه / کانال."""
    input_user = await client.get_input_entity(user)
    if isinstance(entity, types.Chat):
        # گروه ساده
        await client(
            functions.messages.AddChatUserRequest(
                chat_id=entity.id,
                user_id=input_user,
                fwd_limit=0,
            )
        )
    elif isinstance(entity, types.Channel):
        # سوپرگروه یا کانال
        await client(
            functions.channels.InviteToChannelRequest(
                channel=entity,
                users=[input_user],
            )
        )
    else:
        raise ValueError("مقصد پشتیبانی نمی‌شود (فقط گروه/سوپرگروه/کانال)")


async def add_phone(client, phone, target):
    """شماره را به مقصد اضافه می‌کند. خروجی: (ok, message)."""
    try:
        entity = await client.get_entity(target)
    except Exception:
        return False, (
            "❌ مقصد پیدا نشد. مطمئن شوید حساب یوزربات عضو گروه/کانال است و آیدی درست است.\n"
            "نمونه: @channel یا -1001234567890 یا لینک دعوت"
        )

    try:
        user = await resolve_user_by_phone(client, phone)
    except FloodWaitError as e:
        await asyncio.sleep(min(e.seconds, 60))
        try:
            user = await resolve_user_by_phone(client, phone)
        except Exception:
            user = None

    if not user:
        return False, "❌ کاربری با این شماره در تلگرام پیدا نشد."

    name = user.first_name or "کاربر"
    phone_norm = normalize_phone(phone)

    try:
        await _add(client, user, entity)
        return True, f"✅ {name} ({phone_norm}) اضافه شد."
    except UserPrivacyRestrictedError:
        return False, f"❌ حریم خصوصی {name} اجازه اضافه شدن با شماره را نمی‌دهد."
    except UserAlreadyParticipantError:
        return False, f"ℹ️ {name} از قبل عضو است."
    except ChatAdminRequiredError:
        return False, "❌ حساب یوزربات ادمین مقصد نیست یا دسترسی اضافه کردن ندارد."
    except ChatWriteForbiddenError:
        return False, "❌ حساب یوزربات اجازه اضافه کردن در این مقصد را ندارد."
    except UserChannelsTooMuchError:
        return False, "❌ کاربر عضو تعداد زیادی کانال است."
    except ChannelPrivateError:
        return False, "❌ گروه/کانال خصوصی است."
    except PeerFloodError:
        return False, "⛔️ فلود: فعلاً امکان اضافه کردن نیست؛ کمی صبر کنید."
    except FloodWaitError as e:
        return False, f"⛔️ محدودیت تلگرام: {e.seconds} ثانیه صبر کنید."
    except ValueError as e:
        return False, f"❌ {e}"
    except Exception as e:
        return False, f"❌ خطای نامشخص: {type(e).__name__}: {e}"

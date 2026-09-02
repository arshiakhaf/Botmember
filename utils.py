"""توابع کمکی: قیمت، اعداد فارسی/عربی، اِسکیپ HTML."""
import html

FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"
EN_DIGITS = "0123456789"
_DIGIT_TABLE = str.maketrans(FA_DIGITS + AR_DIGITS, EN_DIGITS + EN_DIGITS)


def fa_to_en(s):
    """تبدیل ارقام فارسی/عربی به انگلیسی."""
    return str(s).translate(_DIGIT_TABLE)


def parse_int(s):
    """استخراج عدد صحیح از متن (پشتیبانی از ارقام فارسی/عربی و جداکننده هزار)."""
    digits = "".join(ch for ch in fa_to_en(s) if ch.isdigit())
    return int(digits) if digits else None


def fmt_price(n):
    """۴۵۰۰۰۰ -> «۴۵۰٬۰۰۰ تومان»"""
    return f"{int(n):,}".replace(",", "٬") + " تومان"


def h(s):
    """اسکیپ متن برای حالت HTML."""
    return html.escape(str(s))


STATUS_LABELS = {
    "pending": "⏳ در انتظار تأیید",
    "confirmed": "✅ تأیید شده",
    "rejected": "❌ رد شده",
}


def status_label(s):
    return STATUS_LABELS.get(s, s)

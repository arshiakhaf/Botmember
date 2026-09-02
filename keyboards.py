"""ساخت کیبوردهای inline ربات."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def _btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data)


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn("🛍 محصولات", "products"), _btn("🛒 سبد خرید", "cart")],
        [_btn("📦 سفارش‌های من", "myorders"), _btn("💳 کارت واریز", "card")],
        [_btn("📞 پشتیبانی", "support"), _btn("ℹ️ راهنما", "help")],
    ])


def back_to_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[_btn("🏠 منوی اصلی", "menu")]])


def products_kb(products) -> InlineKeyboardMarkup:
    rows = [[_btn(f"{p['emoji']} {p['name']}", f"p:{p['id']}")] for p in products]
    rows.append([_btn("🏠 منوی اصلی", "menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def product_detail_kb(pid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn("➕ افزودن به سبد", f"add:{pid}")],
        [_btn("🛒 سبد خرید", "cart"), _btn("🔙 محصولات", "products")],
    ])


def cart_kb(cart) -> InlineKeyboardMarkup:
    rows = []
    for e in cart:
        pid = e["product_id"]
        rows.append([
            _btn("➖", f"dec:{pid}"),
            _btn("➕", f"inc:{pid}"),
            _btn("🗑", f"del:{pid}"),
        ])
    rows.append([_btn("✅ ثبت سفارش", "checkout"), _btn("🧹 خالی کردن", "clearcart")])
    rows.append([_btn("🏠 منوی اصلی", "menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def empty_cart_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn("🛍 مشاهده محصولات", "products")],
        [_btn("🏠 منوی اصلی", "menu")],
    ])


def my_orders_kb(orders) -> InlineKeyboardMarkup:
    rows = [[_btn(f"🧾 سفارش #{o['id']}", f"orderinfo:{o['id']}")] for o in orders]
    rows.append([_btn("🏠 منوی اصلی", "menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_myorders() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn("↩️ بازگشت به سفارش‌ها", "myorders")],
        [_btn("🏠 منوی اصلی", "menu")],
    ])


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[_btn("❌ انصراف", "cancel")]])


# ---------- پنل مدیریت ----------
def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn("📋 سفارش‌ها", "admin_orders"), _btn("➕ افزودن کالا", "admin_addproduct")],
        [_btn("🗂 مدیریت کالاها", "admin_products"), _btn("📊 آمار", "admin_stats")],
        [_btn("📢 پیام همگانی", "admin_broadcast"), _btn("🏠 منوی کاربر", "menu")],
    ])


def back_to_admin() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[_btn("↩️ بازگشت به پنل", "admin")]])


def admin_orders_kb(orders) -> InlineKeyboardMarkup:
    rows = [[_btn(f"🔎 سفارش #{o['id']}", f"order:{o['id']}")] for o in orders]
    rows.append([_btn("↩️ بازگشت به پنل", "admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def order_admin_kb(oid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn("✅ تأیید", f"confirm:{oid}"), _btn("❌ رد", f"reject:{oid}")],
        [_btn("↩️ بازگشت به سفارش‌ها", "admin_orders")],
    ])


def admin_products_kb(products) -> InlineKeyboardMarkup:
    rows = []
    for p in products:
        rows.append([
            _btn(f"{'✅' if p['active'] else '⛔️'} {p['name']}", f"toggle:{p['id']}"),
            _btn("🗑", f"delprod:{p['id']}"),
        ])
    rows.append([_btn("➕ افزودن کالا", "admin_addproduct")])
    rows.append([_btn("↩️ بازگشت به پنل", "admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

"""هندلرهای سمت مشتری (کاربر عادی)."""
from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import config
import keyboards as kb
import store
from states import ReceiptFlow
from utils import fmt_price, h, status_label

router = Router()

WELCOME = (
    "سلام {name} 👋\n"
    "به <b>فروشگاه اینترنتی کافئین</b> خوش آمدید. ☕️\n\n"
    "از منوی زیر می‌توانید:\n"
    "• 🛍 محصولات را ببینید\n"
    "• 🛒 به سبد خرید اضافه کنید\n"
    "• 💳 مبلغ را کارت‌به‌کارت واریز و رسید بفرستید\n\n"
    "برای شروع یکی از دکمه‌ها را بزنید:"
)


@router.message(CommandStart())
async def cmd_start(m: Message):
    store.register_user(m.from_user)
    await m.answer(WELCOME.format(name=h(m.from_user.first_name)), reply_markup=kb.main_menu())


@router.message(Command("menu"))
async def cmd_menu(m: Message):
    await m.answer("🏠 منوی اصلی:", reply_markup=kb.main_menu())


@router.message(Command("id"))
async def cmd_id(m: Message):
    await m.answer(
        f"آی‌دی عددی شما: <code>{m.from_user.id}</code>\n"
        "(برای قرار دادن در ADMIN_IDS)"
    )


@router.message(Command("cancel"))
async def cmd_cancel(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("❌ عملیات لغو شد.", reply_markup=kb.main_menu())


@router.callback_query(F.data == "cancel")
async def cb_cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("❌ عملیات لغو شد.", reply_markup=kb.main_menu())
    await cb.answer()


@router.callback_query(F.data == "menu")
async def cb_menu(cb: CallbackQuery):
    await cb.message.edit_text("🏠 منوی اصلی:", reply_markup=kb.main_menu())
    await cb.answer()


# ---------- محصولات ----------
@router.callback_query(F.data == "products")
async def cb_products(cb: CallbackQuery):
    prods = store.get_products(active_only=True)
    if not prods:
        await cb.message.edit_text("فعلاً محصولی موجود نیست. 😕", reply_markup=kb.back_to_menu())
    else:
        lines = ["🛍 <b>محصولات فروشگاه:</b>\n"]
        for p in prods:
            lines.append(f"{p['emoji']} <b>{h(p['name'])}</b>\n   💰 {fmt_price(p['price'])}\n")
        await cb.message.edit_text("\n".join(lines), reply_markup=kb.products_kb(prods))
    await cb.answer()


@router.callback_query(F.data.startswith("p:"))
async def cb_product(cb: CallbackQuery):
    pid = int(cb.data.split(":", 1)[1])
    p = store.get_product(pid)
    if not p or not p.get("active"):
        await cb.answer("محصول یافت نشد.", show_alert=True)
        return
    text = (
        f"{p['emoji']} <b>{h(p['name'])}</b>\n\n"
        f"{h(p['description'])}\n\n"
        f"💰 قیمت: {fmt_price(p['price'])}\n"
        f"📦 موجودی: {p['stock']} عدد"
    )
    await cb.message.edit_text(text, reply_markup=kb.product_detail_kb(pid))
    await cb.answer()


@router.callback_query(F.data.startswith("add:"))
async def cb_add(cb: CallbackQuery):
    pid = int(cb.data.split(":", 1)[1])
    p = store.get_product(pid)
    if not p or not p.get("active"):
        await cb.answer("محصول یافت نشد.", show_alert=True)
        return
    store.add_to_cart(cb.from_user.id, pid)
    await cb.answer(f"{p['name']} به سبد اضافه شد ✅", show_alert=True)


# ---------- سبد خرید ----------
async def show_cart(cb: CallbackQuery):
    items, total = store.expand_cart(cb.from_user.id)
    if not items:
        await cb.message.edit_text("🛒 سبد خرید شما خالی است.", reply_markup=kb.empty_cart_kb())
    else:
        lines = ["🛒 <b>سبد خرید شما:</b>\n"]
        for it in items:
            p = it["product"]
            lines.append(
                f"{p['emoji']} {h(p['name'])}\n"
                f"   {it['qty']} × {fmt_price(p['price'])} = {fmt_price(p['price'] * it['qty'])}\n"
            )
        lines.append(f"\n💰 <b>جمع کل: {fmt_price(total)}</b>")
        await cb.message.edit_text("\n".join(lines), reply_markup=kb.cart_kb(store.get_cart(cb.from_user.id)))
    await cb.answer()


@router.callback_query(F.data == "cart")
async def cb_cart(cb: CallbackQuery):
    await show_cart(cb)


@router.callback_query(F.data.startswith("inc:"))
async def cb_inc(cb: CallbackQuery):
    pid = int(cb.data.split(":", 1)[1])
    store.change_qty(cb.from_user.id, pid, +1)
    await show_cart(cb)


@router.callback_query(F.data.startswith("dec:"))
async def cb_dec(cb: CallbackQuery):
    pid = int(cb.data.split(":", 1)[1])
    store.change_qty(cb.from_user.id, pid, -1)
    await show_cart(cb)


@router.callback_query(F.data.startswith("del:"))
async def cb_del(cb: CallbackQuery):
    pid = int(cb.data.split(":", 1)[1])
    store.remove_from_cart(cb.from_user.id, pid)
    await show_cart(cb)


@router.callback_query(F.data == "clearcart")
async def cb_clearcart(cb: CallbackQuery):
    store.clear_cart(cb.from_user.id)
    await show_cart(cb)


# ---------- ثبت سفارش / رسید ----------
@router.callback_query(F.data == "checkout")
async def cb_checkout(cb: CallbackQuery, state: FSMContext):
    items, total = store.expand_cart(cb.from_user.id)
    if not items:
        await cb.answer("سبد خرید شما خالی است.", show_alert=True)
        return

    snapshot = [
        {"name": it["product"]["name"], "price": it["product"]["price"], "qty": it["qty"]}
        for it in items
    ]
    await state.update_data(order={"items": snapshot, "total": total})
    await state.set_state(ReceiptFlow.awaiting_receipt)

    lines = ["🧾 <b>پیش‌فاکتور</b>\n"]
    for it in snapshot:
        lines.append(f"{h(it['name'])} × {it['qty']} = {fmt_price(it['price'] * it['qty'])}")
    lines.append(f"\n💰 <b>مبلغ قابل پرداخت: {fmt_price(total)}</b>")
    lines.append(
        "\n💳 <b>شماره کارت:</b>\n"
        f"<code>{h(config.CARD_NUMBER)}</code>\n"
        f"👤 به نام: {h(config.CARD_HOLDER)}\n\n"
        "پس از واریز، <b>رسید پرداخت</b> را به صورت عکس یا فایل ارسال کنید."
    )
    await cb.message.edit_text("\n".join(lines), reply_markup=kb.cancel_kb())
    await cb.answer()


@router.message(ReceiptFlow.awaiting_receipt, F.photo | F.document)
async def handle_receipt(m: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    snapshot = data.get("order")
    if not snapshot:
        await m.answer("خطا: سفارشی در جریان نیست.")
        await state.clear()
        return

    if m.photo:
        file_id = m.photo[-1].file_id
        ext = "jpg"
    else:
        file_id = m.document.file_id
        name = m.document.file_name or "receipt"
        ext = name.rsplit(".", 1)[-1] if "." in name else "bin"

    order = store.create_order(
        user_id=m.from_user.id,
        username=m.from_user.username,
        full_name=m.from_user.full_name,
        items=snapshot["items"],
        total=snapshot["total"],
        card_number=config.CARD_NUMBER,
        receipt_file_id=file_id,
    )

    # دانلود رسید برای بایگانی محلی (اختیاری)
    try:
        await bot.download(file_id, destination=f"data/receipts/order_{order['id']}.{ext}")
    except Exception:
        pass

    store.clear_cart(m.from_user.id)
    await state.clear()
    await m.answer(
        f"✅ رسید دریافت شد!\n\n"
        f"سفارش شما با شماره <b>#{order['id']}</b> ثبت شد و در انتظار تأیید مدیریت است. 🙏\n\n"
        f"از خرید شما سپاسگزاریم ☕️",
        reply_markup=kb.main_menu(),
    )


@router.message(ReceiptFlow.awaiting_receipt, F.text)
async def receipt_needs_file(m: Message):
    await m.answer(
        "لطفاً رسید واریز را به صورت <b>عکس یا فایل</b> ارسال کنید، یا /cancel بزنید."
    )


# ---------- سفارش‌های من ----------
@router.callback_query(F.data == "myorders")
async def cb_myorders(cb: CallbackQuery):
    orders = store.get_user_orders(cb.from_user.id)
    if not orders:
        await cb.message.edit_text("📦 شما هنوز سفارشی ندارید.", reply_markup=kb.back_to_menu())
    else:
        lines = ["📦 <b>سفارش‌های شما:</b>\n"]
        for o in orders:
            lines.append(f"#{o['id']} — {status_label(o['status'])} — {fmt_price(o['total'])}")
        await cb.message.edit_text("\n".join(lines), reply_markup=kb.my_orders_kb(orders))
    await cb.answer()


@router.callback_query(F.data.startswith("orderinfo:"))
async def cb_order_info(cb: CallbackQuery):
    oid = int(cb.data.split(":", 1)[1])
    order = store.get_order(oid)
    if not order or int(order["user_id"]) != cb.from_user.id:
        await cb.answer("سفارش یافت نشد.", show_alert=True)
        return
    lines = [f"🧾 <b>سفارش #{order['id']}</b>\n"]
    for it in order["items"]:
        lines.append(f"{h(it['name'])} × {it['qty']} = {fmt_price(it['price'] * it['qty'])}")
    lines.append(f"\n💰 مبلغ: {fmt_price(order['total'])}")
    lines.append(f"📅 تاریخ: {order['created_at']}")
    lines.append(f"وضعیت: {status_label(order['status'])}")
    await cb.message.edit_text("\n".join(lines), reply_markup=kb.back_to_myorders())
    await cb.answer()


# ---------- کارت / پشتیبانی / راهنما ----------
@router.callback_query(F.data == "card")
async def cb_card(cb: CallbackQuery):
    text = (
        "💳 <b>اطلاعات کارت واریز:</b>\n\n"
        f"شماره کارت: <code>{h(config.CARD_NUMBER)}</code>\n"
        f"به نام: {h(config.CARD_HOLDER)}\n\n"
        "پس از واریز، هنگام ثبت سفارش، رسید را ارسال کنید."
    )
    await cb.message.edit_text(text, reply_markup=kb.back_to_menu())
    await cb.answer()


@router.callback_query(F.data == "support")
async def cb_support(cb: CallbackQuery):
    text = (
        "📞 <b>پشتیبانی</b>\n\n"
        f"پشتیبان فروشگاه: {h(config.SUPPORT)}\n"
        "ساعت پاسخگویی: همه‌روزه ۹ تا ۱۸\n\n"
        "سفارش شما پس از بررسی رسید، تأیید و ارسال می‌شود."
    )
    await cb.message.edit_text(text, reply_markup=kb.back_to_menu())
    await cb.answer()


@router.callback_query(F.data == "help")
async def cb_help(cb: CallbackQuery):
    text = (
        "ℹ️ <b>راهنمای خرید</b>\n\n"
        "۱. از «🛍 محصولات» کالا را انتخاب کنید.\n"
        "۲. به سبد خرید اضافه کنید.\n"
        "۳. «✅ ثبت سفارش» را بزنید.\n"
        "۴. شماره کارت نمایش داده می‌شود؛ مبلغ را واریز کنید.\n"
        "۵. رسید واریز را به صورت عکس/فایل بفرستید.\n"
        "۶. سفارش شما پس از تأیید مدیریت ارسال می‌شود. 🚚\n\n"
        "برای مشاهده وضعیت: «📦 سفارش‌های من»"
    )
    await cb.message.edit_text(text, reply_markup=kb.back_to_menu())
    await cb.answer()

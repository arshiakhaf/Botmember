"""هندلرهای پنل مدیریت (ادمین)."""
from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import config
import keyboards as kb
import store
from states import AddProductFlow, BroadcastFlow
from utils import fmt_price, h, parse_int, status_label

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


# ---------- ورود به پنل ----------
@router.message(Command("admin"))
async def cmd_admin(m: Message):
    if not is_admin(m.from_user.id):
        await m.answer(
            f"⛔️ شما به پنل مدیریت دسترسی ندارید.\n\n"
            f"آی‌دی شما: <code>{m.from_user.id}</code>\n"
            "این عدد را در فایل .env کنار ADMIN_IDS قرار دهید."
        )
        return
    await m.answer("🛠 <b>پنل مدیریت</b>", reply_markup=kb.admin_menu())


@router.callback_query(F.data == "admin")
async def cb_admin(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("دسترسی ندارید.", show_alert=True)
        return
    await cb.message.edit_text("🛠 <b>پنل مدیریت</b>", reply_markup=kb.admin_menu())
    await cb.answer()


# ---------- سفارش‌ها ----------
@router.callback_query(F.data == "admin_orders")
async def cb_admin_orders(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("دسترسی ندارید.", show_alert=True)
        return
    orders = store.get_orders()
    if not orders:
        await cb.message.edit_text("📋 هنوز سفارشی ثبت نشده.", reply_markup=kb.back_to_admin())
    else:
        lines = ["📋 <b>سفارش‌ها:</b>\n"]
        for o in orders:
            who = o["full_name"] or o["username"] or "؟"
            lines.append(f"#{o['id']} — {status_label(o['status'])} — {fmt_price(o['total'])} — {h(who)}")
        await cb.message.edit_text("\n".join(lines), reply_markup=kb.admin_orders_kb(orders))
    await cb.answer()


@router.callback_query(F.data.startswith("order:"))
async def cb_order_detail(cb: CallbackQuery, bot: Bot):
    if not is_admin(cb.from_user.id):
        await cb.answer("دسترسی ندارید.", show_alert=True)
        return
    oid = int(cb.data.split(":", 1)[1])
    order = store.get_order(oid)
    if not order:
        await cb.answer("سفارش یافت نشد.", show_alert=True)
        return

    # نمایش رسید پرداخت برای ادمین
    if order.get("receipt_file_id"):
        try:
            await bot.send_photo(cb.from_user.id, order["receipt_file_id"],
                                 caption=f"🧾 رسید سفارش #{order['id']}")
        except Exception:
            try:
                await bot.send_document(cb.from_user.id, order["receipt_file_id"],
                                        caption=f"🧾 رسید سفارش #{order['id']}")
            except Exception:
                pass

    lines = [f"🧾 <b>سفارش #{order['id']}</b>\n"]
    lines.append(
        f"👤 مشتری: {h(order['full_name'] or '—')} "
        f"(@{h(order['username'] or '—')}) [<code>{order['user_id']}</code>]"
    )
    lines.append(f"📅 تاریخ: {order['created_at']}")
    lines.append("\n🛒 اقلام:")
    for it in order["items"]:
        lines.append(f"• {h(it['name'])} × {it['qty']} = {fmt_price(it['price'] * it['qty'])}")
    lines.append(f"\n💰 مبلغ کل: {fmt_price(order['total'])}")
    lines.append(f"💳 کارت واریزی: <code>{h(order['card_number'])}</code>")
    lines.append(f"وضعیت: {status_label(order['status'])}")

    await cb.message.answer("\n".join(lines), reply_markup=kb.order_admin_kb(oid))
    await cb.answer()


@router.callback_query(F.data.startswith("confirm:"))
async def cb_confirm(cb: CallbackQuery, bot: Bot):
    if not is_admin(cb.from_user.id):
        await cb.answer("دسترسی ندارید.", show_alert=True)
        return
    oid = int(cb.data.split(":", 1)[1])
    order = store.update_order_status(oid, "confirmed")
    if not order:
        await cb.answer("سفارش یافت نشد.", show_alert=True)
        return
    await cb.answer("سفارش تأیید شد ✅")
    await cb.message.edit_reply_markup(reply_markup=kb.order_admin_kb(oid))
    try:
        await bot.send_message(
            order["user_id"],
            f"✅ سفارش <b>#{oid}</b> شما تأیید شد و به‌زودی ارسال می‌شود. 🚚",
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("reject:"))
async def cb_reject(cb: CallbackQuery, bot: Bot):
    if not is_admin(cb.from_user.id):
        await cb.answer("دسترسی ندارید.", show_alert=True)
        return
    oid = int(cb.data.split(":", 1)[1])
    order = store.update_order_status(oid, "rejected")
    if not order:
        await cb.answer("سفارش یافت نشد.", show_alert=True)
        return
    await cb.answer("سفارش رد شد ❌")
    await cb.message.edit_reply_markup(reply_markup=kb.order_admin_kb(oid))
    try:
        await bot.send_message(
            order["user_id"],
            f"❌ سفارش <b>#{oid}</b> شما رد شد. برای پیگیری با پشتیبانی تماس بگیرید.",
        )
    except Exception:
        pass


# ---------- مدیریت کالاها ----------
@router.callback_query(F.data == "admin_products")
async def cb_admin_products(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("دسترسی ندارید.", show_alert=True)
        return
    prods = store.get_products(active_only=False)
    if not prods:
        await cb.message.edit_text(
            "🗂 کالایی وجود ندارد. از «➕ افزودن کالا» اضافه کنید.",
            reply_markup=kb.back_to_admin(),
        )
    else:
        await cb.message.edit_text(
            "🗂 <b>مدیریت کالاها</b>\n(برای فعال/غیرفعال کردن کلیک کنید)",
            reply_markup=kb.admin_products_kb(prods),
        )
    await cb.answer()


@router.callback_query(F.data.startswith("toggle:"))
async def cb_toggle(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("دسترسی ندارید.", show_alert=True)
        return
    pid = int(cb.data.split(":", 1)[1])
    store.toggle_product(pid)
    await cb_admin_products(cb)


@router.callback_query(F.data.startswith("delprod:"))
async def cb_delprod(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("دسترسی ندارید.", show_alert=True)
        return
    pid = int(cb.data.split(":", 1)[1])
    store.delete_product(pid)
    await cb.answer("کالا حذف شد 🗑")
    await cb_admin_products(cb)


# ---------- افزودن کالا ----------
@router.callback_query(F.data == "admin_addproduct")
async def cb_addproduct(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer("دسترسی ندارید.", show_alert=True)
        return
    await state.set_state(AddProductFlow.name)
    await cb.message.answer("➕ نام محصول را وارد کنید (برای انصراف /cancel):")
    await cb.answer()


@router.message(AddProductFlow.name)
async def step_name(m: Message, state: FSMContext):
    name = m.text.strip()
    if len(name) < 2:
        await m.answer("نام خیلی کوتاه است. دوباره وارد کنید:")
        return
    await state.update_data(name=name)
    await state.set_state(AddProductFlow.price)
    await m.answer("💰 قیمت را به تومان وارد کنید (فقط عدد):")


@router.message(AddProductFlow.price)
async def step_price(m: Message, state: FSMContext):
    price = parse_int(m.text)
    if price is None or price <= 0:
        await m.answer("لطفاً یک عدد معتبر وارد کنید:")
        return
    await state.update_data(price=price)
    await state.set_state(AddProductFlow.description)
    await m.answer("📝 توضیحات محصول را وارد کنید (یا «-» بزنید):")


@router.message(AddProductFlow.description)
async def step_desc(m: Message, state: FSMContext):
    desc = m.text.strip()
    if desc == "-":
        desc = ""
    await state.update_data(description=desc)
    await state.set_state(AddProductFlow.stock)
    await m.answer("📦 موجودی را وارد کنید (فقط عدد):")


@router.message(AddProductFlow.stock)
async def step_stock(m: Message, state: FSMContext):
    stock = parse_int(m.text)
    if stock is None or stock < 0:
        await m.answer("لطفاً یک عدد معتبر وارد کنید:")
        return
    data = await state.get_data()
    product = store.add_product(
        name=data["name"],
        price=data["price"],
        description=data.get("description", ""),
        stock=stock,
        emoji="🛍️",
    )
    await state.clear()
    await m.answer(
        f"✅ کالا اضافه شد:\n\n"
        f"{product['emoji']} <b>{h(product['name'])}</b>\n"
        f"💰 {fmt_price(product['price'])}\n"
        f"📦 موجودی: {product['stock']}",
        reply_markup=kb.back_to_admin(),
    )


# ---------- آمار ----------
@router.callback_query(F.data == "admin_stats")
async def cb_stats(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("دسترسی ندارید.", show_alert=True)
        return
    orders = store.get_orders()
    confirmed = [o for o in orders if o["status"] == "confirmed"]
    revenue = sum(o["total"] for o in confirmed)
    text = (
        "📊 <b>آمار فروشگاه</b>\n\n"
        f"🛍 تعداد کالاها: {len(store.get_products(active_only=False))}\n"
        f"👥 تعداد کاربران: {len(store.get_all_users())}\n"
        f"📦 کل سفارش‌ها: {len(orders)}\n"
        f"⏳ در انتظار: {sum(1 for o in orders if o['status'] == 'pending')}\n"
        f"✅ تأیید شده: {len(confirmed)}\n"
        f"❌ رد شده: {sum(1 for o in orders if o['status'] == 'rejected')}\n"
        f"💰 فروش تأیید شده: {fmt_price(revenue)}"
    )
    await cb.message.edit_text(text, reply_markup=kb.back_to_admin())
    await cb.answer()


# ---------- پیام همگانی ----------
@router.callback_query(F.data == "admin_broadcast")
async def cb_broadcast(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer("دسترسی ندارید.", show_alert=True)
        return
    await state.set_state(BroadcastFlow.text)
    await cb.message.answer("📢 متن پیام همگانی را بفرستید (برای انصراف /cancel):")
    await cb.answer()


@router.message(BroadcastFlow.text)
async def step_broadcast(m: Message, state: FSMContext, bot: Bot):
    users = store.get_all_users()
    ok = fail = 0
    for uid in list(users.keys()):
        try:
            await bot.send_message(int(uid), m.text)
            ok += 1
        except Exception:
            fail += 1
    await state.clear()
    await m.answer(f"📢 ارسال پیام همگانی انجام شد:\n✅ موفق: {ok}\n❌ ناموفق: {fail}")

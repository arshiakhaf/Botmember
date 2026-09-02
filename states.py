"""حالت‌های FSM ربات."""
from aiogram.fsm.state import State, StatesGroup


class ReceiptFlow(StatesGroup):
    """در انتظار دریافت رسید پرداخت از مشتری."""
    awaiting_receipt = State()


class AddProductFlow(StatesGroup):
    """فرایند افزودن کالا توسط ادمین."""
    name = State()
    price = State()
    description = State()
    stock = State()


class BroadcastFlow(StatesGroup):
    """فرایند ارسال پیام همگانی توسط ادمین."""
    text = State()

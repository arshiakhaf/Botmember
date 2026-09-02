"""لایه داده فروشگاه — ذخیره در فایل‌های JSON (بدون نیاز به دیتابیس)."""
import json
import os
import time

DATA_DIR = "data"
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
CARTS_FILE = os.path.join(DATA_DIR, "carts.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

SEED_PRODUCTS = [
    {
        "id": 1, "name": "قهوه اسپشیال ۲۵۰ گرمی", "emoji": "☕️", "price": 450000,
        "description": "دانه قهوه تازه‌رست مناسب اسپرسو و موکاپات.", "stock": 25, "active": True,
    },
    {
        "id": 2, "name": "قهوه ترک ۱۰۰ گرمی", "emoji": "☕️", "price": 180000,
        "description": "قهوه ترک با آسیاب ریز و عطر غلیظ.", "stock": 40, "active": True,
    },
    {
        "id": 3, "name": "چای ممتاز ایرانی ۵۰۰ گرمی", "emoji": "🍃", "price": 220000,
        "description": "چای سیاه درجه یک لاهیجان.", "stock": 30, "active": True,
    },
    {
        "id": 4, "name": "شکلات تلخ ۷۰٪", "emoji": "🍫", "price": 95000,
        "description": "شکلات تلخ ۷۰ درصد کاکائو، ۱۰۰ گرمی.", "stock": 50, "active": True,
    },
    {
        "id": 5, "name": "ماگ سرامیکی طرح خاص", "emoji": "🥛", "price": 320000,
        "description": "ماگ سرامیکی دست‌ساز با طرح اختصاصی.", "stock": 15, "active": True,
    },
    {
        "id": 6, "name": "فرنچ پرس ۶۰۰ میلی", "emoji": "🫖", "price": 1250000,
        "description": "فرنچ پرس شیشه‌ای مقاوم برای دم‌آوری قهوه.", "stock": 8, "active": True,
    },
]


def _load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _save(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def ensure_seed_products():
    if not os.path.exists(PRODUCTS_FILE):
        _save(PRODUCTS_FILE, SEED_PRODUCTS)


# ---------- محصولات ----------
def get_products(active_only=True):
    prods = _load(PRODUCTS_FILE, [])
    if active_only:
        prods = [p for p in prods if p.get("active", True)]
    return sorted(prods, key=lambda p: p["id"])


def get_product(pid):
    for p in _load(PRODUCTS_FILE, []):
        if p["id"] == int(pid):
            return p
    return None


def _next_product_id(prods):
    return max([p["id"] for p in prods] or [0]) + 1


def add_product(name, price, description="", stock=0, emoji="🛍️"):
    prods = _load(PRODUCTS_FILE, [])
    product = {
        "id": _next_product_id(prods),
        "name": name,
        "emoji": emoji,
        "price": int(price),
        "description": description,
        "stock": int(stock),
        "active": True,
    }
    prods.append(product)
    _save(PRODUCTS_FILE, prods)
    return product


def toggle_product(pid):
    prods = _load(PRODUCTS_FILE, [])
    for p in prods:
        if p["id"] == int(pid):
            p["active"] = not p.get("active", True)
    _save(PRODUCTS_FILE, prods)


def delete_product(pid):
    prods = _load(PRODUCTS_FILE, [])
    prods = [p for p in prods if p["id"] != int(pid)]
    _save(PRODUCTS_FILE, prods)


# ---------- سبد خرید ----------
def get_cart(user_id):
    carts = _load(CARTS_FILE, {})
    return carts.get(str(user_id), [])


def save_cart(user_id, cart):
    carts = _load(CARTS_FILE, {})
    carts[str(user_id)] = cart
    _save(CARTS_FILE, carts)


def add_to_cart(user_id, product_id, qty=1):
    cart = get_cart(user_id)
    for e in cart:
        if e["product_id"] == int(product_id):
            e["qty"] += qty
            save_cart(user_id, cart)
            return
    cart.append({"product_id": int(product_id), "qty": qty})
    save_cart(user_id, cart)


def change_qty(user_id, product_id, delta):
    cart = get_cart(user_id)
    for e in cart:
        if e["product_id"] == int(product_id):
            e["qty"] += delta
            if e["qty"] <= 0:
                cart.remove(e)
            save_cart(user_id, cart)
            return


def remove_from_cart(user_id, product_id):
    cart = [e for e in get_cart(user_id) if e["product_id"] != int(product_id)]
    save_cart(user_id, cart)


def clear_cart(user_id):
    save_cart(user_id, [])


def expand_cart(user_id):
    """سبد را با اطلاعات کامل محصول برمی‌گرداند: (items, total)."""
    items, total = [], 0
    for e in get_cart(user_id):
        p = get_product(e["product_id"])
        if not p:
            continue
        qty = max(1, int(e["qty"]))
        items.append({"product": p, "qty": qty})
        total += p["price"] * qty
    return items, total


# ---------- سفارش‌ها ----------
def _next_order_id(orders):
    return max([o["id"] for o in orders] or [0]) + 1


def create_order(user_id, username, full_name, items, total, card_number,
                 receipt_file_id, note=""):
    orders = _load(ORDERS_FILE, [])
    order = {
        "id": _next_order_id(orders),
        "user_id": int(user_id),
        "username": username or "",
        "full_name": full_name or "",
        "items": items,
        "total": int(total),
        "card_number": card_number,
        "receipt_file_id": receipt_file_id,
        "status": "pending",
        "note": note,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    orders.append(order)
    _save(ORDERS_FILE, orders)
    return order


def get_orders():
    orders = _load(ORDERS_FILE, [])
    return sorted(orders, key=lambda o: o["id"], reverse=True)


def get_order(oid):
    for o in _load(ORDERS_FILE, []):
        if o["id"] == int(oid):
            return o
    return None


def get_user_orders(user_id):
    orders = [o for o in _load(ORDERS_FILE, []) if int(o["user_id"]) == int(user_id)]
    return sorted(orders, key=lambda o: o["id"], reverse=True)


def update_order_status(oid, status):
    orders = _load(ORDERS_FILE, [])
    for o in orders:
        if o["id"] == int(oid):
            o["status"] = status
            _save(ORDERS_FILE, orders)
            return o
    return None


# ---------- کاربران ----------
def register_user(user):
    users = _load(USERS_FILE, {})
    key = str(user.id)
    if key not in users:
        users[key] = {
            "id": user.id,
            "username": user.username or "",
            "full_name": user.full_name or "",
            "first_seen": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        _save(USERS_FILE, users)
    return users[key]


def get_all_users():
    return _load(USERS_FILE, {})

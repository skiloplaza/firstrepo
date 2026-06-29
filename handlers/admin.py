from aiogram import Router, F
from aiogram.filters import Command, BaseFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from config import ADMIN_IDS
from keyboards import (
    admin_panel_kb, admin_back_kb, admin_users_kb, admin_user_detail_kb,
    admin_products_kb, admin_product_detail_kb, admin_product_edit_kb,
    admin_orders_kb, admin_orders_filter_kb, admin_order_detail_kb,
    admin_stickers_kb, admin_settings_kb, broadcast_confirm_kb, main_menu_kb,
)
from utils import send_sticker, send_with_effect, fmt_price, load_stickers, save_sticker
from states import AdminProduct, AdminBroadcast, AdminUserMsg

router = Router()


class IsAdmin(BaseFilter):
    async def __call__(self, event) -> bool:
        uid = getattr(getattr(event, "from_user", None), "id", None)
        return uid in ADMIN_IDS


router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


# ──────────────── /panel ────────────────

@router.message(Command("panel"))
async def cmd_panel(message: Message, state: FSMContext):
    await state.clear()
    await send_sticker(message.bot, message.chat.id, "admin")
    await send_with_effect(
        message.bot, message.chat.id,
        "⚙️ <b>Admin Panel</b>\n\nXush kelibsiz, Admin!",
        effect_key="thumbsup",
        reply_markup=admin_panel_kb(),
    )


@router.callback_query(F.data == "adm_panel")
async def cb_panel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.edit_text(
            "⚙️ <b>Admin Panel</b>",
            reply_markup=admin_panel_kb(),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            "⚙️ <b>Admin Panel</b>",
            reply_markup=admin_panel_kb(),
            parse_mode="HTML",
        )
    await callback.answer()


# ──────────────── statistics ────────────────

@router.callback_query(F.data == "adm_stats")
async def cb_stats(callback: CallbackQuery):
    stats = await db.get_stats()
    text = (
        f"📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{stats['total_users']}</b> ta\n"
        f"  ↳ Bugun: <b>+{stats['today_users']}</b> ta\n\n"
        f"📋 Buyurtmalar: <b>{stats['total_orders']}</b> ta\n"
        f"  ↳ Bugun: <b>{stats['today_orders']}</b> ta\n"
        f"  ↳ Kutmoqda: <b>{stats['pending_orders']}</b> ta\n\n"
        f"💰 Daromad: <b>{fmt_price(stats['revenue'])} so'm</b>\n\n"
        f"📦 Mahsulotlar: <b>{stats['products']}</b> ta"
    )
    try:
        await callback.message.edit_text(text, reply_markup=admin_back_kb(), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=admin_back_kb(), parse_mode="HTML")
    await callback.answer()


# ──────────────── users ────────────────

@router.callback_query(F.data.startswith("adm_users:"))
async def cb_users(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    users, total = await db.get_users_page(page)
    try:
        await callback.message.edit_text(
            f"👥 <b>Foydalanuvchilar</b> (jami: {total})",
            reply_markup=admin_users_kb(users, page, total),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            f"👥 <b>Foydalanuvchilar</b> (jami: {total})",
            reply_markup=admin_users_kb(users, page, total),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_user:"))
async def cb_user_detail(callback: CallbackQuery):
    tg_id = int(callback.data.split(":")[1])
    user = await db.get_user(tg_id)
    if not user:
        await callback.answer("Foydalanuvchi topilmadi", show_alert=True)
        return

    orders = await db.get_user_orders(tg_id)
    ban_str = "Ha" if user['is_banned'] else "Yo'q"
    text = (
        f"👤 <b>Foydalanuvchi ma'lumotlari</b>\n\n"
        f"🆔 ID: <code>{tg_id}</code>\n"
        f"📝 Ism: {user['full_name'] or '—'}\n"
        f"👤 Username: @{user['username'] or '—'}\n"
        f"📱 Telefon: {user['phone'] or '—'}\n"
        f"🚫 Bloklangan: {ban_str}\n"
        f"📅 Ro'yxat: {str(user['created_at'])[:10]}\n\n"
        f"📋 Buyurtmalar soni: {len(orders)}"
    )
    try:
        await callback.message.edit_text(
            text,
            reply_markup=admin_user_detail_kb(tg_id, user["is_banned"]),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            text,
            reply_markup=admin_user_detail_kb(tg_id, user["is_banned"]),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_ban:"))
async def cb_ban(callback: CallbackQuery):
    tg_id = int(callback.data.split(":")[1])
    await db.ban_user(tg_id, 1)
    await callback.answer("🚫 Foydalanuvchi bloklandi", show_alert=True)
    user = await db.get_user(tg_id)
    try:
        await callback.message.edit_reply_markup(
            reply_markup=admin_user_detail_kb(tg_id, True)
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_unban:"))
async def cb_unban(callback: CallbackQuery):
    tg_id = int(callback.data.split(":")[1])
    await db.ban_user(tg_id, 0)
    await callback.answer("✅ Foydalanuvchi blokdan chiqarildi", show_alert=True)
    try:
        await callback.message.edit_reply_markup(
            reply_markup=admin_user_detail_kb(tg_id, False)
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_msg:"))
async def cb_admin_msg_start(callback: CallbackQuery, state: FSMContext):
    tg_id = int(callback.data.split(":")[1])
    await state.set_state(AdminUserMsg.message)
    await state.update_data(target_id=tg_id, sticker_mode=False)
    await callback.message.answer(
        f"✉️ Foydalanuvchiga (<code>{tg_id}</code>) xabar yozing:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminUserMsg.message, F.text)
async def admin_send_user_msg(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("sticker_mode"):
        return
    target_id = data.get("target_id")
    if not target_id:
        await state.clear()
        return
    try:
        await message.bot.send_message(target_id, message.text)
        await message.answer("✅ Xabar yuborildi!")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")
    await state.clear()


# ──────────────── products ────────────────

@router.callback_query(F.data.startswith("adm_products:"))
async def cb_admin_products(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    page = int(callback.data.split(":")[1])
    products, total = await db.get_all_products_admin(page)
    try:
        await callback.message.edit_text(
            f"📦 <b>Mahsulotlar</b> (jami: {total})",
            reply_markup=admin_products_kb(products, page, total),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            f"📦 <b>Mahsulotlar</b> (jami: {total})",
            reply_markup=admin_products_kb(products, page, total),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_prod:"))
async def cb_admin_prod_detail(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product(product_id)
    if not product:
        await callback.answer("Topilmadi", show_alert=True)
        return

    desc = product["description"] or "Tavsif yo'q"
    from utils import _row_get
    avail_str = "Ha" if product['is_available'] else "Yo'q"
    rasm_str = "✅ Bor" if product['image_file_id'] else "❌ Yo'q"
    text = (
        f"📦 <b>{product['name']}</b>\n\n"
        f"🏷 Brend: {_row_get(product, 'brand', '—')}\n"
        f"📂 Kategoriya: {_row_get(product, 'cat_name', '—')}\n"
        f"📝 Tavsif: {desc[:200]}\n\n"
        f"💰 Narx: <b>{fmt_price(product['price'])} so'm</b>\n"
        f"🏷 Eski narx: {fmt_price(product['old_price']) if product['old_price'] else '—'} so'm\n"
        f"📦 Miqdor: {product['stock']} ta\n"
        f"✅ Mavjud: {avail_str}\n"
        f"🖼 Rasm: {rasm_str}"
    )

    image = product["image_file_id"]
    kb = admin_product_detail_kb(product_id, product["is_available"])
    if image:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer_photo(photo=image, caption=text, reply_markup=kb, parse_mode="HTML")
    else:
        try:
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("adm_prod_toggle:"))
async def cb_prod_toggle(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product(product_id)
    if not product:
        await callback.answer("Topilmadi", show_alert=True)
        return
    new_val = 0 if product["is_available"] else 1
    await db.update_product_field(product_id, "is_available", new_val)
    status = "yoqildi ✅" if new_val else "o'chirildi ❌"
    await callback.answer(f"Mahsulot {status}", show_alert=True)
    # Refresh
    product = await db.get_product(product_id)
    try:
        await callback.message.edit_reply_markup(
            reply_markup=admin_product_detail_kb(product_id, product["is_available"])
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_prod_del:"))
async def cb_prod_del(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    await db.delete_product(product_id)
    await callback.answer("🗑 Mahsulot o'chirildi", show_alert=True)
    products, total = await db.get_all_products_admin(1)
    try:
        await callback.message.edit_text(
            f"📦 <b>Mahsulotlar</b> (jami: {total})",
            reply_markup=admin_products_kb(products, 1, total),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            f"📦 <b>Mahsulotlar</b> (jami: {total})",
            reply_markup=admin_products_kb(products, 1, total),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("adm_prod_edit:"))
async def cb_prod_edit(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    try:
        await callback.message.edit_reply_markup(
            reply_markup=admin_product_edit_kb(product_id)
        )
    except Exception:
        await callback.message.answer("✏️ Qaysi maydonni o'zgartirmoqchisiz?",
                                      reply_markup=admin_product_edit_kb(product_id))
    await callback.answer()


@router.callback_query(F.data.startswith("adm_edit_field:"))
async def cb_edit_field(callback: CallbackQuery, state: FSMContext):
    _, product_id, field = callback.data.split(":")
    await state.set_state(AdminProduct.edit_value)
    await state.update_data(edit_product_id=int(product_id), edit_field=field)
    field_names = {
        "name": "Nomi", "description": "Tavsif",
        "price": "Narxi (raqam)", "old_price": "Eski narxi (raqam)",
        "stock": "Miqdori (raqam)",
    }
    await callback.message.answer(
        f"✏️ <b>{field_names.get(field, field)}</b> uchun yangi qiymat kiriting:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminProduct.edit_value)
async def admin_edit_value(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data["edit_product_id"]
    field = data["edit_field"]
    value = message.text.strip()

    if field in ("price", "old_price", "stock"):
        val = value.replace(" ", "").replace(",", "")
        if not val.isdigit():
            await message.answer("❌ Raqam kiriting!")
            return
        value = int(val)

    await db.update_product_field(product_id, field, value)
    await state.clear()
    await message.answer(f"✅ Yangilandi!")

    product = await db.get_product(product_id)
    desc = product["description"] or "Tavsif yo'q"
    text = (
        f"📦 <b>{product['name']}</b>\n\n"
        f"💰 Narx: <b>{fmt_price(product['price'])} so'm</b>\n"
        f"📦 Miqdor: {product['stock']} ta\n"
        f"📝 {desc[:100]}"
    )
    await message.answer(
        text,
        reply_markup=admin_product_detail_kb(product_id, product["is_available"]),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("adm_prod_photo:"))
async def cb_prod_photo(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split(":")[1])
    await state.set_state(AdminProduct.edit_value)
    await state.update_data(edit_product_id=product_id, edit_field="image_file_id")
    await callback.message.answer(
        "🖼 Mahsulot rasmini yuboring (fotosuratni to'g'ridan-to'g'ri yuboring):"
    )
    await callback.answer()


@router.message(AdminProduct.edit_value, F.photo)
async def admin_edit_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("edit_field") != "image_file_id":
        return
    product_id = data["edit_product_id"]
    file_id = message.photo[-1].file_id
    await db.update_product_field(product_id, "image_file_id", file_id)
    await state.clear()
    await message.answer("✅ Rasm yangilandi!")


# ──────────────── add product FSM ────────────────

@router.callback_query(F.data == "adm_prod_add")
async def cb_prod_add(callback: CallbackQuery, state: FSMContext):
    cats = await db.get_categories()
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for cat in cats:
        builder.button(text=f"{cat['icon']} {cat['brand']} · {cat['name']}", callback_data=f"addcat:{cat['id']}")
    builder.adjust(2)
    await state.set_state(AdminProduct.category)
    try:
        await callback.message.edit_text(
            "➕ <b>Yangi mahsulot qo'shish</b>\n\nKategoriyani tanlang:",
            reply_markup=builder.as_markup(),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            "➕ <b>Yangi mahsulot qo'shish</b>\n\nKategoriyani tanlang:",
            reply_markup=builder.as_markup(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(AdminProduct.category, F.data.startswith("addcat:"))
async def add_prod_cat(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split(":")[1])
    await state.update_data(category=cat_id)
    await state.set_state(AdminProduct.name)
    await callback.message.answer("📝 Mahsulot nomini kiriting:")
    await callback.answer()


@router.message(AdminProduct.name)
async def add_prod_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminProduct.description)
    await message.answer("📄 Tavsif kiriting (yoki «-» deb yozing):")


@router.message(AdminProduct.description)
async def add_prod_desc(message: Message, state: FSMContext):
    desc = "" if message.text.strip() == "-" else message.text.strip()
    await state.update_data(description=desc)
    await state.set_state(AdminProduct.price)
    await message.answer("💰 Narxini kiriting (so'mda, faqat raqam):")


@router.message(AdminProduct.price)
async def add_prod_price(message: Message, state: FSMContext):
    val = message.text.replace(" ", "").replace(",", "")
    if not val.isdigit():
        await message.answer("❌ Faqat raqam kiriting!")
        return
    await state.update_data(price=int(val))
    await state.set_state(AdminProduct.old_price)
    await message.answer("🏷 Eski narxini kiriting (chegirmadan oldingi, yoki «0»):")


@router.message(AdminProduct.old_price)
async def add_prod_old_price(message: Message, state: FSMContext):
    val = message.text.replace(" ", "").replace(",", "")
    if not val.isdigit():
        await message.answer("❌ Faqat raqam kiriting!")
        return
    await state.update_data(old_price=int(val))
    await state.set_state(AdminProduct.stock)
    await message.answer("📦 Mavjud miqdorini kiriting:")


@router.message(AdminProduct.stock)
async def add_prod_stock(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam kiriting!")
        return
    await state.update_data(stock=int(message.text))
    await state.set_state(AdminProduct.confirm)
    data = await state.get_data()
    cats = await db.get_categories()
    cat = next((c for c in cats if c["id"] == data["category"]), None)
    cat_name = f"{cat['brand']} · {cat['name']}" if cat else "?"

    text = (
        f"📋 <b>Yangi mahsulot tasdiqlash:</b>\n\n"
        f"📂 Kategoriya: {cat_name}\n"
        f"📝 Nomi: {data['name']}\n"
        f"📄 Tavsif: {data.get('description') or '—'}\n"
        f"💰 Narx: {fmt_price(data['price'])} so'm\n"
        f"🏷 Eski narx: {fmt_price(data['old_price'])} so'm\n"
        f"📦 Miqdor: {data['stock']} ta\n\n"
        "Tasdiqlaysizmi?"
    )
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.enums import ButtonStyle
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Saqlash", callback_data="adm_prod_save", style=ButtonStyle.SUCCESS)
    builder.button(text="❌ Bekor", callback_data="adm_products:1", style=ButtonStyle.DANGER)
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(AdminProduct.confirm, F.data == "adm_prod_save")
async def add_prod_save(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await db.add_product(
        cat_id=data["category"],
        name=data["name"],
        description=data.get("description", ""),
        price=data["price"],
        old_price=data.get("old_price", 0),
        stock=data["stock"],
    )
    await state.clear()
    await callback.answer("✅ Mahsulot qo'shildi!", show_alert=True)
    products, total = await db.get_all_products_admin(1)
    try:
        await callback.message.edit_text(
            f"📦 <b>Mahsulotlar</b> (jami: {total})",
            reply_markup=admin_products_kb(products, 1, total),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            f"📦 <b>Mahsulotlar</b> (jami: {total})",
            reply_markup=admin_products_kb(products, 1, total),
            parse_mode="HTML",
        )


# ──────────────── orders ────────────────

@router.callback_query(F.data == "adm_orders_filter")
async def cb_orders_filter(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            "📋 <b>Buyurtmalar filteri</b>",
            reply_markup=admin_orders_filter_kb(),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            "📋 <b>Buyurtmalar filteri</b>",
            reply_markup=admin_orders_filter_kb(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_orders:"))
async def cb_admin_orders(callback: CallbackQuery):
    parts = callback.data.split(":")
    status, page = parts[1], int(parts[2])
    orders, total = await db.get_all_orders(page, status)

    status_label = {
        "all": "Hammasi", "pending": "Kutmoqda",
        "processing": "Jarayonda", "completed": "Yetkazildi", "cancelled": "Bekor",
    }.get(status, status)

    try:
        await callback.message.edit_text(
            f"📋 <b>Buyurtmalar — {status_label}</b> (jami: {total})",
            reply_markup=admin_orders_kb(orders, status, page, total),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            f"📋 <b>Buyurtmalar — {status_label}</b> (jami: {total})",
            reply_markup=admin_orders_kb(orders, status, page, total),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_order:"))
async def cb_admin_order_detail(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    order, items = await db.get_order(order_id)
    if not order:
        await callback.answer("Topilmadi", show_alert=True)
        return

    items_text = "\n".join(
        f"• {i['name']} × {i['quantity']} — {fmt_price(i['price'])} so'm"
        for i in items
    )
    user = await db.get_user(order["user_id"])
    user_info = ""
    if user:
        user_info = (
            f"👤 {user['full_name'] or '—'}"
            + (f" (@{user['username']})" if user["username"] else "")
            + f"\n🆔 <code>{user['telegram_id']}</code>\n"
        )

    STATUS_LABELS = {
        "pending": "⏳ Kutmoqda", "processing": "📦 Jarayonda",
        "completed": "✅ Yetkazildi", "cancelled": "❌ Bekor",
    }

    text = (
        f"📋 <b>Buyurtma #{order_id}</b>\n\n"
        f"{user_info}"
        f"📊 Holat: <b>{STATUS_LABELS.get(order['status'], order['status'])}</b>\n"
        f"📅 Sana: {str(order['created_at'])[:16]}\n\n"
        f"🛍 Mahsulotlar:\n{items_text}\n\n"
        f"💰 Jami: <b>{fmt_price(order['total_price'])} so'm</b>\n\n"
        f"📱 Tel: {order['phone']}\n"
        f"📍 Manzil: {order['address']}\n"
        + (f"📝 Izoh: {order['note']}\n" if order['note'] else "")
    )
    try:
        await callback.message.edit_text(
            text, reply_markup=admin_order_detail_kb(order_id, order["status"]), parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            text, reply_markup=admin_order_detail_kb(order_id, order["status"]), parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_order_status:"))
async def cb_order_status(callback: CallbackQuery):
    _, order_id, new_status = callback.data.split(":")
    order_id = int(order_id)
    await db.update_order_status(order_id, new_status)
    await callback.answer(f"✅ Holat yangilandi: {new_status}", show_alert=True)

    order, _ = await db.get_order(order_id)
    STATUS_LABELS = {
        "pending": "⏳ Kutmoqda", "processing": "📦 Jarayonda",
        "completed": "✅ Buyurtmangiz yetkazildi!", "cancelled": "❌ Buyurtma bekor qilindi.",
    }
    try:
        notify = (
            f"📦 <b>Buyurtma #{order_id} holati yangilandi!</b>\n\n"
            f"Yangi holat: <b>{STATUS_LABELS.get(new_status, new_status)}</b>"
        )
        await callback.bot.send_message(order["user_id"], notify, parse_mode="HTML")
    except Exception:
        pass

    try:
        await callback.message.edit_reply_markup(
            reply_markup=admin_order_detail_kb(order_id, new_status)
        )
    except Exception:
        pass


# ──────────────── broadcast ────────────────

@router.callback_query(F.data == "adm_broadcast")
async def cb_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminBroadcast.content)
    await callback.message.answer(
        "📢 <b>Broadcast</b>\n\nXabar yozing (matn, rasm, video):",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminBroadcast.content)
async def broadcast_content(message: Message, state: FSMContext):
    await state.update_data(
        msg_type="photo" if message.photo else "video" if message.video else "text",
        msg_text=message.caption or message.text or "",
        msg_file_id=(message.photo[-1].file_id if message.photo else
                     message.video.file_id if message.video else None),
    )
    await state.set_state(AdminBroadcast.confirm)
    await message.answer(
        "📢 Yuqoridagi xabar barcha foydalanuvchilarga yuboriladi. Tasdiqlaysizmi?",
        reply_markup=broadcast_confirm_kb(),
    )


@router.callback_query(AdminBroadcast.confirm, F.data == "adm_broadcast_send")
async def broadcast_send(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    users = await db.get_all_users()
    sent, failed = 0, 0
    for user in users:
        try:
            if data["msg_type"] == "photo":
                await callback.bot.send_photo(
                    user["telegram_id"], data["msg_file_id"], caption=data["msg_text"]
                )
            elif data["msg_type"] == "video":
                await callback.bot.send_video(
                    user["telegram_id"], data["msg_file_id"], caption=data["msg_text"]
                )
            else:
                await callback.bot.send_message(user["telegram_id"], data["msg_text"])
            sent += 1
        except Exception:
            failed += 1
    await callback.message.answer(
        f"📢 <b>Broadcast tugadi!</b>\n\n✅ Yuborildi: {sent}\n❌ Xato: {failed}",
        parse_mode="HTML",
        reply_markup=admin_panel_kb(),
    )
    await callback.answer()


@router.callback_query(AdminBroadcast.confirm, F.data == "adm_broadcast_cancel")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("❌ Bekor qilindi.", reply_markup=admin_panel_kb())
    await callback.answer()


# ──────────────── stickers ────────────────

@router.callback_query(F.data == "adm_stickers")
async def cb_stickers(callback: CallbackQuery):
    stickers = load_stickers()
    keys = list(stickers.keys()) or ["welcome", "success", "order", "admin", "error", "hello"]
    try:
        await callback.message.edit_text(
            "🖼 <b>Stikerlarni sozlash</b>\n\nQaysi stikerni o'zgartirmoqchisiz?",
            reply_markup=admin_stickers_kb(keys),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            "🖼 <b>Stikerlarni sozlash</b>\n\nQaysi stikerni o'zgartirmoqchisiz?",
            reply_markup=admin_stickers_kb(keys),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_sticker_set:"))
async def cb_sticker_set(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split(":")[1]
    await state.set_state(AdminUserMsg.message)
    await state.update_data(sticker_key=key, sticker_mode=True)
    await callback.message.answer(
        f"🖼 <b>'{key}'</b> stikeri uchun yangi stiker yuboring:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminUserMsg.message, F.sticker)
async def admin_capture_sticker(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data.get("sticker_mode"):
        await state.clear()
        return
    key = data.get("sticker_key")
    file_id = message.sticker.file_id
    is_premium = getattr(message.sticker, "is_premium", False)
    save_sticker(key, file_id)
    await state.clear()
    prem_str = "Ha" if is_premium else "Yo'q"
    await message.answer(
        f"✅ <b>'{key}'</b> stikeri saqlandi!\n"
        f"🆔 file_id: <code>{file_id}</code>\n"
        f"⭐ Premium: {prem_str}",
        parse_mode="HTML",
    )


@router.message(Command("getsticker"))
async def cmd_getsticker(message: Message):
    await message.answer("Stiker yuboring — men uning file_id sini ko'rsataman.")


@router.message(F.sticker)
async def any_sticker(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("sticker_mode"):
        return
    s = message.sticker
    is_premium = getattr(s, "is_premium", False)
    await message.answer(
        f"🖼 Stiker ma'lumoti:\n"
        f"<code>{s.file_id}</code>\n"
        f"Set: {s.set_name or '—'}\n"
        f"Premium: {'✅' if is_premium else '❌'}\n"
        f"Emoji: {s.emoji or '—'}",
        parse_mode="HTML",
    )


# ──────────────── settings ────────────────

@router.callback_query(F.data == "adm_settings")
async def cb_settings(callback: CallbackQuery):
    discount = await db.get_setting("global_discount", "0")
    try:
        await callback.message.edit_text(
            f"⚙️ <b>Sozlamalar</b>\n\n"
            f"💰 Joriy global chegirma: <b>{discount}%</b>",
            reply_markup=admin_settings_kb(),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            f"⚙️ <b>Sozlamalar</b>\n\n💰 Joriy global chegirma: <b>{discount}%</b>",
            reply_markup=admin_settings_kb(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data == "adm_set_discount")
async def cb_set_discount(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminProduct.edit_value)
    await state.update_data(edit_field="global_discount", edit_product_id=0)
    await callback.message.answer(
        "💰 Global chegirma foizini kiriting (0-99):\n"
        "<i>Misol: 10 (10% chegirma)</i>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminProduct.edit_value)
async def admin_set_global_discount(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("edit_field") == "global_discount":
        val = message.text.strip()
        if not val.isdigit() or int(val) > 99:
            await message.answer("❌ 0 dan 99 gacha raqam kiriting!")
            return
        await db.set_setting("global_discount", val)
        await state.clear()
        await message.answer(
            f"✅ Global chegirma <b>{val}%</b> ga o'rnatildi!",
            parse_mode="HTML",
            reply_markup=admin_settings_kb(),
        )

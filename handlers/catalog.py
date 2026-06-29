from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

import database as db
from keyboards import (
    brands_kb, categories_kb, products_kb, product_detail_kb,
    main_menu_kb, cancel_kb,
)
from utils import make_product_text
from states import Search
from config import ITEMS_PER_PAGE

router = Router()


# ──────────────── catalog entry ────────────────

@router.message(F.text == "🛒 Mahsulotlar")
async def menu_catalog(message: Message, state: FSMContext):
    await state.clear()
    brands = await db.get_brands()
    if brands:
        await message.answer(
            "🏷 <b>Brendni tanlang:</b>",
            reply_markup=brands_kb(brands),
            parse_mode="HTML",
        )
    else:
        cats = await db.get_categories()
        await message.answer(
            "📂 <b>Kategoriyani tanlang:</b>",
            reply_markup=categories_kb(cats),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "all_categories")
async def cb_all_categories(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    brands = await db.get_brands()
    if brands:
        await callback.message.edit_text(
            "🏷 <b>Brendni tanlang:</b>",
            reply_markup=brands_kb(brands),
            parse_mode="HTML",
        )
    else:
        cats = await db.get_categories()
        await callback.message.edit_text(
            "📂 <b>Kategoriyani tanlang:</b>",
            reply_markup=categories_kb(cats),
            parse_mode="HTML",
        )
    await callback.answer()


# ──────────────── brand → categories ────────────────

@router.callback_query(F.data.startswith("brand:"))
async def cb_brand(callback: CallbackQuery):
    brand = callback.data.split(":", 1)[1]
    cats = await db.get_categories_by_brand(brand)
    await callback.message.edit_text(
        f"🏷 <b>{brand}</b> — Kategoriya tanlang:",
        reply_markup=categories_kb(cats, brand=brand),
        parse_mode="HTML",
    )
    await callback.answer()


# ──────────────── category → products ────────────────

@router.callback_query(F.data.startswith("cat:"))
async def cb_category(callback: CallbackQuery):
    _, cat_id, page = callback.data.split(":")
    cat_id, page = int(cat_id), int(page)
    cat = await db.get_category(cat_id)
    products, total = await db.get_products(cat_id, page, ITEMS_PER_PAGE)

    if not products:
        await callback.answer("Bu kategoriyada mahsulot yo'q", show_alert=True)
        return

    cat_name = cat["name"] if cat else "Kategoriya"
    brand = cat["brand"] if cat else ""
    title = f"{brand} · {cat_name}" if brand else cat_name

    await callback.message.edit_text(
        f"📦 <b>{title}</b>\n"
        f"<i>Jami: {total} ta mahsulot</i>",
        reply_markup=products_kb(products, cat_id, page, total, ITEMS_PER_PAGE),
        parse_mode="HTML",
    )
    await callback.answer()


# ──────────────── product detail ────────────────

@router.callback_query(F.data.startswith("prod:"))
async def cb_product(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product(product_id)

    if not product:
        await callback.answer("Mahsulot topilmadi", show_alert=True)
        return

    try:
        text = make_product_text(product)
    except Exception as e:
        await callback.answer(f"Xatolik: {e}", show_alert=True)
        return

    cat_id = product["category_id"]
    kb = product_detail_kb(product_id, cat_id)
    image = product["image_file_id"]

    await callback.answer()

    if image:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer_photo(
            photo=image,
            caption=text,
            reply_markup=kb,
            parse_mode="HTML",
        )
    else:
        try:
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")


# ──────────────── search ────────────────

@router.message(F.text == "🔍 Qidirish")
async def menu_search(message: Message, state: FSMContext):
    await state.set_state(Search.query)
    await message.answer(
        "🔍 <b>Qidirish</b>\n\nMahsulot nomini yozing:",
        reply_markup=cancel_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "search")
async def cb_search(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Search.query)
    await callback.message.answer(
        "🔍 <b>Qidirish</b>\n\nMahsulot nomini yozing:",
        reply_markup=cancel_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Search.query)
async def do_search(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())
        return

    query = message.text.strip()
    if len(query) < 2:
        await message.answer("⚠️ Kamida 2 ta harf kiriting!")
        return

    # Show loading indicator
    loading = await message.answer("🔍 Qidirilmoqda...")

    results = await db.search_products(query, limit=5)
    await state.clear()

    try:
        await loading.delete()
    except Exception:
        pass

    if not results:
        await message.answer(
            f"😔 <b>«{query}»</b> bo'yicha hech narsa topilmadi.\n\n"
            "💡 Maslahat: brend yoki kategoriya nomini yozing\n"
            "<i>Misol: Samsung, iPhone, muzlatgich, noutbuk…</i>",
            reply_markup=main_menu_kb(),
            parse_mode="HTML",
        )
        return

    builder = InlineKeyboardBuilder()
    for i, p in enumerate(results, 1):
        price_str = f"{p['price']:,}".replace(",", " ")
        stock_icon = "✅" if p["stock"] > 0 else "❌"
        builder.button(
            text=f"{i}. {stock_icon} {p['name']} — {price_str} so'm",
            callback_data=f"prod:{p['id']}",
        )
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="🔍 Qayta qidirish", callback_data="search"),
        InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu"),
    )

    await message.answer(
        f"🔍 <b>«{query}»</b> — eng mos {len(results)} ta natija:\n"
        f"<i>Mahsulotga bosib batafsil ko'ring</i>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )

from typing import Callable, Awaitable, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from config import REQUIRED_CHANNELS, ADMIN_IDS


class SubscriptionMiddleware(BaseMiddleware):
    """Block non-subscribed users until they join required channels."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable[Any]],
        event: TelegramObject,
        data: dict,
    ) -> Any:
        if not REQUIRED_CHANNELS:
            return await handler(event, data)

        bot = data["bot"]
        user_id = None

        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        if user_id is None or user_id in ADMIN_IDS:
            return await handler(event, data)

        # Check subscription status for all required channels
        not_subscribed = []
        for ch in REQUIRED_CHANNELS:
            try:
                member = await bot.get_chat_member(ch["username"], user_id)
                if member.status in ("left", "kicked", "banned"):
                    not_subscribed.append(ch)
            except Exception:
                not_subscribed.append(ch)

        if not not_subscribed:
            return await handler(event, data)

        # Show subscription prompt
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        from aiogram.types import InlineKeyboardButton
        from aiogram.enums import ButtonStyle

        builder = InlineKeyboardBuilder()
        for ch in not_subscribed:
            builder.row(InlineKeyboardButton(text=f"📢 {ch['title']}", url=ch["url"]))
        builder.row(InlineKeyboardButton(
            text="✅ Obunani tekshirish",
            callback_data="check_subscription",
            style=ButtonStyle.SUCCESS,
        ))

        text = (
            "⚠️ <b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:</b>\n\n"
            + "\n".join(f"• <a href='{ch['url']}'>{ch['title']}</a>" for ch in not_subscribed)
            + "\n\nObuna bo'lgandan so'ng \"✅ Obunani tekshirish\" tugmasini bosing."
        )

        if isinstance(event, Message):
            await event.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        elif isinstance(event, CallbackQuery):
            await event.answer("Avval kanallarga obuna bo'ling!", show_alert=True)
            await event.message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from server import DEMO_LEADS

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

dp = Dispatcher()


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔥 Свежие лиды", callback_data="leads:all")],
            [
                InlineKeyboardButton(text="Telegram", callback_data="leads:Telegram"),
                InlineKeyboardButton(text="2GIS", callback_data="leads:2GIS"),
                InlineKeyboardButton(text="Avito", callback_data="leads:Avito"),
            ],
            [InlineKeyboardButton(text="ℹ️ О проекте", callback_data="about")],
        ]
    )


def format_leads(source: str = "all") -> str:
    items = DEMO_LEADS if source == "all" else [x for x in DEMO_LEADS if x["source"] == source]
    if not items:
        return "Пока пусто по этому фильтру."
    lines = [f"📡 <b>LeadRadar — поток ({source})</b>\n"]
    for item in items[:5]:
        lines.append(
            f"• <b>{item['title']}</b> [{item['source']}]\n"
            f"  💰 {item['budget']} | 👤 {item['contact']}\n"
            f"  💬 <i>{item['outreach']}</i>\n"
        )
    return "\n".join(lines)


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "👋 <b>LeadRadar Bot (Free)</b>\n\n"
        "Показываю отфильтрованные заказы и лиды без рекламного спама и ботов.\n"
        "Выбери источник ниже:",
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )


@dp.message(Command("leads"))
async def cmd_leads(message: Message) -> None:
    await message.answer(format_leads("all"), reply_markup=main_keyboard(), parse_mode="HTML")


@dp.callback_query(F.data.startswith("leads:"))
async def cb_leads(call: CallbackQuery) -> None:
    source = call.data.split(":", 1)[1]
    await call.message.edit_text(format_leads(source), reply_markup=main_keyboard(), parse_mode="HTML")
    await call.answer()


@dp.callback_query(F.data == "about")
async def cb_about(call: CallbackQuery) -> None:
    await call.message.edit_text(
        "🛰 <b>LeadRadar</b>\n\n"
        "Открытый агрегатор лидов и заказов для разработчиков и агентств.\n"
        "GitHub: https://github.com/Goldiii-sudo/Lead--Radar",
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )
    await call.answer()


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("Set BOT_TOKEN environment variable before starting bot.py")
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

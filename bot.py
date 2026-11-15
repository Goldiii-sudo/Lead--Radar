import asyncio
import html
import os
import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from app import db
from server import DEMO_LEADS

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
USER_LANG: dict[int, str] = {}

dp = Dispatcher()

TEXTS = {
    "ru": {
        "welcome": (
            "👋 <b>LeadRadar Bot (@LeadRadarStartUpbot)</b>\n\n"
            "Показываю отфильтрованные заказы и лиды без рекламного спама и ботов.\n"
            "Выбери действие ниже:"
        ),
        "btn_leads": "🔥 Свежие лиды",
        "btn_scan": "🔄 Сканировать",
        "btn_lang": "🌐 Language: EN",
        "btn_about": "ℹ️ О проекте",
        "about": (
            "🛰 <b>LeadRadar</b>\n\n"
            "Открытый агрегатор лидов и заказов для разработчиков и агентств.\n"
            "GitHub: https://github.com/Goldiii-sudo/Lead--Radar"
        ),
        "scan_ok": "🔄 Сканирование запущено! Нажми «Свежие лиды» через 5–10 секунд.",
        "empty": "Пока нет лидов. Нажми «Сканировать».",
        "header": "📡 <b>LeadRadar — свежие лиды</b>\n",
    },
    "en": {
        "welcome": (
            "👋 <b>LeadRadar Bot (@LeadRadarStartUpbot)</b>\n\n"
            "Filtered client leads and freelance requests with zero ad spam or bots.\n"
            "Choose an action below:"
        ),
        "btn_leads": "🔥 Live Leads",
        "btn_scan": "🔄 Scan Now",
        "btn_lang": "🌐 Язык: RU",
        "btn_about": "ℹ️ About",
        "about": (
            "🛰 <b>LeadRadar</b>\n\n"
            "Open-source lead & project discovery for developers and small teams.\n"
            "GitHub: https://github.com/Goldiii-sudo/Lead--Radar"
        ),
        "scan_ok": "🔄 Scan started! Tap «Live Leads» in 5–10 seconds.",
        "empty": "No leads yet. Tap «Scan Now».",
        "header": "📡 <b>LeadRadar — Live Leads</b>\n",
    },
}


def get_lang(user_id: int) -> str:
    return USER_LANG.get(user_id, "ru")


def main_keyboard(lang: str) -> InlineKeyboardMarkup:
    t = TEXTS[lang]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t["btn_leads"], callback_data="leads"),
                InlineKeyboardButton(text=t["btn_scan"], callback_data="scan"),
            ],
            [
                InlineKeyboardButton(text=t["btn_lang"], callback_data="toggle_lang"),
                InlineKeyboardButton(text=t["btn_about"], callback_data="about"),
            ],
        ]
    )


def format_leads(lang: str) -> str:
    t = TEXTS[lang]
    try:
        db.init()
        rows = db.conn().execute(
            "SELECT source, score, author, email, url, text, translated_text FROM leads ORDER BY created_at DESC LIMIT 5"
        ).fetchall()
    except Exception:
        rows = []

    if rows:
        lines = [t["header"]]
        for r in rows:
            txt = html.escape((r["translated_text"] or r["text"] or "")[:180])
            src = html.escape(str(r["source"] or "web"))
            lines.append(f"• <b>[{src} • {r['score']}]</b> {txt}")
            if r["url"]:
                lines.append(f"  🔗 {r['url']}")
            lines.append("")
        return "\n".join(lines)

    lines = [t["header"]]
    for item in DEMO_LEADS[:4]:
        lines.append(
            f"• <b>{html.escape(item['title'])}</b> [{item['source']}]\n"
            f"  💰 {item['budget']} | 👤 {item['contact']}\n"
        )
    return "\n".join(lines)


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    lang = get_lang(message.from_user.id)
    await message.answer(TEXTS[lang]["welcome"], reply_markup=main_keyboard(lang), parse_mode="HTML")


@dp.message(Command("leads"))
async def cmd_leads(message: Message) -> None:
    lang = get_lang(message.from_user.id)
    await message.answer(format_leads(lang), reply_markup=main_keyboard(lang), parse_mode="HTML")


@dp.callback_query(F.data == "leads")
async def cb_leads(call: CallbackQuery) -> None:
    lang = get_lang(call.from_user.id)
    await call.message.edit_text(format_leads(lang), reply_markup=main_keyboard(lang), parse_mode="HTML")
    await call.answer()


@dp.callback_query(F.data == "scan")
async def cb_scan(call: CallbackQuery) -> None:
    lang = get_lang(call.from_user.id)
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post("http://127.0.0.1:8000/api/scan")
    except Exception:
        pass
    await call.answer(TEXTS[lang]["scan_ok"], show_alert=True)


@dp.callback_query(F.data == "toggle_lang")
async def cb_lang(call: CallbackQuery) -> None:
    uid = call.from_user.id
    new_lang = "en" if get_lang(uid) == "ru" else "ru"
    USER_LANG[uid] = new_lang
    await call.message.edit_text(TEXTS[new_lang]["welcome"], reply_markup=main_keyboard(new_lang), parse_mode="HTML")
    await call.answer()


@dp.callback_query(F.data == "about")
async def cb_about(call: CallbackQuery) -> None:
    lang = get_lang(call.from_user.id)
    await call.message.edit_text(TEXTS[lang]["about"], reply_markup=main_keyboard(lang), parse_mode="HTML")
    await call.answer()


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("Set BOT_TOKEN environment variable before starting bot.py")
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

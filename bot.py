import asyncio
import html
import json
import os
import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BufferedInputFile

from app import db, filters

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
USER_STATE: dict[int, dict] = {}
dp = Dispatcher()


def get_st(uid: int) -> dict:
    if uid not in USER_STATE:
        USER_STATE[uid] = {"lang": "ru", "source": "", "idx": 0}
    return USER_STATE[uid]


def fetch_leads(source: str = "") -> list[dict]:
    db.init()
    sql = (
        "SELECT id, source, score, author, email, phone, url, service, text, translated_text, draft "
        "FROM leads WHERE LOWER(text) NOT LIKE '%[offer]%' AND LOWER(text) NOT LIKE '%[for hire]%'"
    )
    args: list = []
    if source:
        sql += " AND source LIKE ?"
        args.append(source + "%")
    sql += " ORDER BY score DESC, created_at DESC LIMIT 30"
    return [dict(r) for r in db.conn().execute(sql, args).fetchall()]


def count_leads() -> int:
    try:
        db.init()
        return db.conn().execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    except Exception:
        return 0


def home_text(st: dict) -> str:
    src = st["source"] or ("Все источники" if st["lang"] == "ru" else "All sources")
    total = count_leads()
    if st["lang"] == "ru":
        return (
            "👋 <b>ЛИЧНЫЙ КАБИНЕТ LEADRADAR</b>\n\n"
            "⚙️ <b>ПАРАМЕТРЫ ПОИСКА:</b>\n"
            f"• 🎯 Источник: <code>{html.escape(src)}</code>\n"
            f"• 🌐 Язык карточек: <code>Русский</code>\n"
            f"• 🛡️ Анти-спам: ✅ Включён (без [OFFER] и ботов)\n"
            f"• 📊 В базе: <b>{total}</b> лидов\n\n"
            "<i>Нажмите «🚀 Начать парсинг» или откройте «🔥 Горячие лиды».</i>"
        )
    return (
        "👋 <b>LEADRADAR DASHBOARD</b>\n\n"
        "⚙️ <b>SEARCH SETTINGS:</b>\n"
        f"• 🎯 Source: <code>{html.escape(src)}</code>\n"
        f"• 🌐 Card language: <code>English</code>\n"
        f"• 🛡️ Anti-spam: ✅ Active (no [OFFER] or bots)\n"
        f"• 📊 In database: <b>{total}</b> leads\n\n"
        "<i>Tap «🚀 Scan Now» or open «🔥 Hot Leads».</i>"
    )


def home_kb(st: dict) -> InlineKeyboardMarkup:
    ru = st["lang"] == "ru"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Начать парсинг" if ru else "🚀 Scan Now", callback_data="scan")],
            [
                InlineKeyboardButton(text="🔥 Горячие лиды" if ru else "🔥 Hot Leads", callback_data="leads:0"),
                InlineKeyboardButton(text="🎯 Источник" if ru else "🎯 Source", callback_data="sources"),
            ],
            [
                InlineKeyboardButton(text="🌐 Язык: RU" if ru else "🌐 Lang: EN", callback_data="toggle_lang"),
                InlineKeyboardButton(text="📥 Скачать (.json)" if ru else "📥 Export (.json)", callback_data="export"),
            ],
        ]
    )


def sources_kb(st: dict) -> InlineKeyboardMarkup:
    ru = st["lang"] == "ru"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌐 Все" if ru else "🌐 All", callback_data="setsrc:"),
                InlineKeyboardButton(text="Reddit", callback_data="setsrc:reddit"),
            ],
            [
                InlineKeyboardButton(text="Freelancer", callback_data="setsrc:freelancer"),
                InlineKeyboardButton(text="Lemmy", callback_data="setsrc:lemmy"),
            ],
            [
                InlineKeyboardButton(text="Telegram", callback_data="setsrc:telegram"),
                InlineKeyboardButton(text="V2EX", callback_data="setsrc:v2ex"),
            ],
            [InlineKeyboardButton(text="◀️ В главное меню" if ru else "◀️ Back to menu", callback_data="home")],
        ]
    )


async def summarize_lead(lead: dict, lang: str) -> dict:
    post_text = (lead.get("translated_text") or lead.get("text") or "")[:1400]
    target = "Russian" if lang == "ru" else "English"
    prompt = (
        f"Analyze this client request and return JSON with 4 short fields in {target} "
        "(except 'pitch', which must be in the post's original language):\n"
        '{"title": "5-7 word project title", "pain": "1 short sentence on client pain", '
        '"solution": "1 short sentence on what to build/offer", '
        '"pitch": "2-3 sentence human outreach message ending with a question"}\n\n'
        f"POST:\n{post_text}"
    )
    raw = await filters.llm(prompt, json_mode=True)
    if raw:
        try:
            d = json.loads(raw)
            return {
                "title": str(d.get("title", ""))[:120],
                "pain": str(d.get("pain", ""))[:300],
                "solution": str(d.get("solution", ""))[:300],
                "pitch": str(d.get("pitch", ""))[:500],
            }
        except Exception:
            pass
    return {
        "title": lead.get("service") or ("Запрос клиента" if lang == "ru" else "Project Request"),
        "pain": post_text[:180],
        "solution": "Разработка под ключ по ТЗ." if lang == "ru" else "Custom build tailored to client brief.",
        "pitch": lead.get("draft") or "Hi! Saw your post — I can build this cleanly. Want to share details?",
    }


def format_lead_card(lead: dict, summary: dict, idx: int, total: int, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    ru = lang == "ru"
    src = html.escape(str(lead.get("source") or "web"))
    score = lead.get("score") or 0
    author = html.escape(str(lead.get("author") or "—"))
    email = html.escape(str(lead.get("email") or "—"))
    url = lead.get("url") or ""

    if ru:
        text = (
            f"🔥 <b>ГОРЯЧИЙ ЛИД • {src}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 <b>Проект:</b> {html.escape(summary['title'])}\n"
            f"📈 <b>Приоритет:</b> {score}/100\n\n"
            f"💢 <b>Боль:</b>\n<i>{html.escape(summary['pain'])}</i>\n\n"
            f"💡 <b>Решение:</b>\n<i>{html.escape(summary['solution'])}</i>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Автор:</b> {author}\n"
            f"✉️ <b>Почта:</b> <code>{email}</code>\n\n"
            f"💬 <b>Готовый питч:</b>\n<pre>{html.escape(summary['pitch'])}</pre>"
        )
    else:
        text = (
            f"🔥 <b>HOT LEAD • {src}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 <b>Project:</b> {html.escape(summary['title'])}\n"
            f"📈 <b>Score:</b> {score}/100\n\n"
            f"💢 <b>Pain:</b>\n<i>{html.escape(summary['pain'])}</i>\n\n"
            f"💡 <b>Solution:</b>\n<i>{html.escape(summary['solution'])}</i>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Author:</b> {author}\n"
            f"✉️ <b>Email:</b> <code>{email}</code>\n\n"
            f"💬 <b>Ready Pitch:</b>\n<pre>{html.escape(summary['pitch'])}</pre>"
        )

    rows = []
    if url:
        rows.append([InlineKeyboardButton(text="🔗 Открыть заказ" if ru else "🔗 Open Post", url=url)])
    prev_idx = (idx - 1) % total
    next_idx = (idx + 1) % total
    rows.append([
        InlineKeyboardButton(text="◀️", callback_data=f"leads:{prev_idx}"),
        InlineKeyboardButton(text=f"{idx + 1}/{total}", callback_data="noop"),
        InlineKeyboardButton(text="▶️", callback_data=f"leads:{next_idx}"),
    ])
    rows.append([InlineKeyboardButton(text="◀️ В главное меню" if ru else "◀️ Main Menu", callback_data="home")])
    return text, InlineKeyboardMarkup(inline_keyboard=rows)


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    st = get_st(message.from_user.id)
    await message.answer(home_text(st), reply_markup=home_kb(st), parse_mode="HTML")


@dp.message(Command("leads"))
async def cmd_leads(message: Message) -> None:
    st = get_st(message.from_user.id)
    items = fetch_leads(st["source"])
    if not items:
        await message.answer("Пока пусто — нажми «🚀 Начать парсинг»." if st["lang"] == "ru" else "No leads yet.", reply_markup=home_kb(st))
        return
    summary = await summarize_lead(items[0], st["lang"])
    txt, kb = format_lead_card(items[0], summary, 0, len(items), st["lang"])
    await message.answer(txt, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)


@dp.callback_query(F.data == "home")
async def cb_home(call: CallbackQuery) -> None:
    st = get_st(call.from_user.id)
    await call.message.edit_text(home_text(st), reply_markup=home_kb(st), parse_mode="HTML")
    await call.answer()


@dp.callback_query(F.data == "sources")
async def cb_sources(call: CallbackQuery) -> None:
    st = get_st(call.from_user.id)
    msg = "📍 <b>ВЫБОР ИСТОЧНИКА</b>\n\nВыберите площадку:" if st["lang"] == "ru" else "📍 <b>SELECT SOURCE</b>\n\nChoose a source:"
    await call.message.edit_text(msg, reply_markup=sources_kb(st), parse_mode="HTML")
    await call.answer()


@dp.callback_query(F.data.startswith("setsrc:"))
async def cb_setsrc(call: CallbackQuery) -> None:
    st = get_st(call.from_user.id)
    st["source"] = call.data.split(":", 1)[1]
    st["idx"] = 0
    await call.message.edit_text(home_text(st), reply_markup=home_kb(st), parse_mode="HTML")
    await call.answer("✅")


@dp.callback_query(F.data == "toggle_lang")
async def cb_lang(call: CallbackQuery) -> None:
    st = get_st(call.from_user.id)
    st["lang"] = "en" if st["lang"] == "ru" else "ru"
    await call.message.edit_text(home_text(st), reply_markup=home_kb(st), parse_mode="HTML")
    await call.answer()


@dp.callback_query(F.data == "scan")
async def cb_scan(call: CallbackQuery) -> None:
    st = get_st(call.from_user.id)
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post("http://127.0.0.1:8000/api/scan")
    except Exception:
        pass
    msg = "🚀 Парсинг запущен! Через 5–10 сек жми «🔥 Горячие лиды»." if st["lang"] == "ru" else "🚀 Scan started! Open «🔥 Hot Leads» in 5–10s."
    await call.answer(msg, show_alert=True)


@dp.callback_query(F.data.startswith("leads:"))
async def cb_leads(call: CallbackQuery) -> None:
    st = get_st(call.from_user.id)
    idx = int(call.data.split(":", 1)[1])
    items = fetch_leads(st["source"])
    if not items:
        await call.answer("Пока нет лидов по этому фильтру." if st["lang"] == "ru" else "No leads yet.", show_alert=True)
        return
    idx = idx % len(items)
    st["idx"] = idx
    await call.answer("⏳")
    summary = await summarize_lead(items[idx], st["lang"])
    txt, kb = format_lead_card(items[idx], summary, idx, len(items), st["lang"])
    await call.message.edit_text(txt, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)


@dp.callback_query(F.data == "export")
async def cb_export(call: CallbackQuery) -> None:
    st = get_st(call.from_user.id)
    items = fetch_leads(st["source"])
    raw = json.dumps(items, ensure_ascii=False, indent=2).encode("utf-8")
    await call.message.answer_document(BufferedInputFile(raw, filename="leadradar_leads.json"))
    await call.answer()


@dp.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery) -> None:
    await call.answer()


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("Set BOT_TOKEN environment variable before starting bot.py")
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="LeadRadar API", version="0.1.0")

DEMO_LEADS = [
    {
        "id": "lead-tg-01",
        "source": "Telegram",
        "channel": "@freelance_ru_jobs",
        "title": "Нужен Telegram-бот для записи клиентов в барбершоп",
        "budget": "25 000 RUB",
        "posted_ago": "4 мин назад",
        "intent_score": 96,
        "ai_outreach": (
            "Привет! Увидел задачу по боту для барбершопа. За 4 дня соберу "
            "бота с выбором мастера, слотов и напоминаниями в Telegram/WhatsApp, "
            "есть готовый кейс для салона. Скину демо и смету?"
        ),
    },
    {
        "id": "lead-av-02",
        "source": "Avito",
        "channel": "Услуги / Разработка сайтов",
        "title": "Лендинг под ключ для доставки фермерских продуктов (Москва)",
        "budget": "35 000 RUB",
        "posted_ago": "11 мин назад",
        "intent_score": 91,
        "ai_outreach": (
            "Здравствуйте! Помогу запустить конверсионный лендинг для доставки "
            "продуктов с корзиной и оплатой за 5 дней. Могу показать 2 похожих "
            "проекта в e-commerce и рассчитать стоимость."
        ),
    },
    {
        "id": "lead-2g-03",
        "source": "2GIS",
        "channel": "Новые компании без сайта",
        "title": "Стоматология «Дента Плюс» — открылась 2 недели назад, нет сайта",
        "budget": "40 000+ RUB",
        "posted_ago": "23 мин назад",
        "intent_score": 88,
        "ai_outreach": (
            "Добрый день! Заметили вашу клинику в 2ГИС — поздравляем с открытием. "
            "У вас пока нет сайта для онлайн-записи: можем за неделю сделать "
            "страницу с формой записи и SEO под район. Актуально?"
        ),
    },
    {
        "id": "lead-tg-04",
        "source": "Telegram",
        "channel": "@digital_tenders",
        "title": "Настройка сквозной аналитики + CRM (amoCRM) для онлайн-школы",
        "budget": "45 000 RUB",
        "posted_ago": "37 мин назад",
        "intent_score": 94,
        "ai_outreach": (
            "Привет! Регулярно настраиваем связку amoCRM + сквозная аналитика "
            "для EdTech. За 3 дня проведём аудит воронки и соберём дашборд "
            "окупаемости рекламы. Удобно созвониться на 15 минут?"
        ),
    },
]


class WaitlistRequest(BaseModel):
    email: str
    plan: Literal["free", "pro", "agency"] = "pro"
    niche: str = ""


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "leadradar"}


@app.get("/api/demo-leads")
def get_demo_leads(source: str | None = None) -> dict:
    leads = DEMO_LEADS
    if source and source.lower() != "all":
        leads = [l for l in DEMO_LEADS if l["source"].lower() == source.lower()]
    return {"count": len(leads), "leads": leads}


@app.post("/api/waitlist")
def join_waitlist(payload: WaitlistRequest) -> dict[str, str]:
    return {
        "status": "accepted",
        "message": f"Заявка для {payload.email} (тариф: {payload.plan.upper()}) принята.",
    }


@app.get("/")
def serve_index() -> FileResponse:
    return FileResponse(BASE_DIR / "index.html")


app.mount("/", StaticFiles(directory=BASE_DIR), name="static")

# LeadRadar

**AI-powered lead & project discovery platform built to help independent developers, freelancers, and small engineering teams find real client work without spam, noise, or middleman fees.**

---

## Why LeadRadar?

Thousands of real engineering projects are posted daily across fragmented channels (Telegram communities, local business directories, classifieds), buried under ad spam and low-quality noise. Independent developers spend hours manually scrolling instead of building.

**LeadRadar** solves this by:
- **Filtering out ad spam & bots** automatically so developers only see genuine, actionable requests.
- **Aggregating multi-source opportunities** (Telegram freelance channels, 2GIS, Avito, local business leads) into a single clean feed.
- **Drafting tailored, human-first outreach** so engineers can respond in seconds without sounding like a template.

---

## Architecture & Tech Stack

- **Backend:** Python 3, FastAPI, Pydantic, Uvicorn
- **Frontend:** Vanilla HTML5 / CSS3 / JS (zero-dependency, fast dark-mode SaaS UI)
- **API Endpoints:**
  - `GET /api/health` — service health check
  - `GET /api/demo-leads` — curated demo lead feed with source filtering
  - `POST /api/waitlist` — early-access waitlist signup

---

## Quick Start

```bash
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000` in your browser.

---

## Roadmap

- [x] FastAPI MVP & interactive lead feed UI
- [x] Anti-spam & bot-filtering pipeline
- [ ] Live multi-source connectors (Telegram, 2GIS, Avito)
- [ ] One-click personalized proposal & CV tailoring
- [ ] Automated webhook / Telegram notifications for Pro & Agency teams

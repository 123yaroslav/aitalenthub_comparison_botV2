# ITMO Masters Advisor (AI vs AI Product)

Готовый MVP системы: парсинг учебных планов, RAG-поиск, рекомендатор выборных и диалоговый Telegram‑бот.

Полностью рабочий телеграмм бот доступный по ссылке: https://t.me/aitalenthub_comparison_bot

**Источники истины (официальные страницы):**
- AI: https://abit.itmo.ru/program/master/ai
- AI Product: https://abit.itmo.ru/program/master/ai_product

**Якоря (обучающие страницы → «Скачать учебный план»):**
- https://abit.itmo.ru/program/master/ai#:~:text=Скачать,-учебный%20план
- https://abit.itmo.ru/program/master/ai_product#:~:text=Скачать-,учебный,-план

**Прямые ссылки «Скачать учебный план»:**
- AI (PDF): https://api.itmo.su/constructor-ep/api/v1/static/programs/10033/plan/abit/pdf
- AI Product (PDF): https://api.itmo.su/constructor-ep/api/v1/static/programs/10130/plan/abit/pdf

Внешние источники (как «недоверенные» до верификации): `ai.itmo.ru`, страницы Альфа‑Банка и т. п.

---

## Быстрый старт (локально)

```bash
git clone <your_repo_url_or_this_archive_unzipped>
cd itmo-masters-advisor
cp .env.example .env
make setup
make scrape      # скачает и распарсит планы в data/normalized/*.json
make index       # построит индексы (Chroma + BM25)
make api         # запустит FastAPI на 8000
# или make bot   # для Telegram-бота (требуется TELEGRAM_TOKEN)
```

### Системные требования
- Python 3.11+
- (опц.) Java для `tabula-py`, Ghostscript для `camelot-py` (иначе будет fallback на `pdfplumber`)
- RAM: 2–4 ГБ для индексации локальными эмбеддингами

### Переменные окружения
- `TELEGRAM_TOKEN` — токен для телеграм-бота
- `EMBEDDINGS_PROVIDER` — `local` (по умолч.) или `openai`
- `LLM_PROVIDER` — не используется напрямую (оставлен для расширения)
- `OPENAI_API_KEY` — если используете `openai` эмбеддинги

### Структура проекта
```
scraper/      # парсинг HTML и планов (PDF), нормализация JSON + SQLite
rag/          # индексация (вектор + BM25), извлечение и ответ с цитатами
recommender/  # эвристический подбор выборных
bot/          # телеграм-бот (aiogram)
api/          # FastAPI обертка
tests/        # pytest: парсинг, релевантность, диалог
data/         # кэш исходников и нормализованные данные
docker/       # Dockerfile
```

### Диалоговый бот
Команды: `/start`, `/compare`, `/plan`, `/electives`, `/help`

Бот отвечает **только** на релевантные вопросы. Вне тематики — мягкий отказ с подсказкой.

### Добавить новую программу
1. Добавьте страницу в `PROGRAM_PAGES` и прямую ссылку/паттерн в `DIRECT_PLAN_PDFS` (в `scraper/main.py`).
2. Запустите `make scrape` → проверьте `data/normalized/*.json`.
3. Запустите `make index`.

### Обновить планы
Повторите `make scrape`. Кэш перезапишется. Нужен интернет-доступ.

### Приватность
Персональные данные не собираются. Токены/секреты — через `.env`. Файлы `.env` и `data/raw/*` в `.gitignore`.

### Контест
Ссылка для README (может ругаться валидатор): https://contest.yandex.ru/contest/79334/enter

### Известные ограничения
- Формат таблиц в PDF может отличаться — используются несколько методов извлечения, возможны пропуски, но сохраняется `source_ref` (страница, строка).
- `Rules.min_electives_ects` оценивается эвристически; источником истины остаются планы на `abit.itmo.ru`.
- Рекомендатор прост и опирается на ключевые слова в названиях дисциплин.

### Лицензия
MIT (при публикации на GitHub).

---

© 2025
# aitalenthub_comparison_bot

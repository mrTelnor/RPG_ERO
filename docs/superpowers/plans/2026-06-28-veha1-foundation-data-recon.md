# Веха 1 — Фундамент и разведка данных pf2.ru — План реализации

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Поднять минимальный, тестируемый скелет бэкенда RPG_Ero и снять реальную структуру данных pf2.ru, чтобы разблокировать проектирование конвейера данных и движка создания персонажа.

**Architecture:** Бэкенд — Python 3.12 + FastAPI как чистый пакет `app` с эндпоинтом `/health` и юнит-тестами (зеркало стека home-page). Разведка данных — отдельный скрипт в `backend/tools`, использующий Playwright (headless Chromium) для прохождения JS-проверки pf2.ru; результат — сохранённые HTML-снимки в фикстуры и письменный документ с наблюдаемой структурой и предложением схемы данных.

**Tech Stack:** Python 3.12, uv, FastAPI, pytest, ruff, Playwright (Python), httpx (для TestClient).

## Global Constraints

- Python: **3.12** (как в home-page).
- Менеджер пакетов бэкенда: **uv**. Линтер: **ruff**. Тесты: **pytest** (+ pytest-asyncio позже, когда появится async-код).
- Пакет бэкенда называется `app`, тесты запускаются из каталога `backend/`.
- Движок и инструменты — **без сетевых обращений в тестах**: тесты парсинга работают только на сохранённых фикстурах.
- Внутренние ID сущностей правил — слаги из URL pf2.ru (например `/ancestries/elf` → `elf`).
- Бережный обход pf2.ru: headless, разовый прогон, без параллельного шквала запросов.
- Все коммиты — на ветке `main` (репозиторий локальный, solo).
- Атрибуция pf2.ru + Paizo/ORC обязательна в README.

---

### Task 1: Скелет бэкенда + `/health`

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/health.py`
- Create: `backend/tests/__init__.py`
- Test: `backend/tests/test_health.py`

**Interfaces:**
- Produces:
  - `app.main.app` — экземпляр `fastapi.FastAPI`.
  - `app.api.health.router` — `fastapi.APIRouter` с маршрутом `GET /health` → `{"status": "ok"}`.

- [ ] **Step 1: Инициализировать проект uv и зависимости**

Выполнить из каталога `backend/` (создать каталог, если его нет):

```bash
cd backend
uv init --bare --python 3.12
uv add fastapi "uvicorn[standard]"
uv add --dev pytest ruff httpx
```

Ожидаемо: появятся `backend/pyproject.toml` и `backend/uv.lock`, создастся `.venv`.

- [ ] **Step 2: Дописать конфигурацию инструментов в `backend/pyproject.toml`**

Добавить в `backend/pyproject.toml` секции (если каких-то ключей нет — создать):

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

- [ ] **Step 3: Написать падающий тест `backend/tests/test_health.py`**

```python
from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
```

Также создать пустые `backend/app/__init__.py`, `backend/app/api/__init__.py`, `backend/tests/__init__.py`.

- [ ] **Step 4: Запустить тест — убедиться, что падает**

Run (из `backend/`): `uv run pytest tests/test_health.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.main'` (или ImportError).

- [ ] **Step 5: Реализовать минимум — роутер и приложение**

`backend/app/api/health.py`:

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

`backend/app/main.py`:

```python
from fastapi import FastAPI

from app.api.health import router as health_router

app = FastAPI(title="RPG_Ero API")
app.include_router(health_router)
```

- [ ] **Step 6: Запустить тест — убедиться, что проходит**

Run (из `backend/`): `uv run pytest tests/test_health.py -v`
Expected: PASS (1 passed).

- [ ] **Step 7: Проверить линтер**

Run (из `backend/`): `uv run ruff check .`
Expected: `All checks passed!`

- [ ] **Step 8: Коммит**

```bash
git add backend/pyproject.toml backend/uv.lock backend/app backend/tests
git commit -m "feat(backend): скелет FastAPI + эндпоинт /health"
```

---

### Task 2: README с атрибуцией

**Files:**
- Create: `README.md`
- Modify: `.gitignore` (добавить каталог снимков разведки, см. ниже)

**Interfaces:**
- Produces: `README.md` в корне репозитория с разделом атрибуции pf2.ru + Paizo/ORC.

- [ ] **Step 1: Написать `README.md`**

Создать `README.md` в корне со следующим содержимым:

```markdown
# RPG_Ero

Текстовая браузерная одиночная RPG на правилах Pathfinder 2e Remaster в эстетике
CRT-терминала 80-х. Веха 1 — самодостаточный конструктор персонажа.

Дизайн: см. `docs/superpowers/specs/`. Планы: `docs/superpowers/plans/`.

## Структура

- `backend/` — Python 3.12 + FastAPI, движок правил (чистый пакет), инструменты парсинга.
- `frontend/` — React 19 + Vite (добавляется в плане UI).
- `infra/` — docker-compose, Traefik (добавляется в плане инфраструктуры).
- `docs/` — спецификации и планы.

## Разработка (backend)

```
cd backend
uv sync
uv run pytest
uv run ruff check .
```

## Атрибуция

Данные правил извлекаются из русского справочника **pf2.ru** (русский перевод сообщества).
Pathfinder 2e — собственность **Paizo Inc.**; механика опубликована под лицензией **ORC**.
Это **некоммерческий** проект; при коммерциализации необходимые лицензии будут получены отдельно.
```

- [ ] **Step 2: Добавить в `.gitignore` каталог сырых снимков разведки**

Добавить в конец `.gitignore`:

```
# Сырые снимки страниц разведки pf2.ru (не канон; в репозиторий попадают только зафиксированные фикстуры)
backend/tools/_recon_raw/
```

- [ ] **Step 3: Коммит**

```bash
git add README.md .gitignore
git commit -m "docs: README с атрибуцией pf2.ru/Paizo/ORC"
```

---

### Task 3: Разведка структуры данных pf2.ru (spike)

> **Это исследовательская задача (spike), а не TDD-цикл.** Цель — установить факты, а не реализовать функциональность. Главные результаты: (1) ответ, проходится ли JS-гейт pf2.ru через Playwright; (2) сохранённые HTML-фикстуры реальных страниц; (3) письменный документ с наблюдаемой структурой и предложением схемы данных. Эти результаты разблокируют План 2 (конвейер данных).

**Files:**
- Create: `backend/tools/__init__.py`
- Create: `backend/tools/pf2ru_recon.py`
- Create: `backend/tests/fixtures/pf2ru/` (сюда коммитятся отобранные снимки)
- Create: `docs/superpowers/specs/2026-06-28-pf2ru-data-findings.md` (документ с выводами)
- Test: `backend/tests/test_pf2ru_fixtures.py`

**Interfaces:**
- Produces:
  - Зафиксированные HTML-снимки в `backend/tests/fixtures/pf2ru/` (минимум: один индекс-список и по одной странице сущности для ancestry, class, background).
  - Документ выводов `docs/superpowers/specs/2026-06-28-pf2ru-data-findings.md`.

- [ ] **Step 1: Установить Playwright и браузер**

Run (из `backend/`):

```bash
uv add --dev playwright
uv run playwright install chromium
```

Expected: Chromium скачан без ошибок.

- [ ] **Step 2: Написать скрипт разведки `backend/tools/pf2ru_recon.py`**

Скрипт должен: (а) открыть несколько индекс-страниц, дождаться прохождения JS-проверки, сохранить их HTML в `_recon_raw/`; (б) напечатать в консоль найденные ссылки на конкретные сущности, чтобы оператор выбрал реальные URL для снятия. Создать также пустой `backend/tools/__init__.py`.

```python
"""Разведка структуры данных pf2.ru.

Запуск:  uv run python tools/pf2ru_recon.py
Назначение: проверить прохождение JS-гейта и снять сырые HTML-страницы
для последующего анализа. Сырьё пишется в tools/_recon_raw/ (в .gitignore).
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "https://pf2.ru"
INDEX_PAGES = {
    "index_ancestries": f"{BASE}/ancestries",
    "index_classes": f"{BASE}/classes",
    "index_backgrounds": f"{BASE}/backgrounds",
}

RAW_DIR = Path(__file__).parent / "_recon_raw"


def fetch(page, url: str) -> str:
    page.goto(url, wait_until="networkidle", timeout=60_000)
    # Дать JS-проверке отработать и отрисовать контент.
    page.wait_for_load_state("networkidle", timeout=60_000)
    return page.content()


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        for name, url in INDEX_PAGES.items():
            html = fetch(page, url)
            out = RAW_DIR / f"{name}.html"
            out.write_text(html, encoding="utf-8")
            blocked = "Проверка безопасности" in html or "Подождите" in html
            print(f"{name}: {len(html)} символов, заблокировано={blocked} -> {out}")
        browser.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Запустить разведку и зафиксировать результат прохождения гейта**

Run (из `backend/`): `uv run python tools/pf2ru_recon.py`

Зафиксировать в выводе: для каждой индекс-страницы — размер HTML и флаг `заблокировано`.

**Развилка по результату:**
- Если `заблокировано=False` и HTML содержательный (десятки КБ, видны ссылки на сущности) — переходить к Step 4.
- Если `заблокировано=True` для всех страниц — гейт не пройден headless-браузером. **Остановиться, не изобретать обходы.** Записать этот факт в документ выводов (Step 6) как блокер и вынести на решение: (а) пробовать `playwright-stealth`/непустой user-agent/не-headless режим, либо (б) пересмотреть источник данных (гибрид Foundry JSON + RU-оверлей как запасной вариант, обсуждавшийся при брейншторме). Дальнейшие шаги этой задачи в таком случае не выполняются до решения.

- [ ] **Step 4: Снять по одной реальной странице сущности каждого типа**

Из сохранённых `_recon_raw/index_*.html` найти реальные URL конкретной родословной, класса и предыстории (открыть файлы, найти ссылки вида `/ancestries/<slug>` и т.п.). Добавить найденные URL в словарь `ENTITY_PAGES` в скрипте и снять их:

```python
ENTITY_PAGES = {
    # Заполнить РЕАЛЬНЫМИ слагами, найденными в index_*.html, например:
    # "ancestry_<slug>": f"{BASE}/ancestries/<slug>",
    # "class_<slug>": f"{BASE}/classes/<slug>",
    # "background_<slug>": f"{BASE}/backgrounds/<slug>",
}
```

Добавить в `main()` после цикла по индексам аналогичный цикл по `ENTITY_PAGES`, пишущий в `_recon_raw/`. Перезапустить: `uv run python tools/pf2ru_recon.py`.

- [ ] **Step 5: Отобрать и зафиксировать фикстуры**

Скопировать в `backend/tests/fixtures/pf2ru/` ровно по одному снимку каждого типа (один индекс + одна ancestry + один class + один background). Эти файлы коммитятся как стабильные фикстуры для тестов парсера в Плане 2. Имена файлов — по слагу, например `ancestry_elf.html`.

- [ ] **Step 6: Написать документ выводов**

Создать `docs/superpowers/specs/2026-06-28-pf2ru-data-findings.md` со следующими разделами (заполнить РЕАЛЬНЫМИ наблюдениями из снятого HTML, не догадками):

```markdown
# pf2.ru — выводы разведки данных

**Дата снимка:** 2026-06-28

## 1. Прохождение JS-гейта
[Проходится ли гейт headless-Chromium? Какие настройки понадобились? Размеры HTML.]

## 2. URL-паттерны
[Реальные паттерны: /ancestries/<slug>, /classes/<slug>, /backgrounds/<slug>, /feats/... — как они устроены, как с индекс-страниц получить список всех слагов.]

## 3. Структура страницы сущности
[Для ancestry / class / background: где в HTML лежат ключевые поля. Это структурированная разметка (таблицы, dl, data-атрибуты, классы CSS) или сплошной текст? Привести реальные имена селекторов/классов.]

## 4. Доступные механические поля
[Что реально извлекаемо: для ancestry — HP, размер, скорость, повышения/изъяны атрибутов, трейты, наследия; для class — ключевая характеристика, HP/уровень, начальные владения, классовые фиты 1 ур.; для background — повышения, обученный навык, навыковый фит.]

## 5. Предложение схемы данных
[Компактная JSON-схема для backend/data на основе наблюдаемых полей — таблицы/сущности и их поля.]

## 6. Открытые вопросы / риски
[Чего не хватает на pf2.ru, что неоднозначно, что потребует ручной доработки.]
```

- [ ] **Step 7: Написать смоук-тест наличия фикстур**

`backend/tests/test_pf2ru_fixtures.py`:

```python
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures" / "pf2ru"


def test_entity_fixtures_present_and_nontrivial():
    captured = list(FIXTURES.glob("*.html"))
    assert captured, "Нет снятых фикстур pf2.ru"
    # Хотя бы по одной странице каждого типа сущности.
    kinds = {"ancestry", "class", "background"}
    present = {k for k in kinds if any(f.name.startswith(k) for f in captured)}
    assert present == kinds, f"Не хватает типов фикстур: {kinds - present}"
    # Снимки должны быть содержательными, а не страницей-заглушкой гейта.
    for f in captured:
        html = f.read_text(encoding="utf-8")
        assert len(html) > 5_000, f"Снимок подозрительно мал: {f.name}"
        assert "Проверка безопасности" not in html, f"Снимок — страница гейта: {f.name}"
```

- [ ] **Step 8: Запустить тест — убедиться, что проходит**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_fixtures.py -v`
Expected: PASS (фикстуры на месте и содержательны).

- [ ] **Step 9: Коммит**

```bash
git add backend/tools/__init__.py backend/tools/pf2ru_recon.py \
  backend/tests/fixtures/pf2ru backend/tests/test_pf2ru_fixtures.py \
  docs/superpowers/specs/2026-06-28-pf2ru-data-findings.md
git commit -m "spike: разведка структуры данных pf2.ru + фикстуры и выводы"
```

---

## Что дальше (после этого плана)

Документ выводов (`2026-06-28-pf2ru-data-findings.md`) фиксирует реальную схему данных. На его основе пишутся следующие планы Вехи 1, уже без догадок:

- **План 2 — конвейер данных:** парсер pf2.ru (тесты на зафиксированных фикстурах) → нормализованный JSON в `backend/data`.
- **План 3 — движок `engine/chargen`:** создание персонажа 1-го уровня по книге (чистые функции, TDD).
- **План 4 — API + персистентность:** аутентификация, эндпоинты создания/валидации персонажа, таблица `characters`, alembic, инфра (docker-compose).
- **План 5 — UI-конструктор:** скелет frontend, мастер создания персонажа в стиле терминала, лист персонажа, экспорт JSON.
```


# Веха 1 — Конвейер данных pf2.ru (индекс-JSON) — План реализации

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Извлечь структурированный датасет родословных, классов и предысторий PF2e из server-rendered JSON pf2.ru (`<pf2-table items="...">`) и записать его как нормализованный JSON в `backend/data`.

**Architecture:** Чистый, оффлайн-детерминированный пайплайн под `backend/tools/pf2ru/`: извлечение JSON-массива из HTML индекс-страницы → нормализация по типу сущности (RU→EN-карты + парсинг wiki-ссылок) → запись `backend/data/{ancestries,classes,backgrounds}.json` + `manifest.json`. Весь датасет каждого типа уже отрисован в одном `<pf2-table>` на индекс-странице, поэтому источник — три закоммиченные HTML-фикстуры (живой рефреш = повторный прогон `pf2ru_recon.py` → `build`). Все тесты читают только фикстуры, без сети.

**Tech Stack:** Python 3.12, uv, pytest, ruff. Только стандартная библиотека (`re`, `json`, `html`, `pathlib`) — новых зависимостей нет.

## Global Constraints

- Python: **3.12**. Менеджер пакетов: **uv**. Линтер: **ruff** (target py312, line-length 100, select E/F/I/UP/B). Тесты: **pytest**, запуск из каталога `backend/`.
- Пакет бэкенда — `app`; инструменты-конвейер — пакет `tools.pf2ru` (каталог `backend/tools/pf2ru/`); `backend/tools/__init__.py` уже существует.
- **Внутренний ID сущности = слаг = `name.lower()` с заменой пробелов на дефисы** (поле `name` в JSON pf2.ru — английское).
- **Никаких сетевых обращений в тестах** — тесты читают только фикстуры из `backend/tests/fixtures/pf2ru/`.
- Локализованные значения характеристик/размеров берём из русских полей через статические RU→EN-карты (у родословных и классов нет `*_search` для характеристик); английские имена сущностей/навыков/фитов берём из ASCII-частей `name` / `*_search` / wiki-ссылок.
- Новых зависимостей не добавлять (только stdlib).
- Все коммиты — на ветке этого плана (НЕ на `main`; ветку создаёт контроллер исполнения).
- Выходной датасет (`backend/data/*.json`) генерируется детерминированно из закоммиченных фикстур и коммитится.

## Ground Truth (реальные значения из фикстур — для ассертов)

Подтверждено извлечением из `backend/tests/fixtures/pf2ru/`:

- **Количества в `items`:** ancestries = **33**, classes = **21**, backgrounds = **140**.
- **Dwarf** (`index_ancestries.html`): `name="Dwarf"`, `rus_name="Дварф"`, `hp=10`, `size="Средний"`, `speed_sort=20`, `ability_boost="Выносливость, Мудрость, Универсальное"`, `ability_flaw="Харизма"`, `vision="Ночное зрение"`, `traits` HTML содержит `href="/traits/dwarf"` и `href="/traits/humanoid"`, `id=59`, `is_legacy=false`, `is_not_translated=false`.
- **Fighter** (`index_classes.html`): `name="Fighter"`, `rus_name="Воин"`, `hp=10`, `ability_boost="Сила или Ловкость"`, `id=35`, `is_not_translated=false`. (У классов нет ключа `is_legacy`.)
- **Acolyte** (`index_backgrounds.html`): `name="Acolyte"`, `rus_name="Прислужник"`, `ability_boost="Интеллект, Мудрость"`, `skills_search="[[skill/13|Religion]], Scribing [[skill/8|Lore]] [[skill/13|Религия]], [[skill/8|Знание]] (письмо)"`, `feat_search="[[feat/847|Student of the Canon]] [[feat/847|Прислужник]]"`, `id=406`, `is_legacy=false`.

---

### Task 1: Извлечение `<pf2-table items>` + фикстура индекса классов

**Files:**
- Create: `backend/tests/fixtures/pf2ru/index_classes.html` (копия из `backend/tools/_recon_raw/index_classes.html`)
- Create: `backend/tools/pf2ru/__init__.py`
- Create: `backend/tools/pf2ru/table.py`
- Test: `backend/tests/test_pf2ru_table.py`

**Interfaces:**
- Produces: `tools.pf2ru.table.extract_items(html_text: str) -> list[dict]` — извлекает и парсит JSON-массив из атрибута `items` элемента `<pf2-table>`.

- [ ] **Step 1: Зафиксировать фикстуру индекса классов**

Скопировать уже снятый сырой снимок в каталог фикстур (он нужен тесту экстрактора и нормализатору классов):

```bash
cp backend/tools/_recon_raw/index_classes.html backend/tests/fixtures/pf2ru/index_classes.html
```

Если файла `backend/tools/_recon_raw/index_classes.html` нет (сырой каталог очищен), однократно вежливо пересними его: из `backend/` добавь `"index_classes": f"{BASE}/classes"` в `INDEX_PAGES` скрипта `tools/pf2ru_recon.py` (если его там нет) и запусти `uv run python tools/pf2ru_recon.py`, затем скопируй из `_recon_raw/`.

- [ ] **Step 2: Написать падающий тест `backend/tests/test_pf2ru_table.py`**

```python
from pathlib import Path

from tools.pf2ru.table import extract_items

FIXTURES = Path(__file__).parent / "fixtures" / "pf2ru"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_extract_items_counts_per_type():
    assert len(extract_items(_read("index_ancestries.html"))) == 33
    assert len(extract_items(_read("index_classes.html"))) == 21
    assert len(extract_items(_read("index_backgrounds.html"))) == 140


def test_extract_items_returns_dicts_with_name():
    items = extract_items(_read("index_ancestries.html"))
    assert all(isinstance(it, dict) for it in items)
    assert any(it.get("name") == "Dwarf" for it in items)


def test_extract_items_raises_when_absent():
    import pytest

    with pytest.raises(ValueError):
        extract_items("<html><body>no table here</body></html>")
```

- [ ] **Step 3: Запустить тест — убедиться, что падает**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_table.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.pf2ru'`.

- [ ] **Step 4: Реализовать `backend/tools/pf2ru/table.py`** (и создать пустой `backend/tools/pf2ru/__init__.py`)

```python
"""Извлечение server-rendered JSON из индекс-страниц pf2.ru.

Весь датасет типа сущности отрисован в атрибуте items элемента
<pf2-table> (HTML-escaped JSON-массив), без подгрузки по XHR.
"""

import html
import json
import re

_PF2_TABLE_ITEMS = re.compile(r'<pf2-table\b[^>]*\sitems="(.*?)"', re.DOTALL)


def extract_items(html_text: str) -> list[dict]:
    """Вернуть список сырых записей сущностей из <pf2-table items="...">."""
    match = _PF2_TABLE_ITEMS.search(html_text)
    if match is None:
        raise ValueError('no <pf2-table items="..."> found in HTML')
    return json.loads(html.unescape(match.group(1)))
```

- [ ] **Step 5: Запустить тест — убедиться, что проходит**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_table.py -v`
Expected: PASS (3 passed).

- [ ] **Step 6: Линт и коммит**

Run (из `backend/`): `uv run ruff check .` → `All checks passed!`

```bash
git add backend/tools/pf2ru/__init__.py backend/tools/pf2ru/table.py \
  backend/tests/test_pf2ru_table.py backend/tests/fixtures/pf2ru/index_classes.html
git commit -m "feat(pipeline): извлечение pf2-table items + фикстура индекса классов"
```

---

### Task 2: RU→EN-карты характеристик и размеров

**Files:**
- Create: `backend/tools/pf2ru/mappings.py`
- Test: `backend/tests/test_pf2ru_mappings.py`

**Interfaces:**
- Produces:
  - `tools.pf2ru.mappings.normalize_abilities(value: str | None) -> list[str]` — русский список характеристик (через запятую / «или») → канонические английские (`Strength`/`Dexterity`/`Constitution`/`Intelligence`/`Wisdom`/`Charisma`/`Free`).
  - `tools.pf2ru.mappings.normalize_sizes(value: str | None) -> list[str]` — русские размеры → английские.
  - Константы `ABILITY_RU_EN`, `SIZE_RU_EN`.

- [ ] **Step 1: Написать падающий тест `backend/tests/test_pf2ru_mappings.py`**

```python
import pytest

from tools.pf2ru.mappings import normalize_abilities, normalize_sizes


def test_abilities_ancestry_boosts_dwarf():
    assert normalize_abilities("Выносливость, Мудрость, Универсальное") == [
        "Constitution",
        "Wisdom",
        "Free",
    ]


def test_abilities_single_flaw():
    assert normalize_abilities("Харизма") == ["Charisma"]


def test_abilities_class_key_or_phrase_fighter():
    assert normalize_abilities("Сила или Ловкость") == ["Strength", "Dexterity"]


def test_abilities_class_key_other_is_free():
    assert normalize_abilities("Ловкость или Другая") == ["Dexterity", "Free"]


def test_abilities_empty_and_dash():
    assert normalize_abilities("") == []
    assert normalize_abilities("-") == []
    assert normalize_abilities(None) == []


def test_abilities_unknown_token_raises():
    with pytest.raises(KeyError):
        normalize_abilities("Хитрость")


def test_sizes_single_and_multi():
    assert normalize_sizes("Средний") == ["Medium"]
    assert normalize_sizes("Средний, Небольшой") == ["Medium", "Small"]
    assert normalize_sizes(None) == []
```

- [ ] **Step 2: Запустить тест — убедиться, что падает**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_mappings.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.pf2ru.mappings'`.

- [ ] **Step 3: Реализовать `backend/tools/pf2ru/mappings.py`**

```python
"""Статические RU→EN-карты для локализованных полей pf2.ru.

У родословных и классов нет `*_search` для характеристик, поэтому английские
эквиваленты восстанавливаем по закрытым множествам, а не парсингом текста.
"""

import re

ABILITY_RU_EN = {
    "Сила": "Strength",
    "Ловкость": "Dexterity",
    "Выносливость": "Constitution",
    "Интеллект": "Intelligence",
    "Мудрость": "Wisdom",
    "Харизма": "Charisma",
    "Универсальное": "Free",
    "Другая": "Free",
}

SIZE_RU_EN = {
    "Маленький": "Tiny",
    "Небольшой": "Small",
    "Средний": "Medium",
    "Крупный": "Large",
    "Огромный": "Huge",
    "Колоссальный": "Gargantuan",
}

# Разделители в строке характеристик: запятая, слэш или слово «или».
_ABILITY_SPLIT = re.compile(r"\s*(?:,|/|\bили\b)\s*")


def normalize_abilities(value: str | None) -> list[str]:
    """Русская строка характеристик → канонические английские имена."""
    if not value or value.strip() in {"", "-"}:
        return []
    result = []
    for token in _ABILITY_SPLIT.split(value):
        token = token.strip()
        if not token:
            continue
        result.append(ABILITY_RU_EN[token])  # KeyError на неизвестном токене (ловит дрейф схемы)
    return result


def normalize_sizes(value: str | None) -> list[str]:
    """Русская строка размеров (через запятую) → английские имена."""
    if not value or not value.strip():
        return []
    result = []
    for token in re.split(r"\s*,\s*", value.strip()):
        token = token.strip()
        if not token:
            continue
        result.append(SIZE_RU_EN[token])
    return result
```

- [ ] **Step 4: Запустить тест — убедиться, что проходит**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_mappings.py -v`
Expected: PASS (8 passed).

- [ ] **Step 5: Линт и коммит**

Run (из `backend/`): `uv run ruff check .` → `All checks passed!`

```bash
git add backend/tools/pf2ru/mappings.py backend/tests/test_pf2ru_mappings.py
git commit -m "feat(pipeline): RU→EN-карты характеристик и размеров"
```

---

### Task 3: Парсинг wiki-ссылок, трейтов и слагов

**Files:**
- Create: `backend/tools/pf2ru/links.py`
- Test: `backend/tests/test_pf2ru_links.py`

**Interfaces:**
- Produces:
  - `tools.pf2ru.links.parse_wikilinks(text: str | None) -> list[tuple[str, int, str]]` — токены `[[kind/id|Name]]` → список `(kind, id, name)`.
  - `tools.pf2ru.links.extract_trait_slugs(html_fragment: str | None) -> list[str]` — слаги трейтов из `href="/traits/<slug>"`, без дублей, с сохранением порядка.
  - `tools.pf2ru.links.slugify(name: str) -> str` — `name.lower()`, пробелы → дефисы.

- [ ] **Step 1: Написать падающий тест `backend/tests/test_pf2ru_links.py`**

```python
from tools.pf2ru.links import extract_trait_slugs, parse_wikilinks, slugify


def test_parse_wikilinks_feat():
    text = "[[feat/847|Student of the Canon]] [[feat/847|Прислужник]]"
    assert parse_wikilinks(text) == [
        ("feat", 847, "Student of the Canon"),
        ("feat", 847, "Прислужник"),
    ]


def test_parse_wikilinks_skills():
    text = "[[skill/13|Religion]], Scribing [[skill/8|Lore]]"
    assert parse_wikilinks(text) == [
        ("skill", 13, "Religion"),
        ("skill", 8, "Lore"),
    ]


def test_parse_wikilinks_empty():
    assert parse_wikilinks("") == []
    assert parse_wikilinks(None) == []


def test_extract_trait_slugs_dedup_order():
    html_fragment = (
        '<a class="item-link--trait" href="/traits/dwarf">Дварф</a>'
        '<a class="item-link--trait" href="/traits/humanoid">Гуманоид</a>'
        '<a href="/traits/dwarf">dup</a>'
    )
    assert extract_trait_slugs(html_fragment) == ["dwarf", "humanoid"]


def test_extract_trait_slugs_empty():
    assert extract_trait_slugs("") == []
    assert extract_trait_slugs(None) == []


def test_slugify():
    assert slugify("Fighter") == "fighter"
    assert slugify("Student of the Canon") == "student-of-the-canon"
```

- [ ] **Step 2: Запустить тест — убедиться, что падает**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_links.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.pf2ru.links'`.

- [ ] **Step 3: Реализовать `backend/tools/pf2ru/links.py`**

```python
"""Парсинг wiki-ссылок pf2.ru ([[kind/id|Name]]), трейтов и слагов."""

import re

_WIKILINK = re.compile(r"\[\[(\w+)/(\d+)\|([^\]]+)\]\]")
_TRAIT_HREF = re.compile(r'href="/traits/([^"]+)"')


def parse_wikilinks(text: str | None) -> list[tuple[str, int, str]]:
    """Токены [[kind/id|Name]] → список (kind, id, name)."""
    return [(kind, int(num), name) for kind, num, name in _WIKILINK.findall(text or "")]


def extract_trait_slugs(html_fragment: str | None) -> list[str]:
    """Слаги трейтов из href="/traits/<slug>", без дублей, порядок сохранён."""
    seen: list[str] = []
    for slug in _TRAIT_HREF.findall(html_fragment or ""):
        if slug not in seen:
            seen.append(slug)
    return seen


def slugify(name: str) -> str:
    """Английское имя → слаг: lowercase, пробелы → дефисы."""
    return name.strip().lower().replace(" ", "-")
```

- [ ] **Step 4: Запустить тест — убедиться, что проходит**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_links.py -v`
Expected: PASS (6 passed).

- [ ] **Step 5: Линт и коммит**

Run (из `backend/`): `uv run ruff check .` → `All checks passed!`

```bash
git add backend/tools/pf2ru/links.py backend/tests/test_pf2ru_links.py
git commit -m "feat(pipeline): парсинг wiki-ссылок, трейтов и слагов"
```

---

### Task 4: Нормализаторы сущностей

**Files:**
- Create: `backend/tools/pf2ru/normalize.py`
- Test: `backend/tests/test_pf2ru_normalize.py`

**Interfaces:**
- Consumes: `extract_items` (Task 1); `normalize_abilities`, `normalize_sizes` (Task 2); `parse_wikilinks`, `extract_trait_slugs`, `slugify` (Task 3).
- Produces:
  - `tools.pf2ru.normalize.normalize_ancestry(raw: dict) -> dict`
  - `tools.pf2ru.normalize.normalize_class(raw: dict) -> dict`
  - `tools.pf2ru.normalize.normalize_background(raw: dict) -> dict`

  Форма нормализованной записи (ключи стабильны — на них опирается Task 5 и будущий движок `chargen`):
  - ancestry: `slug, name_en, name_ru, hp, size (list[str]), speed (int|None), ability_boosts (list[str]), ability_flaws (list[str]), vision_ru (str|None), traits (list[str]), source_ru, is_legacy, is_not_translated, pf2ru_id`
  - class: `slug, name_en, name_ru, hp_per_level, key_ability (list[str]), source_ru, is_not_translated, pf2ru_id` (начальные владения и классовые фиты 1 ур. — НЕ здесь; см. «Что дальше»)
  - background: `slug, name_en, name_ru, ability_boosts (list[str]), trained_skill (str|None), lore (str|None), skill_feat (dict|None: {slug, name_en, pf2ru_feat_id}), source_ru, is_legacy, is_not_translated, pf2ru_id`

- [ ] **Step 1: Написать падающий тест `backend/tests/test_pf2ru_normalize.py`**

```python
from pathlib import Path

from tools.pf2ru.normalize import (
    normalize_ancestry,
    normalize_background,
    normalize_class,
)
from tools.pf2ru.table import extract_items

FIXTURES = Path(__file__).parent / "fixtures" / "pf2ru"


def _find(fixture: str, name: str) -> dict:
    items = extract_items((FIXTURES / fixture).read_text(encoding="utf-8"))
    return next(it for it in items if it.get("name") == name)


def test_normalize_ancestry_dwarf():
    result = normalize_ancestry(_find("index_ancestries.html", "Dwarf"))
    assert result["slug"] == "dwarf"
    assert result["name_en"] == "Dwarf"
    assert result["name_ru"] == "Дварф"
    assert result["hp"] == 10
    assert result["size"] == ["Medium"]
    assert result["speed"] == 20
    assert result["ability_boosts"] == ["Constitution", "Wisdom", "Free"]
    assert result["ability_flaws"] == ["Charisma"]
    assert result["traits"] == ["dwarf", "humanoid"]
    assert result["pf2ru_id"] == 59
    assert result["is_legacy"] is False
    assert isinstance(result["name_ru"], str) and result["name_ru"]


def test_normalize_class_fighter():
    result = normalize_class(_find("index_classes.html", "Fighter"))
    assert result["slug"] == "fighter"
    assert result["name_en"] == "Fighter"
    assert result["name_ru"] == "Воин"
    assert result["hp_per_level"] == 10
    assert result["key_ability"] == ["Strength", "Dexterity"]
    assert result["pf2ru_id"] == 35
    # начальные владения/классовые фиты сюда НЕ входят
    assert "initial_proficiencies" not in result


def test_normalize_background_acolyte():
    result = normalize_background(_find("index_backgrounds.html", "Acolyte"))
    assert result["slug"] == "acolyte"
    assert result["name_en"] == "Acolyte"
    assert result["ability_boosts"] == ["Intelligence", "Wisdom"]
    assert result["trained_skill"] == "Religion"
    assert result["lore"] == "Scribing Lore"
    assert result["skill_feat"] == {
        "slug": "student-of-the-canon",
        "name_en": "Student of the Canon",
        "pf2ru_feat_id": 847,
    }
    assert result["pf2ru_id"] == 406
```

- [ ] **Step 2: Запустить тест — убедиться, что падает**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_normalize.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.pf2ru.normalize'`.

- [ ] **Step 3: Реализовать `backend/tools/pf2ru/normalize.py`**

```python
"""Нормализаторы сырых записей pf2.ru → компактная схема backend/data."""

import re

from tools.pf2ru.links import extract_trait_slugs, parse_wikilinks, slugify
from tools.pf2ru.mappings import normalize_abilities, normalize_sizes

# Английское слово (тип знания) перед ссылкой на навык Lore: "Scribing [[skill/8|Lore]]".
_LORE_WORD = re.compile(r"([A-Za-z]+)\s+\[\[skill/\d+\|Lore\]\]")


def normalize_ancestry(raw: dict) -> dict:
    return {
        "slug": slugify(raw["name"]),
        "name_en": raw["name"],
        "name_ru": raw.get("rus_name"),
        "hp": raw.get("hp"),
        "size": normalize_sizes(raw.get("size")),
        "speed": raw.get("speed_sort"),
        "ability_boosts": normalize_abilities(raw.get("ability_boost")),
        "ability_flaws": normalize_abilities(raw.get("ability_flaw")),
        "vision_ru": raw.get("vision") or None,
        "traits": extract_trait_slugs(raw.get("traits", "")),
        "source_ru": raw.get("source"),
        "is_legacy": raw.get("is_legacy", False),
        "is_not_translated": raw.get("is_not_translated", False),
        "pf2ru_id": raw.get("id"),
    }


def normalize_class(raw: dict) -> dict:
    return {
        "slug": slugify(raw["name"]),
        "name_en": raw["name"],
        "name_ru": raw.get("rus_name"),
        "hp_per_level": raw.get("hp"),
        "key_ability": normalize_abilities(raw.get("ability_boost")),
        "source_ru": raw.get("source"),
        "is_not_translated": raw.get("is_not_translated", False),
        "pf2ru_id": raw.get("id"),
    }


def _english_wikilinks(text: str | None) -> list[tuple[str, int, str]]:
    """Только англоязычные (ASCII-имя) wiki-ссылки — в *_search английский идёт первым."""
    return [(k, i, n) for (k, i, n) in parse_wikilinks(text) if n.isascii()]


def normalize_background(raw: dict) -> dict:
    skills_search = raw.get("skills_search", "")
    skill_links = _english_wikilinks(skills_search)
    trained_skill = next((n for (_, _, n) in skill_links if n != "Lore"), None)

    lore = None
    lore_match = _LORE_WORD.search(skills_search)
    if lore_match:
        lore = f"{lore_match.group(1)} Lore"

    skill_feat = None
    feat_links = _english_wikilinks(raw.get("feat_search", ""))
    if feat_links:
        _, feat_id, feat_name = feat_links[0]
        skill_feat = {
            "slug": slugify(feat_name),
            "name_en": feat_name,
            "pf2ru_feat_id": feat_id,
        }

    return {
        "slug": slugify(raw["name"]),
        "name_en": raw["name"],
        "name_ru": raw.get("rus_name"),
        "ability_boosts": normalize_abilities(raw.get("ability_boost")),
        "trained_skill": trained_skill,
        "lore": lore,
        "skill_feat": skill_feat,
        "source_ru": raw.get("source"),
        "is_legacy": raw.get("is_legacy", False),
        "is_not_translated": raw.get("is_not_translated", False),
        "pf2ru_id": raw.get("id"),
    }
```

- [ ] **Step 4: Запустить тест — убедиться, что проходит**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_normalize.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Линт и коммит**

Run (из `backend/`): `uv run ruff check .` → `All checks passed!`

```bash
git add backend/tools/pf2ru/normalize.py backend/tests/test_pf2ru_normalize.py
git commit -m "feat(pipeline): нормализаторы родословных, классов, предысторий"
```

---

### Task 5: Сборка датасета (`build`) + коммит `backend/data`

**Files:**
- Create: `backend/tools/pf2ru/build.py`
- Create (генерируется и коммитится): `backend/data/ancestries.json`, `backend/data/classes.json`, `backend/data/backgrounds.json`, `backend/data/manifest.json`
- Test: `backend/tests/test_pf2ru_build.py`

**Interfaces:**
- Consumes: `extract_items` (Task 1); `normalize_ancestry`, `normalize_class`, `normalize_background` (Task 4).
- Produces: `tools.pf2ru.build.build(raw_dir: Path, out_dir: Path) -> dict[str, int]` — читает три индекс-фикстуры из `raw_dir`, пишет нормализованный JSON + `manifest.json` в `out_dir`, возвращает счётчики по типам. Плюс CLI `python -m tools.pf2ru.build`.

- [ ] **Step 1: Написать падающий тест `backend/tests/test_pf2ru_build.py`**

```python
import json
from pathlib import Path

from tools.pf2ru.build import build

FIXTURES = Path(__file__).parent / "fixtures" / "pf2ru"


def test_build_writes_dataset(tmp_path):
    counts = build(FIXTURES, tmp_path)
    assert counts == {"ancestries": 33, "classes": 21, "backgrounds": 140}

    for name in ("ancestries", "classes", "backgrounds", "manifest"):
        assert (tmp_path / f"{name}.json").exists()

    ancestries = json.loads((tmp_path / "ancestries.json").read_text(encoding="utf-8"))
    dwarf = next(a for a in ancestries if a["slug"] == "dwarf")
    assert dwarf["ability_boosts"] == ["Constitution", "Wisdom", "Free"]
    assert dwarf["hp"] == 10

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["source"] == "https://pf2.ru"
    assert manifest["counts"] == {"ancestries": 33, "classes": 21, "backgrounds": 140}
```

- [ ] **Step 2: Запустить тест — убедиться, что падает**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_build.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.pf2ru.build'`.

- [ ] **Step 3: Реализовать `backend/tools/pf2ru/build.py`**

```python
"""Сборка нормализованного датасета pf2.ru в backend/data.

Источник — три индекс-фикстуры (весь датасет типа в одном <pf2-table>).
Живой рефреш: `uv run python tools/pf2ru_recon.py` (снимет индексы в
tools/_recon_raw/) затем `uv run python -m tools.pf2ru.build --raw tools/_recon_raw`.
"""

import argparse
import json
from pathlib import Path

from tools.pf2ru.normalize import (
    normalize_ancestry,
    normalize_background,
    normalize_class,
)
from tools.pf2ru.table import extract_items

SOURCE = "https://pf2.ru"
SNAPSHOT = "2026-06-28"

_SPECS = (
    ("ancestries", "index_ancestries.html", normalize_ancestry),
    ("classes", "index_classes.html", normalize_class),
    ("backgrounds", "index_backgrounds.html", normalize_background),
)

# Каталоги по умолчанию относительно backend/ (запуск из каталога backend).
_DEFAULT_RAW = Path("tests/fixtures/pf2ru")
_DEFAULT_OUT = Path("data")


def build(raw_dir: Path, out_dir: Path) -> dict[str, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for name, fixture, normalizer in _SPECS:
        items = extract_items((raw_dir / fixture).read_text(encoding="utf-8"))
        records = [normalizer(item) for item in items]
        (out_dir / f"{name}.json").write_text(
            json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        counts[name] = len(records)
    manifest = {"source": SOURCE, "snapshot": SNAPSHOT, "counts": counts}
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Сборка датасета pf2.ru в backend/data.")
    parser.add_argument("--raw", type=Path, default=_DEFAULT_RAW, help="каталог с индекс-HTML")
    parser.add_argument("--out", type=Path, default=_DEFAULT_OUT, help="выходной каталог JSON")
    args = parser.parse_args()
    counts = build(args.raw, args.out)
    print(f"built: {counts} -> {args.out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Запустить тест — убедиться, что проходит**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_build.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Сгенерировать канонический датасет**

Run (из `backend/`): `uv run python -m tools.pf2ru.build`
Expected: вывод `built: {'ancestries': 33, 'classes': 21, 'backgrounds': 140} -> data`; появятся `backend/data/{ancestries,classes,backgrounds,manifest}.json`.

- [ ] **Step 6: Прогнать всю сюиту и линт**

Run (из `backend/`): `uv run pytest -v` → все тесты зелёные, 0 warnings.
Run (из `backend/`): `uv run ruff check .` → `All checks passed!`

- [ ] **Step 7: Коммит (код + сгенерированный датасет)**

```bash
git add backend/tools/pf2ru/build.py backend/tests/test_pf2ru_build.py backend/data
git commit -m "feat(pipeline): сборка датасета pf2.ru в backend/data"
```

---

## Что дальше (после этого плана)

Этот план даёт надёжный, оффлайн-детерминированный датасет из индекс-JSON. **Не покрыто** (требует прозы детальных страниц — хрупко, нужен отдельный план/спайк перед движком `chargen`):

- **Наследия (heritages)** родословных (вкладка `?tab=heritages`).
- **Начальные владения класса** (восприятие, спасброски, атаки, защита, навыки) и **классовые фиты 1 уровня** (секции `<h2 class="h2-header">` в прозе детальной страницы).
- Справочники навыков/трейтов/фитов по ссылкам (`skill/<id>`, `/traits/<slug>`, `/feats/<slug>`), если понадобятся движку.

Следующий план Вехи 1: **извлечение механики 1-го уровня с детальных страниц** (спайк структуры прозы → парсер для ключевых сущностей создания персонажа, с троттлингом обхода), затем **движок `engine/chargen`**.

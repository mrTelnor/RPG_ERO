# Веха 1 — Извлечение структурных данных детальных страниц pf2.ru — План реализации

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Обогатить датасет `backend/data` структурными данными детальных страниц pf2.ru: наследиями родословных и фитами 1-го уровня (родовыми и классовыми).

**Architecture:** Чистые парсеры под `backend/tools/pf2ru/` извлекают из HTML детальной страницы (а) наследия из якорей вкладки `#heritages`, (б) фиты 1 ур. из `<pf2-table itemtype="feats">` (фильтр `level_sort==1`). Троттленый резюмируемый фетчер снимает 54 детальные страницы (33 рода + 21 класс) в сырой каталог; шаг `enrich` мерджит распарсенные данные в `ancestries.json`/`classes.json`. Парсеры и enrich тестируются оффлайн на закоммиченных фикстурах Dwarf/Fighter; полный датасет собирается троттленым обходом. Начальные владения класса (проза) — НЕ в этом плане.

**Tech Stack:** Python 3.12, uv, pytest, ruff, Playwright (только для фетчера, не в тестах). Парсеры — stdlib.

## Global Constraints

- Python 3.12, uv, ruff (target py312, line-length 100, select E/F/I/UP/B), pytest из `backend/`.
- Пакет конвейера — `tools.pf2ru` (`backend/tools/pf2ru/`). Парсеры — только stdlib; Playwright уже в dev-зависимостях (используется фетчером).
- **Никаких сетевых обращений в тестах** — тесты читают закоммиченные фикстуры `backend/tests/fixtures/pf2ru/` (`ancestry_dwarf.html`, `class_fighter.html`).
- Внутренний слаг = `name.lower()` пробелы→дефисы (для фитов); слаг наследия = из фрагмента `#<ancestry>-heritage-<slug>`.
- Фит 1 ур. = `level_sort == 1`. Отсутствующий/`"-"` prerequisites → `None`.
- **Вежливый обход:** фетчер троттлит (пауза ≥1.5 с между страницами), один браузер, последовательно, резюмируемо (пропускать уже снятые файлы). Сырьё — в `backend/tools/_recon_raw/` (git-ignored).
- Имена файлов детальных страниц: `ancestry_<slug>.html`, `class_<slug>.html` (совпадает с уже закоммиченными фикстурами Dwarf/Fighter).
- Обогащённый датасет `backend/data/*.json` коммитится.
- Все коммиты — на ветке этого плана (создаёт контроллер; НЕ `main`).
- Вне охвата: начальные владения класса (проза h2-секций), универсальные родословные (versatile heritages), фиты выше 1 ур. — последующие планы.

## Ground Truth (из закоммиченных фикстур — для ассертов)

- **Dwarf** (`ancestry_dwarf.html`): вкладка `<div ... id="heritages">` содержит 5 якорей `<a class="content-header" href="#dwarf-heritage-<slug>">РусИмя</a>`: `ancient-blooded-dwarf` (Дварф древних кровей), `forge-dwarf` (Дварф кузни), `death-warden-dwarf` (Дварф - страж мёртвых), `strong-blooded-dwarf` (Полнокровный дварф), `rock-dwarf` (Скальный дварф). `<pf2-table itemtype="feats">` = 21 запись, из них `level_sort==1` — 8 (Mountain Strategy, Dwarven Doughtiness, Stonemason's Eye, Dwarven Lore, Unburdened Iron, Dwarven Weapon Familiarity, Rock Runner, Eye for Treasure).
- **Fighter** (`class_fighter.html`): `<pf2-table itemtype="feats">` = 96 записей, `level_sort==1` — 8 (вкл. Sudden Charge, Double Slice, Exacting Strike, Combat Assessment, Reactive Shield, Vicious Swing). Есть вторая `<pf2-table itemtype="spells">` с 0 записей. Поле `prerequisites` бывает `"-"` (нет пререквизитов). Ключи записи фита: `name`, `rus_name`, `level`, `level_sort`, `traits`, `prerequisites`, `id`, ...

---

### Task 1: Выбор `<pf2-table>` по `itemtype`

**Files:**
- Modify: `backend/tools/pf2ru/table.py`
- Test: `backend/tests/test_pf2ru_table.py` (дополнить)

**Interfaces:**
- Consumes: ничего нового.
- Produces: `tools.pf2ru.table.extract_items_by_itemtype(html_text: str, itemtype: str) -> list[dict]` — возвращает `items` первой `<pf2-table>` с данным `itemtype`; `ValueError`, если такой нет.

- [ ] **Step 1: Дописать падающие тесты в `backend/tests/test_pf2ru_table.py`**

Добавить в конец файла:

```python
from tools.pf2ru.table import extract_items_by_itemtype


def test_extract_by_itemtype_feats_counts():
    dwarf = _read("ancestry_dwarf.html")
    fighter = _read("class_fighter.html")
    assert len(extract_items_by_itemtype(dwarf, "feats")) == 21
    assert len(extract_items_by_itemtype(fighter, "feats")) == 96


def test_extract_by_itemtype_empty_spells_table():
    fighter = _read("class_fighter.html")
    assert extract_items_by_itemtype(fighter, "spells") == []


def test_extract_by_itemtype_absent_raises():
    import pytest

    with pytest.raises(ValueError):
        extract_items_by_itemtype("<html></html>", "feats")
```

- [ ] **Step 2: Запустить тест — убедиться, что падает**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_table.py -k itemtype -v`
Expected: FAIL — `ImportError: cannot import name 'extract_items_by_itemtype'`.

- [ ] **Step 3: Реализовать в `backend/tools/pf2ru/table.py`**

Добавить (рядом с существующим `extract_items`):

```python
_PF2_TABLE_TAG = re.compile(r"<pf2-table\b([^>]*)>", re.DOTALL)
_TABLE_ITEMS = re.compile(r'\bitems="(.*?)"', re.DOTALL)
_TABLE_ITEMTYPE = re.compile(r'\bitemtype="([^"]*)"')


def extract_items_by_itemtype(html_text: str, itemtype: str) -> list[dict]:
    """items первой <pf2-table> с заданным itemtype (на детальных страницах
    их несколько, напр. feats и spells). ValueError, если такой таблицы нет."""
    for tag in _PF2_TABLE_TAG.finditer(html_text):
        attrs = tag.group(1)
        type_match = _TABLE_ITEMTYPE.search(attrs)
        if not type_match or type_match.group(1) != itemtype:
            continue
        items_match = _TABLE_ITEMS.search(attrs)
        if items_match:
            return json.loads(html.unescape(items_match.group(1)))
    raise ValueError(f'no <pf2-table itemtype="{itemtype}"> with items found')
```

- [ ] **Step 4: Запустить тест — убедиться, что проходит**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_table.py -v`
Expected: PASS (все тесты файла, включая новые 3).

- [ ] **Step 5: Линт и коммит**

Run (из `backend/`): `uv run ruff check .` → `All checks passed!`

```bash
git add backend/tools/pf2ru/table.py backend/tests/test_pf2ru_table.py
git commit -m "feat(detail): выбор pf2-table по itemtype"
```

---

### Task 2: Парсеры наследий и фитов 1-го уровня

**Files:**
- Create: `backend/tools/pf2ru/detail.py`
- Test: `backend/tests/test_pf2ru_detail.py`

**Interfaces:**
- Consumes: `extract_items_by_itemtype` (Task 1); `slugify`, `extract_trait_slugs` (`tools.pf2ru.links`).
- Produces:
  - `tools.pf2ru.detail.parse_heritages(html_text: str, ancestry_slug: str) -> list[dict]` — наследия конкретной родословной из якорей вкладки `#heritages`. Каждое: `{slug, name_en, name_ru}`.
  - `tools.pf2ru.detail.level1_feats(feat_records: list[dict]) -> list[dict]` — из записей `<pf2-table itemtype="feats">` берёт `level_sort==1`. Каждое: `{slug, name_en, name_ru, traits (list[str]), prerequisites (str|None), pf2ru_id}`.

- [ ] **Step 1: Написать падающий тест `backend/tests/test_pf2ru_detail.py`**

```python
from pathlib import Path

from tools.pf2ru.detail import level1_feats, parse_heritages
from tools.pf2ru.table import extract_items_by_itemtype

FIXTURES = Path(__file__).parent / "fixtures" / "pf2ru"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_heritages_dwarf():
    result = parse_heritages(_read("ancestry_dwarf.html"), "dwarf")
    slugs = [h["slug"] for h in result]
    assert slugs == [
        "ancient-blooded-dwarf",
        "forge-dwarf",
        "death-warden-dwarf",
        "strong-blooded-dwarf",
        "rock-dwarf",
    ]
    ancient = result[0]
    assert ancient["name_en"] == "Ancient Blooded Dwarf"
    assert ancient["name_ru"] == "Дварф древних кровей"


def test_level1_feats_dwarf_ancestry():
    feats = extract_items_by_itemtype(_read("ancestry_dwarf.html"), "feats")
    l1 = level1_feats(feats)
    assert len(l1) == 8
    names = {f["name_en"] for f in l1}
    assert "Dwarven Lore" in names and "Rock Runner" in names
    lore = next(f for f in l1 if f["name_en"] == "Dwarven Lore")
    assert lore["slug"] == "dwarven-lore"
    assert isinstance(lore["traits"], list)
    assert lore["pf2ru_id"] is not None


def test_level1_feats_fighter_class():
    feats = extract_items_by_itemtype(_read("class_fighter.html"), "feats")
    l1 = level1_feats(feats)
    assert len(l1) == 8
    sudden = next(f for f in l1 if f["name_en"] == "Sudden Charge")
    assert sudden["slug"] == "sudden-charge"
    assert sudden["name_ru"] == "Внезапный натиск"
    assert sudden["prerequisites"] is None  # исходное "-" → None


def test_level1_feats_empty():
    assert level1_feats([]) == []
```

- [ ] **Step 2: Запустить тест — убедиться, что падает**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_detail.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.pf2ru.detail'`.

- [ ] **Step 3: Реализовать `backend/tools/pf2ru/detail.py`**

```python
"""Парсеры структурных данных детальной страницы pf2.ru: наследия и фиты 1 ур."""

import re

from tools.pf2ru.links import extract_trait_slugs, slugify


def parse_heritages(html_text: str, ancestry_slug: str) -> list[dict]:
    """Наследия родословной из якорей вкладки #heritages
    (<a class="content-header" href="#<ancestry>-heritage-<slug>">РусИмя</a>)."""
    pattern = re.compile(
        r'<a class="content-header" href="#'
        + re.escape(ancestry_slug)
        + r'-heritage-([a-z0-9-]+)">\s*(.*?)\s*</a>',
        re.DOTALL,
    )
    result = []
    for slug, name_html in pattern.findall(html_text):
        name_ru = re.sub(r"<[^>]+>", "", name_html).strip()
        result.append(
            {
                "slug": slug,
                "name_en": slug.replace("-", " ").title(),
                "name_ru": name_ru,
            }
        )
    return result


def level1_feats(feat_records: list[dict]) -> list[dict]:
    """Из записей <pf2-table itemtype='feats'> — фиты 1 уровня (level_sort==1)."""
    result = []
    for raw in feat_records:
        if raw.get("level_sort") != 1:
            continue
        prereq = raw.get("prerequisites")
        prereq = None if (not prereq or prereq.strip() == "-") else prereq.strip()
        result.append(
            {
                "slug": slugify(raw["name"]),
                "name_en": raw["name"],
                "name_ru": raw.get("rus_name"),
                "traits": extract_trait_slugs(raw.get("traits", "")),
                "prerequisites": prereq,
                "pf2ru_id": raw.get("id"),
            }
        )
    return result
```

- [ ] **Step 4: Запустить тест — убедиться, что проходит**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_detail.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Линт и коммит**

Run (из `backend/`): `uv run ruff check .` → `All checks passed!`

```bash
git add backend/tools/pf2ru/detail.py backend/tests/test_pf2ru_detail.py
git commit -m "feat(detail): парсеры наследий и фитов 1 уровня"
```

---

### Task 3: Построитель списка целей обхода детальных страниц

**Files:**
- Create: `backend/tools/pf2ru/detail_fetch.py`
- Test: `backend/tests/test_pf2ru_detail_fetch.py`

**Interfaces:**
- Produces:
  - `tools.pf2ru.detail_fetch.detail_targets(data_dir: Path) -> list[tuple[str, str]]` — по `ancestries.json`/`classes.json` строит список `(url, filename)`: `("https://pf2.ru/ancestries/<slug>", "ancestry_<slug>.html")` и `(".../classes/<slug>", "class_<slug>.html")`. URL-слаг с пробелами URL-кодируется.
  - `tools.pf2ru.detail_fetch.fetch_all(data_dir: Path, raw_dir: Path, delay_s: float = 1.5) -> dict` — троттленый резюмируемый обход (пропускает уже снятые файлы). Использует Playwright. **Не покрывается тестами** (сеть).

- [ ] **Step 1: Написать падающий тест `backend/tests/test_pf2ru_detail_fetch.py`** (тестируем только чистый `detail_targets`)

```python
import json
from pathlib import Path

from tools.pf2ru.detail_fetch import detail_targets


def test_detail_targets_builds_urls_and_filenames(tmp_path):
    (tmp_path / "ancestries.json").write_text(
        json.dumps([{"slug": "dwarf"}, {"slug": "half-elf"}]), encoding="utf-8"
    )
    (tmp_path / "classes.json").write_text(
        json.dumps([{"slug": "fighter"}]), encoding="utf-8"
    )
    targets = detail_targets(tmp_path)
    assert ("https://pf2.ru/ancestries/dwarf", "ancestry_dwarf.html") in targets
    assert ("https://pf2.ru/ancestries/half-elf", "ancestry_half-elf.html") in targets
    assert ("https://pf2.ru/classes/fighter", "class_fighter.html") in targets
    assert len(targets) == 3
```

- [ ] **Step 2: Запустить тест — убедиться, что падает**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_detail_fetch.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.pf2ru.detail_fetch'`.

- [ ] **Step 3: Реализовать `backend/tools/pf2ru/detail_fetch.py`**

```python
"""Троттленый резюмируемый обход детальных страниц pf2.ru.

Запуск: uv run python -m tools.pf2ru.detail_fetch
Снимает ancestries/classes detail-страницы в tools/_recon_raw/ (git-ignored),
по одной, с паузой, пропуская уже снятые файлы. Затем используйте enrich.
"""

import argparse
import json
import urllib.parse
from pathlib import Path

BASE = "https://pf2.ru"
_DEFAULT_DATA = Path("data")
_DEFAULT_RAW = Path("tools/_recon_raw")


def detail_targets(data_dir: Path) -> list[tuple[str, str]]:
    """Список (url, filename) детальных страниц по датасету."""
    targets: list[tuple[str, str]] = []
    for kind, plural in (("ancestry", "ancestries"), ("class", "classes")):
        records = json.loads((data_dir / f"{plural}.json").read_text(encoding="utf-8"))
        for record in records:
            slug = record["slug"]
            url = f"{BASE}/{plural}/{urllib.parse.quote(slug)}"
            targets.append((url, f"{kind}_{slug}.html"))
    return targets


def fetch_all(data_dir: Path, raw_dir: Path, delay_s: float = 1.5) -> dict:
    """Вежливый последовательный обход; пропускает уже снятые файлы."""
    from playwright.sync_api import sync_playwright

    raw_dir.mkdir(parents=True, exist_ok=True)
    targets = detail_targets(data_dir)
    fetched, skipped = 0, 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        for url, filename in targets:
            out = raw_dir / filename
            if out.exists():
                skipped += 1
                continue
            page.goto(url, wait_until="networkidle", timeout=60_000)
            page.wait_for_timeout(int(delay_s * 1000))
            out.write_text(page.content(), encoding="utf-8")
            fetched += 1
            print(f"  fetched {filename} ({fetched}/{len(targets)})")
        browser.close()
    return {"fetched": fetched, "skipped": skipped, "total": len(targets)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Обход детальных страниц pf2.ru.")
    parser.add_argument("--data", type=Path, default=_DEFAULT_DATA)
    parser.add_argument("--raw", type=Path, default=_DEFAULT_RAW)
    parser.add_argument("--delay", type=float, default=1.5)
    args = parser.parse_args()
    print(fetch_all(args.data, args.raw, args.delay))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Запустить тест — убедиться, что проходит**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_detail_fetch.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Линт и коммит**

Run (из `backend/`): `uv run ruff check .` → `All checks passed!`

```bash
git add backend/tools/pf2ru/detail_fetch.py backend/tests/test_pf2ru_detail_fetch.py
git commit -m "feat(detail): троттленый резюмируемый фетчер детальных страниц"
```

---

### Task 4: Обогащение датасета (`enrich`)

**Files:**
- Create: `backend/tools/pf2ru/enrich.py`
- Test: `backend/tests/test_pf2ru_enrich.py`

**Interfaces:**
- Consumes: `extract_items_by_itemtype` (Task 1); `parse_heritages`, `level1_feats` (Task 2).
- Produces: `tools.pf2ru.enrich.enrich(data_dir: Path, detail_dir: Path) -> dict` — для каждой записи `ancestries.json`/`classes.json`, у которой в `detail_dir` есть файл `ancestry_<slug>.html` / `class_<slug>.html`, добавляет: родословным — `heritages` и `ancestry_feats_l1`; классам — `class_feats_l1`. Перезаписывает JSON на месте. Записи без детального файла пропускаются (их новые ключи не появляются). Возвращает `{"ancestries_enriched": n, "classes_enriched": n, "skipped": [...]}`.

- [ ] **Step 1: Написать падающий тест `backend/tests/test_pf2ru_enrich.py`**

```python
import json
from pathlib import Path

from tools.pf2ru.enrich import enrich

FIXTURES = Path(__file__).parent / "fixtures" / "pf2ru"


def test_enrich_dwarf_and_fighter(tmp_path):
    # Мини-датасет: одна родословная (dwarf) + один класс (fighter) + «пустышка».
    (tmp_path / "ancestries.json").write_text(
        json.dumps([{"slug": "dwarf", "name_en": "Dwarf"}, {"slug": "elf", "name_en": "Elf"}]),
        encoding="utf-8",
    )
    (tmp_path / "classes.json").write_text(
        json.dumps([{"slug": "fighter", "name_en": "Fighter"}]), encoding="utf-8"
    )

    summary = enrich(tmp_path, FIXTURES)

    ancestries = json.loads((tmp_path / "ancestries.json").read_text(encoding="utf-8"))
    dwarf = next(a for a in ancestries if a["slug"] == "dwarf")
    assert [h["slug"] for h in dwarf["heritages"]] == [
        "ancient-blooded-dwarf",
        "forge-dwarf",
        "death-warden-dwarf",
        "strong-blooded-dwarf",
        "rock-dwarf",
    ]
    assert len(dwarf["ancestry_feats_l1"]) == 8

    # Нет детального файла для elf → не обогащается.
    elf = next(a for a in ancestries if a["slug"] == "elf")
    assert "heritages" not in elf
    assert "elf" in summary["skipped"]

    classes = json.loads((tmp_path / "classes.json").read_text(encoding="utf-8"))
    fighter = next(c for c in classes if c["slug"] == "fighter")
    assert len(fighter["class_feats_l1"]) == 8

    assert summary["ancestries_enriched"] == 1
    assert summary["classes_enriched"] == 1
```

- [ ] **Step 2: Запустить тест — убедиться, что падает**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_enrich.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.pf2ru.enrich'`.

- [ ] **Step 3: Реализовать `backend/tools/pf2ru/enrich.py`**

```python
"""Обогащение датасета backend/data структурными данными детальных страниц."""

import json
from pathlib import Path

from tools.pf2ru.detail import level1_feats, parse_heritages
from tools.pf2ru.table import extract_items_by_itemtype


def _load(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump(path: Path, data: list[dict]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def enrich(data_dir: Path, detail_dir: Path) -> dict:
    skipped: list[str] = []

    ancestries = _load(data_dir / "ancestries.json")
    ancestries_enriched = 0
    for record in ancestries:
        detail = detail_dir / f"ancestry_{record['slug']}.html"
        if not detail.exists():
            skipped.append(record["slug"])
            continue
        html_text = detail.read_text(encoding="utf-8")
        record["heritages"] = parse_heritages(html_text, record["slug"])
        record["ancestry_feats_l1"] = level1_feats(
            extract_items_by_itemtype(html_text, "feats")
        )
        ancestries_enriched += 1
    _dump(data_dir / "ancestries.json", ancestries)

    classes = _load(data_dir / "classes.json")
    classes_enriched = 0
    for record in classes:
        detail = detail_dir / f"class_{record['slug']}.html"
        if not detail.exists():
            skipped.append(record["slug"])
            continue
        html_text = detail.read_text(encoding="utf-8")
        record["class_feats_l1"] = level1_feats(
            extract_items_by_itemtype(html_text, "feats")
        )
        classes_enriched += 1
    _dump(data_dir / "classes.json", classes)

    return {
        "ancestries_enriched": ancestries_enriched,
        "classes_enriched": classes_enriched,
        "skipped": skipped,
    }
```

- [ ] **Step 4: Запустить тест — убедиться, что проходит**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_enrich.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Линт и коммит**

Run (из `backend/`): `uv run ruff check .` → `All checks passed!`

```bash
git add backend/tools/pf2ru/enrich.py backend/tests/test_pf2ru_enrich.py
git commit -m "feat(detail): обогащение датасета наследиями и фитами 1 ур."
```

---

### Task 5: Полный обход + обогащённый датасет

> Эта задача делает реальный троттленый обход ~54 детальных страниц pf2.ru и коммитит обогащённый датасет. Обход вежливый, последовательный, резюмируемый (повторный запуск дочёрпывает недостающее). Если гейт начнёт отбивать — остановиться, не долбить; перезапуск продолжит с места.

**Files:**
- Modify (перегенерируются): `backend/data/ancestries.json`, `backend/data/classes.json`
- Modify: `backend/data/manifest.json` (добавить признак обогащения)

**Interfaces:**
- Consumes: `fetch_all` (Task 3), `enrich` (Task 4).

- [ ] **Step 1: Снять детальные страницы (троттленый обход)**

Run (из `backend/`): `uv run python -m tools.pf2ru.detail_fetch`
Expected: вывод вида `{'fetched': N, 'skipped': M, 'total': 54}`; в `tools/_recon_raw/` появятся `ancestry_<slug>.html` (33) и `class_<slug>.html` (21). `ancestry_dwarf.html`/`class_fighter.html` могут уже присутствовать (пропустятся). Если обход прервался — просто запусти команду повторно (дочёрпает остаток).

- [ ] **Step 2: Проверить полноту снимков**

Run (из `backend/`):
```bash
uv run python -c "import json,glob; from pathlib import Path; a=len(json.load(open('data/ancestries.json'))); c=len(json.load(open('data/classes.json'))); ah=len(glob.glob('tools/_recon_raw/ancestry_*.html')); ch=len(glob.glob('tools/_recon_raw/class_*.html')); print('ancestry html', ah, 'of', a, '| class html', ch, 'of', c)"
```
Expected: число снятых `ancestry_*` = числу родословных (33), `class_*` = числу классов (21). Если меньше — повторить Step 1.

- [ ] **Step 3: Обогатить датасет из снятых страниц**

Run (из `backend/`): `uv run python -c "from pathlib import Path; from tools.pf2ru.enrich import enrich; print(enrich(Path('data'), Path('tools/_recon_raw')))"`
Expected: `{'ancestries_enriched': 33, 'classes_enriched': 21, 'skipped': []}`.

- [ ] **Step 4: Пометить датасет как обогащённый в manifest**

Отредактировать `backend/data/manifest.json`: добавить ключ `"enriched": ["heritages", "ancestry_feats_l1", "class_feats_l1"]` в объект верхнего уровня (рядом с `source`, `snapshot`, `counts`). Сохранить.

- [ ] **Step 5: Прогнать всю сюиту и линт**

Run (из `backend/`): `uv run pytest -q` → все тесты зелёные, 0 warnings (тесты не зависят от обхода — читают фикстуры).
Run (из `backend/`): `uv run ruff check .` → `All checks passed!`

- [ ] **Step 6: Санити-проверка обогащённых данных**

Run (из `backend/`):
```bash
uv run python -c "import json; a=json.load(open('data/ancestries.json',encoding='utf-8')); c=json.load(open('data/classes.json',encoding='utf-8')); print('ancestries with heritages key:', sum('heritages' in x for x in a), '/', len(a)); print('classes with class_feats_l1:', sum('class_feats_l1' in x for x in c), '/', len(c)); d=next(x for x in a if x['slug']=='dwarf'); print('dwarf heritages:', len(d['heritages']), 'feats_l1:', len(d['ancestry_feats_l1']))"
```
Expected: все родословные имеют ключ `heritages`, все классы — `class_feats_l1`; dwarf: 5 наследий, 8 фитов 1 ур.

- [ ] **Step 7: Коммит обогащённого датасета**

```bash
git add backend/data/ancestries.json backend/data/classes.json backend/data/manifest.json
git commit -m "data(detail): обогащённый датасет — наследия и фиты 1 уровня"
```

---

## Что дальше (после этого плана)

- **Начальные владения класса** (восприятие, спасброски, атаки, защита, число обученных навыков, классовая СЛ) — лежат в прозе h2-секций детальной страницы («Начальные умения», «Испытания», «Навыки», «Атака», «Защита», «Классовая СЛ»). Отдельный план: спайк структуры прозы → парсер или ручная курация для классов MVP.
- **Универсальные родословные** (versatile heritages) и фиты выше 1 ур. — по мере надобности движка.
- Затем — **движок `engine/chargen`** (создание персонажа 1 ур. по книге) на собранном датасете.

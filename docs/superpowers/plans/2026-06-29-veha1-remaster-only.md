# Веха 1 — Только Remaster: отсев Legacy-контента — План реализации

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Привести датасет `backend/data` к редакции **только Remaster**, отсеяв Legacy-сущности и Legacy-фиты, как требует дизайн (§1).

**Architecture:** pf2.ru помечает Legacy-контент полем `is_legacy` в индекс-JSON (родословные, предыстории, фиты). Фильтруем по нему: в `level1_feats` исключаем legacy-фиты; в `build` отбрасываем legacy-родословные и legacy-предыстории. Классы фильтра не имеют (индекс отдаёт дефолтные Remaster-версии; legacy-вариант доступен лишь через `?legacy=true`, который мы не запрашиваем) — оставляем все 21. Затем пересобираем датасет оффлайн из уже снятого `backend/tools/_recon_raw/` (без повторного обхода) и помечаем редакцию в manifest.

**Tech Stack:** Python 3.12, uv, pytest, ruff. Только stdlib.

## Global Constraints

- Python 3.12, uv, ruff (target py312, line-length 100, select E/F/I/UP/B), pytest из `backend/`.
- Пакет конвейера — `tools.pf2ru`. Только stdlib. **Никаких сетевых обращений в тестах** (фикстуры).
- **Редакция: только Remaster.** Дискриминатор — `is_legacy` (pf2.ru) для родословных/предысторий/фитов. Классы — фильтра нет, оставляем все (дефолтный индекс = Remaster).
- Сборка остаётся детерминированной и оффлайн (источник — `backend/tests/fixtures/pf2ru/` для тестов; `backend/tools/_recon_raw/` для полной пересборки).
- Обогащённый датасет `backend/data/*.json` коммитится.
- Все коммиты — на ветке этого плана (создаёт контроллер; НЕ `main`).

## Ground Truth (из фикстур — для ассертов)

- Индекс-родословные: 33 всего, **4 `is_legacy=True`** (Kitsune, Poppet, Nagaji, Sprite) → после отсева **29**.
- Индекс-предыстории: 140 всего, **18 `is_legacy=True`** → после отсева **122**.
- Индекс-классы: 21, ключа `is_legacy` нет → **остаётся 21**.
- Dwarf, фиты 1 ур.: 8 всего, **1 legacy** («Eye for Treasure»), 7 Remaster → после отсева **7**.
- Fighter, фиты 1 ур.: 8, **0 legacy** → остаётся **8**.
- Записи фитов в `<pf2-table itemtype="feats">` содержат ключ `is_legacy` (булев).

---

### Task 1: `level1_feats` отсевает Legacy-фиты

**Files:**
- Modify: `backend/tools/pf2ru/detail.py`
- Test: `backend/tests/test_pf2ru_detail.py` (обновить ожидания)
- Test: `backend/tests/test_pf2ru_enrich.py` (обновить ожидание dwarf-фитов)

**Interfaces:**
- Consumes: ничего нового.
- Produces: `level1_feats(feat_records)` теперь возвращает только фиты с `level_sort==1` **и** `is_legacy` ложным/отсутствующим.

- [ ] **Step 1: Обновить тесты под Remaster-only**

В `backend/tests/test_pf2ru_detail.py`, в `test_level1_feats_dwarf_ancestry`, заменить ассерты количества/наличия на Remaster-набор (7 фитов, без «Eye for Treasure»):

```python
def test_level1_feats_dwarf_ancestry():
    feats = extract_items_by_itemtype(_read("ancestry_dwarf.html"), "feats")
    l1 = level1_feats(feats)
    assert len(l1) == 7  # 8 на 1 ур. минус 1 legacy («Eye for Treasure»)
    names = {f["name_en"] for f in l1}
    assert "Dwarven Lore" in names and "Rock Runner" in names
    assert "Eye for Treasure" not in names  # legacy отсеян
    lore = next(f for f in l1 if f["name_en"] == "Dwarven Lore")
    assert lore["slug"] == "dwarven-lore"
    assert isinstance(lore["traits"], list)
    assert "prerequisites" in lore
    assert lore["pf2ru_id"] is not None
```

В `backend/tests/test_pf2ru_enrich.py`, в `test_enrich_dwarf_and_fighter`, заменить ожидание количества фитов dwarf:

```python
    assert len(dwarf["ancestry_feats_l1"]) == 7  # Remaster-only (legacy отсеян)
```

(Ассерт `len(fighter["class_feats_l1"]) == 8` оставить без изменений — у воина legacy-фитов 1 ур. нет.)

- [ ] **Step 2: Запустить тесты — убедиться, что падают**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_detail.py::test_level1_feats_dwarf_ancestry tests/test_pf2ru_enrich.py -v`
Expected: FAIL — текущий `level1_feats` возвращает 8 фитов dwarf (legacy ещё не отсеян), ассерт `== 7` падает.

- [ ] **Step 3: Добавить фильтр legacy в `level1_feats`**

В `backend/tools/pf2ru/detail.py`, в цикле `level1_feats`, добавить отсев legacy сразу после проверки уровня:

```python
def level1_feats(feat_records: list[dict]) -> list[dict]:
    """Из записей <pf2-table itemtype='feats'> — фиты 1 уровня (level_sort==1),
    только редакции Remaster (is_legacy ложно/отсутствует)."""
    result = []
    for raw in feat_records:
        if raw.get("level_sort") != 1:
            continue
        if raw.get("is_legacy"):
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

- [ ] **Step 4: Запустить тесты — убедиться, что проходят**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_detail.py tests/test_pf2ru_enrich.py -v`
Expected: PASS (dwarf L1 = 7, fighter = 8).

- [ ] **Step 5: Прогон всей сюиты, линт, коммит**

Run (из `backend/`): `uv run pytest -q` → зелёная; `uv run ruff check .` → `All checks passed!`

```bash
git add backend/tools/pf2ru/detail.py backend/tests/test_pf2ru_detail.py backend/tests/test_pf2ru_enrich.py
git commit -m "feat(remaster): level1_feats отсевает legacy-фиты"
```

---

### Task 2: `build` отсевает Legacy-родословные и -предыстории + редакция в manifest

**Files:**
- Modify: `backend/tools/pf2ru/build.py`
- Test: `backend/tests/test_pf2ru_build.py` (обновить ожидания)

**Interfaces:**
- Consumes: `extract_items`, нормализаторы (как раньше).
- Produces: `build(raw_dir, out_dir, snapshot=SNAPSHOT)` теперь отбрасывает `is_legacy`-записи для ancestries и backgrounds (classes — без фильтра); manifest содержит `"edition": "remaster"`. Возвращаемые counts отражают отсев (29/21/122 на полном датасете).

- [ ] **Step 1: Обновить тест сборки под Remaster-only**

В `backend/tests/test_pf2ru_build.py`, в `test_build_writes_dataset`, заменить ожидаемые counts и добавить проверку отсева legacy:

```python
def test_build_writes_dataset(tmp_path):
    counts = build(FIXTURES, tmp_path)
    assert counts == {"ancestries": 29, "classes": 21, "backgrounds": 122}

    for name in ("ancestries", "classes", "backgrounds", "manifest"):
        assert (tmp_path / f"{name}.json").exists()

    ancestries = json.loads((tmp_path / "ancestries.json").read_text(encoding="utf-8"))
    slugs = {a["slug"] for a in ancestries}
    assert "dwarf" in slugs            # Remaster — присутствует
    assert "kitsune" not in slugs      # legacy — отсеян
    dwarf = next(a for a in ancestries if a["slug"] == "dwarf")
    assert dwarf["ability_boosts"] == ["Constitution", "Wisdom", "Free"]
    assert dwarf["hp"] == 10

    backgrounds = json.loads((tmp_path / "backgrounds.json").read_text(encoding="utf-8"))
    assert not any(b.get("is_legacy") for b in backgrounds)  # ни одной legacy-предыстории

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["source"] == "https://pf2.ru"
    assert manifest["edition"] == "remaster"
    assert manifest["counts"] == {"ancestries": 29, "classes": 21, "backgrounds": 122}
```

- [ ] **Step 2: Запустить тест — убедиться, что падает**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_build.py -v`
Expected: FAIL — текущий build даёт 33/140 и нет `edition` в manifest.

- [ ] **Step 3: Добавить фильтр legacy и редакцию в `build.py`**

В `backend/tools/pf2ru/build.py`:

Добавить флаг отсева в `_SPECS` (4-й элемент кортежа) и константу редакции:

```python
EDITION = "remaster"

# (name, fixture, normalizer, drop_legacy)
_SPECS = (
    ("ancestries", "index_ancestries.html", normalize_ancestry, True),
    ("classes", "index_classes.html", normalize_class, False),
    ("backgrounds", "index_backgrounds.html", normalize_background, True),
)
```

Обновить тело цикла и manifest в `build`:

```python
def build(raw_dir: Path, out_dir: Path, snapshot: str = SNAPSHOT) -> dict[str, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for name, fixture, normalizer, drop_legacy in _SPECS:
        items = extract_items((raw_dir / fixture).read_text(encoding="utf-8"))
        if drop_legacy:
            items = [item for item in items if not item.get("is_legacy")]
        records = [normalizer(item) for item in items]
        (out_dir / f"{name}.json").write_text(
            json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        counts[name] = len(records)
    manifest = {"source": SOURCE, "edition": EDITION, "snapshot": snapshot, "counts": counts}
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return counts
```

- [ ] **Step 4: Запустить тест — убедиться, что проходит**

Run (из `backend/`): `uv run pytest tests/test_pf2ru_build.py -v`
Expected: PASS (counts 29/21/122, manifest edition remaster, kitsune отсеян).

- [ ] **Step 5: Прогон всей сюиты, линт, коммит**

Run (из `backend/`): `uv run pytest -q` → зелёная; `uv run ruff check .` → `All checks passed!`

```bash
git add backend/tools/pf2ru/build.py backend/tests/test_pf2ru_build.py
git commit -m "feat(remaster): build отсевает legacy-родословные/предыстории + edition в manifest"
```

---

### Task 3: Пересборка Remaster-only датасета

> Пересборка оффлайн из уже снятого `backend/tools/_recon_raw/` (33 ancestry + 21 class detail-страницы там есть с предыдущего плана). Повторный обход НЕ нужен. Если `_recon_raw` пуст (свежий клон) — сначала `uv run python -m tools.pf2ru.detail_fetch`, затем продолжить.

**Files:**
- Modify (перегенерируются): `backend/data/ancestries.json`, `backend/data/classes.json`, `backend/data/backgrounds.json`, `backend/data/manifest.json`

**Interfaces:**
- Consumes: `build` (Task 2), `enrich` (существующий).

- [ ] **Step 1: Пересобрать индекс-датасет (с отсевом legacy)**

Run (из `backend/`): `uv run python -m tools.pf2ru.build`
Expected: `built: {'ancestries': 29, 'classes': 21, 'backgrounds': 122} -> data`.

- [ ] **Step 2: Проверить наличие detail-снимков для пересборки enrich**

Run (из `backend/`):
```bash
uv run python -c "import glob; print('ancestry html', len(glob.glob('tools/_recon_raw/ancestry_*.html')), '| class html', len(glob.glob('tools/_recon_raw/class_*.html')))"
```
Expected: ancestry html ≥ 29, class html ≥ 21 (с предыдущего обхода там 33 и 21 — лишние legacy-страницы безвредны, enrich их просто не тронет). Если меньше — выполнить `uv run python -m tools.pf2ru.detail_fetch` (резюмируемо) и повторить.

- [ ] **Step 3: Обогатить (наследия + Remaster-фиты 1 ур.)**

Run (из `backend/`): `uv run python -c "from pathlib import Path; from tools.pf2ru.enrich import enrich; print(enrich(Path('data'), Path('tools/_recon_raw')))"`
Expected: `{'ancestries_enriched': 29, 'classes_enriched': 21, 'skipped': []}`.

- [ ] **Step 4: Прогон всей сюиты и линт**

Run (из `backend/`): `uv run pytest -q` → все тесты зелёные, 0 warnings.
Run (из `backend/`): `uv run ruff check .` → `All checks passed!`

- [ ] **Step 5: Санити-проверка Remaster-only датасета**

Run (из `backend/`):
```bash
uv run python -c "import json; a=json.load(open('data/ancestries.json',encoding='utf-8')); c=json.load(open('data/classes.json',encoding='utf-8')); b=json.load(open('data/backgrounds.json',encoding='utf-8')); m=json.load(open('data/manifest.json',encoding='utf-8')); print('counts', len(a), len(c), len(b), '| edition', m.get('edition')); print('any legacy ancestry:', any(x.get('is_legacy') for x in a), '| any legacy background:', any(x.get('is_legacy') for x in b)); d=next(x for x in a if x['slug']=='dwarf'); print('dwarf heritages', len(d['heritages']), 'feats_l1', len(d['ancestry_feats_l1'])); print('kitsune present:', any(x['slug']=='kitsune' for x in a))"
```
Expected: `counts 29 21 122 | edition remaster`; `any legacy ancestry: False | any legacy background: False`; `dwarf heritages 5 feats_l1 7`; `kitsune present: False`.

- [ ] **Step 6: Коммит Remaster-only датасета**

```bash
git add backend/data/ancestries.json backend/data/classes.json backend/data/backgrounds.json backend/data/manifest.json
git commit -m "data(remaster): пересборка датасета только в редакции Remaster"
```

---

## Что дальше (после этого плана)

- **Известное ограничение:** наследия (heritages) извлекаются из дефолтной (Remaster) detail-страницы и не имеют per-record `is_legacy`; считаем их Remaster по факту источника. Классы оставлены все 21 (индекс = дефолтные Remaster-версии). Если позже обнаружится legacy-класс в индексе — вернуться к эвристике по `source`.
- **Начальные владения класса** (проза h2-секций) — следующий план (спайк прозы → парсер).
- Затем — движок `engine/chargen` на Remaster-only датасете.

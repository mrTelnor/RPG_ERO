# pf2.ru — выводы разведки данных

**Дата снимка:** 2026-06-28
**Метод:** headless Playwright Chromium 1.60.0 (Chrome for Testing 148), скрипт `backend/tools/pf2ru_recon.py`.
**Сырьё:** `backend/tools/_recon_raw/` (git-ignored). Зафиксированные фикстуры: `backend/tests/fixtures/pf2ru/`.

---

## 1. Прохождение JS-гейта

**Гейт ПРОЙДЕН headless-браузером без специальных ухищрений.** Достаточно стандартного
`playwright.chromium.launch(headless=True)` + `page.goto(url, wait_until="networkidle")` +
повторный `wait_for_load_state("networkidle")`. **Не понадобились** ни `playwright-stealth`, ни
подменённый user-agent, ни не-headless режим. Все страницы вернули содержательный HTML, флаг
`заблокировано` (`"Проверка безопасности" in html or "Подождите" in html`) = `False` на всех 6 запросах.

Размеры снятого HTML (символы Python `len(page.content())`):

| Страница | URL | Размер | Заблокировано |
|---|---|---|---|
| index_ancestries | `/ancestries` | 422 109 | False |
| index_classes | `/classes` | 323 570 | False |
| index_backgrounds | `/backgrounds` | 964 191 | False |
| ancestry_dwarf | `/ancestries/dwarf` | 273 367 | False |
| class_fighter | `/classes/fighter` | 637 312 | False |
| background_acolyte | `/backgrounds/acolyte` | 146 903 | False |

Замечание: первый запрос к домену иногда отрабатывает дольше (прохождение JS-проверки
Cloudflare-подобного гейта), но `networkidle`-ожидание это покрывает. Гейт устойчиво проходится
при вежливом доступе (одна страница за раз, без retry-циклов).

---

## 2. URL-паттерны

Чистые, предсказуемые слаги на основе **английских** имён сущностей:

- Список: `https://pf2.ru/ancestries`, `/classes`, `/backgrounds` (мн. число).
- Сущность: `https://pf2.ru/ancestries/<slug>`, `/classes/<slug>`, `/backgrounds/<slug>`.
  - Примеры реальных слагов: `/ancestries/dwarf`, `/ancestries/gnome`, `/ancestries/goblin`,
    `/classes/fighter`, `/classes/wizard`, `/classes/alchemist`, `/backgrounds/acolyte`,
    `/backgrounds/criminal`, `/backgrounds/scout`.
  - Слаг = lowercase английское имя. Многословные слаги встречаются с пробелом в href
    (напр. `/backgrounds/group impression`, `/feats/group impression`) — при выборке URL-слаги
    надо URL-кодировать.
- Связанные сущности ссылаются по тому же паттерну: фиты — `/feats/<slug>`, трейты —
  `/traits/<slug>`, навыки — упоминаются как `[[skill/<id>|Name]]`.
- Вкладки сущности: `?tab=details`, `?tab=heritages` (для наследий родословной).

**Как получить полный список слагов с индекс-страницы — ВАЖНЕЙШИЙ вывод:**
весь датасет каждого типа отрисован server-side в **JSON-атрибуте `items` у веб-компонента
`<pf2-table ...>`**, а не подгружается XHR'ом. То есть для получения списка достаточно
одной загрузки индекс-страницы. Английское имя из поля `name` → lowercase → слаг URL.
Количества по снимку: **33 родословных, 21 класс, 140 предысторий.**

---

## 3. Структура страницы

Сайт — Svelte/SSR-приложение. Две принципиально разные структуры:

### 3.1 Индекс-страницы (структурированные — основной источник данных)

Главный контент — кастомный элемент `<pf2-table>` с атрибутами:
- `items="[{...}, ...]"` — **HTML-escaped JSON-массив всех сущностей** с готовыми механическими
  полями. Это самый чистый путь извлечения: распарсить `html.unescape(items)` → `json.loads`.
- `defaultvisiblecolumns="[...]"` — список колонок, фактически перечисляющий ключевые механические
  поля типа сущности (см. §4).
- Также присутствуют атрибуты вида `itemtype` (`ancestries` / `class_` / `background`).

Над таблицей — навигационная сетка карточек `div.content-table.content-table--menu` с
`div.content-item` → `a.content-header[href=".../<slug>?tab=details"]`. В самой таблице:
`table.table--list.need-filters` → `tr.item-row[data-id="<numeric id>"]`, ячейки `td.cell-*`,
ссылки `a.item-link.item-link--<type>`, бейджи трейтов `span.item-trait` /
`a.item-link--trait[href="/traits/<slug>"]`. Пагинации нет — всё на одной странице;
фильтрация/сортировка клиентские. Есть тумблер `.untranslated-filter` (скрыть непереведённое).

### 3.2 Страницы сущности (повествовательные — НЕ структурированы)

Контент детальной страницы — это статья-проза внутри `div.content-window`: заголовки
`<h2 class="h2-header">` (напр. «Повышения Характеристик», «Начальные умения», «Спасброски»),
якоря `<a class="anchor--link" id="<русский-слаг>">`, и сплошной текст с `<br>`. Числовые
владения/значения зашиты в текст параграфов, **не** в `dl`/таблицы/`data-`атрибуты.
Вывод: детальные страницы пригодны для извлечения описательного текста и, при необходимости,
парсинга прозы регулярками, но **структурированные механические значения надёжнее брать из JSON
`items` индекс-страницы.**

---

## 4. Доступные механические поля

Поля ниже — реальные ключи JSON `items` (значения локализованы; рядом всегда есть `*_search`
с английским эквивалентом, что удобно для маппинга на канонические термины PF2e).

### Ancestry (`defaultvisiblecolumns`: name, traits, hp, size, speed, ability_boost, ability_flaw, source)
Ключи: `name` (англ.), `rus_name`, `hp` (int, напр. Dwarf=10), `size` (Medium/Small...),
`speed` («20 футов», + `speed_sort`=20), `ability_boost` (напр. Dwarf: Constitution, Wisdom, Free),
`ability_flaw` (Dwarf: Charisma; «-» если нет), `vision` (Darkvision/Low-light...),
`traits` (HTML с ссылками на трейты, напр. Dwarf, Humanoid), `source`, `is_legacy`,
`is_not_translated`, `id`. **Наследия (heritages) на индексе НЕТ** — они на вкладке
`?tab=heritages` детальной страницы.

### Class (`defaultvisiblecolumns`: name, hp, ability_boost, source)
Ключи: `name`, `rus_name`, `hp` (HP/уровень, напр. Fighter=10), `ability_boost` (= ключевая
характеристика; Fighter = Free/«любая по выбору», Wizard = Intelligence), `source`,
`is_not_translated`, `id`. **Начальные владения (восприятие, спасброски, атаки, защита, навыки)
и классовые фиты 1 уровня на индексе ОТСУТСТВУЮТ** — они только в прозе детальной страницы
(секции `<h2>` «Начальные умения», «Спасброски» и т.п.).

### Background (`defaultvisiblecolumns`: name, skills, ability_boost, feat, source; региональные — ещё region)
Ключи: `name`, `rus_name`, `ability_boost` (напр. Acolyte: Intelligence, Wisdom),
`skills` (обученный навык + Lore; Acolyte: Religion + Scribing Lore, ссылки `[[skill/<id>|...]]`),
`feat` (навыковый фит с прямой ссылкой, Acolyte: Student of the Canon → `/feats/847`),
`source`, `is_legacy`, `is_not_translated`, `id`. **Backgrounds — самый полный по механике тип:
все 4 ключевых поля (повышения, навык, Lore, фит) есть прямо в индекс-JSON.**

**Важно:** поля `pf2ru_id` / `pf2ru_feat_id` (§5 схема) происходят из массива `items` JSON индекс-страницы;
это **отличается** от `data-key="feat/NNNN"` атрибута на детальной странице — две разные системы идентификации.

---

## 5. Предложение схемы данных

Нормализованный JSON для `backend/data`. Идентификатор сущности = URL-слаг (lowercase английское
имя). Локализованные строки храним парами (en/ru), т.к. `*_search` всегда даёт английский.

```json
{
  "ancestries": [{
    "slug": "dwarf",
    "name_en": "Dwarf",
    "name_ru": "Дварф",
    "hp": 10,
    "size": ["Medium"],
    "speed": 20,
    "ability_boosts": ["Constitution", "Wisdom", "Free"],
    "ability_flaws": ["Charisma"],
    "vision": "Darkvision",
    "traits": ["Dwarf", "Humanoid"],
    "source": "Player Core",
    "heritages": [],          // дозаполнить с ?tab=heritages
    "pf2ru_id": 59
  }],
  "classes": [{
    "slug": "fighter",
    "name_en": "Fighter",
    "name_ru": "Воин",
    "hp_per_level": 10,
    "key_ability": ["Free"],          // или конкретная, напр. ["Intelligence"]
    "source": "Player Core",
    "initial_proficiencies": {         // парсится из прозы детальной страницы
      "perception": null, "saves": {}, "attacks": {}, "defenses": {}, "skills": null
    },
    "class_feats_level1": [],          // из детальной страницы
    "pf2ru_id": 35
  }],
  "backgrounds": [{
    "slug": "acolyte",
    "name_en": "Acolyte",
    "name_ru": "Прислужник",
    "ability_boosts": ["Intelligence", "Wisdom"],
    "trained_skill": "Religion",
    "lore": "Scribing Lore",
    "skill_feat": {"slug": "student-of-the-canon", "pf2ru_feat_id": 847},
    "region": null,
    "source": "Player Core",
    "pf2ru_id": 406
  }]
}
```

Вспомогательные справочники (по ссылкам из `items`): `skills` (`skill/<id>`), `traits`
(`/traits/<slug>`), `feats` (`/feats/<slug>`).

---

## 6. Открытые вопросы / риски

1. **Наследия (heritages)** и **полный набор начальных владений класса / классовые фиты 1 ур.**
   на индекс-страницах отсутствуют. Их придётся снимать с детальных страниц, где они лежат в
   прозе (`<h2 class="h2-header">` + текст), а не в структурированном виде → потребуется парсинг
   текста (хрупко) или ручная доработка для ключевых сущностей создания персонажа.
2. **`<pf2-table>` — недокументированный приватный контракт сайта.** Имена ключей JSON (`hp`,
   `ability_boost`, `speed_sort`...) могут поменяться при обновлении pf2.ru. Парсер План 2 должен
   быть устойчив (отсутствующие ключи → None) и тестироваться на зафиксированных фикстурах.
3. **Локализация значений.** `ability_boost`/`size`/`speed` отдаются по-русски; для маппинга на
   канонические PF2e-термины опираться на парный `*_search` (содержит английский), а не парсить
   русский текст.
4. **Многословные слаги с пробелами** (`group impression`) требуют URL-кодирования при выборке.
5. **Флаги `is_legacy` / `is_not_translated`.** Часть сущностей — legacy-редакция или без перевода;
   при сборке датасета их надо фильтровать/помечать, чтобы конструктор не предлагал устаревшее.
6. **Вежливость и стабильность гейта.** Гейт пройден headless, но это Cloudflare-подобная защита:
   при массовом обходе всех ~194 сущностей нужен троттлинг (пауза между запросами, один поток),
   иначе риск блокировки. Кэшировать снятое в сыром виде, не дёргать сайт повторно без нужды.

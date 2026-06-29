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

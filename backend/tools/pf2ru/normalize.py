"""Нормализаторы сырых записей pf2.ru → компактная схема backend/data."""

import re

from tools.pf2ru.links import extract_trait_slugs, parse_wikilinks, slugify
from tools.pf2ru.mappings import normalize_abilities, normalize_sizes

# Английское слово (тип знания) перед ссылкой на навык Lore: "Scribing [[skill/8|Lore]]".
_LORE_WORD = re.compile(r"((?:[A-Za-z]+\s+)+)\[\[skill/\d+\|Lore\]\]")


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
        lore = f"{lore_match.group(1).strip()} Lore"

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

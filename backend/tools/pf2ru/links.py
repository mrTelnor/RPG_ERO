"""Парсинг wiki-ссылок pf2.ru ([[kind/id|Name]]), трейтов и слагов."""

import re

_WIKILINK = re.compile(r"\[\[(\w+)/(\d+)\|([^\]]+)\]\]")
_TRAIT_HREF = re.compile(r'href="/traits/([^"?#]+)(?:[?#][^"]*)?\"')


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

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

"""Извлечение server-rendered JSON из индекс-страниц pf2.ru.

Весь датасет типа сущности отрисован в атрибуте items элемента
<pf2-table> (HTML-escaped JSON-массив), без подгрузки по XHR.
"""

import html
import json
import re

_PF2_TABLE_ITEMS = re.compile(r'<pf2-table\b[^>]*\s+items="(.*?)"', re.DOTALL)


def extract_items(html_text: str) -> list[dict]:
    """Вернуть список сырых записей сущностей из <pf2-table items="...">."""
    match = _PF2_TABLE_ITEMS.search(html_text)
    if match is None:
        raise ValueError('no <pf2-table items="..."> found in HTML')
    return json.loads(html.unescape(match.group(1)))

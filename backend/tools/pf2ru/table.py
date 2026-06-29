"""Извлечение server-rendered JSON из индекс-страниц pf2.ru.

Весь датасет типа сущности отрисован в атрибуте items элемента
<pf2-table> (HTML-escaped JSON-массив), без подгрузки по XHR.
"""

import html
import json
import re

_PF2_TABLE_ITEMS = re.compile(r'<pf2-table\b[^>]*\s+items="(.*?)"', re.DOTALL)
_PF2_TABLE_TAG = re.compile(r"<pf2-table\b([^>]*)>", re.DOTALL)
_TABLE_ITEMS = re.compile(r'\bitems="(.*?)"', re.DOTALL)
_TABLE_ITEMTYPE = re.compile(r'\bitemtype="([^"]*)"')


def extract_items(html_text: str) -> list[dict]:
    """Вернуть список сырых записей сущностей из <pf2-table items="...">."""
    match = _PF2_TABLE_ITEMS.search(html_text)
    if match is None:
        raise ValueError('no <pf2-table items="..."> found in HTML')
    return json.loads(html.unescape(match.group(1)))


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

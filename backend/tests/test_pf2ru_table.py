from pathlib import Path

import pytest

from tools.pf2ru.table import extract_items, extract_items_by_itemtype

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
    with pytest.raises(ValueError):
        extract_items("<html><body>no table here</body></html>")


def test_extract_by_itemtype_feats_counts():
    dwarf = _read("ancestry_dwarf.html")
    fighter = _read("class_fighter.html")
    assert len(extract_items_by_itemtype(dwarf, "feats")) == 21
    assert len(extract_items_by_itemtype(fighter, "feats")) == 96


def test_extract_by_itemtype_empty_spells_table():
    fighter = _read("class_fighter.html")
    assert extract_items_by_itemtype(fighter, "spells") == []


def test_extract_by_itemtype_absent_raises():
    with pytest.raises(ValueError):
        extract_items_by_itemtype("<html></html>", "feats")

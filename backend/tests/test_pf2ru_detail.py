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
    assert "prerequisites" in lore


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

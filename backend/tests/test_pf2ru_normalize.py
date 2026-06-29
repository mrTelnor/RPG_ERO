from pathlib import Path

from tools.pf2ru.normalize import (
    normalize_ancestry,
    normalize_background,
    normalize_class,
)
from tools.pf2ru.table import extract_items

FIXTURES = Path(__file__).parent / "fixtures" / "pf2ru"


def _find(fixture: str, name: str) -> dict:
    items = extract_items((FIXTURES / fixture).read_text(encoding="utf-8"))
    return next(it for it in items if it.get("name") == name)


def test_normalize_ancestry_dwarf():
    result = normalize_ancestry(_find("index_ancestries.html", "Dwarf"))
    assert result["slug"] == "dwarf"
    assert result["name_en"] == "Dwarf"
    assert result["name_ru"] == "Дварф"
    assert result["hp"] == 10
    assert result["size"] == ["Medium"]
    assert result["speed"] == 20
    assert result["ability_boosts"] == ["Constitution", "Wisdom", "Free"]
    assert result["ability_flaws"] == ["Charisma"]
    assert result["traits"] == ["dwarf", "humanoid"]
    assert result["pf2ru_id"] == 59
    assert result["is_legacy"] is False
    assert isinstance(result["name_ru"], str) and result["name_ru"]


def test_normalize_class_fighter():
    result = normalize_class(_find("index_classes.html", "Fighter"))
    assert result["slug"] == "fighter"
    assert result["name_en"] == "Fighter"
    assert result["name_ru"] == "Воин"
    assert result["hp_per_level"] == 10
    assert result["key_ability"] == ["Strength", "Dexterity"]
    assert result["pf2ru_id"] == 35
    # начальные владения/классовые фиты сюда НЕ входят
    assert "initial_proficiencies" not in result
    assert "class_feats" not in result
    assert result["source_ru"] is not None
    assert result["is_not_translated"] is False


def test_normalize_background_acolyte():
    result = normalize_background(_find("index_backgrounds.html", "Acolyte"))
    assert result["slug"] == "acolyte"
    assert result["name_en"] == "Acolyte"
    assert result["ability_boosts"] == ["Intelligence", "Wisdom"]
    assert result["trained_skill"] == "Religion"
    assert result["lore"] == "Scribing Lore"
    assert result["skill_feat"] == {
        "slug": "student-of-the-canon",
        "name_en": "Student of the Canon",
        "pf2ru_feat_id": 847,
    }
    assert result["pf2ru_id"] == 406


def test_normalize_background_multiword_lore():
    raw = {
        "name": "Example",
        "rus_name": "Пример",
        "ability_boost": "Интеллект",
        "skills_search": "[[skill/1|Foo]], Ancient Scribing [[skill/8|Lore]] [[skill/1|Фу]]",
        "feat_search": "",
        "id": 1,
    }
    result = normalize_background(raw)
    assert result["lore"] == "Ancient Scribing Lore"
    assert result["trained_skill"] == "Foo"
    assert result["skill_feat"] is None

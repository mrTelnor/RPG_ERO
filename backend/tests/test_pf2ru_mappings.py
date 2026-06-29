import pytest

from tools.pf2ru.mappings import normalize_abilities, normalize_sizes


def test_abilities_ancestry_boosts_dwarf():
    assert normalize_abilities("Выносливость, Мудрость, Универсальное") == [
        "Constitution",
        "Wisdom",
        "Free",
    ]


def test_abilities_single_flaw():
    assert normalize_abilities("Харизма") == ["Charisma"]


def test_abilities_class_key_or_phrase_fighter():
    assert normalize_abilities("Сила или Ловкость") == ["Strength", "Dexterity"]


def test_abilities_class_key_other_is_free():
    assert normalize_abilities("Ловкость или Другая") == ["Dexterity", "Free"]


def test_abilities_empty_and_dash():
    assert normalize_abilities("") == []
    assert normalize_abilities("-") == []
    assert normalize_abilities(None) == []


def test_abilities_unknown_token_raises():
    with pytest.raises(KeyError):
        normalize_abilities("Хитрость")


def test_sizes_single_and_multi():
    assert normalize_sizes("Средний") == ["Medium"]
    assert normalize_sizes("Средний, Небольшой") == ["Medium", "Small"]
    assert normalize_sizes(None) == []

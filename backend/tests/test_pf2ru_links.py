from tools.pf2ru.links import extract_trait_slugs, parse_wikilinks, slugify


def test_parse_wikilinks_feat():
    text = "[[feat/847|Student of the Canon]] [[feat/847|Прислужник]]"
    assert parse_wikilinks(text) == [
        ("feat", 847, "Student of the Canon"),
        ("feat", 847, "Прислужник"),
    ]


def test_parse_wikilinks_skills():
    text = "[[skill/13|Religion]], Scribing [[skill/8|Lore]]"
    assert parse_wikilinks(text) == [
        ("skill", 13, "Religion"),
        ("skill", 8, "Lore"),
    ]


def test_parse_wikilinks_empty():
    assert parse_wikilinks("") == []
    assert parse_wikilinks(None) == []


def test_extract_trait_slugs_dedup_order():
    html_fragment = (
        '<a class="item-link--trait" href="/traits/dwarf">Дварф</a>'
        '<a class="item-link--trait" href="/traits/humanoid">Гуманоид</a>'
        '<a href="/traits/dwarf">dup</a>'
    )
    assert extract_trait_slugs(html_fragment) == ["dwarf", "humanoid"]


def test_extract_trait_slugs_empty():
    assert extract_trait_slugs("") == []
    assert extract_trait_slugs(None) == []


def test_slugify():
    assert slugify("Fighter") == "fighter"
    assert slugify("Student of the Canon") == "student-of-the-canon"

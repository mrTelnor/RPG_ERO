import json
from pathlib import Path

from tools.pf2ru.enrich import enrich

FIXTURES = Path(__file__).parent / "fixtures" / "pf2ru"


def test_enrich_dwarf_and_fighter(tmp_path):
    # Мини-датасет: одна родословная (dwarf) + один класс (fighter) + «пустышка».
    (tmp_path / "ancestries.json").write_text(
        json.dumps([{"slug": "dwarf", "name_en": "Dwarf"}, {"slug": "elf", "name_en": "Elf"}]),
        encoding="utf-8",
    )
    (tmp_path / "classes.json").write_text(
        json.dumps([{"slug": "fighter", "name_en": "Fighter"}]), encoding="utf-8"
    )

    summary = enrich(tmp_path, FIXTURES)

    ancestries = json.loads((tmp_path / "ancestries.json").read_text(encoding="utf-8"))
    dwarf = next(a for a in ancestries if a["slug"] == "dwarf")
    assert [h["slug"] for h in dwarf["heritages"]] == [
        "ancient-blooded-dwarf",
        "forge-dwarf",
        "death-warden-dwarf",
        "strong-blooded-dwarf",
        "rock-dwarf",
    ]
    assert len(dwarf["ancestry_feats_l1"]) == 8

    # Нет детального файла для elf → не обогащается.
    elf = next(a for a in ancestries if a["slug"] == "elf")
    assert "heritages" not in elf
    assert "elf" in summary["skipped"]
    assert elf["name_en"] == "Elf"

    classes = json.loads((tmp_path / "classes.json").read_text(encoding="utf-8"))
    fighter = next(c for c in classes if c["slug"] == "fighter")
    assert len(fighter["class_feats_l1"]) == 8

    assert summary["ancestries_enriched"] == 1
    assert summary["classes_enriched"] == 1

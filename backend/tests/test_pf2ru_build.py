import json
from pathlib import Path

from tools.pf2ru.build import build

FIXTURES = Path(__file__).parent / "fixtures" / "pf2ru"


def test_build_writes_dataset(tmp_path):
    counts = build(FIXTURES, tmp_path)
    assert counts == {"ancestries": 29, "classes": 21, "backgrounds": 122}

    for name in ("ancestries", "classes", "backgrounds", "manifest"):
        assert (tmp_path / f"{name}.json").exists()

    ancestries = json.loads((tmp_path / "ancestries.json").read_text(encoding="utf-8"))
    slugs = {a["slug"] for a in ancestries}
    assert "dwarf" in slugs            # Remaster — присутствует
    assert "kitsune" not in slugs      # legacy — отсеян
    dwarf = next(a for a in ancestries if a["slug"] == "dwarf")
    assert dwarf["ability_boosts"] == ["Constitution", "Wisdom", "Free"]
    assert dwarf["hp"] == 10

    backgrounds = json.loads((tmp_path / "backgrounds.json").read_text(encoding="utf-8"))
    assert not any(b.get("is_legacy") for b in backgrounds)  # ни одной legacy-предыстории

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["source"] == "https://pf2.ru"
    assert manifest["edition"] == "remaster"
    assert manifest["counts"] == {"ancestries": 29, "classes": 21, "backgrounds": 122}

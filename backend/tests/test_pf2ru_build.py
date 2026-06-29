import json
from pathlib import Path

from tools.pf2ru.build import build

FIXTURES = Path(__file__).parent / "fixtures" / "pf2ru"


def test_build_writes_dataset(tmp_path):
    counts = build(FIXTURES, tmp_path)
    assert counts == {"ancestries": 33, "classes": 21, "backgrounds": 140}

    for name in ("ancestries", "classes", "backgrounds", "manifest"):
        assert (tmp_path / f"{name}.json").exists()

    ancestries = json.loads((tmp_path / "ancestries.json").read_text(encoding="utf-8"))
    dwarf = next(a for a in ancestries if a["slug"] == "dwarf")
    assert dwarf["ability_boosts"] == ["Constitution", "Wisdom", "Free"]
    assert dwarf["hp"] == 10

    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["source"] == "https://pf2.ru"
    assert manifest["counts"] == {"ancestries": 33, "classes": 21, "backgrounds": 140}

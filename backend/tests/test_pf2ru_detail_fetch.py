import json

from tools.pf2ru.detail_fetch import detail_targets


def test_detail_targets_builds_urls_and_filenames(tmp_path):
    (tmp_path / "ancestries.json").write_text(
        json.dumps([{"slug": "dwarf"}, {"slug": "half-elf"}]), encoding="utf-8"
    )
    (tmp_path / "classes.json").write_text(
        json.dumps([{"slug": "fighter"}]), encoding="utf-8"
    )
    targets = detail_targets(tmp_path)
    assert ("https://pf2.ru/ancestries/dwarf", "ancestry_dwarf.html") in targets
    assert ("https://pf2.ru/ancestries/half-elf", "ancestry_half-elf.html") in targets
    assert ("https://pf2.ru/classes/fighter", "class_fighter.html") in targets
    assert len(targets) == 3

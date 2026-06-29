"""Обогащение датасета backend/data структурными данными детальных страниц."""

import json
from pathlib import Path

from tools.pf2ru.detail import level1_feats, parse_heritages
from tools.pf2ru.table import extract_items_by_itemtype


def _load(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump(path: Path, data: list[dict]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def enrich(data_dir: Path, detail_dir: Path) -> dict:
    skipped: list[str] = []

    ancestries = _load(data_dir / "ancestries.json")
    ancestries_enriched = 0
    for record in ancestries:
        detail = detail_dir / f"ancestry_{record['slug']}.html"
        if not detail.exists():
            skipped.append(record["slug"])
            continue
        html_text = detail.read_text(encoding="utf-8")
        record["heritages"] = parse_heritages(html_text, record["slug"])
        record["ancestry_feats_l1"] = level1_feats(
            extract_items_by_itemtype(html_text, "feats")
        )
        ancestries_enriched += 1
    _dump(data_dir / "ancestries.json", ancestries)

    classes = _load(data_dir / "classes.json")
    classes_enriched = 0
    for record in classes:
        detail = detail_dir / f"class_{record['slug']}.html"
        if not detail.exists():
            skipped.append(record["slug"])
            continue
        html_text = detail.read_text(encoding="utf-8")
        record["class_feats_l1"] = level1_feats(
            extract_items_by_itemtype(html_text, "feats")
        )
        classes_enriched += 1
    _dump(data_dir / "classes.json", classes)

    return {
        "ancestries_enriched": ancestries_enriched,
        "classes_enriched": classes_enriched,
        "skipped": skipped,
    }

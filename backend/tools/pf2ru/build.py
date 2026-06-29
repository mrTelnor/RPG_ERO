"""Сборка нормализованного датасета pf2.ru в backend/data.

Источник — три индекс-фикстуры (весь датасет типа в одном <pf2-table>).
Живой рефреш: `uv run python tools/pf2ru_recon.py` (снимет индексы в
tools/_recon_raw/) затем `uv run python -m tools.pf2ru.build --raw tools/_recon_raw`.
"""

import argparse
import json
from pathlib import Path

from tools.pf2ru.normalize import (
    normalize_ancestry,
    normalize_background,
    normalize_class,
)
from tools.pf2ru.table import extract_items

SOURCE = "https://pf2.ru"
SNAPSHOT = "2026-06-28"

_SPECS = (
    ("ancestries", "index_ancestries.html", normalize_ancestry),
    ("classes", "index_classes.html", normalize_class),
    ("backgrounds", "index_backgrounds.html", normalize_background),
)

# Каталоги по умолчанию относительно backend/ (запуск из каталога backend).
_DEFAULT_RAW = Path("tests/fixtures/pf2ru")
_DEFAULT_OUT = Path("data")


def build(raw_dir: Path, out_dir: Path) -> dict[str, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for name, fixture, normalizer in _SPECS:
        items = extract_items((raw_dir / fixture).read_text(encoding="utf-8"))
        records = [normalizer(item) for item in items]
        (out_dir / f"{name}.json").write_text(
            json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        counts[name] = len(records)
    manifest = {"source": SOURCE, "snapshot": SNAPSHOT, "counts": counts}
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Сборка датасета pf2.ru в backend/data.")
    parser.add_argument("--raw", type=Path, default=_DEFAULT_RAW, help="каталог с индекс-HTML")
    parser.add_argument("--out", type=Path, default=_DEFAULT_OUT, help="выходной каталог JSON")
    args = parser.parse_args()
    counts = build(args.raw, args.out)
    print(f"built: {counts} -> {args.out}")


if __name__ == "__main__":
    main()

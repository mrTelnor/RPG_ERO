"""Троттленый резюмируемый обход детальных страниц pf2.ru.

Запуск: uv run python -m tools.pf2ru.detail_fetch
Снимает ancestries/classes detail-страницы в tools/_recon_raw/ (git-ignored),
по одной, с паузой, пропуская уже снятые файлы. Затем используйте enrich.
"""

import argparse
import json
import urllib.parse
from pathlib import Path

BASE = "https://pf2.ru"
_DEFAULT_DATA = Path("data")
_DEFAULT_RAW = Path("tools/_recon_raw")


def detail_targets(data_dir: Path) -> list[tuple[str, str]]:
    """Список (url, filename) детальных страниц по датасету.

    URL pf2.ru использует английское имя в нижнем регистре с сохранением пробелов
    (напр. «Awakened Animal» → /ancestries/awakened%20animal), поэтому токен URL
    берём из name_en, а не из дефисного slug. Имя файла — по slug.
    """
    targets: list[tuple[str, str]] = []
    for kind, plural in (("ancestry", "ancestries"), ("class", "classes")):
        records = json.loads((data_dir / f"{plural}.json").read_text(encoding="utf-8"))
        for record in records:
            slug = record["slug"]
            url_token = record["name_en"].lower()
            url = f"{BASE}/{plural}/{urllib.parse.quote(url_token)}"
            targets.append((url, f"{kind}_{slug}.html"))
    return targets


def fetch_all(data_dir: Path, raw_dir: Path, delay_s: float = 1.5) -> dict:
    """Вежливый последовательный обход; пропускает уже снятые файлы."""
    from playwright.sync_api import sync_playwright

    raw_dir.mkdir(parents=True, exist_ok=True)
    targets = detail_targets(data_dir)
    fetched, skipped, errors = 0, 0, 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        for url, filename in targets:
            out = raw_dir / filename
            if out.exists():
                skipped += 1
                continue
            try:
                page.goto(url, wait_until="networkidle", timeout=60_000)
                page.wait_for_timeout(int(delay_s * 1000))
                out.write_text(page.content(), encoding="utf-8")
                fetched += 1
                print(f"  fetched {filename} ({fetched}/{len(targets)})")
            except Exception as exc:  # noqa: BLE001
                errors += 1
                print(f"  ERROR {filename}: {exc}")
                page.wait_for_timeout(int(delay_s * 1000))
        browser.close()
    return {"fetched": fetched, "skipped": skipped, "errors": errors, "total": len(targets)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Обход детальных страниц pf2.ru.")
    parser.add_argument("--data", type=Path, default=_DEFAULT_DATA)
    parser.add_argument("--raw", type=Path, default=_DEFAULT_RAW)
    parser.add_argument("--delay", type=float, default=1.5)
    args = parser.parse_args()
    print(fetch_all(args.data, args.raw, args.delay))


if __name__ == "__main__":
    main()

"""Разведка структуры данных pf2.ru.

Запуск:  uv run python tools/pf2ru_recon.py
Назначение: проверить прохождение JS-гейта и снять сырые HTML-страницы
для последующего анализа. Сырьё пишется в tools/_recon_raw/ (в .gitignore).
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "https://pf2.ru"
INDEX_PAGES = {
    "index_ancestries": f"{BASE}/ancestries",
    "index_classes": f"{BASE}/classes",
    "index_backgrounds": f"{BASE}/backgrounds",
}

ENTITY_PAGES: dict[str, str] = {
    # Реальные слаги, найденные в index_*.html (grep по href-паттернам).
    "ancestry_dwarf": f"{BASE}/ancestries/dwarf",
    "class_fighter": f"{BASE}/classes/fighter",
    "background_acolyte": f"{BASE}/backgrounds/acolyte",
}

RAW_DIR = Path(__file__).parent / "_recon_raw"


def fetch(page, url: str) -> str:
    page.goto(url, wait_until="networkidle", timeout=60_000)
    # Дать JS-проверке отработать и отрисовать контент.
    page.wait_for_load_state("networkidle", timeout=60_000)
    return page.content()


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        for name, url in INDEX_PAGES.items():
            html = fetch(page, url)
            out = RAW_DIR / f"{name}.html"
            out.write_text(html, encoding="utf-8")
            blocked = "Проверка безопасности" in html or "Подождите" in html
            print(f"{name}: {len(html)} символов, заблокировано={blocked} -> {out}")
        for name, url in ENTITY_PAGES.items():
            html = fetch(page, url)
            out = RAW_DIR / f"{name}.html"
            out.write_text(html, encoding="utf-8")
            blocked = "Проверка безопасности" in html or "Подождите" in html
            print(f"{name}: {len(html)} символов, заблокировано={blocked} -> {out}")
        browser.close()


if __name__ == "__main__":
    main()

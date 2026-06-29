from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures" / "pf2ru"


def test_entity_fixtures_present_and_nontrivial():
    captured = list(FIXTURES.glob("*.html"))
    assert captured, "Нет снятых фикстур pf2.ru"
    # Хотя бы по одной странице каждого типа сущности.
    kinds = {"ancestry", "class", "background"}
    present = {k for k in kinds if any(f.name.startswith(k) for f in captured)}
    assert present == kinds, f"Не хватает типов фикстур: {kinds - present}"
    # Снимки должны быть содержательными, а не страницей-заглушкой гейта.
    for f in captured:
        html = f.read_text(encoding="utf-8")
        assert len(html) > 5_000, f"Снимок подозрительно мал: {f.name}"
        assert "Проверка безопасности" not in html, f"Снимок — страница гейта: {f.name}"

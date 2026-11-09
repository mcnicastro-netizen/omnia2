"""D-150 — catalogo live + roadmap; MLS matrix metadata; roadmap non in THEME_IDS."""
from apps.immoweb.theme_catalog import THEME_CATALOG, THEME_IDS, THEME_ROADMAP


def test_live_themes_declare_mls_variants():
    assert {t["id"] for t in THEME_CATALOG} == {"minimal", "classic", "bold", "luxury"}
    for t in THEME_CATALOG:
        assert t["status"] == "live"
        assert set(t["mls_variants"]) == {"on", "off"}
        assert t["id"] in THEME_IDS


def test_roadmap_not_selectable():
    ids = {t["id"] for t in THEME_ROADMAP}
    assert ids == {"atelier", "cinematic", "editorial", "mediterranean"}
    for t in THEME_ROADMAP:
        assert t["status"] == "planned"
        assert t["id"] not in THEME_IDS
        assert set(t["mls_variants"]) == {"on", "off"}

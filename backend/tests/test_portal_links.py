"""Link enter_url per email attivazione gestionale."""
from shared.email.portal_links import gestionale_enter_urls


def test_gestionale_enter_urls(monkeypatch):
    monkeypatch.setattr(
        "shared.email.portal_links.get_public_base_url",
        lambda: "https://omniarealestateecosystem.it",
    )
    links = gestionale_enter_urls("it")
    assert links["dashboard_url"].endswith("/it/app/dashboard")
    assert links["login_url"].endswith("/it/login")
    assert "from=app" in links["enter_url"]
    assert "next=" in links["enter_url"]
    assert "%2Fit%2Fapp%2Fdashboard" in links["enter_url"]

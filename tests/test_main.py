import os
import tempfile
import pytest
from aggregator.app import create_app
from aggregator.database import add_source, get_articles, get_sources, init_db, upsert_article
from aggregator.fetcher import clean_html_summary


@pytest.fixture
def app_client():
    db_fd, db_path = tempfile.mkstemp()
    os.environ["NEWS_DB_PATH"] = db_path
    app = create_app({"TESTING": True})
    client = app.test_client()

    yield client

    os.close(db_fd)
    if os.path.exists(db_path):
        os.unlink(db_path)


def test_clean_html_summary():
    raw = "<p>Hello <b>World</b> &amp; friends! <a href='#'>Click here</a></p>"
    cleaned = clean_html_summary(raw)
    assert cleaned == "Hello World & friends! Click here"


def test_sources_and_articles(app_client):
    sources = get_sources()
    assert len(sources) >= 4

    # Insert sample article
    article = {
        "source_id": sources[0]["id"],
        "title": "Quantum Computing Leap",
        "link": "https://example.com/quantum",
        "summary": "Scientists build error-resilient qubits.",
        "category": "Science",
    }
    success = upsert_article(article)
    assert success is True

    # Retrieve articles
    items = get_articles(category="Science")
    assert len(items) >= 1
    assert items[0]["title"] == "Quantum Computing Leap"


def test_api_endpoints(app_client):
    # 1. Fetch articles
    res = app_client.get("/api/articles")
    assert res.status_code == 200
    data = res.get_json()
    assert "articles" in data

    # 2. Add an article to bookmark
    article = {
        "title": "AI Breakthrough",
        "link": "https://example.com/ai-breakthrough",
        "summary": "Models now reason with formal logic.",
        "category": "Tech",
    }
    upsert_article(article)
    articles = get_articles()
    art_id = articles[0]["id"]

    # 3. Toggle Bookmark
    bm_res = app_client.post(f"/api/articles/{art_id}/bookmark")
    assert bm_res.status_code == 200
    assert bm_res.get_json()["is_bookmarked"] is True

    # 4. Toggle Read
    read_res = app_client.post(f"/api/articles/{art_id}/read")
    assert read_res.status_code == 200
    assert read_res.get_json()["is_read"] is True

    # 5. Add custom source
    src_res = app_client.post("/api/sources", json={
        "name": "Test Tech Feed",
        "url": "https://example.com/test-feed.xml",
        "category": "Tech"
    })
    assert src_res.status_code == 201

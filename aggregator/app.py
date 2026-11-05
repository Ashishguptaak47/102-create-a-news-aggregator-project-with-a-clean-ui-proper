from flask import Flask, jsonify, render_template, request
from aggregator.database import (
    add_source,
    get_articles,
    get_sources,
    init_db,
    toggle_bookmark,
    toggle_read,
)
from aggregator.fetcher import sync_feeds


def create_app(test_config=None) -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_mapping(
        SECRET_KEY="dev-secret-key-pulse-news",
    )

    if test_config:
        app.config.update(test_config)

    with app.app_context():
        init_db()

    @app.route("/")
    def index():
        sources = get_sources()
        categories = sorted(list({s["category"] for s in sources} | {"Tech", "Science", "World", "General"}))
        return render_template("index.html", categories=categories, sources=sources)

    @app.route("/api/articles", methods=["GET"])
    def api_articles():
        category = request.args.get("category")
        search = request.args.get("search")
        bookmarked = request.args.get("bookmarked", "false").lower() == "true"
        limit = request.args.get("limit", 50, type=int)
        offset = request.args.get("offset", 0, type=int)

        items = get_articles(
            category=category,
            search=search,
            bookmarked_only=bookmarked,
            limit=limit,
            offset=offset,
        )
        return jsonify({"status": "ok", "count": len(items), "articles": items})

    @app.route("/api/refresh", methods=["POST"])
    def api_refresh():
        updated = sync_feeds()
        return jsonify({"status": "ok", "synced_count": updated})

    @app.route("/api/articles/<int:article_id>/bookmark", methods=["POST"])
    def api_toggle_bookmark(article_id: int):
        new_state = toggle_bookmark(article_id)
        if new_state is None:
            return jsonify({"error": "Article not found"}), 404
        return jsonify({"status": "ok", "is_bookmarked": bool(new_state)})

    @app.route("/api/articles/<int:article_id>/read", methods=["POST"])
    def api_toggle_read(article_id: int):
        new_state = toggle_read(article_id)
        if new_state is None:
            return jsonify({"error": "Article not found"}), 404
        return jsonify({"status": "ok", "is_read": bool(new_state)})

    @app.route("/api/sources", methods=["GET", "POST"])
    def api_sources():
        if request.method == "POST":
            payload = request.get_json() or {}
            name = payload.get("name")
            url = payload.get("url")
            cat = payload.get("category", "General")
            if not name or not url:
                return jsonify({"error": "Missing name or url parameter"}), 400
            source_id = add_source(name, url, cat)
            if not source_id:
                return jsonify({"error": "Source already exists or failed to add"}), 409
            return jsonify({"status": "ok", "id": source_id}), 201
        return jsonify({"sources": get_sources()})

    return app

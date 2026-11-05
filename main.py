import os
from aggregator.app import create_app
from aggregator.fetcher import sync_feeds

app = create_app()

if __name__ == "__main__":
    # Sync initial news articles upon startup if empty
    sync_feeds()
    port = int(os.environ.get("PORT", 5000))
    print(f"* PulseNews Aggregator running on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)

# PulseNews - Intelligent News Aggregator

A modern, responsive News Aggregator built with Python and Flask. It fetches, sanitizes, and categorizes RSS and Atom feeds, providing search, category filtering, bookmarking, and offline-safe fallback feeds.

## Features
- **Multi-Source Aggregation**: Fetches articles across Tech, Science, World, and Business feeds.
- **Custom Feeds**: Add your own RSS/Atom feeds dynamically from the UI or API.
- **Clean Reading UI**: Modern card layout built with Tailwind CSS, read-later bookmarks, and instant search.
- **Resilient Ingestion**: Extracts cover images, strips noisy markup, parses publish dates, and falls back to curated sample articles if internet access is limited.
- **REST API**: Easily integrate with mobile apps, CLI tools, or external services.

## Quickstart

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**:
   ```bash
   python main.py
   ```

3. **Access the web dashboard**:
   Open `http://localhost:5000` in your web browser.

## Running Tests
```bash
pytest
```

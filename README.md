# News Scraper

A Flask-based news aggregator that fetches and displays articles from BBC and SCMP with themeable UI and text-to-speech support.

## Features

- **Multiple News Sources**: BBC and SCMP
- **Section Navigation**: Browse news by category (Home, Tech, Science, Business, Politics, Sport, Culture)
- **Themeable UI**: Aurora, Sunset, Forest, Midnight, Neon
- **Article View**: Full articles with related news
- **Text-to-Speech**: Convert articles to audio using Piper TTS
- **Image Toggle**: Show/hide article images

## Installation

```bash
pip install flask beautifulsoup4 requests
```

For TTS support:
```bash
pip install piper-tts
```

## Running

```bash
python server.py
```

Server runs at `http://localhost:8080`

## API Endpoints

- `GET /` - Home page
- `GET /article?url=<article_url>&source=<source>` - Article view
- `GET /api/sections?source=<bbc|scmp>` - Get available sections
- `GET /api/news?source=<source>&images=<true|false>` - Get home news
- `GET /api/section?source=<source>&section=<section>&images=<true|false>` - Get section news
- `POST /api/tts` - Generate TTS audio (expects `{"text": "..."}`)
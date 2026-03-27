# Gaming PR Platform

A service that scrapes the biggest gaming news outlets across the top 10 most spoken languages, lets users create articles, and automatically translates them into all supported languages.

## Supported Languages

| Code | Language |
|------|----------|
| en | English |
| zh-CN | Mandarin Chinese |
| hi | Hindi |
| es | Spanish |
| fr | French |
| ar | Arabic |
| bn | Bengali |
| pt | Portuguese |
| ru | Russian |
| ja | Japanese |

## Features

- **Gaming Outlet Database**: 40+ pre-seeded gaming news outlets across all 10 languages
- **News Scraping**: RSS and HTML-based scrapers to pull latest gaming news
- **Article CRUD**: Create, read, update, and delete your own articles
- **Auto-Translation**: Articles are automatically translated into all 9 other languages on creation
- **REST API**: Full JSON API built with FastAPI

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy env config
cp .env.example .env

# Run the server
python main.py
```

The server starts at `http://localhost:8000`. Interactive API docs at `http://localhost:8000/docs`.

## API Endpoints

### Articles
- `POST /api/articles/` - Create an article (triggers auto-translation)
- `GET /api/articles/` - List articles
- `GET /api/articles/{id}` - Get article with translations
- `PUT /api/articles/{id}` - Update article
- `DELETE /api/articles/{id}` - Delete article

### Translations
- `GET /api/articles/{id}/translations` - List translations for an article
- `GET /api/articles/{id}/translations/{language}` - Get specific translation
- `POST /api/articles/{id}/translations/retry` - Retry failed translations

### Gaming Outlets
- `GET /api/outlets/` - List outlets (filter by `?language=en`)
- `GET /api/outlets/{id}` - Get outlet details
- `POST /api/outlets/` - Add a new outlet
- `PATCH /api/outlets/{id}` - Update outlet

### Scraper
- `POST /api/scraper/run` - Scrape all active outlets
- `POST /api/scraper/run/{outlet_id}` - Scrape a single outlet
- `GET /api/scraper/articles` - List scraped articles (filter by `?language=en`)

### Utilities
- `GET /health` - Health check
- `GET /api/languages` - List supported languages

## Example: Create & Translate an Article

```bash
curl -X POST http://localhost:8000/api/articles/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New RPG Announced at E3",
    "body": "A major studio has revealed their latest open-world RPG...",
    "source_language": "en",
    "author_name": "Jane Doe"
  }'
```

The article is created instantly and translations into all 9 other languages begin in the background.

## Architecture

```
app/
├── models/          # SQLAlchemy models (Article, Outlet, ScrapedArticle)
├── schemas/         # Pydantic request/response schemas
├── routers/         # FastAPI route handlers
├── services/        # Business logic (scraping, translation, article mgmt)
├── scrapers/        # RSS and HTML scraper implementations
└── seed/            # Pre-seeded gaming outlet data
```

- **Database**: SQLite (via SQLAlchemy, easily swappable to PostgreSQL)
- **Translation**: Google Translate via `deep-translator`
- **Scraping**: `feedparser` for RSS, `BeautifulSoup` for HTML fallback

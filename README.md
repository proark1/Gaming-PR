# Gaming PR Platform v2.0

The world's best gaming news scraper. Extracts **everything** from 80+ gaming outlets across 10 languages, stores it all in PostgreSQL, and auto-translates your press releases.

## What It Does

1. **Scrapes 80+ gaming outlets** across 10 languages with full content extraction
2. **Extracts everything**: full article body, images, videos, author info, tags, categories, OpenGraph, JSON-LD structured data, SEO metadata, review scores, comment counts, gaming platforms mentioned, and more
3. **Users create articles** that get automatically translated into 9 other languages
4. **Scheduled scraping** runs automatically every 30 minutes

## Supported Languages & Outlets

| Language | Code | Outlets | Examples |
|----------|------|---------|----------|
| English | en | 20 | IGN, GameSpot, Kotaku, PC Gamer, Polygon, Eurogamer |
| Mandarin Chinese | zh-CN | 9 | GamerSky, 17173, GameLook, Bahamut, VGtime |
| Hindi | hi | 6 | IGN India, Sportskeeda, AFK Gaming |
| Spanish | es | 9 | Vandal, 3DJuegos, MeriStation, HobbyConsolas |
| French | fr | 8 | Jeuxvideo.com, Gamekult, JeuxActu, Millenium |
| Arabic | ar | 5 | Saudi Gamer, ArabHardware, TRUE Gaming |
| Bengali | bn | 4 | TechShhor, GameBangla, Potaka Gaming |
| Portuguese | pt | 8 | IGN Brasil, The Enemy, Techtudo, Voxel |
| Russian | ru | 7 | DTF, Igromania, StopGame, PlayGround |
| Japanese | ja | 9 | 4Gamer, Famitsu, Game Watch, Automaton |

## Setup

### With Railway PostgreSQL

```bash
pip install -r requirements.txt
export DATABASE_URL="postgresql://user:pass@host:port/dbname"  # from Railway
python main.py
```

### Local Development

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your DATABASE_URL
python main.py
```

Server runs at `http://localhost:8000`. API docs at `/docs`.

## What Gets Extracted Per Article

Every scraped article stores:

- **Core**: title, URL, canonical URL, slug
- **Content**: full body HTML, full body plain text, word count, reading time
- **Authors**: name, URL, multiple authors support
- **Dates**: published, updated (from meta tags, JSON-LD, time elements)
- **Media**: featured image, thumbnail, all images (URL/alt/dimensions), videos (with platform detection for YouTube/Twitch/Vimeo)
- **Classification**: categories, tags, article type (news/review/preview/guide/opinion/interview), gaming platforms (PS5/Xbox/PC/Switch), game titles
- **SEO**: meta title, meta description, OpenGraph (title/desc/image/type), Twitter Card
- **Structured Data**: full JSON-LD (Schema.org) extraction
- **Engagement**: comment count, review score/max rating
- **Tracking**: content hash (change detection), HTTP status, scrape timestamps, extraction errors

## API Endpoints

### Articles (CRUD + Auto-Translation)
- `POST /api/articles/` - Create article (auto-translates to 9 languages)
- `GET /api/articles/` - List articles
- `GET /api/articles/{id}` - Get article with translations
- `PUT /api/articles/{id}` - Update (re-translates)
- `DELETE /api/articles/{id}` - Delete

### Translations
- `GET /api/articles/{id}/translations` - All translations
- `GET /api/articles/{id}/translations/{lang}` - Specific language
- `POST /api/articles/{id}/translations/retry` - Retry failed

### Scraper
- `POST /api/scraper/run` - Scrape all outlets (with full content extraction)
- `POST /api/scraper/run?run_async=true` - Run in background
- `POST /api/scraper/run/{outlet_id}` - Scrape single outlet
- `GET /api/scraper/articles` - List scraped articles (filter by language, outlet, type, full_content)
- `GET /api/scraper/articles/{id}` - Full article detail
- `GET /api/scraper/jobs` - List scrape jobs
- `GET /api/scraper/jobs/{id}` - Job detail
- `GET /api/scraper/stats` - Scraper statistics

### Outlets
- `GET /api/outlets/` - List outlets (filter by language, active status, category)
- `GET /api/outlets/stats` - Aggregate stats
- `POST /api/outlets/` - Add outlet
- `PATCH /api/outlets/{id}` - Update outlet
- `DELETE /api/outlets/{id}` - Remove outlet

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://...` | PostgreSQL connection string |
| `SCRAPE_INTERVAL_MINUTES` | 30 | Auto-scrape interval |
| `SCRAPE_CONCURRENCY` | 5 | Parallel outlet scraping threads |
| `SCRAPE_REQUEST_TIMEOUT` | 20 | HTTP timeout per request (seconds) |
| `SCRAPE_RATE_LIMIT_DELAY` | 1.0 | Delay between requests to same outlet |
| `FULL_CONTENT_EXTRACTION` | true | Fetch and parse full article pages |

## Architecture

```
app/
├── models/              # SQLAlchemy models (PostgreSQL with JSON columns)
│   ├── article.py       # User articles + translations
│   ├── outlet.py        # Gaming outlets with scrape tracking
│   ├── scraped_article.py  # 40+ fields per article
│   └── scrape_job.py    # Job tracking with per-outlet results
├── scrapers/
│   ├── base.py          # Abstract scraper interface
│   ├── generic_rss.py   # RSS/Atom with media, tags, enclosures
│   ├── content_extractor.py  # Full page content extraction engine
│   └── site_specific/
│       └── generic_html.py   # Smart HTML article discovery
├── services/
│   ├── scraper_service.py    # Concurrent engine with rate limiting
│   ├── translation_service.py # Google Translate with chunking
│   └── article_service.py    # Article CRUD
├── routers/             # FastAPI endpoints
├── schemas/             # Pydantic request/response models
└── seed/                # 80+ pre-seeded outlets
```

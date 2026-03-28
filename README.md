# Gaming PR Platform v4.0

The world's most advanced gaming news aggregator. Scrapes **188 outlets across 34 languages**, auto-translates articles, and provides a full admin dashboard with email outreach tools.

## What It Does

1. **Scrapes 188 gaming outlets** across 34 languages with full content extraction
2. **Extracts everything**: body text, images, videos, author info, tags, categories, OpenGraph, JSON-LD, SEO metadata, review scores, gaming platforms, game titles
3. **Auto-translates** articles into 33 languages via Google Translate
4. **Contact discovery**: automatically finds outlet email addresses and phone numbers
5. **Email outreach**: send emails to outlets directly through connected domains
6. **Real-time feed**: WebSocket live stream of new articles as they're scraped
7. **Admin dashboard**: 11 UI screens with sidebar navigation, role-based access

## Supported Languages & Outlets (188 total)

| Language | Code | Outlets | Examples |
|----------|------|---------|----------|
| English | en | 34 | IGN, GameSpot, Kotaku, PC Gamer, Polygon, Eurogamer, VGC, The Escapist |
| Spanish | es | 12 | Vandal, 3DJuegos, MeriStation, HobbyConsolas, Cultura Geek |
| Mandarin Chinese | zh-CN | 9 | GamerSky, 17173, GameLook, Bahamut, VGtime |
| Portuguese | pt | 9 | IGN Brasil, The Enemy, Techtudo, Eurogamer PT, 4gnews |
| Japanese | ja | 9 | 4Gamer, Famitsu, Game Watch, Automaton, Inside Games |
| French | fr | 8 | Jeuxvideo.com, Gamekult, JeuxActu, Millenium |
| Russian | ru | 7 | DTF, Igromania, StopGame, PlayGround |
| Hindi | hi | 6 | IGN India, Sportskeeda, AFK Gaming |
| Korean | ko | 6 | Inven, GameMeca, This Is Game, Ruliweb |
| German | de | 6 | GameStar, GamePro, Gameswelt, PC Games |
| Arabic | ar | 6 | Saudi Gamer, ArabHardware, TRUE Gaming, IGN ME |
| Turkish | tr | 5 | Oyungezer, DonanımHaber, Merlin'in Kazanı |
| Indonesian | id | 5 | DuniaGames, KotakGame, IniGame |
| Dutch | nl | 5 | Power Unlimited, Gamereactor NL, InsideGamer |
| Finnish | fi | 5 | Pelaaja, Muropaketti, V2.fi |
| Czech | cs | 5 | BonusWeb, Games.cz, Zing |
| Filipino | tl | 5 | UnGeek, GG Network, Sirus Gaming |
| Bengali | bn | 4 | TechShhor, GameBangla, Potaka Gaming |
| Thai | th | 4 | Online Station, GamingDose |
| Polish | pl | 4 | GRYOnline.pl, Gram.pl |
| Hungarian | hu | 4 | GameStar HU, Logout, GameChannel |
| Vietnamese | vi | 4 | GameK, Genk, VNGames |
| Italian | it | 3 | Multiplayer.it, Everyeye.it |
| Swedish | sv | 3 | FZ.se, Gamereactor SE |
| Romanian | ro | 3 | Go4Games, Games-ede |
| Malay | ms | 3 | Amanz Gaming, SoyaCincau |
| Ukrainian | uk | 3 | GamePost, IGN Ukraine, PlayUA |
| Norwegian | no | 2 | Gamer.no, PressFire.no |
| Greek | el | 2 | Enternity.gr, GameWorld.gr |
| Hebrew | he | 2 | GamePro Israel, Gaming.co.il |
| Persian | fa | 2 | Zoomg, Bazinama |
| Danish | da | 1 | Gamereactor DK |
| Cantonese | zh-HK | 1 | Unwire.hk |
| Swahili | sw | 1 | GameZone Africa |

## UI Screens

| Screen | Path | Description |
|--------|------|-------------|
| Dashboard | `/dashboard` | System health, stats, language coverage, top outlets |
| Scraped Articles | `/articles` | Browse/search/filter scraped articles with detail modal |
| My Articles | `/manage/articles` | Create/edit articles with auto-translation to 33 languages |
| Translations | `/translations` | View per-language translations, retry failed ones |
| Outlets | `/outlets` | Table of all outlets, detail panel, admin edit, bulk scrape/email |
| Scraper Console | `/scraper` | Run scrapes, job history, circuit breakers, retry queue, schedule |
| Live Feed | `/feed` | WebSocket real-time article stream with filters |
| Email | `/emails` | Domain management, send emails, delivery stats |
| Webhooks | `/webhooks` | Create/toggle/test webhooks with event filtering |
| Export | `/export` | Download as JSON/CSV/RSS with filters |
| Profile | `/profile` | Account info, API token, quick actions |

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env — at minimum set JWT_SECRET_KEY for production
python main.py
```

Server runs at `http://localhost:8000`. API docs at `/docs`.

For PostgreSQL, set `DATABASE_URL=postgresql://user:pass@host:port/dbname` in `.env`.
SQLite is the default for local development.

## Advanced Scraping Features (v4)

- **Circuit breaker**: auto-disables failing outlets, recovers after timeout
- **Stealth headers**: rotates User-Agent, adds domain-specific headers
- **Playwright fallback**: browser rendering for JS-heavy sites
- **Retry queue**: failed extractions queued with exponential backoff
- **Adaptive scheduling**: learns outlet update frequency, scrapes accordingly
- **Content change tracking**: detects article updates via content hashing
- **SimHash deduplication**: 85% similarity threshold across 500 recent articles
- **Sitemap discovery**: auto-discovers sitemaps from robots.txt
- **robots.txt compliance**: respects crawl delays and disallow rules
- **Contact scraper**: discovers outlet emails and phone numbers automatically
- **SSRF protection**: blocks requests to private IPs, metadata endpoints

## Security

- **JWT authentication** with auto-generated cryptographic secret
- **Admin role system** with `get_admin_user` dependency for protected endpoints
- **Rate limiting**: login (10/min), register (5/min) per IP
- **SSRF protection**: blocks webhooks and scrapers from targeting internal networks
- **Security headers**: X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- **CORS**: configurable allowed origins (defaults to same-origin in production)
- **Input validation**: Pydantic schemas on all endpoints, SQLAlchemy parameterized queries
- **Global exception handler**: unhandled errors return clean JSON, never raw tracebacks

## Design System

A unified design system (`styles.css`) governs the look of all 11 UI screens:

- **7-step type scale**: `--text-xs` (0.68rem) through `--text-2xl` (1.6rem)
- **9-step spacing**: `--sp-1` (4px) through `--sp-9` (48px) on 8px grid
- **3 border radii**: `--radius-sm` (6px), `--radius` (10px), `--radius-lg` (16px)
- **Material motion**: `--ease` cubic-bezier(0.4, 0, 0.2, 1) on all transitions
- **Unified components**: `.card`, `.stat-card`, `.badge` (5 variants), `.btn` (4 variants), tables, forms
- **Micro-interactions**: card hover lift, button press scale, input focus glow, zebra-striped tables
- **Skeleton loaders**: shimmer animation for loading states
- **Accessibility**: `:focus-visible` outline, proper contrast ratios, custom scrollbar

Sidebar navigation (`nav.js`):
- Active link with left accent bar + gradient background
- Link hover with translateX motion
- Toast notification system for background job completion
- Mobile hamburger with backdrop-blur overlay (768px breakpoint)

## Testing

31 automated tests covering:

| Suite | Tests | Coverage |
|-------|-------|----------|
| `test_url_safety.py` | 13 | SSRF protection — private IPs, metadata, schemes |
| `test_webhooks.py` | 8 | CRUD, toggle, SSRF blocking, auth required |
| `test_admin.py` | 5 | Admin-only mutations, user rejection, seed dedup |
| `test_monitoring.py` | 3 | Dashboard and health endpoints |
| `test_rate_limit.py` | 2 | Login and register brute-force protection |

Run tests: `pytest tests/ -v`

## API Endpoints

All endpoints are documented at `/docs` (Swagger UI) and `/redoc` (ReDoc).

### Auth
- `POST /api/auth/register` — Create account (rate limited)
- `POST /api/auth/login` — Login (rate limited)
- `GET /api/auth/me` — Current user profile

### Articles (CRUD + Auto-Translation)
- `POST /api/articles/` — Create article (auto-translates to 33 languages)
- `GET /api/articles/` — List articles
- `GET /api/articles/{id}` — Get with translations
- `PUT /api/articles/{id}` — Update (re-translates changed content)
- `DELETE /api/articles/{id}` — Delete

### Translations
- `GET /api/articles/{id}/translations/` — All translations
- `GET /api/articles/{id}/translations/{lang}` — Specific language
- `POST /api/articles/{id}/translations/retry` — Retry failed/pending only

### Scraped Articles
- `GET /api/scraper/articles` — List (filter: language, outlet, type, full_content, search)
- `GET /api/scraper/articles/{id}` — Full detail
- `GET /api/scraper/articles/{id}/history` — Content change history

### Scraper Control
- `POST /api/scraper/run` — Scrape all outlets (sync or async)
- `POST /api/scraper/run/{outlet_id}` — Scrape single outlet
- `GET /api/scraper/jobs` — Job history
- `GET /api/scraper/stats` — Statistics
- `GET /api/scraper/circuit-breakers` — Circuit breaker status
- `GET /api/scraper/retry-queue` — Retry queue stats
- `GET /api/scraper/schedule` — Adaptive schedule

### Outlets (admin-only for mutations)
- `GET /api/outlets/` — List (filter: language, active, category, search)
- `GET /api/outlets/stats` — Aggregate stats
- `POST /api/outlets/` — Create (admin)
- `PATCH /api/outlets/{id}` — Update (admin)
- `DELETE /api/outlets/{id}` — Delete (admin)

### Email
- `POST /api/email/domains` — Connect domain
- `GET /api/email/domains` — List domains
- `POST /api/email/domains/{id}/verify` — Verify DNS
- `POST /api/email/send` — Send email
- `GET /api/email/emails` — Sent email list
- `GET /api/email/stats` — Delivery stats

### Webhooks
- `POST /api/webhooks/` — Create (SSRF-validated)
- `GET /api/webhooks/` — List all
- `POST /api/webhooks/{id}/toggle` — Enable/disable
- `POST /api/webhooks/{id}/test` — Send test event

### Export
- `GET /api/export/json` — JSON export with filters
- `GET /api/export/csv` — CSV export
- `GET /api/export/rss` — RSS 2.0 feed

### Monitoring
- `GET /api/monitoring/dashboard` — Full health dashboard
- `GET /api/monitoring/health` — Health check

### WebSocket
- `WS /ws/feed` — Real-time article stream with filter support

## Architecture

```
app/
├── models/                  # SQLAlchemy models
│   ├── outlet.py            # 188 outlets with contact info, scrape tracking
│   ├── scraped_article.py   # 40+ fields per article
│   ├── article.py           # User articles + translations
│   ├── scrape_job.py        # Job tracking with per-outlet results
│   ├── webhook.py           # Webhook + content snapshots
│   ├── email.py             # Domains + sent emails
│   └── user.py              # Users with admin role
├── scrapers/
│   ├── generic_rss.py       # RSS/Atom parser
│   ├── content_extractor.py # Full page extraction engine
│   ├── contact_scraper.py   # Email/phone discovery
│   ├── circuit_breaker.py   # Per-outlet failure tracking
│   ├── retry_queue.py       # Failed extraction retry
│   ├── dedup.py             # SimHash deduplication
│   ├── stealth.py           # Header rotation
│   ├── robots.py            # robots.txt compliance
│   └── sitemap.py           # Sitemap discovery
├── services/
│   ├── scraper_service.py   # Concurrent scraping engine
│   ├── translation_service.py # Google Translate with chunking
│   ├── webhook_service.py   # HMAC-signed delivery
│   ├── email_service.py     # Domain + email management
│   ├── auth_service.py      # JWT + password hashing
│   └── adaptive_scheduler.py # Smart scrape scheduling
├── routers/                 # FastAPI endpoint handlers
├── schemas/                 # Pydantic request/response models
├── utils/
│   └── url_safety.py        # SSRF protection
├── static/
│   ├── styles.css           # Unified design system (tokens, components)
│   ├── nav.js               # Sidebar nav + auth modals + toast notifications
│   ├── landing.html          # Public marketing page
│   ├── dashboard.html        # Monitoring dashboard
│   ├── outlets.html          # Outlet table + detail + admin edit + bulk scrape/email
│   ├── articles.html         # Scraped article browser
│   ├── scraper.html          # Admin scraper console
│   └── ...                   # 5 more screens (feed, emails, webhooks, export, profile)
├── seed/                    # 188 pre-seeded outlets
└── config.py                # All settings with env overrides

tests/
├── conftest.py              # Fixtures: in-memory SQLite, auth helpers
├── test_url_safety.py       # SSRF protection (13 tests)
├── test_webhooks.py         # Webhook CRUD + SSRF (8 tests)
├── test_admin.py            # Admin access control (5 tests)
├── test_monitoring.py       # Dashboard + health (3 tests)
├── test_rate_limit.py       # Auth rate limiting (2 tests)
├── test_auth.py             # Registration + login
├── test_articles.py         # Article CRUD
├── test_outlets.py          # Outlet operations
├── test_scraper.py          # RSS scraper + video detection
├── test_translations.py     # Translation logic
├── test_content_extractor.py # Content extraction
└── test_v4_features.py      # Circuit breaker, retry, stealth, dedup
```

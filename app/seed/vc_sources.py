from sqlalchemy.orm import Session

from app.models.outlet import GamingOutlet

GAMING_VC_SOURCES = [
    # ═══════════════════════════════════════════
    # GAMING-FOCUSED VC FIRMS
    # ═══════════════════════════════════════════

    # Tier 1: Dedicated Gaming VCs
    {"name": "BITKRAFT Ventures", "url": "https://www.bitkraft.vc", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "vc", "priority": 1, "category": "gaming_vc", "description": "Leading gaming and interactive media venture fund", "social_twitter": "https://twitter.com/BITKRAFTvc", "scraper_config": {"blog_paths": ["/blog", "/news", "/insights"], "portfolio_url": "/portfolio"}},
    {"name": "Griffin Gaming Partners", "url": "https://www.griffingp.com", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "vc", "priority": 1, "category": "gaming_vc", "description": "Venture capital firm focused exclusively on gaming", "social_twitter": "https://twitter.com/GriffinGaming", "scraper_config": {"blog_paths": ["/blog", "/news"], "portfolio_url": "/portfolio"}},
    {"name": "Makers Fund", "url": "https://www.makersfund.com", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "vc", "priority": 1, "category": "gaming_vc", "description": "Global interactive entertainment venture fund", "scraper_config": {"blog_paths": ["/blog", "/news"], "portfolio_url": "/portfolio"}},
    {"name": "Galaxy Interactive", "url": "https://www.galaxyinteractive.io", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "vc", "priority": 1, "category": "gaming_vc", "description": "Gaming and interactive technology investment firm", "social_twitter": "https://twitter.com/GLXYInteractive", "scraper_config": {"blog_paths": ["/blog", "/insights"], "portfolio_url": "/portfolio"}},
    {"name": "Play Ventures", "url": "https://www.playventures.vc", "rss_feed_url": None, "language": "en", "region": "EU", "country": "Finland", "scraper_type": "vc", "priority": 1, "category": "gaming_vc", "description": "Gaming-focused venture capital firm", "social_twitter": "https://twitter.com/playventures", "scraper_config": {"blog_paths": ["/blog", "/news"], "portfolio_url": "/portfolio"}},
    {"name": "Konvoy Ventures", "url": "https://www.konvoy.vc", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "vc", "priority": 1, "category": "gaming_vc", "description": "Venture capital fund dedicated to gaming", "social_twitter": "https://twitter.com/KonvoyVentures", "scraper_config": {"blog_paths": ["/blog", "/insights", "/research"], "portfolio_url": "/portfolio"}},
    {"name": "Hiro Capital", "url": "https://www.hirocapital.com", "rss_feed_url": None, "language": "en", "region": "UK", "country": "United Kingdom", "scraper_type": "vc", "priority": 2, "category": "gaming_vc", "description": "European gaming, metaverse, and esports VC", "social_twitter": "https://twitter.com/HiroCapital_", "scraper_config": {"blog_paths": ["/blog", "/news"], "portfolio_url": "/portfolio"}},
    {"name": "Vgames", "url": "https://www.vgames.vc", "rss_feed_url": None, "language": "en", "region": "IL", "country": "Israel", "scraper_type": "vc", "priority": 2, "category": "gaming_vc", "description": "Israel-based gaming venture fund", "social_twitter": "https://twitter.com/VgamesFund", "scraper_config": {"blog_paths": ["/blog", "/news"], "portfolio_url": "/portfolio"}},
    {"name": "1Up Ventures", "url": "https://www.1upventures.com", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "vc", "priority": 2, "category": "gaming_vc", "description": "Gaming-focused venture capital", "scraper_config": {"blog_paths": ["/blog", "/news"], "portfolio_url": "/portfolio"}},
    {"name": "GameGroove Capital", "url": "https://www.gamegroovecapital.com", "rss_feed_url": None, "language": "en", "region": "EU", "country": "Austria", "scraper_type": "vc", "priority": 3, "category": "gaming_vc", "description": "European gaming investment firm", "scraper_config": {"blog_paths": ["/blog", "/news"], "portfolio_url": "/portfolio"}},

    # Tier 2: Major VCs with Gaming Divisions
    {"name": "a16z Games", "url": "https://a16z.com/games", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "vc", "priority": 1, "category": "gaming_vc", "description": "Andreessen Horowitz gaming investment arm", "social_twitter": "https://twitter.com/a16z", "scraper_config": {"blog_paths": ["/blog", "/content"], "portfolio_url": "/portfolio"}},
    {"name": "Lego Ventures", "url": "https://www.legoventures.com", "rss_feed_url": None, "language": "en", "region": "EU", "country": "Denmark", "scraper_type": "vc", "priority": 2, "category": "gaming_vc", "description": "LEGO Group venture arm investing in play and gaming", "scraper_config": {"blog_paths": ["/blog", "/news"], "portfolio_url": "/portfolio"}},
    {"name": "MTG (Modern Times Group)", "url": "https://www.mtg.com", "rss_feed_url": None, "language": "en", "region": "EU", "country": "Sweden", "scraper_type": "vc", "priority": 2, "category": "gaming_vc", "description": "Gaming and esports investment company", "social_twitter": "https://twitter.com/MTGab", "scraper_config": {"blog_paths": ["/news", "/press-releases"], "portfolio_url": "/our-companies"}},
    {"name": "Krafton Ventures", "url": "https://www.krafton.com", "rss_feed_url": None, "language": "en", "region": "KR", "country": "South Korea", "scraper_type": "vc", "priority": 2, "category": "gaming_vc", "description": "PUBG creator's investment arm for gaming", "social_twitter": "https://twitter.com/krafton_inc", "scraper_config": {"blog_paths": ["/blog", "/news", "/press"], "portfolio_url": "/investment"}},

    # Tier 3: Web3/Blockchain Gaming VCs
    {"name": "Animoca Brands", "url": "https://www.animocabrands.com", "rss_feed_url": None, "language": "en", "region": "HK", "country": "Hong Kong", "scraper_type": "vc", "priority": 2, "category": "gaming_vc", "description": "Web3 gaming investor and publisher", "social_twitter": "https://twitter.com/animocabrands", "scraper_config": {"blog_paths": ["/blog", "/news"], "portfolio_url": "/portfolio"}},
    {"name": "Delphi Digital", "url": "https://delphidigital.io", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "vc", "priority": 3, "category": "gaming_vc", "description": "Crypto and gaming research and investment", "social_twitter": "https://twitter.com/Delphi_Digital", "scraper_config": {"blog_paths": ["/blog", "/research"], "portfolio_url": "/ventures"}},

    # Tier 4: Gaming Industry Investment Firms
    {"name": "Overwolf Fund", "url": "https://fund.overwolf.com", "rss_feed_url": None, "language": "en", "region": "IL", "country": "Israel", "scraper_type": "vc", "priority": 2, "category": "gaming_vc", "description": "Fund for in-game creator tools and gaming platforms", "social_twitter": "https://twitter.com/TheOverwolf", "scraper_config": {"blog_paths": ["/blog", "/news"], "portfolio_url": "/portfolio"}},
    {"name": "Xsolla Capital", "url": "https://xsolla.com", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "vc", "priority": 3, "category": "gaming_vc", "description": "Gaming commerce platform and investment", "social_twitter": "https://twitter.com/Xsolla", "scraper_config": {"blog_paths": ["/blog", "/news", "/resources"], "portfolio_url": "/partner"}},
    {"name": "Naavik", "url": "https://naavik.co", "rss_feed_url": "https://naavik.co/feed", "language": "en", "region": "US", "country": "United States", "scraper_type": "vc", "priority": 2, "category": "gaming_vc", "description": "Gaming industry research, advisory, and investment", "social_twitter": "https://twitter.com/NaavikCo", "scraper_config": {"blog_paths": ["/blog", "/digest", "/deep-dives"]}},

    # Asian Gaming VCs
    {"name": "NetEase Capital", "url": "https://www.neteasegames.com", "rss_feed_url": None, "language": "en", "region": "CN", "country": "China", "scraper_type": "vc", "priority": 2, "category": "gaming_vc", "description": "NetEase gaming investment and publishing arm", "scraper_config": {"blog_paths": ["/news", "/blog"]}},
    {"name": "Sea Capital (Garena)", "url": "https://www.sea.com", "rss_feed_url": None, "language": "en", "region": "SG", "country": "Singapore", "scraper_type": "vc", "priority": 2, "category": "gaming_vc", "description": "Southeast Asian gaming and digital entertainment conglomerate", "scraper_config": {"blog_paths": ["/news", "/press-releases"]}},
    {"name": "Tencent Investment", "url": "https://www.tencent.com", "rss_feed_url": None, "language": "en", "region": "CN", "country": "China", "scraper_type": "vc", "priority": 1, "category": "gaming_vc", "description": "World's largest gaming company investment arm", "scraper_config": {"blog_paths": ["/en-us/articles", "/news"]}},
    {"name": "Savvy Games Group", "url": "https://www.savvygames.com", "rss_feed_url": None, "language": "en", "region": "SA", "country": "Saudi Arabia", "scraper_type": "vc", "priority": 2, "category": "gaming_vc", "description": "Saudi Arabian gaming investment group", "scraper_config": {"blog_paths": ["/news", "/blog", "/media"]}},
    {"name": "Embracer Group", "url": "https://www.embracer.com", "rss_feed_url": None, "language": "en", "region": "EU", "country": "Sweden", "scraper_type": "vc", "priority": 2, "category": "gaming_vc", "description": "Major European gaming investment and holding company", "social_twitter": "https://twitter.com/EmbracerGroup", "scraper_config": {"blog_paths": ["/news", "/press-releases"], "portfolio_url": "/companies"}},
]


def seed_vc_sources(db: Session) -> int:
    """Seed the database with gaming VC sources. Returns the number of new sources added."""
    added = 0
    for source_data in GAMING_VC_SOURCES:
        existing = db.query(GamingOutlet).filter(GamingOutlet.url == source_data["url"]).first()
        if not existing:
            outlet = GamingOutlet(**source_data)
            db.add(outlet)
            added += 1
    db.commit()
    return added

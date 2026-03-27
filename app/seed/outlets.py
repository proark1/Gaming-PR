from sqlalchemy.orm import Session

from app.models.outlet import GamingOutlet

GAMING_OUTLETS = [
    # English
    {"name": "IGN", "url": "https://www.ign.com", "rss_feed_url": "https://feeds.feedburner.com/ign/games-all", "language": "en", "region": "US", "scraper_type": "rss"},
    {"name": "GameSpot", "url": "https://www.gamespot.com", "rss_feed_url": "https://www.gamespot.com/feeds/news", "language": "en", "region": "US", "scraper_type": "rss"},
    {"name": "Kotaku", "url": "https://kotaku.com", "rss_feed_url": "https://kotaku.com/rss", "language": "en", "region": "US", "scraper_type": "rss"},
    {"name": "PC Gamer", "url": "https://www.pcgamer.com", "rss_feed_url": "https://www.pcgamer.com/rss/", "language": "en", "region": "US", "scraper_type": "rss"},
    {"name": "Eurogamer", "url": "https://www.eurogamer.net", "rss_feed_url": "https://www.eurogamer.net/feed", "language": "en", "region": "UK", "scraper_type": "rss"},
    {"name": "Polygon", "url": "https://www.polygon.com", "rss_feed_url": "https://www.polygon.com/rss/index.xml", "language": "en", "region": "US", "scraper_type": "rss"},
    {"name": "Rock Paper Shotgun", "url": "https://www.rockpapershotgun.com", "rss_feed_url": "https://www.rockpapershotgun.com/feed", "language": "en", "region": "UK", "scraper_type": "rss"},

    # Mandarin Chinese
    {"name": "GamerSky", "url": "https://www.gamersky.com", "rss_feed_url": None, "language": "zh-CN", "region": "CN", "scraper_type": "generic"},
    {"name": "17173", "url": "https://www.17173.com", "rss_feed_url": None, "language": "zh-CN", "region": "CN", "scraper_type": "generic"},
    {"name": "GameLook", "url": "https://www.gamelook.com.cn", "rss_feed_url": "https://www.gamelook.com.cn/feed", "language": "zh-CN", "region": "CN", "scraper_type": "rss"},
    {"name": "游民星空 (Youmin Xingkong)", "url": "https://www.gamersky.com/news/", "rss_feed_url": None, "language": "zh-CN", "region": "CN", "scraper_type": "generic"},
    {"name": "游侠网 (Ali213)", "url": "https://www.ali213.net", "rss_feed_url": None, "language": "zh-CN", "region": "CN", "scraper_type": "generic"},

    # Hindi
    {"name": "IGN India", "url": "https://in.ign.com", "rss_feed_url": "https://in.ign.com/feed", "language": "hi", "region": "IN", "scraper_type": "rss"},
    {"name": "GamingMonk", "url": "https://www.gamingmonk.com", "rss_feed_url": None, "language": "hi", "region": "IN", "scraper_type": "generic"},
    {"name": "Sportskeeda Esports", "url": "https://www.sportskeeda.com/esports", "rss_feed_url": "https://www.sportskeeda.com/feed/esports", "language": "hi", "region": "IN", "scraper_type": "rss"},

    # Spanish
    {"name": "Vandal", "url": "https://vandal.elespanol.com", "rss_feed_url": "https://vandal.elespanol.com/xml.cgi", "language": "es", "region": "ES", "scraper_type": "rss"},
    {"name": "3DJuegos", "url": "https://www.3djuegos.com", "rss_feed_url": "https://www.3djuegos.com/universo/rss/rss.php?plats=0", "language": "es", "region": "ES", "scraper_type": "rss"},
    {"name": "MeriStation", "url": "https://as.com/meristation/", "rss_feed_url": None, "language": "es", "region": "ES", "scraper_type": "generic"},
    {"name": "Vida Extra", "url": "https://www.vidaextra.com", "rss_feed_url": "https://www.vidaextra.com/atom.xml", "language": "es", "region": "ES", "scraper_type": "rss"},
    {"name": "LevelUp", "url": "https://www.levelup.com", "rss_feed_url": "https://www.levelup.com/rss/", "language": "es", "region": "MX", "scraper_type": "rss"},

    # French
    {"name": "Jeuxvideo.com", "url": "https://www.jeuxvideo.com", "rss_feed_url": "https://www.jeuxvideo.com/rss/rss.xml", "language": "fr", "region": "FR", "scraper_type": "rss"},
    {"name": "Gamekult", "url": "https://www.gamekult.com", "rss_feed_url": "https://www.gamekult.com/feed.xml", "language": "fr", "region": "FR", "scraper_type": "rss"},
    {"name": "JeuxActu", "url": "https://www.jeuxactu.com", "rss_feed_url": "https://www.jeuxactu.com/rss/news.xml", "language": "fr", "region": "FR", "scraper_type": "rss"},
    {"name": "Millenium", "url": "https://www.millenium.org", "rss_feed_url": "https://www.millenium.org/rss", "language": "fr", "region": "FR", "scraper_type": "rss"},

    # Arabic
    {"name": "Saudi Gamer", "url": "https://saudigamer.com", "rss_feed_url": "https://saudigamer.com/feed/", "language": "ar", "region": "SA", "scraper_type": "rss"},
    {"name": "ArabHardware", "url": "https://arabhardware.net", "rss_feed_url": "https://arabhardware.net/feed/", "language": "ar", "region": "EG", "scraper_type": "rss"},
    {"name": "TRUE Gaming", "url": "https://true-gaming.net", "rss_feed_url": "https://true-gaming.net/feed/", "language": "ar", "region": "SA", "scraper_type": "rss"},

    # Bengali
    {"name": "TechShhor Gaming", "url": "https://techshhor.com", "rss_feed_url": "https://techshhor.com/feed/", "language": "bn", "region": "BD", "scraper_type": "rss"},
    {"name": "GameBangla", "url": "https://gamebangla.com", "rss_feed_url": None, "language": "bn", "region": "BD", "scraper_type": "generic"},
    {"name": "Potaka Gaming", "url": "https://potakagaming.com", "rss_feed_url": None, "language": "bn", "region": "BD", "scraper_type": "generic"},

    # Portuguese
    {"name": "IGN Brasil", "url": "https://br.ign.com", "rss_feed_url": "https://br.ign.com/feed", "language": "pt", "region": "BR", "scraper_type": "rss"},
    {"name": "The Enemy", "url": "https://www.theenemy.com.br", "rss_feed_url": "https://www.theenemy.com.br/feed", "language": "pt", "region": "BR", "scraper_type": "rss"},
    {"name": "Techtudo Gaming", "url": "https://www.techtudo.com.br/jogos/", "rss_feed_url": "https://www.techtudo.com.br/rss/jogos/", "language": "pt", "region": "BR", "scraper_type": "rss"},
    {"name": "Eurogamer Portugal", "url": "https://www.eurogamer.pt", "rss_feed_url": "https://www.eurogamer.pt/feed", "language": "pt", "region": "PT", "scraper_type": "rss"},

    # Russian
    {"name": "DTF", "url": "https://dtf.ru", "rss_feed_url": "https://dtf.ru/rss", "language": "ru", "region": "RU", "scraper_type": "rss"},
    {"name": "Igromania", "url": "https://www.igromania.ru", "rss_feed_url": "https://www.igromania.ru/rss/rss_news.xml", "language": "ru", "region": "RU", "scraper_type": "rss"},
    {"name": "StopGame", "url": "https://stopgame.ru", "rss_feed_url": "https://stopgame.ru/rss/news.xml", "language": "ru", "region": "RU", "scraper_type": "rss"},
    {"name": "Kanobu", "url": "https://kanobu.ru", "rss_feed_url": "https://kanobu.ru/rss/", "language": "ru", "region": "RU", "scraper_type": "rss"},

    # Japanese
    {"name": "4Gamer.net", "url": "https://www.4gamer.net", "rss_feed_url": "https://www.4gamer.net/rss/index.xml", "language": "ja", "region": "JP", "scraper_type": "rss"},
    {"name": "Famitsu", "url": "https://www.famitsu.com", "rss_feed_url": "https://www.famitsu.com/feed/", "language": "ja", "region": "JP", "scraper_type": "rss"},
    {"name": "Game Watch", "url": "https://game.watch.impress.co.jp", "rss_feed_url": "https://game.watch.impress.co.jp/data/rss/1.0/gmw/feed.rdf", "language": "ja", "region": "JP", "scraper_type": "rss"},
    {"name": "Dengeki Online", "url": "https://dengekionline.com", "rss_feed_url": "https://dengekionline.com/feed/", "language": "ja", "region": "JP", "scraper_type": "rss"},
    {"name": "Inside Games", "url": "https://www.inside-games.jp", "rss_feed_url": "https://www.inside-games.jp/rss/index.rdf", "language": "ja", "region": "JP", "scraper_type": "rss"},
]


def seed_outlets(db: Session) -> int:
    """Seed the database with known gaming outlets. Returns the number of new outlets added."""
    added = 0
    for outlet_data in GAMING_OUTLETS:
        existing = db.query(GamingOutlet).filter(GamingOutlet.url == outlet_data["url"]).first()
        if not existing:
            outlet = GamingOutlet(**outlet_data)
            db.add(outlet)
            added += 1
    db.commit()
    return added

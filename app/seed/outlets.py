from sqlalchemy.orm import Session

from app.models.outlet import GamingOutlet

GAMING_OUTLETS = [
    # ═══════════════════════════════════════════
    # ENGLISH (en) - Global leaders
    # ═══════════════════════════════════════════
    {"name": "IGN", "url": "https://www.ign.com", "rss_feed_url": "https://feeds.feedburner.com/ign/games-all", "language": "en", "region": "US", "country": "United States", "scraper_type": "rss", "priority": 1, "category": "gaming_news", "description": "Leading gaming media covering news, reviews, and guides"},
    {"name": "GameSpot", "url": "https://www.gamespot.com", "rss_feed_url": "https://www.gamespot.com/feeds/news", "language": "en", "region": "US", "country": "United States", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},
    {"name": "Kotaku", "url": "https://kotaku.com", "rss_feed_url": "https://kotaku.com/rss", "language": "en", "region": "US", "country": "United States", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},
    {"name": "PC Gamer", "url": "https://www.pcgamer.com", "rss_feed_url": "https://www.pcgamer.com/rss/", "language": "en", "region": "US", "country": "United States", "scraper_type": "rss", "priority": 1, "category": "pc_gaming"},
    {"name": "Eurogamer", "url": "https://www.eurogamer.net", "rss_feed_url": "https://www.eurogamer.net/feed", "language": "en", "region": "UK", "country": "United Kingdom", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},
    {"name": "Polygon", "url": "https://www.polygon.com", "rss_feed_url": "https://www.polygon.com/rss/index.xml", "language": "en", "region": "US", "country": "United States", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},
    {"name": "Rock Paper Shotgun", "url": "https://www.rockpapershotgun.com", "rss_feed_url": "https://www.rockpapershotgun.com/feed", "language": "en", "region": "UK", "country": "United Kingdom", "scraper_type": "rss", "priority": 2, "category": "pc_gaming"},
    {"name": "GamesRadar+", "url": "https://www.gamesradar.com", "rss_feed_url": "https://www.gamesradar.com/rss/", "language": "en", "region": "UK", "country": "United Kingdom", "scraper_type": "rss", "priority": 2, "category": "gaming_news"},
    {"name": "The Verge Gaming", "url": "https://www.theverge.com/games", "rss_feed_url": "https://www.theverge.com/rss/games/index.xml", "language": "en", "region": "US", "country": "United States", "scraper_type": "rss", "priority": 2, "category": "gaming_news"},
    {"name": "VG247", "url": "https://www.vg247.com", "rss_feed_url": "https://www.vg247.com/feed", "language": "en", "region": "UK", "country": "United Kingdom", "scraper_type": "rss", "priority": 2, "category": "gaming_news"},
    {"name": "Destructoid", "url": "https://www.destructoid.com", "rss_feed_url": "https://www.destructoid.com/feed/", "language": "en", "region": "US", "country": "United States", "scraper_type": "rss", "priority": 3, "category": "gaming_news"},
    {"name": "Game Informer", "url": "https://www.gameinformer.com", "rss_feed_url": "https://www.gameinformer.com/rss.xml", "language": "en", "region": "US", "country": "United States", "scraper_type": "rss", "priority": 2, "category": "gaming_news"},
    {"name": "Push Square", "url": "https://www.pushsquare.com", "rss_feed_url": "https://www.pushsquare.com/feeds/latest", "language": "en", "region": "UK", "country": "United Kingdom", "scraper_type": "rss", "priority": 3, "category": "playstation"},
    {"name": "Nintendo Life", "url": "https://www.nintendolife.com", "rss_feed_url": "https://www.nintendolife.com/feeds/latest", "language": "en", "region": "UK", "country": "United Kingdom", "scraper_type": "rss", "priority": 3, "category": "nintendo"},
    {"name": "Pure Xbox", "url": "https://www.purexbox.com", "rss_feed_url": "https://www.purexbox.com/feeds/latest", "language": "en", "region": "UK", "country": "United Kingdom", "scraper_type": "rss", "priority": 3, "category": "xbox"},
    {"name": "Dexerto Gaming", "url": "https://www.dexerto.com/gaming/", "rss_feed_url": "https://www.dexerto.com/feed/", "language": "en", "region": "UK", "country": "United Kingdom", "scraper_type": "rss", "priority": 3, "category": "esports"},
    {"name": "PCGamesN", "url": "https://www.pcgamesn.com", "rss_feed_url": "https://www.pcgamesn.com/mainrss.xml", "language": "en", "region": "UK", "country": "United Kingdom", "scraper_type": "rss", "priority": 3, "category": "pc_gaming"},
    {"name": "TouchArcade", "url": "https://toucharcade.com", "rss_feed_url": "https://toucharcade.com/feed/", "language": "en", "region": "US", "country": "United States", "scraper_type": "rss", "priority": 4, "category": "mobile_gaming"},
    {"name": "TheGamer", "url": "https://www.thegamer.com", "rss_feed_url": "https://www.thegamer.com/feed/", "language": "en", "region": "US", "country": "United States", "scraper_type": "rss", "priority": 3, "category": "gaming_news"},
    {"name": "GameRant", "url": "https://gamerant.com", "rss_feed_url": "https://gamerant.com/feed/", "language": "en", "region": "US", "country": "United States", "scraper_type": "rss", "priority": 3, "category": "gaming_news"},

    # ═══════════════════════════════════════════
    # MANDARIN CHINESE (zh-CN)
    # ═══════════════════════════════════════════
    {"name": "GamerSky (游民星空)", "url": "https://www.gamersky.com", "rss_feed_url": None, "language": "zh-CN", "region": "CN", "country": "China", "scraper_type": "generic", "priority": 1, "category": "gaming_news"},
    {"name": "17173", "url": "https://www.17173.com", "rss_feed_url": None, "language": "zh-CN", "region": "CN", "country": "China", "scraper_type": "generic", "priority": 1, "category": "gaming_news"},
    {"name": "GameLook", "url": "https://www.gamelook.com.cn", "rss_feed_url": "https://www.gamelook.com.cn/feed", "language": "zh-CN", "region": "CN", "country": "China", "scraper_type": "rss", "priority": 2, "category": "gaming_industry"},
    {"name": "Ali213 (游侠网)", "url": "https://www.ali213.net", "rss_feed_url": None, "language": "zh-CN", "region": "CN", "country": "China", "scraper_type": "generic", "priority": 1, "category": "gaming_news"},
    {"name": "3DM Game", "url": "https://www.3dmgame.com", "rss_feed_url": None, "language": "zh-CN", "region": "CN", "country": "China", "scraper_type": "generic", "priority": 2, "category": "gaming_news"},
    {"name": "游研社 (Yystv)", "url": "https://www.yystv.cn", "rss_feed_url": None, "language": "zh-CN", "region": "CN", "country": "China", "scraper_type": "generic", "priority": 2, "category": "gaming_culture"},
    {"name": "A9VG", "url": "https://www.a9vg.com", "rss_feed_url": None, "language": "zh-CN", "region": "CN", "country": "China", "scraper_type": "generic", "priority": 3, "category": "console_gaming"},
    {"name": "VGtime (游戏时光)", "url": "https://www.vgtime.com", "rss_feed_url": None, "language": "zh-CN", "region": "CN", "country": "China", "scraper_type": "generic", "priority": 2, "category": "gaming_news"},
    {"name": "巴哈姆特 (Bahamut)", "url": "https://gnn.gamer.com.tw", "rss_feed_url": "https://gnn.gamer.com.tw/rss.xml", "language": "zh-CN", "region": "TW", "country": "Taiwan", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},

    # ═══════════════════════════════════════════
    # HINDI (hi)
    # ═══════════════════════════════════════════
    {"name": "IGN India", "url": "https://in.ign.com", "rss_feed_url": "https://in.ign.com/feed", "language": "hi", "region": "IN", "country": "India", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},
    {"name": "Sportskeeda Esports", "url": "https://www.sportskeeda.com/esports", "rss_feed_url": "https://www.sportskeeda.com/feed/esports", "language": "hi", "region": "IN", "country": "India", "scraper_type": "rss", "priority": 1, "category": "esports"},
    {"name": "GamingMonk", "url": "https://www.gamingmonk.com", "rss_feed_url": None, "language": "hi", "region": "IN", "country": "India", "scraper_type": "generic", "priority": 2, "category": "esports"},
    {"name": "AFK Gaming", "url": "https://afkgaming.com", "rss_feed_url": "https://afkgaming.com/feed", "language": "hi", "region": "IN", "country": "India", "scraper_type": "rss", "priority": 2, "category": "esports"},
    {"name": "GameRiv", "url": "https://gameriv.com", "rss_feed_url": "https://gameriv.com/feed/", "language": "hi", "region": "IN", "country": "India", "scraper_type": "rss", "priority": 3, "category": "gaming_news"},
    {"name": "91mobiles Gaming", "url": "https://www.91mobiles.com/hub/gaming/", "rss_feed_url": None, "language": "hi", "region": "IN", "country": "India", "scraper_type": "generic", "priority": 3, "category": "mobile_gaming"},

    # ═══════════════════════════════════════════
    # SPANISH (es)
    # ═══════════════════════════════════════════
    {"name": "Vandal", "url": "https://vandal.elespanol.com", "rss_feed_url": "https://vandal.elespanol.com/xml.cgi", "language": "es", "region": "ES", "country": "Spain", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},
    {"name": "3DJuegos", "url": "https://www.3djuegos.com", "rss_feed_url": "https://www.3djuegos.com/universo/rss/rss.php?plats=0", "language": "es", "region": "ES", "country": "Spain", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},
    {"name": "MeriStation", "url": "https://as.com/meristation/", "rss_feed_url": None, "language": "es", "region": "ES", "country": "Spain", "scraper_type": "generic", "priority": 1, "category": "gaming_news"},
    {"name": "Vida Extra", "url": "https://www.vidaextra.com", "rss_feed_url": "https://www.vidaextra.com/atom.xml", "language": "es", "region": "ES", "country": "Spain", "scraper_type": "rss", "priority": 2, "category": "gaming_news"},
    {"name": "LevelUp", "url": "https://www.levelup.com", "rss_feed_url": "https://www.levelup.com/rss/", "language": "es", "region": "MX", "country": "Mexico", "scraper_type": "rss", "priority": 2, "category": "gaming_news"},
    {"name": "HobbyConsolas", "url": "https://www.hobbyconsolas.com", "rss_feed_url": "https://www.hobbyconsolas.com/rss", "language": "es", "region": "ES", "country": "Spain", "scraper_type": "rss", "priority": 2, "category": "gaming_news"},
    {"name": "IGN España", "url": "https://es.ign.com", "rss_feed_url": "https://es.ign.com/feed", "language": "es", "region": "ES", "country": "Spain", "scraper_type": "rss", "priority": 2, "category": "gaming_news"},
    {"name": "Areajugones", "url": "https://areajugones.sport.es", "rss_feed_url": "https://areajugones.sport.es/feed/", "language": "es", "region": "ES", "country": "Spain", "scraper_type": "rss", "priority": 3, "category": "gaming_news"},
    {"name": "Atomix", "url": "https://atomix.vg", "rss_feed_url": "https://atomix.vg/feed/", "language": "es", "region": "MX", "country": "Mexico", "scraper_type": "rss", "priority": 3, "category": "gaming_news"},

    # ═══════════════════════════════════════════
    # FRENCH (fr)
    # ═══════════════════════════════════════════
    {"name": "Jeuxvideo.com", "url": "https://www.jeuxvideo.com", "rss_feed_url": "https://www.jeuxvideo.com/rss/rss.xml", "language": "fr", "region": "FR", "country": "France", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},
    {"name": "Gamekult", "url": "https://www.gamekult.com", "rss_feed_url": "https://www.gamekult.com/feed.xml", "language": "fr", "region": "FR", "country": "France", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},
    {"name": "JeuxActu", "url": "https://www.jeuxactu.com", "rss_feed_url": "https://www.jeuxactu.com/rss/news.xml", "language": "fr", "region": "FR", "country": "France", "scraper_type": "rss", "priority": 2, "category": "gaming_news"},
    {"name": "Millenium", "url": "https://www.millenium.org", "rss_feed_url": "https://www.millenium.org/rss", "language": "fr", "region": "FR", "country": "France", "scraper_type": "rss", "priority": 2, "category": "esports"},
    {"name": "IGN France", "url": "https://fr.ign.com", "rss_feed_url": "https://fr.ign.com/feed", "language": "fr", "region": "FR", "country": "France", "scraper_type": "rss", "priority": 2, "category": "gaming_news"},
    {"name": "Gamergen", "url": "https://gamergen.com", "rss_feed_url": "https://gamergen.com/rss", "language": "fr", "region": "FR", "country": "France", "scraper_type": "rss", "priority": 3, "category": "gaming_news"},
    {"name": "NoFrag", "url": "https://nofrag.com", "rss_feed_url": "https://nofrag.com/feed/", "language": "fr", "region": "FR", "country": "France", "scraper_type": "rss", "priority": 3, "category": "pc_gaming"},
    {"name": "Gameblog", "url": "https://www.gameblog.fr", "rss_feed_url": "https://www.gameblog.fr/rss.php", "language": "fr", "region": "FR", "country": "France", "scraper_type": "rss", "priority": 3, "category": "gaming_news"},

    # ═══════════════════════════════════════════
    # ARABIC (ar)
    # ═══════════════════════════════════════════
    {"name": "Saudi Gamer", "url": "https://saudigamer.com", "rss_feed_url": "https://saudigamer.com/feed/", "language": "ar", "region": "SA", "country": "Saudi Arabia", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},
    {"name": "ArabHardware", "url": "https://arabhardware.net", "rss_feed_url": "https://arabhardware.net/feed/", "language": "ar", "region": "EG", "country": "Egypt", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},
    {"name": "TRUE Gaming", "url": "https://true-gaming.net", "rss_feed_url": "https://true-gaming.net/feed/", "language": "ar", "region": "SA", "country": "Saudi Arabia", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},
    {"name": "عرب جيمرز (Arab Gamers)", "url": "https://arabgamers.net", "rss_feed_url": None, "language": "ar", "region": "AE", "country": "UAE", "scraper_type": "generic", "priority": 2, "category": "gaming_news"},
    {"name": "جيمز ميكس (GamesMix)", "url": "https://gamesmix.net", "rss_feed_url": None, "language": "ar", "region": "EG", "country": "Egypt", "scraper_type": "generic", "priority": 3, "category": "gaming_news"},

    # ═══════════════════════════════════════════
    # BENGALI (bn)
    # ═══════════════════════════════════════════
    {"name": "TechShhor Gaming", "url": "https://techshhor.com", "rss_feed_url": "https://techshhor.com/feed/", "language": "bn", "region": "BD", "country": "Bangladesh", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},
    {"name": "GameBangla", "url": "https://gamebangla.com", "rss_feed_url": None, "language": "bn", "region": "BD", "country": "Bangladesh", "scraper_type": "generic", "priority": 2, "category": "gaming_news"},
    {"name": "Potaka Gaming", "url": "https://potakagaming.com", "rss_feed_url": None, "language": "bn", "region": "BD", "country": "Bangladesh", "scraper_type": "generic", "priority": 2, "category": "gaming_news"},
    {"name": "Gamers BD", "url": "https://gamers.com.bd", "rss_feed_url": None, "language": "bn", "region": "BD", "country": "Bangladesh", "scraper_type": "generic", "priority": 3, "category": "gaming_news"},

    # ═══════════════════════════════════════════
    # PORTUGUESE (pt)
    # ═══════════════════════════════════════════
    {"name": "IGN Brasil", "url": "https://br.ign.com", "rss_feed_url": "https://br.ign.com/feed", "language": "pt", "region": "BR", "country": "Brazil", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},
    {"name": "The Enemy", "url": "https://www.theenemy.com.br", "rss_feed_url": "https://www.theenemy.com.br/feed", "language": "pt", "region": "BR", "country": "Brazil", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},
    {"name": "Techtudo Gaming", "url": "https://www.techtudo.com.br/jogos/", "rss_feed_url": "https://www.techtudo.com.br/rss/jogos/", "language": "pt", "region": "BR", "country": "Brazil", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},
    {"name": "Eurogamer Portugal", "url": "https://www.eurogamer.pt", "rss_feed_url": "https://www.eurogamer.pt/feed", "language": "pt", "region": "PT", "country": "Portugal", "scraper_type": "rss", "priority": 2, "category": "gaming_news"},
    {"name": "Adrenaline", "url": "https://www.adrenaline.com.br", "rss_feed_url": "https://www.adrenaline.com.br/feed/", "language": "pt", "region": "BR", "country": "Brazil", "scraper_type": "rss", "priority": 2, "category": "gaming_news"},
    {"name": "Voxel", "url": "https://www.voxel.com.br", "rss_feed_url": "https://www.voxel.com.br/feed/", "language": "pt", "region": "BR", "country": "Brazil", "scraper_type": "rss", "priority": 2, "category": "gaming_news"},
    {"name": "MeuPS (PlayStation Brasil)", "url": "https://meups.com.br", "rss_feed_url": "https://meups.com.br/feed/", "language": "pt", "region": "BR", "country": "Brazil", "scraper_type": "rss", "priority": 3, "category": "playstation"},
    {"name": "Critical Hits", "url": "https://www.criticalhits.com.br", "rss_feed_url": "https://www.criticalhits.com.br/feed/", "language": "pt", "region": "BR", "country": "Brazil", "scraper_type": "rss", "priority": 3, "category": "gaming_news"},

    # ═══════════════════════════════════════════
    # RUSSIAN (ru)
    # ═══════════════════════════════════════════
    {"name": "DTF", "url": "https://dtf.ru", "rss_feed_url": "https://dtf.ru/rss", "language": "ru", "region": "RU", "country": "Russia", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},
    {"name": "Igromania", "url": "https://www.igromania.ru", "rss_feed_url": "https://www.igromania.ru/rss/rss_news.xml", "language": "ru", "region": "RU", "country": "Russia", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},
    {"name": "StopGame", "url": "https://stopgame.ru", "rss_feed_url": "https://stopgame.ru/rss/news.xml", "language": "ru", "region": "RU", "country": "Russia", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},
    {"name": "Kanobu", "url": "https://kanobu.ru", "rss_feed_url": "https://kanobu.ru/rss/", "language": "ru", "region": "RU", "country": "Russia", "scraper_type": "rss", "priority": 2, "category": "gaming_news"},
    {"name": "3DNews Games", "url": "https://3dnews.ru/games/", "rss_feed_url": "https://3dnews.ru/games/rss/", "language": "ru", "region": "RU", "country": "Russia", "scraper_type": "rss", "priority": 2, "category": "gaming_news"},
    {"name": "Riot Pixels", "url": "https://riotpixels.com", "rss_feed_url": "https://riotpixels.com/feed/", "language": "ru", "region": "RU", "country": "Russia", "scraper_type": "rss", "priority": 3, "category": "gaming_news"},
    {"name": "PlayGround", "url": "https://www.playground.ru", "rss_feed_url": "https://www.playground.ru/rss/", "language": "ru", "region": "RU", "country": "Russia", "scraper_type": "rss", "priority": 2, "category": "gaming_news"},

    # ═══════════════════════════════════════════
    # JAPANESE (ja)
    # ═══════════════════════════════════════════
    {"name": "4Gamer.net", "url": "https://www.4gamer.net", "rss_feed_url": "https://www.4gamer.net/rss/index.xml", "language": "ja", "region": "JP", "country": "Japan", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},
    {"name": "Famitsu", "url": "https://www.famitsu.com", "rss_feed_url": "https://www.famitsu.com/feed/", "language": "ja", "region": "JP", "country": "Japan", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},
    {"name": "Game Watch", "url": "https://game.watch.impress.co.jp", "rss_feed_url": "https://game.watch.impress.co.jp/data/rss/1.0/gmw/feed.rdf", "language": "ja", "region": "JP", "country": "Japan", "scraper_type": "rss", "priority": 1, "category": "gaming_news"},
    {"name": "Dengeki Online", "url": "https://dengekionline.com", "rss_feed_url": "https://dengekionline.com/feed/", "language": "ja", "region": "JP", "country": "Japan", "scraper_type": "rss", "priority": 2, "category": "gaming_news"},
    {"name": "Inside Games", "url": "https://www.inside-games.jp", "rss_feed_url": "https://www.inside-games.jp/rss/index.rdf", "language": "ja", "region": "JP", "country": "Japan", "scraper_type": "rss", "priority": 2, "category": "gaming_news"},
    {"name": "Game*Spark", "url": "https://www.gamespark.jp", "rss_feed_url": "https://www.gamespark.jp/rss/index.rdf", "language": "ja", "region": "JP", "country": "Japan", "scraper_type": "rss", "priority": 2, "category": "gaming_news"},
    {"name": "Automaton", "url": "https://automaton-media.com", "rss_feed_url": "https://automaton-media.com/feed/", "language": "ja", "region": "JP", "country": "Japan", "scraper_type": "rss", "priority": 2, "category": "gaming_news"},
    {"name": "PlayStation Blog Japan", "url": "https://blog.ja.playstation.com", "rss_feed_url": "https://blog.ja.playstation.com/feed/", "language": "ja", "region": "JP", "country": "Japan", "scraper_type": "rss", "priority": 3, "category": "playstation"},
    {"name": "Nintendo Dream", "url": "https://www.ndw.jp", "rss_feed_url": None, "language": "ja", "region": "JP", "country": "Japan", "scraper_type": "generic", "priority": 3, "category": "nintendo"},
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

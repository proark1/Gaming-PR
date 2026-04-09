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

    # ═══════════════════════════════════════════
    # STREAMERS & CONTENT CREATORS
    # ═══════════════════════════════════════════
    # English Streamers
    {"name": "Ninja", "url": "https://www.twitch.tv/ninja", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 1, "category": "streamer", "description": "One of the most recognized gaming streamers worldwide"},
    {"name": "Shroud", "url": "https://www.twitch.tv/shroud", "rss_feed_url": None, "language": "en", "region": "CA", "country": "Canada", "scraper_type": "generic", "priority": 1, "category": "streamer", "description": "Former CS:GO pro, top FPS streamer"},
    {"name": "Pokimane", "url": "https://www.twitch.tv/pokimane", "rss_feed_url": None, "language": "en", "region": "CA", "country": "Canada", "scraper_type": "generic", "priority": 1, "category": "streamer", "description": "Top female gaming content creator and streamer"},
    {"name": "xQc", "url": "https://www.twitch.tv/xqc", "rss_feed_url": None, "language": "en", "region": "CA", "country": "Canada", "scraper_type": "generic", "priority": 1, "category": "streamer", "description": "Most-watched Twitch streamer, variety content"},
    {"name": "DrDisrespect", "url": "https://www.youtube.com/@DrDisrespect", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 1, "category": "streamer", "description": "Iconic gaming entertainer and streamer"},
    {"name": "TimTheTatman", "url": "https://www.twitch.tv/timthetatman", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 2, "category": "streamer", "description": "Popular variety gaming streamer"},
    {"name": "summit1g", "url": "https://www.twitch.tv/summit1g", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 2, "category": "streamer", "description": "Veteran FPS and variety streamer"},
    {"name": "NICKMERCS", "url": "https://www.twitch.tv/nickmercs", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 2, "category": "streamer", "description": "FPS and battle royale content creator"},
    {"name": "Valkyrae", "url": "https://www.youtube.com/@Valkyrae", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 2, "category": "streamer", "description": "YouTube Gaming co-owner and content creator"},
    {"name": "Tfue", "url": "https://www.twitch.tv/tfue", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 2, "category": "streamer", "description": "Competitive gaming streamer"},
    {"name": "Asmongold", "url": "https://www.twitch.tv/asmongold", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 1, "category": "streamer", "description": "MMO and gaming culture commentator"},
    {"name": "Sodapoppin", "url": "https://www.twitch.tv/sodapoppin", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 2, "category": "streamer", "description": "Veteran variety and MMO streamer"},
    {"name": "Myth", "url": "https://www.twitch.tv/myth", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 3, "category": "streamer", "description": "Former Fortnite pro, variety streamer"},
    {"name": "CohhCarnage", "url": "https://www.twitch.tv/cohhcarnage", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 2, "category": "streamer", "description": "RPG and story-driven game streamer"},
    {"name": "Lirik", "url": "https://www.twitch.tv/lirik", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 2, "category": "streamer", "description": "Veteran variety streamer, one of the OG Twitch streamers"},
    # Spanish Streamers
    {"name": "Rubius", "url": "https://www.twitch.tv/rubius", "rss_feed_url": None, "language": "es", "region": "ES", "country": "Spain", "scraper_type": "generic", "priority": 1, "category": "streamer", "description": "Top Spanish-speaking gaming content creator"},
    {"name": "Ibai", "url": "https://www.twitch.tv/ibai", "rss_feed_url": None, "language": "es", "region": "ES", "country": "Spain", "scraper_type": "generic", "priority": 1, "category": "streamer", "description": "Massive Spanish streamer and entertainment creator"},
    {"name": "Auronplay", "url": "https://www.twitch.tv/auronplay", "rss_feed_url": None, "language": "es", "region": "ES", "country": "Spain", "scraper_type": "generic", "priority": 1, "category": "streamer", "description": "Top Spanish gaming and variety streamer"},
    # Portuguese Streamers
    {"name": "Gaules", "url": "https://www.twitch.tv/gaules", "rss_feed_url": None, "language": "pt", "region": "BR", "country": "Brazil", "scraper_type": "generic", "priority": 1, "category": "streamer", "description": "Biggest Brazilian CS and gaming streamer"},
    {"name": "Alanzoka", "url": "https://www.twitch.tv/alanzoka", "rss_feed_url": None, "language": "pt", "region": "BR", "country": "Brazil", "scraper_type": "generic", "priority": 1, "category": "streamer", "description": "Top Brazilian variety gaming streamer"},
    # French Streamers
    {"name": "Squeezie", "url": "https://www.twitch.tv/squeezie", "rss_feed_url": None, "language": "fr", "region": "FR", "country": "France", "scraper_type": "generic", "priority": 1, "category": "streamer", "description": "France's biggest gaming content creator"},
    {"name": "Gotaga", "url": "https://www.twitch.tv/gotaga", "rss_feed_url": None, "language": "fr", "region": "FR", "country": "France", "scraper_type": "generic", "priority": 1, "category": "streamer", "description": "Top French esports and FPS streamer"},
    # Japanese Streamers
    {"name": "Kuzuha", "url": "https://www.youtube.com/@Kuzuha", "rss_feed_url": None, "language": "ja", "region": "JP", "country": "Japan", "scraper_type": "generic", "priority": 1, "category": "streamer", "description": "Top Japanese VTuber and gaming streamer"},
    {"name": "Stylishnoob", "url": "https://www.twitch.tv/stylishnoob4", "rss_feed_url": None, "language": "ja", "region": "JP", "country": "Japan", "scraper_type": "generic", "priority": 2, "category": "streamer", "description": "Popular Japanese FPS streamer"},
    # Chinese Streamers
    {"name": "PDD", "url": "https://www.douyu.com/101", "rss_feed_url": None, "language": "zh-CN", "region": "CN", "country": "China", "scraper_type": "generic", "priority": 1, "category": "streamer", "description": "Former LoL pro, top Chinese gaming streamer"},
    # Russian Streamers
    {"name": "Bratishkinoff", "url": "https://www.twitch.tv/bratishkinoff", "rss_feed_url": None, "language": "ru", "region": "RU", "country": "Russia", "scraper_type": "generic", "priority": 1, "category": "streamer", "description": "Top Russian variety gaming streamer"},
    # Arabic Streamers
    {"name": "BanderitaX", "url": "https://www.youtube.com/@BanderitaX", "rss_feed_url": None, "language": "ar", "region": "SA", "country": "Saudi Arabia", "scraper_type": "generic", "priority": 1, "category": "streamer", "description": "Biggest Arab gaming YouTuber and content creator"},

    # ═══════════════════════════════════════════
    # VCs & GAMING INFLUENCERS
    # ═══════════════════════════════════════════
    # Gaming-Focused Venture Capital
    {"name": "a16z Games", "url": "https://a16z.com/games/", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 1, "category": "vc", "description": "Andreessen Horowitz gaming fund, major gaming/web3 investor"},
    {"name": "BITKRAFT Ventures", "url": "https://www.bitkraft.vc", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 1, "category": "vc", "description": "Leading gaming and esports-focused VC firm"},
    {"name": "Griffin Gaming Partners", "url": "https://griffingp.com", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 1, "category": "vc", "description": "Gaming-dedicated venture capital fund"},
    {"name": "Makers Fund", "url": "https://www.makersfund.com", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 1, "category": "vc", "description": "Global interactive entertainment venture fund"},
    {"name": "Galaxy Interactive", "url": "https://galaxyinteractive.com", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 1, "category": "vc", "description": "VC focused on interactive entertainment and gaming"},
    {"name": "Konvoy Ventures", "url": "https://www.konvoy.vc", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 1, "category": "vc", "description": "Dedicated gaming venture fund"},
    {"name": "Play Ventures", "url": "https://www.playventures.vc", "rss_feed_url": None, "language": "en", "region": "FI", "country": "Finland", "scraper_type": "generic", "priority": 1, "category": "vc", "description": "Gaming-focused VC by industry veterans"},
    {"name": "Hiro Capital", "url": "https://hiro.capital", "rss_feed_url": None, "language": "en", "region": "UK", "country": "United Kingdom", "scraper_type": "generic", "priority": 2, "category": "vc", "description": "European games, esports and digital sports VC"},
    {"name": "Ludus Ventures", "url": "https://www.ludus.vc", "rss_feed_url": None, "language": "en", "region": "UK", "country": "United Kingdom", "scraper_type": "generic", "priority": 2, "category": "vc", "description": "Early-stage gaming VC fund"},
    {"name": "Vgames", "url": "https://www.vgames.vc", "rss_feed_url": None, "language": "en", "region": "IL", "country": "Israel", "scraper_type": "generic", "priority": 2, "category": "vc", "description": "Gaming-focused investment fund"},
    {"name": "Sisu Game Ventures", "url": "https://www.sisugameventures.com", "rss_feed_url": None, "language": "en", "region": "FI", "country": "Finland", "scraper_type": "generic", "priority": 2, "category": "vc", "description": "Nordic gaming VC fund"},
    {"name": "Transcend Fund", "url": "https://transcendfund.com", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 2, "category": "vc", "description": "Gaming and interactive media VC"},
    {"name": "NetEase Capital", "url": "https://www.neteasecapital.com", "rss_feed_url": None, "language": "zh-CN", "region": "CN", "country": "China", "scraper_type": "generic", "priority": 1, "category": "vc", "description": "NetEase's gaming investment arm"},
    {"name": "Tencent Investment", "url": "https://www.tencentinvestment.com", "rss_feed_url": None, "language": "zh-CN", "region": "CN", "country": "China", "scraper_type": "generic", "priority": 1, "category": "vc", "description": "World's largest gaming company investment division"},
    # Gaming Industry Influencers
    {"name": "Geoff Keighley", "url": "https://twitter.com/geoffkeighley", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 1, "category": "gaming_influencer", "description": "Creator of The Game Awards and gaming journalism icon"},
    {"name": "Jason Schreier", "url": "https://twitter.com/jasonschreier", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 1, "category": "gaming_influencer", "description": "Bloomberg gaming journalist and industry insider"},
    {"name": "SkillUp", "url": "https://www.youtube.com/@SkillUp", "rss_feed_url": None, "language": "en", "region": "AU", "country": "Australia", "scraper_type": "generic", "priority": 2, "category": "gaming_influencer", "description": "In-depth gaming reviews and industry analysis"},
    {"name": "YongYea", "url": "https://www.youtube.com/@YongYea", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 2, "category": "gaming_influencer", "description": "Gaming industry news and commentary"},
    {"name": "Angry Joe", "url": "https://www.youtube.com/@AngryJoeShow", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 2, "category": "gaming_influencer", "description": "Gaming reviews and industry commentary"},
    {"name": "Jim Sterling", "url": "https://www.youtube.com/@jimsterling", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 2, "category": "gaming_influencer", "description": "Gaming industry critic and consumer advocate"},
    {"name": "Noclip", "url": "https://www.youtube.com/@NoclipDocs", "rss_feed_url": None, "language": "en", "region": "US", "country": "United States", "scraper_type": "generic", "priority": 2, "category": "gaming_influencer", "description": "Gaming documentary channel and industry storytelling"},
    {"name": "DigitalFoundry", "url": "https://www.youtube.com/@DigitalFoundry", "rss_feed_url": None, "language": "en", "region": "UK", "country": "United Kingdom", "scraper_type": "generic", "priority": 1, "category": "gaming_influencer", "description": "Technical analysis of gaming hardware and software"},
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

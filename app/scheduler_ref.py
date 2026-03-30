# Holds a reference to the APScheduler instance so routers can access it
# without circular imports. Set by main.py lifespan after scheduler.start().
scheduler = None

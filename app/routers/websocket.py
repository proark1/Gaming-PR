"""
WebSocket live feed for real-time article streaming.

Clients connect and receive new articles as they're scraped in real-time.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Manages WebSocket connections with language/type filtering."""

    def __init__(self):
        self._connections: dict[WebSocket, dict] = {}
        self._lock: Optional[asyncio.Lock] = None

    def _get_lock(self) -> asyncio.Lock:
        """Lazily create the asyncio.Lock to avoid event loop issues at import time."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def connect(self, websocket: WebSocket, filters: dict = None):
        await websocket.accept()
        async with self._get_lock():
            self._connections[websocket] = filters or {}
        logger.info(f"WebSocket client connected. Total: {len(self._connections)}")

    async def disconnect(self, websocket: WebSocket):
        async with self._get_lock():
            self._connections.pop(websocket, None)
        logger.info(f"WebSocket client disconnected. Total: {len(self._connections)}")

    async def broadcast_article(self, article_data: dict):
        """Send a new article to all matching connected clients."""
        if not self._connections:
            return

        message = json.dumps({
            "type": "new_article",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": article_data,
        }, default=str)

        async with self._get_lock():
            dead = []
            for ws, filters in self._connections.items():
                if self._matches_filters(article_data, filters):
                    try:
                        await ws.send_text(message)
                    except Exception:
                        dead.append(ws)

            for ws in dead:
                self._connections.pop(ws, None)

    async def broadcast_scrape_progress(self, progress_data: dict):
        """Broadcast scrape job progress updates."""
        if not self._connections:
            return

        message = json.dumps({
            "type": "scrape_progress",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": progress_data,
        }, default=str)

        async with self._get_lock():
            dead = []
            for ws in self._connections:
                try:
                    await ws.send_text(message)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self._connections.pop(ws, None)

    async def broadcast_stats(self, stats: dict):
        """Broadcast periodic stats updates."""
        if not self._connections:
            return

        message = json.dumps({
            "type": "stats_update",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": stats,
        }, default=str)

        async with self._get_lock():
            dead = []
            for ws in self._connections:
                try:
                    await ws.send_text(message)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self._connections.pop(ws, None)

    @staticmethod
    def _matches_filters(article_data: dict, filters: dict) -> bool:
        """Check if an article matches the client's subscription filters."""
        if not filters:
            return True

        lang_filter = filters.get("language")
        if lang_filter and article_data.get("language") != lang_filter:
            return False

        type_filter = filters.get("article_type")
        if type_filter and article_data.get("article_type") != type_filter:
            return False

        outlet_filter = filters.get("outlet_id")
        if outlet_filter and article_data.get("outlet_id") != outlet_filter:
            return False

        category_filter = filters.get("outlet_category")
        if category_filter and article_data.get("outlet_category") != category_filter:
            return False

        return True

    async def update_filters(self, websocket: WebSocket, new_filters: dict):
        """Thread-safe filter update for a connected client."""
        async with self._get_lock():
            if websocket in self._connections:
                self._connections[websocket] = new_filters

    @property
    def connection_count(self) -> int:
        return len(self._connections)


# Global manager
ws_manager = ConnectionManager()


@router.websocket("/ws/feed")
async def live_feed(
    websocket: WebSocket,
    language: Optional[str] = Query(default=None),
    article_type: Optional[str] = Query(default=None),
    outlet_id: Optional[int] = Query(default=None),
    outlet_category: Optional[str] = Query(default=None),
):
    """
    WebSocket live feed endpoint.

    Connect to receive real-time article notifications.
    Optional query params for filtering: ?language=en&article_type=review&outlet_category=gaming_vc
    """
    filters = {}
    if language:
        filters["language"] = language
    if article_type:
        filters["article_type"] = article_type
    if outlet_id:
        filters["outlet_id"] = outlet_id
    if outlet_category:
        filters["outlet_category"] = outlet_category

    await ws_manager.connect(websocket, filters)

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to Gaming PR live feed",
            "filters": filters,
        })

        # Keep connection alive, handle client messages
        while True:
            data = await websocket.receive_text()
            # Clients can update filters
            try:
                msg = json.loads(data)
                if msg.get("type") == "update_filters":
                    new_filters = msg.get("filters", {})
                    await ws_manager.update_filters(websocket, new_filters)
                    await websocket.send_json({
                        "type": "filters_updated",
                        "filters": new_filters,
                    })
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)

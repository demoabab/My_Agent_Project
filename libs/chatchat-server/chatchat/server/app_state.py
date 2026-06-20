"""Typed application state for FastAPI app.state access."""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chatchat.server.api_server.server_app import AppConfig
    from chatchat.server.db.manager import DatabaseManager


class AppState:
    """Typed wrapper for app.state."""

    config: "AppConfig"

    @property
    def db(self) -> "DatabaseManager":
        return self.config.db

"""NuSyQ Icon Library Manager.

Provides easy access to SVG icons for the unified desktop application.
All icons are Material Design inspired, scalable, and theme-aware.

Usage:
    from src.interface.icon_manager import IconManager

    icon_mgr = IconManager()
    dashboard_icon = icon_mgr.get_icon('dashboard')
    self.tab_widget.setTabIcon(0, dashboard_icon)
"""

import logging
from pathlib import Path

from PyQt5.QtCore import QByteArray, Qt
from PyQt5.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt5.QtSvg import QSvgRenderer

logger = logging.getLogger(__name__)


class IconManager:
    """Manages SVG icon loading and caching for the NuSyQ unified desktop application.

    Features:
    - SVG icons scalable to any size
    - Color/theme customization
    - Icon caching for performance
    - Fallback to placeholder on error
    """

    def __init__(self, icon_dir: Path | None = None):
        """Initialize icon manager.

        Args:
            icon_dir: Path to icon directory (defaults to src/interface/icons/)
        """
        if icon_dir is None:
            # Default to icons/ directory next to this file
            self.icon_dir = Path(__file__).parent / "icons"
        else:
            self.icon_dir = Path(icon_dir)

        # Icon cache {name: QIcon}
        self._cache: dict[str, QIcon] = {}

        # Available icons
        self.available_icons = self._scan_icons()

    def _scan_icons(self) -> list[str]:
        """Scan icon directory and return list of available icon names."""
        if not self.icon_dir.exists():
            return []

        icons = []
        for file_path in self.icon_dir.glob("*.svg"):
            icon_name = file_path.stem  # filename without extension
            icons.append(icon_name)

        return sorted(icons)

    def get_icon(
        self, name: str, size: int = 24, color: str | None = None, use_cache: bool = True
    ) -> QIcon:
        """Get icon by name.

        Args:
            name: Icon name (without .svg extension)
            size: Icon size in pixels (default: 24)
            color: Optional hex color (e.g., "#2196F3") to override icon color
            use_cache: Whether to use cached icon (default: True)

        Returns:
            QIcon object (placeholder if icon not found)

        Example:
            icon = icon_mgr.get_icon('dashboard', size=32, color='#2196F3')
        """
        cache_key = f"{name}_{size}_{color or 'default'}"

        # Return cached icon
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        icon_path = self.icon_dir / f"{name}.svg"

        # Load icon
        if icon_path.exists():
            icon = self._load_svg_icon(icon_path, size, color)
        else:
            # Fallback to placeholder
            icon = self._create_placeholder_icon(size)

        # Cache and return
        if use_cache:
            self._cache[cache_key] = icon

        return icon

    def _load_svg_icon(self, path: Path, size: int = 24, color: str | None = None) -> QIcon:
        """Load SVG icon from file.

        Args:
            path: Path to SVG file
            size: Icon size in pixels
            color: Optional hex color to override 'currentColor' in SVG

        Returns:
            QIcon object
        """
        # Read SVG content
        with open(path, encoding="utf-8") as f:
            svg_content = f.read()

        # Override color if specified
        if color:
            # Replace 'currentColor' with specified color
            svg_content = svg_content.replace("currentColor", color)

        # Create QSvgRenderer from modified content
        svg_bytes = QByteArray(svg_content.encode("utf-8"))
        renderer = QSvgRenderer(svg_bytes)

        # Render to QPixmap
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return QIcon(pixmap)

    def _create_placeholder_icon(self, size: int = 24) -> QIcon:
        """Create a placeholder icon (gray square) when icon is not found.

        Args:
            size: Icon size in pixels

        Returns:
            QIcon with gray square placeholder
        """
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor("#757575"))  # Gray placeholder
        return QIcon(pixmap)

    def list_icons(self) -> list[str]:
        """Return list of all available icon names."""
        return self.available_icons.copy()

    def has_icon(self, name: str) -> bool:
        """Check if icon exists."""
        return name in self.available_icons

    def clear_cache(self):
        """Clear icon cache to free memory."""
        self._cache.clear()

    def preload_all(self, size: int = 24):
        """Preload all icons into cache for instant access.

        Args:
            size: Icon size to preload (default: 24)
        """
        for icon_name in self.available_icons:
            self.get_icon(icon_name, size=size, use_cache=True)


# Global icon manager instance
_icon_manager: IconManager | None = None


def get_icon_manager() -> IconManager:
    """Get global IconManager instance (singleton pattern)."""
    global _icon_manager
    if _icon_manager is None:
        _icon_manager = IconManager()
    return _icon_manager


def get_icon(name: str, size: int = 24, color: str | None = None) -> QIcon:
    """Convenience function to get icon using global manager.

    Args:
        name: Icon name (without .svg)
        size: Icon size in pixels (default: 24)
        color: Optional hex color

    Returns:
        QIcon object

    Example:
        from src.interface.icon_manager import get_icon
        icon = get_icon('dashboard', size=32, color='#2196F3')
    """
    manager = get_icon_manager()
    return manager.get_icon(name, size, color)


# Icon name constants for easy access
class Icons:
    """Icon name constants to avoid typos."""

    # Tab icons
    DASHBOARD = "dashboard"
    REPOSITORY = "repository"
    HEALTH = "health"
    NAVIGATOR = "navigator"
    NAVIGATE = "navigator"
    TASKS = "tasks"
    METRICS = "metrics"
    SETTINGS = "settings"
    DEBUG = "debug"

    # Action icons
    SAVE = "save"
    EXPORT = "export"
    REFRESH = "refresh"
    CLOSE = "close"
    ABOUT = "about"

    # Status icons
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"

    # Sidebar icons
    HISTORY = "history"
    BOOKMARK = "bookmark"
    SIDEBAR = "sidebar"
    WORKSPACE = "workspace"
    FOLDER_OPEN = "folder_open"
    FILE = "file"
    HELP = "help"
    INFO = "info"
    VIEW = "view"
    TOOLS = "tools"
    TERMINAL = "terminal"
    PLUGINS = "plugins"
    PALETTE = "palette"
    SHORTCUTS = "shortcuts"
    FULLSCREEN = "fullscreen"

    # Other icons
    CHARTS = "charts"
    SEARCH = "search"
    THEME = "theme"


if __name__ == "__main__":
    # Test icon manager
    manager = IconManager()
    logger.info("🎨 Icon Manager Test")
    logger.info(f"Icon directory: {manager.icon_dir}")
    logger.info(f"Available icons: {len(manager.available_icons)}")
    logger.info(f"Icons: {', '.join(manager.available_icons)}")

    # Test loading
    dashboard_icon = manager.get_icon("dashboard")
    logger.info(f"\n✅ Loaded 'dashboard' icon: {not dashboard_icon.isNull()}")

    # Test color override
    blue_health_icon = manager.get_icon("health", size=32, color="#2196F3")
    logger.info(f"✅ Loaded 'health' icon with blue color: {not blue_health_icon.isNull()}")

    # Test missing icon (should return placeholder)
    missing_icon = manager.get_icon("nonexistent")
    logger.info(f"✅ Placeholder for missing icon: {not missing_icon.isNull()}")

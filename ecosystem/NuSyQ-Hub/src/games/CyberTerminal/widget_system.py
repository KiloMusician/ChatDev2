"""CyberTerminal Widget System - UI Components and Management.

Provides modular widget architecture for game UI with switching,
navigation, and event handling.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

# Widget UI Constants
BACK_BUTTON_LABEL = "🔙 Back"
ACTIONS_HEADER = "\n🔘 Actions:"


class WidgetType(Enum):
    """Types of widgets available in the game."""

    MAIN_HUB = "main_hub"
    SHOP = "shop"
    INVENTORY = "inventory"
    STATS = "stats"
    TERMINAL = "terminal"
    SETTINGS = "settings"
    PAUSE_MENU = "pause_menu"
    CUSTOM = "custom"


class ButtonState(Enum):
    """States a button can be in."""

    NORMAL = "normal"
    HOVERED = "hovered"
    ACTIVE = "active"
    DISABLED = "disabled"


@dataclass
class WidgetEvent:
    """Event that occurs when interacting with a widget."""

    event_type: str  # "click", "select", "input", etc.
    widget_id: str  # Widget that generated the event
    data: dict[str, Any]  # Event-specific data


class UIButton:
    """A clickable button in a widget."""

    def __init__(
        self,
        label: str,
        button_id: str,
        on_click: Callable[[WidgetEvent], None] | None = None,
        enabled: bool = True,
    ):
        """Initialize a button.

        Args:
            label: Display text for the button
            button_id: Unique identifier for this button
            on_click: Callback function when button is clicked
            enabled: Whether button is interactable
        """
        self.label = label
        self.button_id = button_id
        self.on_click = on_click
        self.enabled = enabled
        self.state = ButtonState.NORMAL

    def render(self, width: int = 20) -> str:
        """Render the button as a string.

        Args:
            width: Button width in characters

        Returns:
            Formatted button string
        """
        if not self.enabled:
            return f"[{self.label:<{width - 2}}] (disabled)"

        if self.state == ButtonState.HOVERED:
            return f">>{self.label:<{width - 4}} <<"
        elif self.state == ButtonState.ACTIVE:
            return f"=={self.label:<{width - 4}}=="

        return f"[{self.label:<{width - 2}}]"

    def click(self) -> WidgetEvent | None:
        """Handle button click.

        Returns:
            WidgetEvent if successful, None otherwise
        """
        if not self.enabled:
            return None

        event = WidgetEvent(
            event_type="click", widget_id=self.button_id, data={"label": self.label}
        )

        if self.on_click:
            self.on_click(event)

        return event


class Widget(ABC):
    """Base class for all UI widgets."""

    def __init__(self, widget_id: str, widget_type: WidgetType):
        """Initialize a widget.

        Args:
            widget_id: Unique identifier for this widget
            widget_type: Type of widget (MAIN_HUB, SHOP, etc.)
        """
        self.widget_id = widget_id
        self.widget_type = widget_type
        self.buttons: dict[str, UIButton] = {}
        self.is_visible = True
        self.parent_widget: Widget | None = None
        self.event_handlers: dict[str, list[Callable[[WidgetEvent], None]]] = {}

    @abstractmethod
    def render(self) -> str:
        """Render the widget as a string for display.

        Returns:
            Formatted widget content
        """

    def add_button(self, button: UIButton) -> None:
        """Add a button to the widget.

        Args:
            button: Button to add
        """
        self.buttons[button.button_id] = button

    def get_button(self, button_id: str) -> UIButton | None:
        """Get a button by its ID.

        Args:
            button_id: ID of button to retrieve

        Returns:
            Button if found, None otherwise
        """
        return self.buttons.get(button_id)

    def on_event(self, event: WidgetEvent) -> None:
        """Handle an event from this widget.

        Args:
            event: The event to handle
        """
        if event.event_type in self.event_handlers:
            for handler in self.event_handlers[event.event_type]:
                handler(event)

    def register_event_handler(
        self, event_type: str, handler: Callable[[WidgetEvent], None]
    ) -> None:
        """Register a handler for a specific event type.

        Args:
            event_type: Type of event to handle
            handler: Callback function for the event
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def set_parent(self, parent: "Widget") -> None:
        """Set this widget's parent widget.

        Args:
            parent: Parent widget
        """
        self.parent_widget = parent

    def get_parent(self) -> Optional["Widget"]:
        """Get this widget's parent widget.

        Returns:
            Parent widget if set, None otherwise
        """
        return self.parent_widget


class MainHubWidget(Widget):
    """Main hub/dashboard widget - central navigation point."""

    def __init__(
        self,
        widget_id: str = "main_hub",
        player_name: str = "netrunner",
        current_level: int = 1,
        player_xp: int = 0,
    ):
        """Initialize the main hub widget.

        Args:
            widget_id: Widget identifier
            player_name: Name of the player
            current_level: Current player level
            player_xp: Current player XP
        """
        super().__init__(widget_id, WidgetType.MAIN_HUB)
        self.player_name = player_name
        self.current_level = current_level
        self.player_xp = player_xp

        # Add navigation buttons
        self.add_button(UIButton("📦 Inventory", "btn_inventory"))
        self.add_button(UIButton("🏪 Shop", "btn_shop"))
        self.add_button(UIButton("📊 Stats", "btn_stats"))
        self.add_button(UIButton("⚙️ Settings", "btn_settings"))
        self.add_button(UIButton("🚪 Quit Game", "btn_quit"))

    def render(self) -> str:
        """Render the main hub widget.

        Returns:
            Formatted main hub display
        """
        output = []
        output.append("\n" + "=" * 50)
        output.append("🏢 NEON DISTRICT CENTRAL HUB")
        output.append("=" * 50)
        output.append(f"\n👤 Player: {self.player_name}")
        output.append(f"📈 Level {self.current_level} | XP: {self.player_xp}")
        output.append("\n📍 Navigation:")
        output.append("-" * 50)

        for idx, (_, button) in enumerate(self.buttons.items(), 1):
            output.append(f"{idx}. {button.render()}")

        output.append("-" * 50)
        output.append("Enter option number or command...\n")

        return "\n".join(output)


class ShopWidget(Widget):
    """Shop widget for buying/selling items."""

    @dataclass
    class Item:
        """Shop item."""

        item_id: str
        name: str
        price: int
        description: str

    def __init__(self, widget_id: str = "shop", player_credits: int = 1000):
        """Initialize the shop widget.

        Args:
            widget_id: Widget identifier
            player_credits: Player's available credits
        """
        super().__init__(widget_id, WidgetType.SHOP)
        self.player_credits = player_credits
        self.items: list[ShopWidget.Item] = []
        self.selected_item: ShopWidget.Item | None = None

        # Add shop buttons
        self.add_button(UIButton(BACK_BUTTON_LABEL, "btn_back"))
        self.add_button(UIButton("💳 Buy", "btn_buy"))
        self.add_button(UIButton("📋 Details", "btn_details"))

        # Add default shop items
        self._initialize_items()

    def _initialize_items(self) -> None:
        """Initialize default shop items."""
        self.items = [
            self.Item("upgrade_cpu", "CPU Upgrade", 500, "Faster processing speed"),
            self.Item("upgrade_ram", "RAM Module", 300, "Increased memory capacity"),
            self.Item("upgrade_net", "Network Card", 400, "Enhanced connectivity"),
            self.Item("tool_scanner", "System Scanner", 200, "Scan networks"),
            self.Item("tool_jammer", "Signal Jammer", 350, "Disrupt signals"),
        ]

    def render(self) -> str:
        """Render the shop widget.

        Returns:
            Formatted shop display
        """
        output = []
        output.append("\n" + "=" * 50)
        output.append("🏪 NEON MARKET - EQUIPMENT SHOP")
        output.append("=" * 50)
        output.append(f"\n💰 Credits: {self.player_credits}")
        output.append("\n📦 Available Items:")
        output.append("-" * 50)

        for idx, item in enumerate(self.items, 1):
            affordable = "✓" if item.price <= self.player_credits else "✗"
            output.append(f"{idx}. {item.name:<20} {item.price:>4}¢ [{affordable}]")

        output.append("-" * 50)
        output.append(ACTIONS_HEADER)
        for idx, (_, button) in enumerate(self.buttons.items(), 1):
            output.append(f"{idx}. {button.render()}")

        output.append("-" * 50)
        output.append("Select item number or action...\n")

        return "\n".join(output)

    def select_item(self, item_index: int) -> bool:
        """Select an item from the shop.

        Args:
            item_index: Index of item to select (1-based)

        Returns:
            True if selection successful, False otherwise
        """
        if 0 < item_index <= len(self.items):
            self.selected_item = self.items[item_index - 1]
            return True
        return False

    def can_buy_selected(self) -> bool:
        """Check if player can buy the selected item.

        Returns:
            True if player has enough credits and item is selected
        """
        if not self.selected_item:
            return False
        return self.player_credits >= self.selected_item.price


class InventoryWidget(Widget):
    """Inventory widget for viewing player items."""

    def __init__(self, widget_id: str = "inventory", items: list[str] | None = None):
        """Initialize the inventory widget.

        Args:
            widget_id: Widget identifier
            items: List of item names in inventory
        """
        super().__init__(widget_id, WidgetType.INVENTORY)
        self.items = items or []

        # Add inventory buttons
        self.add_button(UIButton(BACK_BUTTON_LABEL, "btn_back"))
        self.add_button(UIButton("🗑️ Drop Item", "btn_drop"))
        self.add_button(UIButton("ℹ️ Info", "btn_info"))

    def render(self) -> str:
        """Render the inventory widget.

        Returns:
            Formatted inventory display
        """
        output = []
        output.append("\n" + "=" * 50)
        output.append("📦 INVENTORY")
        output.append("=" * 50)
        output.append(f"\n Items ({len(self.items)}/20):")
        output.append("-" * 50)

        if self.items:
            for idx, item in enumerate(self.items, 1):
                output.append(f"{idx}. {item}")
        else:
            output.append("(empty)")

        output.append("-" * 50)
        output.append(ACTIONS_HEADER)
        for idx, (_, button) in enumerate(self.buttons.items(), 1):
            output.append(f"{idx}. {button.render()}")

        output.append("-" * 50)
        output.append("Select item or action...\n")

        return "\n".join(output)

    def add_item(self, item_name: str) -> bool:
        """Add an item to inventory.

        Args:
            item_name: Name of item to add

        Returns:
            True if added successfully, False if inventory is full
        """
        if len(self.items) < 20:
            self.items.append(item_name)
            return True
        return False

    def remove_item(self, item_name: str) -> bool:
        """Remove an item from inventory.

        Args:
            item_name: Name of item to remove

        Returns:
            True if removed, False if not found
        """
        if item_name in self.items:
            self.items.remove(item_name)
            return True
        return False


class StatsWidget(Widget):
    """Stats widget for displaying player statistics."""

    def __init__(
        self,
        widget_id: str = "stats",
        player_name: str = "netrunner",
        level: int = 1,
        xp: int = 0,
        health: int = 100,
        credits_amount: int = 1000,
    ):
        """Initialize the stats widget.

        Args:
            widget_id: Widget identifier
            player_name: Player's name
            level: Current level
            xp: Current experience
            health: Current health
            credits_amount: Current credits
        """
        super().__init__(widget_id, WidgetType.STATS)
        self.player_name = player_name
        self.level = level
        self.xp = xp
        self.health = health
        self.credits = credits_amount

        # Add stats buttons
        self.add_button(UIButton(BACK_BUTTON_LABEL, "btn_back"))

    def render(self) -> str:
        """Render the stats widget.

        Returns:
            Formatted stats display
        """
        output = []
        output.append("\n" + "=" * 50)
        output.append("📊 PLAYER STATISTICS")
        output.append("=" * 50)
        output.append(f"\n👤 Name: {self.player_name}")
        output.append(f"📈 Level: {self.level}")
        output.append(f"✨ XP: {self.xp}")
        output.append(f"❤️  Health: {self.health}/100")
        output.append(f"💰 Credits: {self.credits}")
        output.append("-" * 50)
        output.append(ACTIONS_HEADER)
        for idx, (_, button) in enumerate(self.buttons.items(), 1):
            output.append(f"{idx}. {button.render()}")

        output.append("-" * 50)

        return "\n".join(output)


class WidgetSwitcher:
    """Manages widget switching and navigation."""

    def __init__(self):
        """Initialize the widget switcher."""
        self.widgets: dict[str, Widget] = {}
        self.current_widget: Widget | None = None
        self.widget_history: list[str] = []

    def register_widget(self, widget: Widget) -> None:
        """Register a widget with the switcher.

        Args:
            widget: Widget to register
        """
        self.widgets[widget.widget_id] = widget

    def switch_to(self, widget_id: str) -> bool:
        """Switch to a different widget.

        Args:
            widget_id: ID of widget to switch to

        Returns:
            True if switch successful, False if widget not found
        """
        if widget_id not in self.widgets:
            return False

        # Save current widget in history
        if self.current_widget:
            self.widget_history.append(self.current_widget.widget_id)

        self.current_widget = self.widgets[widget_id]
        return True

    def go_back(self) -> bool:
        """Go back to the previous widget.

        Returns:
            True if successful, False if no history
        """
        if not self.widget_history:
            return False

        previous_widget_id = self.widget_history.pop()
        if previous_widget_id in self.widgets:
            self.current_widget = self.widgets[previous_widget_id]
            return True

        return False

    def get_current_widget(self) -> Widget | None:
        """Get the currently active widget.

        Returns:
            Current widget or None
        """
        return self.current_widget

    def render_current(self) -> str:
        """Render the current widget.

        Returns:
            Rendered widget content or empty string
        """
        if not self.current_widget:
            return "No widget loaded"

        return self.current_widget.render()

    def handle_button_click(self, button_id: str) -> WidgetEvent | None:
        """Handle a button click in the current widget.

        Args:
            button_id: ID of button that was clicked

        Returns:
            WidgetEvent if successful, None otherwise
        """
        if not self.current_widget:
            return None

        button = self.current_widget.get_button(button_id)
        if not button:
            return None

        event = button.click()
        if event:
            self.current_widget.on_event(event)

        return event

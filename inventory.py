"""
inventory.py

A small inventory management system used to teach unit testing concepts:
- Setting up test fixtures
- Testing normal ("happy path") behavior
- Testing edge cases and boundary conditions
- Testing error handling with exceptions
- Testing state changes across multiple method calls
- Mocking external dependencies (e.g., a clock or notification service)
"""

from datetime import datetime


class OutOfStockError(Exception):
    """Raised when attempting to remove more stock than is available."""
    pass


class ItemNotFoundError(Exception):
    """Raised when an item does not exist in the inventory."""
    pass


class InventoryItem:
    """Represents a single item tracked in the inventory."""

    def __init__(self, sku, name, quantity=0, price=0.0, low_stock_threshold=5):
        if not sku:
            raise ValueError("SKU cannot be empty")
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        if price < 0:
            raise ValueError("Price cannot be negative")

        self.sku = sku
        self.name = name
        self.quantity = quantity
        self.price = price
        self.low_stock_threshold = low_stock_threshold

    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold

    def total_value(self):
        return round(self.quantity * self.price, 2)

    def __repr__(self):
        return f"InventoryItem(sku={self.sku!r}, name={self.name!r}, quantity={self.quantity})"


class Inventory:
    """
    Manages a collection of InventoryItem objects.

    An optional `notifier` and `clock` can be injected to demonstrate
    dependency injection and mocking in tests.
    """

    def __init__(self, notifier=None, clock=None):
        self._items = {}
        self._notifier = notifier
        self._clock = clock or datetime.now
        self._transaction_log = []

    # ------------------------------------------------------------------
    # Item management
    # ------------------------------------------------------------------
    def add_item(self, item):
        if not isinstance(item, InventoryItem):
            raise TypeError("item must be an InventoryItem instance")
        if item.sku in self._items:
            raise ValueError(f"Item with SKU '{item.sku}' already exists")
        self._items[item.sku] = item
        self._log("ADD_ITEM", item.sku, item.quantity)

    def get_item(self, sku):
        try:
            return self._items[sku]
        except KeyError:
            raise ItemNotFoundError(f"No item found with SKU '{sku}'")

    def remove_item(self, sku):
        if sku not in self._items:
            raise ItemNotFoundError(f"No item found with SKU '{sku}'")
        del self._items[sku]
        self._log("REMOVE_ITEM", sku, None)

    # ------------------------------------------------------------------
    # Stock operations
    # ------------------------------------------------------------------
    def restock(self, sku, amount):
        if amount <= 0:
            raise ValueError("Restock amount must be positive")

        item = self.get_item(sku)
        item.quantity += amount
        self._log("RESTOCK", sku, amount)
        return item.quantity

    def sell(self, sku, amount):
        if amount <= 0:
            raise ValueError("Sell amount must be positive")

        item = self.get_item(sku)
        if amount > item.quantity:
            raise OutOfStockError(
                f"Cannot sell {amount} units of '{sku}'; only {item.quantity} in stock"
            )

        item.quantity -= amount
        self._log("SELL", sku, amount)

        if item.is_low_stock() and self._notifier is not None:
            self._notifier.send_low_stock_alert(item)

        return item.quantity

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def total_inventory_value(self):
        return round(sum(item.total_value() for item in self._items.values()), 2)

    def low_stock_items(self):
        return [item for item in self._items.values() if item.is_low_stock()]

    def item_count(self):
        return len(self._items)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _log(self, action, sku, amount):
        self._transaction_log.append({
            "action": action,
            "sku": sku,
            "amount": amount,
            "timestamp": self._clock(),
        })

    def get_transaction_log(self):
        return list(self._transaction_log)

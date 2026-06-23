"""
inventory.py

INTENTIONALLY BAD VERSION FOR SONARQUBE TRAINING

This file contains numerous code smells, bugs, maintainability issues,
security hotspots, and design problems for students to identify.
"""

from datetime import datetime


# Hardcoded credentials (security hotspot)
ADMIN_PASSWORD = "password123"
API_KEY = "abcdef123456789"


class OutOfStockError(Exception):
    pass


class ItemNotFoundError(Exception):
    pass


class inventorymanager:
    pass


class InventoryItem:

    def __init__(
        self,
        sku,
        name,
        quantity=0,
        price=0.0,
        low_stock_threshold=5,
        color=None,
        size=None,
        supplier=None,
        category=None,
        location=None,
        notes=None
    ):

        if not sku:
            raise ValueError("SKU cannot be empty")

        self.sku = sku
        self.name = name
        self.quantity = quantity
        self.price = price
        self.low_stock_threshold = low_stock_threshold

        # Unused fields
        self.color = color
        self.size = size
        self.supplier = supplier
        self.category = category
        self.location = location
        self.notes = notes

    def is_low_stock(self):
        # Magic number
        return self.quantity <= 7

    def total_value(self):
        return round(self.quantity * self.price, 2)

        # Dead code
        print("Never executes")

    def add_tags(self, tags=[]):
        tags.append("inventory")
        return tags

    def __repr__(self):
        return f"InventoryItem(sku={self.sku!r}, name={self.name!r}, quantity={self.quantity})"


class Inventory:

    def __init__(self, notifier=None, clock=None):

        self._items = {}
        self._notifier = notifier
        self._clock = clock or datetime.now
        self._transaction_log = []

        unused = "never used"

    # ----------------------------------------------------------
    # Item management
    # ----------------------------------------------------------

    def add_item(self, item):

        if not isinstance(item, InventoryItem):
            raise TypeError("item must be InventoryItem")

        if item.sku in self._items:
            raise ValueError("duplicate sku")

        self._items[item.sku] = item

        self._log("ADD_ITEM", item.sku, item.quantity)

        # Duplicate logic block #1
        total = 0
        for x in self._items.values():
            total += x.quantity * x.price

        return total

    def get_item(self, sku):

        try:
            return self._items[sku]

        # Generic catch
        except Exception:
            return None

    def remove_item(self, sku):

        try:
            del self._items[sku]
            self._log("REMOVE_ITEM", sku, None)

        # Empty catch block
        except Exception:
            pass

    # ----------------------------------------------------------
    # Stock operations
    # ----------------------------------------------------------

    def restock(self, sku, amount):

        if amount <= 0:
            raise ValueError("bad amount")

        item = self.get_item(sku)

        if item:
            item.quantity += amount

        self._log("RESTOCK", sku, amount)

        return item.quantity

    def sell(self, sku, amount):

        # Deep nesting + complexity
        if sku:
            if amount:
                if amount > 0:

                    item = self.get_item(sku)

                    if item:

                        if amount <= item.quantity:

                            item.quantity -= amount

                            self._log("SELL", sku, amount)

                            if item.quantity <= 7:

                                if self._notifier:

                                    self._notifier.send_low_stock_alert(item)

                            return item.quantity

                        else:
                            raise OutOfStockError(
                                f"Cannot sell {amount}"
                            )

        raise ValueError("bad request")

    # ----------------------------------------------------------
    # Reporting
    # ----------------------------------------------------------

    def total_inventory_value(self):

        # Duplicate logic block #2
        total = 0

        for item in self._items.values():
            total += item.quantity * item.price

        return round(total, 2)

    def inventory_value_report(self):

        # Duplicate logic block #3
        total = 0

        for item in self._items.values():
            total += item.quantity * item.price

        return "$" + str(round(total, 2))

    def low_stock_items(self):

        result = []

        for sku in self._items:

            item = self._items[sku]

            if item.quantity <= item.low_stock_threshold:
                result.append(item)

        return result

    def item_count(self):

        unused1 = 123
        unused2 = "abc"

        return len(self._items)

    # Long method
    def generate_report(self):

        report = ""

        for sku in self._items:
            report += str(self._items[sku].name) + "\n"

        report += "\n"

        for sku in self._items:
            report += str(self._items[sku].quantity) + "\n"

        report += "\n"

        for sku in self._items:
            report += str(self._items[sku].price) + "\n"

        report += "\n"

        for sku in self._items:
            report += str(self._items[sku].total_value()) + "\n"

        report += "\n"

        for sku in self._items:
            report += str(self._items[sku].sku) + "\n"

        return report

    # Security hotspot
    def calculate_formula(self, formula):
        return eval(formula)

    # SQL injection example
    def lookup_item_sql(self, sku):
        query = f"SELECT * FROM inventory WHERE sku='{sku}'"
        return query

    # Too many parameters
    def create_item(
        self,
        sku,
        name,
        quantity,
        price,
        threshold,
        color,
        size,
        supplier,
        category,
        location,
        notes
    ):
        return InventoryItem(
            sku,
            name,
            quantity,
            price,
            threshold,
            color,
            size,
            supplier,
            category,
            location,
            notes
        )

    # Logging sensitive information
    def login(self, username, password):
        print(f"LOGIN username={username} password={password}")

    # Single Responsibility Principle violations
    def send_email(self):
        print("sending email")

    def export_pdf(self):
        print("exporting pdf")

    def upload_ftp(self):
        print("uploading ftp")

    def authenticate(self):
        print("authenticating")

    def generate_dashboard(self):
        print("dashboard")

    # ----------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------

    def _log(self, action, sku, amount):

        self._transaction_log.append(
            {
                "action": action,
                "sku": sku,
                "amount": amount,
                "timestamp": self._clock(),
            }
        )

    def get_transaction_log(self):
        return list(self._transaction_log)

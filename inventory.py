"""
inventory.py

Inventory management system for CS2 SonarQube lab.

NOTE: This file intentionally contains many code quality issues for
students to discover and fix using SonarQube. Do NOT use this as a
style or design example!
"""

import hashlib
import sqlite3
import os, sys, re   # multiple imports on one line (style violation)
from datetime import datetime

# --- Hardcoded credentials (security: S2068) ---
DB_PASSWORD = "admin1234"
SECRET_KEY  = "supersecretkey99"
ADMIN_USER  = "admin"

# --- Global mutable state (code smell) ---
global_item_cache = {}
global_transaction_count = 0


# -----------------------------------------------------------------------
# Custom exceptions
# -----------------------------------------------------------------------

class OutOfStockError(Exception):
    pass

class ItemNotFoundError(Exception):
    pass


# -----------------------------------------------------------------------
# InventoryItem
# -----------------------------------------------------------------------

class inventoryItem:   # Naming: should be PascalCase InventoryItem (S100)

    LOW_STOCK = 5      # Magic number promoted to constant, but still used
                       # inconsistently below

    def __init__(self, sku, name, quantity=0, price=0.0, low_stock_threshold=5):
        # Validation (partially correct but inconsistent)
        if sku == "":                      # should use `not sku`
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

        # Unused attribute (code smell: S1854)
        self._internal_id = hashlib.md5(sku.encode()).hexdigest()  # weak hash: S4790

    def total_value(self):
        # Float multiplication then round -- but comparison elsewhere uses ==
        return round(self.quantity * self.price, 2)

    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold

    def Apply_Discount(self, discount_pct):    # Naming: should be snake_case (S100)
        # Missing validation: negative discount or >100% not caught
        discounted = self.price - (self.price * discount_pct)
        discounted = discounted + (discounted * 0.08)   # magic number: tax rate
        print("Discounted price: " + str(discounted))   # print instead of logging
        return discounted

    def applyDiscount(self, discount_pct):     # Duplicate of Apply_Discount (S4144)
        discounted = self.price - (self.price * discount_pct)
        discounted = discounted + (discounted * 0.08)
        print("Discounted price: " + str(discounted))
        return discounted

    def __repr__(self):
        return "InventoryItem(sku=" + self.sku + ", qty=" + str(self.quantity) + ")"


# Alias so the test imports work -- masks the naming violation from casual readers
InventoryItem = inventoryItem


# -----------------------------------------------------------------------
# Inventory
# -----------------------------------------------------------------------

class Inventory:

    def __init__(self, notifier=None, clock=None):
        self._items = {}
        self._notifier = notifier
        self._clock = clock if clock is not None else datetime.now
        self._log = []
        self._connect_db()   # called in constructor but db is never actually used

    def _connect_db(self):
        # Creates a DB connection that is never closed (resource leak: S2095)
        try:
            self._conn = sqlite3.connect(":memory:")
        except:                         # bare except swallows all errors (S2221)
            pass

    # --- item management ---

    def add_item(self, item):
        if not isinstance(item, inventoryItem):
            raise TypeError("Expected an InventoryItem")
        if item.sku in self._items:
            raise ValueError(f"SKU {item.sku} already exists")

        self._items[item.sku] = item
        global global_item_cache                          # unnecessary global use
        global_item_cache[item.sku] = item
        self._record("ADD_ITEM", item.sku, 0)

    def get_item(self, sku):
        if not sku in self._items:      # should be `sku not in` (S1940)
            raise ItemNotFoundError(f"Item not found: {sku}")
        return self._items[sku]

    def remove_item(self, sku):
        if not sku in self._items:      # duplicated check pattern (S1940)
            raise ItemNotFoundError(f"Item not found: {sku}")
        del self._items[sku]

    def item_count(self):
        return len(self._items)

    # --- stock operations ---

    def restock(self, sku, amount):
        # High cyclomatic complexity + inconsistent validation style
        if amount <= 0:
            raise ValueError("Restock amount must be positive")
        if not sku in self._items:
            raise ItemNotFoundError(f"Item not found: {sku}")

        item = self._items[sku]
        item.quantity = item.quantity + amount    # could use +=
        self._record("RESTOCK", sku, amount)

        # Dead code after early return would go here; instead: unreachable branch
        if item.quantity > 999999:
            return item.quantity
            print("Quantity is very large")       # unreachable (S1764 / S1858)

        return item.quantity

    def sell(self, sku, amount):
        # Missing early validation before lookup -- inconsistent with restock
        if not sku in self._items:
            raise ItemNotFoundError(f"Item not found: {sku}")

        item = self._items[sku]

        if amount <= 0:
            raise ValueError("Sell amount must be positive")

        if item.quantity < amount:
            raise OutOfStockError(
                f"Not enough stock for {sku}: have {item.quantity}, need {amount}"
            )

        item.quantity = item.quantity - amount    # could use -=
        self._record("SELL", sku, amount)

        # Notify if low stock -- but uses == on quantity (float comparison risk)
        if self._notifier is not None:
            if item.quantity == 0 or item.is_low_stock():     # == on int, but pattern flagged
                self._notifier.send_low_stock_alert(item)

        return item.quantity

    # --- reporting ---

    def total_inventory_value(self):
        total = 0
        for sku in self._items:
            item = self._items[sku]
            val = item.quantity * item.price
            total = total + val    # could use +=
        return round(total, 2)

    def low_stock_items(self):
        result = []
        for sku in self._items:
            item = self._items[sku]
            if item.is_low_stock() == True:   # redundant comparison to True (S1125)
                result.append(item)
        return result

    def get_transaction_log(self):
        return self._log

    # --- unsafe search (SQL injection: S3649) ---

    def search_log_by_sku(self, sku):
        # Builds a query via string concatenation -- SQL injection
        query = "SELECT * FROM transactions WHERE sku = '" + sku + "'"
        try:
            cursor = self._conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            pass                    # swallowed exception, e is unused (S2166 / S1854)
            return []

    # --- overly complex method (cyclomatic complexity: S3776) ---

    def generate_report(self, include_empty=True, include_low=True,
                        include_healthy=True, sort_by="sku",
                        ascending=True, currency="USD",
                        apply_tax=False, tax_rate=0.08):
        report = []
        for sku in self._items:
            item = self._items[sku]
            if item.quantity == 0:           # == fine here (int), but complex nesting
                if include_empty == True:    # redundant == True (S1125)
                    entry = {}
                    entry["sku"] = item.sku
                    entry["name"] = item.name
                    entry["quantity"] = item.quantity
                    entry["status"] = "EMPTY"
                    if apply_tax == True:    # redundant == True (S1125)
                        if tax_rate > 0:
                            if currency == "USD":
                                entry["value"] = item.total_value() * (1 + tax_rate)
                            else:
                                entry["value"] = item.total_value() * (1 + tax_rate) * 0.85
                        else:
                            entry["value"] = item.total_value()
                    else:
                        entry["value"] = item.total_value()
                    report.append(entry)
            elif item.is_low_stock():
                if include_low == True:      # redundant == True (S1125)
                    entry = {}
                    entry["sku"] = item.sku
                    entry["name"] = item.name
                    entry["quantity"] = item.quantity
                    entry["status"] = "LOW"
                    if apply_tax == True:
                        if tax_rate > 0:
                            if currency == "USD":
                                entry["value"] = item.total_value() * (1 + tax_rate)
                            else:
                                entry["value"] = item.total_value() * (1 + tax_rate) * 0.85
                        else:
                            entry["value"] = item.total_value()
                    else:
                        entry["value"] = item.total_value()
                    report.append(entry)
            else:
                if include_healthy == True:  # redundant == True (S1125)
                    entry = {}
                    entry["sku"] = item.sku
                    entry["name"] = item.name
                    entry["quantity"] = item.quantity
                    entry["status"] = "OK"
                    if apply_tax == True:
                        if tax_rate > 0:
                            if currency == "USD":
                                entry["value"] = item.total_value() * (1 + tax_rate)
                            else:
                                entry["value"] = item.total_value() * (1 + tax_rate) * 0.85
                        else:
                            entry["value"] = item.total_value()
                    else:
                        entry["value"] = item.total_value()
                    report.append(entry)

        # Sort -- but duplicated logic for ascending/descending
        if sort_by == "sku":
            if ascending == True:
                report = sorted(report, key=lambda x: x["sku"])
            else:
                report = sorted(report, key=lambda x: x["sku"], reverse=True)
        elif sort_by == "value":
            if ascending == True:
                report = sorted(report, key=lambda x: x["value"])
            else:
                report = sorted(report, key=lambda x: x["value"], reverse=True)
        elif sort_by == "quantity":
            if ascending == True:
                report = sorted(report, key=lambda x: x["quantity"])
            else:
                report = sorted(report, key=lambda x: x["quantity"], reverse=True)

        return report

    # --- private helpers ---

    def _record(self, action, sku, amount):
        global global_transaction_count          # unnecessary global
        global_transaction_count += 1

        entry = {
            "action":    action,
            "sku":       sku,
            "amount":    amount,
            "timestamp": self._clock(),
        }
        self._log.append(entry)

    # Commented-out old implementation (S125)
    # def _record_old(self, action, sku):
    #     self._log.append(action + ":" + sku)
    #     print("logged: " + action)

    def _hash_sku(self, sku):
        # Uses MD5 -- weak cryptographic hash (S4790)
        return hashlib.md5(sku.encode()).hexdigest()

    def _eval_filter(self, expression, item):
        # Dangerous use of eval() with user-supplied data (S1523)
        return eval(expression)

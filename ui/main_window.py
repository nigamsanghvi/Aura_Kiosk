from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFormLayout,
    QHBoxLayout,
    QMessageBox,
)
from PySide6.QtGui import QIntValidator
from PySide6.QtCore import Qt

from core.kiosk import Kiosk
from core.kiosk_interface import KioskInterface
from inventory.inventory import Inventory
from models.product import Product
from payment.strategy import UPIPayment, CardPayment
from pricing.strategy import StandardPricing, DiscountPricing, EmergencyPricing
from failure.handler import Retry, Alert


class KioskGUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aura Retail OS")
        self.setMinimumSize(520, 420)

        self._build_ui()
        self._connect_signals()
        self.setup_backend()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)

        form = QFormLayout()

        self.product_input = QLineEdit()
        self.product_input.setPlaceholderText("e.g. P1")

        # product selection dropdown (optional UX improvement)
        self.product_select = QComboBox()
        self.product_select.setEditable(False)

        self.qty_input = QLineEdit()
        self.qty_input.setPlaceholderText("Quantity")
        self.qty_input.setValidator(QIntValidator(1, 1000000, self))

        self.payment_box = QComboBox()
        self.payment_box.addItems(["UPI", "Card"])  # user-visible

        self.pricing_box = QComboBox()
        self.pricing_box.addItems(["Standard", "Discount", "Emergency"])

        self.price_display = QLabel("Total Price: --")
        self.price_display.setStyleSheet("font-weight: bold; color: green; font-size: 12pt;")

        form.addRow(QLabel("Product ID:"), self.product_input)
        form.addRow(QLabel("Or select product:"), self.product_select)
        form.addRow(QLabel("Quantity:"), self.qty_input)
        form.addRow(QLabel("Payment Method:"), self.payment_box)
        form.addRow(QLabel("Pricing Strategy:"), self.pricing_box)
        form.addRow(QLabel(""), self.price_display)

        main_layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        self.purchase_btn = QPushButton("Purchase")
        self.restock_btn = QPushButton("Restock")
        self.refund_btn = QPushButton("Refund")
        btn_layout.addWidget(self.purchase_btn)
        btn_layout.addWidget(self.restock_btn)
        btn_layout.addWidget(self.refund_btn)
        btn_layout.addStretch()

        main_layout.addLayout(btn_layout)

        # Output
        main_layout.addWidget(QLabel("System Output:"))
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setAcceptRichText(False)
        main_layout.addWidget(self.output, stretch=1)

        # Product creation area
        main_layout.addWidget(QLabel("Add New Product:"))
        create_layout = QFormLayout()
        self.new_id = QLineEdit()
        self.new_name = QLineEdit()
        self.new_price = QLineEdit()
        self.new_price.setPlaceholderText("e.g. 9.99")
        self.new_qty = QLineEdit()
        self.new_qty.setValidator(QIntValidator(0, 1000000, self))
        create_layout.addRow(QLabel("Product ID:"), self.new_id)
        create_layout.addRow(QLabel("Name:"), self.new_name)
        create_layout.addRow(QLabel("Price:"), self.new_price)
        create_layout.addRow(QLabel("Quantity:"), self.new_qty)
        self.add_product_btn = QPushButton("Add Product")
        create_btn_layout = QHBoxLayout()
        create_btn_layout.addWidget(self.add_product_btn)
        create_btn_layout.addStretch()
        main_layout.addLayout(create_layout)
        main_layout.addLayout(create_btn_layout)

        # Product list table
        main_layout.addWidget(QLabel("Available Products:"))
        self.product_table = QTableWidget(0, 4)
        self.product_table.setHorizontalHeaderLabels(["Product ID", "Name", "Price", "Quantity"])
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.product_table, stretch=1)

    def _connect_signals(self):
        self.purchase_btn.clicked.connect(self.purchase)
        self.restock_btn.clicked.connect(self.restock)
        self.refund_btn.clicked.connect(self.refund)
        self.add_product_btn.clicked.connect(self.add_product)
        self.product_select.currentIndexChanged.connect(self.on_product_selected)
        
        # Connect signals for real-time price calculation
        self.qty_input.textChanged.connect(self.update_price_display)
        self.product_input.textChanged.connect(self.update_price_display)
        self.product_select.currentIndexChanged.connect(self.update_price_display)
        self.pricing_box.currentIndexChanged.connect(self.update_price_display)

    def setup_backend(self):
        # Minimal demo inventory; in production this would come from persistence
        inventory = Inventory()
        inventory.add_product(Product("P1", "Medicine", 100), 10)

        handler = Retry(Alert())
        kiosk = Kiosk(inventory, handler)
        self.interface = KioskInterface(kiosk)

        # initial population
        self.refresh_product_list()

    # --- Helpers ---
    def append_log(self, text):
        self.output.append(text)

    def show_error(self, msg):
        QMessageBox.warning(self, "Input Error", msg)

    def get_payment(self):
        return UPIPayment() if self.payment_box.currentText() == "UPI" else CardPayment()

    def get_pricing(self):
        val = self.pricing_box.currentText()
        if val == "Discount":
            return DiscountPricing()
        if val == "Emergency":
            return EmergencyPricing()
        return StandardPricing()

    # --- Actions ---
    def purchase(self):
        # prefer selected product if set
        pid = self.product_select.currentText().strip() or self.product_input.text().strip()
        if not pid:
            self.show_error("Product ID cannot be empty")
            return

        qty_text = self.qty_input.text().strip()
        if not qty_text:
            self.show_error("Quantity is required")
            return

        try:
            qty = int(qty_text)
            if qty <= 0:
                raise ValueError()
        except ValueError:
            self.show_error("Quantity must be a positive integer")
            return

        payment = self.get_payment()
        pricing = self.get_pricing()

        try:
            result = self.interface.purchaseItem(pid, qty, payment, pricing)
            pricing_type = self.pricing_box.currentText()
            if result == "Out of stock":
                self.append_log("[ERROR] Out of stock")
            elif result == "Blocked":
                self.append_log("[ERROR] Purchase blocked by current state")
            elif result == "Rollback":
                self.append_log("[ERROR] Transaction failed; rollback performed")
            else:
                self.append_log(f"[PURCHASE] {result} | Pricing: {pricing_type}")
        except Exception as e:
            self.append_log(f"[ERROR] {e}")
        finally:
            self.refresh_product_list()

    def restock(self):
        pid = self.product_select.currentText().strip() or self.product_input.text().strip()
        if not pid:
            self.show_error("Product ID cannot be empty for restock")
            return

        qty_text = self.qty_input.text().strip()
        if not qty_text:
            self.show_error("Quantity is required for restock")
            return

        try:
            qty = int(qty_text)
            if qty <= 0:
                raise ValueError()
        except ValueError:
            self.show_error("Quantity must be a positive integer")
            return

        try:
            result = self.interface.restockInventory(pid, qty)
            self.append_log(f"[RESTOCK] {result}")
        except Exception as e:
            self.append_log(f"[ERROR] {e}")
        finally:
            self.refresh_product_list()

    def refund(self):
        pid = self.product_select.currentText().strip() or self.product_input.text().strip()
        if not pid:
            self.show_error("Product ID cannot be empty for refund")
            return

        try:
            result = self.interface.refundTransaction(pid)
            self.append_log(f"[REFUND] {result}")
        except Exception as e:
            self.append_log(f"[ERROR] {e}")
        finally:
            self.refresh_product_list()

    # --- Product creation & list ---
    def add_product(self):
        pid = self.new_id.text().strip()
        name = self.new_name.text().strip()
        price_text = self.new_price.text().strip()
        qty_text = self.new_qty.text().strip()

        if not pid or not name or not price_text:
            self.append_log("[ERROR] Product ID, Name and Price are required")
            return

        try:
            price = float(price_text)
            if price < 0:
                raise ValueError()
        except ValueError:
            self.append_log("[ERROR] Price must be a non-negative number")
            return

        try:
            qty = int(qty_text) if qty_text else 0
            if qty < 0:
                raise ValueError()
        except ValueError:
            self.append_log("[ERROR] Quantity must be a non-negative integer")
            return

        product = Product(pid, name, price)
        try:
            result = self.interface.addProduct(product, qty)
            self.append_log(f"[ADD] {result}: {pid} - {name}")
            # clear inputs
            self.new_id.clear()
            self.new_name.clear()
            self.new_price.clear()
            self.new_qty.clear()
        except Exception as e:
            self.append_log(f"[ERROR] {e}")
        finally:
            self.refresh_product_list()

    def refresh_product_list(self):
        try:
            items = self.interface.listProducts()
            # update table
            self.product_table.setRowCount(0)
            self.product_select.clear()
            for row_idx, it in enumerate(items):
                self.product_table.insertRow(row_idx)
                self.product_table.setItem(row_idx, 0, QTableWidgetItem(str(it.get("id"))))
                self.product_table.setItem(row_idx, 1, QTableWidgetItem(str(it.get("name"))))
                self.product_table.setItem(row_idx, 2, QTableWidgetItem(str(it.get("price"))))
                self.product_table.setItem(row_idx, 3, QTableWidgetItem(str(it.get("qty"))))
                # also populate dropdown
                self.product_select.addItem(str(it.get("id")))
        except Exception as e:
            self.append_log(f"[ERROR] {e}")

    def on_product_selected(self, idx):
        # sync selected product id into product_input for convenience
        if idx >= 0:
            self.product_input.setText(self.product_select.currentText())

    def update_price_display(self):
        """Calculate and display the total price based on product, quantity, and pricing strategy."""
        pid = self.product_select.currentText().strip() or self.product_input.text().strip()
        qty_text = self.qty_input.text().strip()

        if not pid or not qty_text:
            self.price_display.setText("Total Price: --")
            return

        try:
            qty = int(qty_text)
            if qty <= 0:
                self.price_display.setText("Total Price: --")
                return

            # Get the base price from inventory via interface
            items = self.interface.listProducts()
            base_price = None
            for item in items:
                if item.get("id") == pid:
                    base_price = float(item.get("price", 0))
                    break

            if base_price is None:
                self.price_display.setText("Total Price: -- (Product not found)")
                return

            # Calculate price with selected strategy
            pricing = self.get_pricing()
            total_price = pricing.calculate(base_price, qty)

            # Display price breakdown
            strategy_name = self.pricing_box.currentText()
            if strategy_name == "Discount":
                discount_percent = 10
                self.price_display.setText(
                    f"Total Price: ₹{total_price:.2f} (10% Discount applied) | Original: ₹{base_price * qty:.2f}"
                )
            elif strategy_name == "Emergency":
                markup_percent = 20
                self.price_display.setText(
                    f"Total Price: ₹{total_price:.2f} (20% Emergency markup) | Original: ₹{base_price * qty:.2f}"
                )
            else:
                self.price_display.setText(f"Total Price: ₹{total_price:.2f}")

        except ValueError:
            self.price_display.setText("Total Price: -- (Invalid quantity)")

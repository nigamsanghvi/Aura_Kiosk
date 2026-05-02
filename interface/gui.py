# Role: Full PySide6 desktop GUI — attractive industrial-dark theme

from __future__ import annotations
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTextEdit,
    QFrame,
    QSplitter,
    QGroupBox,
    QFormLayout,
    QStackedWidget,
    QScrollArea,
    QMessageBox,
    QStatusBar,
    QSizePolicy,
    QTabWidget,
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import (
    QFont,
    QColor,
    QPalette,
    QIcon,
    QPixmap,
    QPainter,
    QBrush,
    QLinearGradient,
)

# ── Project imports ────────────────────────────────────────────
from core.central_registry import CentralRegistry
from core.kiosk_factory import (
    PharmacyKioskFactory,
    FoodKioskFactory,
    EmergencyReliefKioskFactory,
)
from core.kiosk_interface import KioskInterface
from events.event_bus import (
    EventBus,
    EventType,
    IEventSubscriber,
    MaintenanceServiceSubscriber,
    SupplyChainSubscriber,
    CityMonitoringSubscriber,
)
from models.product import Product
from payment.strategy import UPIPayment, CardPayment, WalletPayment
from pricing.strategy import StandardPricing, DiscountPricing, EmergencyPricing
from state.kiosk_state import (
    ActiveState,
    PowerSavingState,
    MaintenanceState,
    EmergencyState,
)
from persistence.storage import Storage

# ──────────────────────────────────────────────────────────────
# COLOUR PALETTE  (industrial-dark with amber accent)
# ──────────────────────────────────────────────────────────────
PAL = {
    "bg": "#0D1117",  # deep navy black
    "surface": "#161B22",  # card background
    "surface2": "#1C2330",  # subtle lift
    "border": "#30363D",  # subtle divider
    "accent": "#E6A817",  # amber / gold
    "accent2": "#F0C040",  # bright amber
    "text": "#E6EDF3",  # primary text
    "text_dim": "#8B949E",  # secondary text
    "green": "#3FB950",  # success
    "red": "#F85149",  # danger/error
    "yellow": "#D29922",  # warning
    "blue": "#58A6FF",  # info / interactive
    "purple": "#BC8CFF",  # highlight
    "teal": "#39D353",
}

STATE_COLOURS = {
    "ACTIVE": PAL["green"],
    "POWER_SAVING": PAL["yellow"],
    "MAINTENANCE": PAL["red"],
    "EMERGENCY": "#FF2020",
}

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {PAL['bg']};
    color: {PAL['text']};
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 13px;
}}
QGroupBox {{
    border: 1px solid {PAL['border']};
    border-radius: 8px;
    margin-top: 16px;
    padding: 8px 12px 12px 12px;
    font-weight: 700;
    font-size: 12px;
    color: {PAL['accent']};
    letter-spacing: 1px;
    text-transform: uppercase;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    background: {PAL['bg']};
}}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background-color: {PAL['surface2']};
    border: 1px solid {PAL['border']};
    border-radius: 6px;
    padding: 6px 10px;
    color: {PAL['text']};
    selection-background-color: {PAL['accent']};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {PAL['accent']};
}}
QComboBox::drop-down {{ border: none; width: 20px; }}
QComboBox::down-arrow {{
    width: 10px; height: 10px;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid {PAL['accent']};
}}
QComboBox QAbstractItemView {{
    background: {PAL['surface2']};
    border: 1px solid {PAL['border']};
    selection-background-color: {PAL['accent']};
    color: {PAL['text']};
    outline: none;
}}
QPushButton {{
    background-color: {PAL['surface2']};
    border: 1px solid {PAL['border']};
    border-radius: 6px;
    padding: 8px 18px;
    color: {PAL['text']};
    font-weight: 600;
    letter-spacing: 0.5px;
}}
QPushButton:hover  {{ background-color: {PAL['accent']}; color: {PAL['bg']}; border-color: {PAL['accent']}; }}
QPushButton:pressed {{ background-color: {PAL['accent2']}; }}
QPushButton.primary  {{ background-color: {PAL['accent']}; color: {PAL['bg']}; border-color: {PAL['accent2']}; }}
QPushButton.primary:hover {{ background-color: {PAL['accent2']}; }}
QPushButton.danger  {{ background-color: #3A1210; color: {PAL['red']}; border-color: {PAL['red']}; }}
QPushButton.danger:hover {{ background-color: {PAL['red']}; color: white; }}
QPushButton.success {{ background-color: #0E2A1A; color: {PAL['green']}; border-color: {PAL['green']}; }}
QPushButton.success:hover {{ background-color: {PAL['green']}; color: {PAL['bg']}; }}
QTableWidget {{
    background-color: {PAL['surface']};
    border: 1px solid {PAL['border']};
    border-radius: 6px;
    gridline-color: {PAL['border']};
    selection-background-color: #1F3A5F;
    alternate-background-color: {PAL['surface2']};
}}
QTableWidget::item {{ padding: 6px 10px; }}
QHeaderView::section {{
    background-color: {PAL['surface2']};
    color: {PAL['accent']};
    border: none;
    border-right: 1px solid {PAL['border']};
    border-bottom: 1px solid {PAL['border']};
    padding: 8px 10px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}
QTextEdit {{
    background-color: {PAL['surface']};
    border: 1px solid {PAL['border']};
    border-radius: 6px;
    padding: 8px;
    color: {PAL['text_dim']};
    font-size: 11px;
    font-family: 'Consolas', monospace;
}}
QTabWidget::pane {{
    border: 1px solid {PAL['border']};
    border-radius: 6px;
    top: -1px;
}}
QTabBar::tab {{
    background: {PAL['surface']};
    color: {PAL['text_dim']};
    border: 1px solid {PAL['border']};
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    padding: 8px 18px;
    margin-right: 3px;
    font-weight: 600;
    font-size: 12px;
}}
QTabBar::tab:selected {{ background: {PAL['surface2']}; color: {PAL['accent']}; }}
QTabBar::tab:hover     {{ color: {PAL['text']}; }}
QScrollBar:vertical {{
    background: {PAL['surface']};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {PAL['border']};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{ background: {PAL['accent']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QStatusBar {{
    background: {PAL['surface']};
    border-top: 1px solid {PAL['border']};
    color: {PAL['text_dim']};
    font-size: 11px;
    padding: 4px 12px;
}}
QSplitter::handle {{ background: {PAL['border']}; width: 1px; }}
QLabel.heading {{
    font-size: 18px;
    font-weight: 800;
    color: {PAL['accent']};
    letter-spacing: 2px;
}}
QLabel.subheading {{
    font-size: 12px;
    color: {PAL['text_dim']};
    letter-spacing: 1px;
}}
QLabel.badge-green  {{ color: {PAL['green']};  font-weight: 700; }}
QLabel.badge-red    {{ color: {PAL['red']};    font-weight: 700; }}
QLabel.badge-yellow {{ color: {PAL['yellow']}; font-weight: 700; }}
QLabel.badge-blue   {{ color: {PAL['blue']};   font-weight: 700; }}
QLabel.badge-accent {{ color: {PAL['accent']}; font-weight: 700; }}
"""


# ──────────────────────────────────────────────────────────────
# GUI event subscriber — forwards events to the log widget
# ──────────────────────────────────────────────────────────────
class GUIEventSubscriber(IEventSubscriber):
    def __init__(self, log_fn):
        self._log = log_fn

    def on_event(self, event_type: str, payload: dict) -> None:
        detail = payload.get("detail", "")
        self._log(f"[EVENT] {event_type}  {detail}")


# ──────────────────────────────────────────────────────────────
# Reusable widgets
# ──────────────────────────────────────────────────────────────
def make_label(text, cls=None, parent=None):
    lbl = QLabel(text, parent)
    if cls:
        lbl.setProperty("class", cls)
    return lbl


def make_btn(text, cls=None):
    btn = QPushButton(text)
    if cls:
        btn.setProperty("class", cls)
    return btn


def h_line():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet(f"color: {PAL['border']}; background: {PAL['border']};")
    return line


def badge(text, colour):
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"background:{colour}22; color:{colour}; border:1px solid {colour}55;"
        f" border-radius:4px; padding:2px 8px; font-weight:700; font-size:11px;"
    )
    return lbl


# ──────────────────────────────────────────────────────────────
# Header bar
# ──────────────────────────────────────────────────────────────
class HeaderBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(72)
        self.setStyleSheet(
            f"background:{PAL['surface']}; border-bottom:1px solid {PAL['border']};"
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 0, 20, 0)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("AURA RETAIL OS")
        title.setStyleSheet(
            f"font-size:20px; font-weight:900; color:{PAL['accent']}; letter-spacing:3px;"
        )
        subtitle = QLabel("Smart City Kiosk Management System  ·  Path A")
        subtitle.setStyleSheet(
            f"font-size:10px; color:{PAL['text_dim']}; letter-spacing:2px;"
        )
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        lay.addLayout(title_col)
        lay.addStretch()

        # Live status badges
        self.state_badge = QLabel("NO KIOSK")
        self.state_badge.setStyleSheet(
            f"background:#1A1A2A; color:{PAL['text_dim']}; border:1px solid {PAL['border']};"
            f" border-radius:4px; padding:4px 12px; font-weight:700; font-size:12px;"
        )
        self.kid_badge = QLabel("─")
        self.kid_badge.setStyleSheet(f"color:{PAL['text_dim']}; font-size:12px;")

        lay.addWidget(self.kid_badge)
        lay.addSpacing(16)
        lay.addWidget(self.state_badge)

    def refresh(self, kiosk_id: str, state: str):
        col = STATE_COLOURS.get(state, PAL["text_dim"])
        self.state_badge.setStyleSheet(
            f"background:{col}22; color:{col}; border:1px solid {col}55;"
            f" border-radius:4px; padding:4px 12px; font-weight:700; font-size:12px;"
        )
        self.state_badge.setText(f"● {state}")
        self.kid_badge.setText(f"🖥  {kiosk_id}")
        self.kid_badge.setStyleSheet(
            f"color:{PAL['text']}; font-size:12px; font-weight:600;"
        )


# ──────────────────────────────────────────────────────────────
# Left sidebar navigation
# ──────────────────────────────────────────────────────────────
class NavButton(QPushButton):
    def __init__(self, icon_text: str, label: str, index: int):
        super().__init__()
        self._index = index
        self.setCheckable(True)
        self.setText(f" {icon_text}  {label}")
        self.setFixedHeight(44)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-left: 3px solid transparent;
                border-radius: 0px;
                padding: 0 16px;
                color: {PAL['text_dim']};
                text-align: left;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {PAL['surface2']};
                color: {PAL['text']};
                border-left-color: {PAL['border']};
            }}
            QPushButton:checked {{
                background: {PAL['accent']}18;
                color: {PAL['accent']};
                border-left-color: {PAL['accent']};
                font-weight: 700;
            }}
        """)


class Sidebar(QWidget):
    page_changed = Signal(int)

    PAGES = [
        ("⚙", "Kiosk Setup", 0),
        ("🛒", "Purchase", 1),
        ("↩", "Refund", 2),
        ("📦", "Restock", 3),
        ("➕", "Add Product", 4),
        ("📊", "Inventory", 5),
        ("🔄", "State Control", 6),
        ("💰", "Pricing", 7),
        ("💳", "Payment", 8),
        ("🔬", "Diagnostics", 9),
        ("📜", "Transactions", 10),
        ("📡", "Event Log", 11),
        ("💾", "Save / Export", 12),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(210)
        self.setStyleSheet(
            f"background:{PAL['surface']}; border-right:1px solid {PAL['border']};"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 12, 0, 12)
        lay.setSpacing(2)

        self._btns: list[NavButton] = []
        for icon, label, idx in self.PAGES:
            btn = NavButton(icon, label, idx)
            btn.clicked.connect(lambda checked, i=idx: self._select(i))
            self._btns.append(btn)
            lay.addWidget(btn)

        lay.addStretch()
        self._btns[0].setChecked(True)

    def _select(self, index: int):
        for b in self._btns:
            b.setChecked(b._index == index)
        self.page_changed.emit(index)


# ──────────────────────────────────────────────────────────────
# Log panel (shared bottom strip)
# ──────────────────────────────────────────────────────────────
class LogPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(140)
        self.setStyleSheet(
            f"background:{PAL['surface']}; border-top:1px solid {PAL['border']};"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        hdr = QHBoxLayout()
        lbl = QLabel("SYSTEM LOG")
        lbl.setStyleSheet(
            f"color:{PAL['accent']}; font-size:10px; font-weight:700; letter-spacing:2px;"
        )
        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setFixedWidth(60)
        self._clear_btn.setStyleSheet(
            f"background:transparent; border:1px solid {PAL['border']}; border-radius:4px;"
            f" color:{PAL['text_dim']}; padding:2px 8px; font-size:11px;"
        )
        hdr.addWidget(lbl)
        hdr.addStretch()
        hdr.addWidget(self._clear_btn)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setStyleSheet(
            f"background:{PAL['bg']}; border:none; color:{PAL['text_dim']}; font-size:11px;"
        )
        lay.addLayout(hdr)
        lay.addWidget(self._log)
        self._clear_btn.clicked.connect(self._log.clear)

    def append(self, text: str, colour: str = PAL["text_dim"]):
        self._log.append(f'<span style="color:{colour}">{text}</span>')
        self._log.verticalScrollBar().setValue(self._log.verticalScrollBar().maximum())


# ──────────────────────────────────────────────────────────────
# Individual page widgets
# ──────────────────────────────────────────────────────────────


class SetupPage(QWidget):
    kiosk_created = Signal(object, str)  # (factory, kiosk_id)

    def __init__(self, log_fn, parent=None):
        super().__init__(parent)
        self._log = log_fn
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)

        heading = QLabel("KIOSK SETUP")
        heading.setStyleSheet(
            f"font-size:22px; font-weight:900; color:{PAL['accent']}; letter-spacing:3px;"
        )
        lay.addWidget(heading)
        sub = QLabel(
            "Create or switch your kiosk. Each type comes pre-loaded with products and defaults."
        )
        sub.setStyleSheet(f"color:{PAL['text_dim']}; font-size:12px;")
        sub.setWordWrap(True)
        lay.addWidget(sub)
        lay.addWidget(h_line())

        # Kiosk type cards
        cards_row = QHBoxLayout()
        self._selected_factory = None
        self._type_btns: list[QPushButton] = []

        factories = [
            (
                "Pharmacy\nKiosk",
                "💊",
                PAL["blue"],
                "Card payments\nStandard pricing\n4 medical products",
                PharmacyKioskFactory,
                "KIOSK-PH",
            ),
            (
                "Food\nKiosk",
                "🍔",
                PAL["green"],
                "UPI payments\n5% discount pricing\n4 food products",
                FoodKioskFactory,
                "KIOSK-FD",
            ),
            (
                "Emergency\nRelief Kiosk",
                "🚨",
                PAL["red"],
                "Wallet payments\nEmergency pricing\n4 essential items",
                EmergencyReliefKioskFactory,
                "KIOSK-ER",
            ),
        ]
        for name, icon, col, desc, FactoryCls, default_id in factories:
            card = QPushButton()
            card.setCheckable(True)
            card_lay = QVBoxLayout(card)
            ico_lbl = QLabel(icon)
            ico_lbl.setStyleSheet(f"font-size:32px;")
            ico_lbl.setAlignment(Qt.AlignCenter)
            name_lbl = QLabel(name)
            name_lbl.setAlignment(Qt.AlignCenter)
            name_lbl.setStyleSheet(f"font-weight:800; font-size:14px; color:{col};")
            desc_lbl = QLabel(desc)
            desc_lbl.setAlignment(Qt.AlignCenter)
            desc_lbl.setStyleSheet(f"color:{PAL['text_dim']}; font-size:11px;")
            card_lay.addWidget(ico_lbl)
            card_lay.addWidget(name_lbl)
            card_lay.addWidget(desc_lbl)
            card.setMinimumHeight(160)
            card.setStyleSheet(
                f"QPushButton{{background:{PAL['surface2']}; border:2px solid {PAL['border']};"
                f" border-radius:10px; padding:8px;}}"
                f"QPushButton:hover{{border-color:{col};}}"
                f"QPushButton:checked{{border-color:{col}; background:{col}18;}}"
            )
            card.clicked.connect(
                lambda checked, fc=FactoryCls, di=default_id: self._select_type(fc, di)
            )
            self._type_btns.append(card)
            cards_row.addWidget(card)

        lay.addLayout(cards_row)

        # ID field
        form = QFormLayout()
        form.setSpacing(10)
        self._kid_input = QLineEdit()
        self._kid_input.setPlaceholderText("e.g. KIOSK-001")
        form.addRow(QLabel("Kiosk ID:"), self._kid_input)
        lay.addLayout(form)

        self._create_btn = make_btn("▶  Launch Kiosk", "primary")
        self._create_btn.setFixedHeight(44)
        self._create_btn.clicked.connect(self._launch)
        lay.addWidget(self._create_btn)
        lay.addStretch()

        self._FactoryCls = None
        self._default_id = ""

    def _select_type(self, FactoryCls, default_id):
        self._FactoryCls = FactoryCls
        self._default_id = default_id
        if not self._kid_input.text().strip():
            self._kid_input.setText(default_id)
        for btn in self._type_btns:
            btn.setChecked(False)
        self.sender().setChecked(True)

    def _launch(self):
        if not self._FactoryCls:
            QMessageBox.warning(self, "Aura", "Please select a kiosk type first.")
            return
        kid = self._kid_input.text().strip() or self._default_id
        self.kiosk_created.emit(self._FactoryCls(), kid)
        self._log(f"Kiosk '{kid}' launched.")


class PurchasePage(QWidget):
    def __init__(self, get_iface, log_fn, parent=None):
        super().__init__(parent)
        self._get_iface = get_iface
        self._log = log_fn
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)

        heading = QLabel("PURCHASE ITEM")
        heading.setStyleSheet(
            f"font-size:22px; font-weight:900; color:{PAL['accent']}; letter-spacing:3px;"
        )
        lay.addWidget(heading)
        lay.addWidget(h_line())

        # Inventory preview
        grp_inv = QGroupBox("Available Products")
        grp_inv_lay = QVBoxLayout(grp_inv)
        self._inv_table = self._make_inv_table()
        grp_inv_lay.addWidget(self._inv_table)
        lay.addWidget(grp_inv)

        # Form
        grp = QGroupBox("Transaction Details")
        form_lay = QFormLayout(grp)
        form_lay.setSpacing(10)

        self._pid = QLineEdit()
        self._pid.setPlaceholderText("e.g. MED-001")
        self._qty = QSpinBox()
        self._qty.setRange(1, 999)
        self._qty.setValue(1)
        self._uid = QLineEdit()
        self._uid.setText("USER-001")
        self._pay = QComboBox()
        self._pay.addItems(["UPI", "Card", "Wallet"])
        self._pric = QComboBox()
        self._pric.addItems(["Standard", "Discount 10%", "Discount 20%", "Emergency"])

        self._price_preview = QLabel("─")
        self._price_preview.setStyleSheet(
            f"color:{PAL['accent']}; font-size:18px; font-weight:800;"
        )

        form_lay.addRow("Product ID:", self._pid)
        form_lay.addRow("Quantity:", self._qty)
        form_lay.addRow("User ID:", self._uid)
        form_lay.addRow("Payment:", self._pay)
        form_lay.addRow("Pricing:", self._pric)
        form_lay.addRow("Est. Price:", self._price_preview)

        # live price preview
        for w in (self._qty, self._pric):
            (
                w.valueChanged.connect(self._update_price)
                if hasattr(w, "valueChanged")
                else None
            )
        self._qty.valueChanged.connect(self._update_price)
        self._pric.currentIndexChanged.connect(self._update_price)
        self._pid.textChanged.connect(self._update_price)

        lay.addWidget(grp)

        self._buy_btn = make_btn("🛒  PURCHASE", "primary")
        self._buy_btn.setFixedHeight(48)
        self._buy_btn.setStyleSheet(
            f"font-size:15px; font-weight:800; background:{PAL['accent']}; color:{PAL['bg']};"
            f" border:none; border-radius:8px;"
        )
        self._buy_btn.clicked.connect(self._do_purchase)
        lay.addWidget(self._buy_btn)
        lay.addStretch()

    def _make_inv_table(self):
        t = QTableWidget(0, 5)
        t.setHorizontalHeaderLabels(["ID", "Name", "Price ₹", "Available", "Essential"])
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t.setAlternatingRowColors(True)
        t.setMaximumHeight(160)
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.setSelectionMode(QTableWidget.SingleSelection)
        t.verticalHeader().setVisible(False)
        t.itemClicked.connect(self._fill_from_table)
        return t

    def _fill_from_table(self, item):
        row = item.row()
        pid = self._inv_table.item(row, 0)
        if pid:
            self._pid.setText(pid.text())

    def refresh_inventory(self):
        iface = self._get_iface()
        if not iface:
            return
        rows = iface.getInventory()
        self._inv_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self._inv_table.setItem(i, 0, QTableWidgetItem(r["product_id"]))
            self._inv_table.setItem(i, 1, QTableWidgetItem(r["name"]))
            self._inv_table.setItem(i, 2, QTableWidgetItem(f"₹{r['base_price']:.2f}"))
            avail_item = QTableWidgetItem(str(r["available"]))
            avail_item.setForeground(
                QColor(
                    PAL["red"]
                    if r["available"] == 0
                    else (PAL["yellow"] if r["available"] <= 5 else PAL["green"])
                )
            )
            self._inv_table.setItem(i, 3, avail_item)
            self._inv_table.setItem(
                i, 4, QTableWidgetItem("✓" if r["is_essential"] else "")
            )

    def _update_price(self):
        iface = self._get_iface()
        if not iface:
            return
        pid = self._pid.text().strip().upper()
        qty = self._qty.value()
        rows = {r["product_id"]: r for r in iface.getInventory()}
        if pid not in rows:
            self._price_preview.setText("─")
            return
        base = rows[pid]["base_price"]
        strategies = [
            StandardPricing(),
            DiscountPricing(0.10),
            DiscountPricing(0.20),
            EmergencyPricing(),
        ]
        pric = strategies[self._pric.currentIndex()]
        from models.product import Product as P

        p = iface.kiosk.inventory.get_product(pid)
        if p:
            total = pric.calculate(p, qty)
            self._price_preview.setText(f"₹ {total:.2f}")

    def _get_payment(self):
        return [UPIPayment(), CardPayment(), WalletPayment()][self._pay.currentIndex()]

    def _get_pricing(self):
        return [
            StandardPricing(),
            DiscountPricing(0.10),
            DiscountPricing(0.20),
            EmergencyPricing(),
        ][self._pric.currentIndex()]

    def _do_purchase(self):
        iface = self._get_iface()
        if not iface:
            QMessageBox.warning(self, "Aura", "No active kiosk. Go to Setup first.")
            return
        pid = self._pid.text().strip().upper()
        qty = self._qty.value()
        uid = self._uid.text().strip() or "ANON"
        if not pid:
            QMessageBox.warning(self, "Aura", "Product ID is required.")
            return

        result = iface.purchaseItem(
            pid, qty, self._get_payment(), self._get_pricing(), uid
        )
        self.refresh_inventory()

        if result.startswith("Success"):
            QMessageBox.information(self, "Purchase Successful", f"✔  {result}")
            self._log(f"PURCHASE OK: {pid} ×{qty}  {result}")
        elif "Blocked" in result or "OutOfStock" in result or "HardwareFault" in result:
            QMessageBox.warning(self, "Purchase Failed", result)
            self._log(f"PURCHASE FAILED: {result}")
        else:
            QMessageBox.critical(
                self, "Transaction Error", f"Failed / Rolled back:\n{result}"
            )
            self._log(f"ROLLBACK: {result}")


class RefundPage(QWidget):
    def __init__(self, get_iface, log_fn, parent=None):
        super().__init__(parent)
        self._get_iface = get_iface
        self._log = log_fn
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)

        heading = QLabel("REFUND TRANSACTION")
        heading.setStyleSheet(
            f"font-size:22px; font-weight:900; color:{PAL['accent']}; letter-spacing:3px;"
        )
        lay.addWidget(heading)
        lay.addWidget(h_line())

        # Recent purchases table
        grp_hist = QGroupBox("Recent Successful Purchases (click to fill form)")
        grp_hist_lay = QVBoxLayout(grp_hist)
        self._hist_table = QTableWidget(0, 5)
        self._hist_table.setHorizontalHeaderLabels(
            ["Product ID", "Qty", "Amount ₹", "Payment", "Txn ID"]
        )
        self._hist_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._hist_table.setAlternatingRowColors(True)
        self._hist_table.setMaximumHeight(180)
        self._hist_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._hist_table.verticalHeader().setVisible(False)
        self._hist_table.itemClicked.connect(self._fill_from_history)
        grp_hist_lay.addWidget(self._hist_table)
        refresh_hist_btn = make_btn("↻  Refresh History")
        refresh_hist_btn.clicked.connect(self.refresh_history)
        grp_hist_lay.addWidget(refresh_hist_btn)
        lay.addWidget(grp_hist)

        grp = QGroupBox("Refund Details")
        form_lay = QFormLayout(grp)
        form_lay.setSpacing(10)
        self._pid = QLineEdit()
        self._pid.setPlaceholderText("Product ID")
        self._qty = QSpinBox()
        self._qty.setRange(1, 999)
        self._amount = QDoubleSpinBox()
        self._amount.setRange(0, 999999)
        self._amount.setDecimals(2)
        self._ref = QLineEdit()
        self._ref.setPlaceholderText("Transaction ID / reference")
        form_lay.addRow("Product ID:", self._pid)
        form_lay.addRow("Quantity:", self._qty)
        form_lay.addRow("Amount ₹:", self._amount)
        form_lay.addRow("Reference:", self._ref)
        lay.addWidget(grp)

        btn = make_btn("↩  PROCESS REFUND", "danger")
        btn.setFixedHeight(44)
        btn.clicked.connect(self._do_refund)
        lay.addWidget(btn)
        lay.addStretch()

    def refresh_history(self):
        iface = self._get_iface()
        if not iface:
            return
        rows = [
            h
            for h in iface.getTransactionHistory()
            if h["type"] == "PURCHASE" and h["status"] == "SUCCESS"
        ]
        self._hist_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self._hist_table.setItem(i, 0, QTableWidgetItem(r.get("product_id", "")))
            self._hist_table.setItem(i, 1, QTableWidgetItem(str(r.get("qty", ""))))
            self._hist_table.setItem(
                i, 2, QTableWidgetItem(f"₹{r.get('amount', 0):.2f}")
            )
            self._hist_table.setItem(i, 3, QTableWidgetItem(r.get("payment", "")))
            self._hist_table.setItem(i, 4, QTableWidgetItem(r.get("txn_id", "")))

    def _fill_from_history(self, item):
        row = item.row()
        self._pid.setText(
            self._hist_table.item(row, 0).text()
            if self._hist_table.item(row, 0)
            else ""
        )
        qty_item = self._hist_table.item(row, 1)
        if qty_item:
            try:
                self._qty.setValue(int(qty_item.text()))
            except:
                pass
        amt_item = self._hist_table.item(row, 2)
        if amt_item:
            try:
                self._amount.setValue(float(amt_item.text().replace("₹", "")))
            except:
                pass
        ref_item = self._hist_table.item(row, 4)
        if ref_item:
            self._ref.setText(ref_item.text())

    def _do_refund(self):
        iface = self._get_iface()
        if not iface:
            QMessageBox.warning(self, "Aura", "No active kiosk.")
            return
        pid = self._pid.text().strip().upper()
        if not pid:
            QMessageBox.warning(self, "Aura", "Product ID required.")
            return
        result = iface.refundTransaction(
            pid, self._qty.value(), self._amount.value(), self._ref.text().strip()
        )
        if result == "Success":
            QMessageBox.information(
                self, "Refund", f"✔  Refund of ₹{self._amount.value():.2f} processed."
            )
            self._log(f"REFUND OK: {pid}  ₹{self._amount.value():.2f}")
            self.refresh_history()
        else:
            QMessageBox.critical(self, "Refund Failed", result)
            self._log(f"REFUND FAILED: {result}")


class RestockPage(QWidget):
    def __init__(self, get_iface, log_fn, parent=None):
        super().__init__(parent)
        self._get_iface = get_iface
        self._log = log_fn
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)

        heading = QLabel("RESTOCK INVENTORY")
        heading.setStyleSheet(
            f"font-size:22px; font-weight:900; color:{PAL['accent']}; letter-spacing:3px;"
        )
        lay.addWidget(heading)
        lay.addWidget(h_line())

        self._inv_table = QTableWidget(0, 4)
        self._inv_table.setHorizontalHeaderLabels(["ID", "Name", "Total", "Available"])
        self._inv_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._inv_table.setAlternatingRowColors(True)
        self._inv_table.setMaximumHeight(200)
        self._inv_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._inv_table.verticalHeader().setVisible(False)
        self._inv_table.itemClicked.connect(
            lambda item: self._pid.setText(
                self._inv_table.item(item.row(), 0).text()
                if self._inv_table.item(item.row(), 0)
                else ""
            )
        )
        lay.addWidget(self._inv_table)

        grp = QGroupBox("Restock Details")
        form = QFormLayout(grp)
        form.setSpacing(10)
        self._pid = QLineEdit()
        self._pid.setPlaceholderText("Product ID")
        self._qty = QSpinBox()
        self._qty.setRange(1, 9999)
        self._qty.setValue(10)
        form.addRow("Product ID:", self._pid)
        form.addRow("Quantity to add:", self._qty)
        lay.addWidget(grp)

        btn = make_btn("📦  RESTOCK", "success")
        btn.setFixedHeight(44)
        btn.clicked.connect(self._do_restock)
        lay.addWidget(btn)
        lay.addStretch()

    def refresh_inventory(self):
        iface = self._get_iface()
        if not iface:
            return
        rows = iface.getInventory()
        self._inv_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self._inv_table.setItem(i, 0, QTableWidgetItem(r["product_id"]))
            self._inv_table.setItem(i, 1, QTableWidgetItem(r["name"]))
            self._inv_table.setItem(i, 2, QTableWidgetItem(str(r["total_stock"])))
            avail = QTableWidgetItem(str(r["available"]))
            avail.setForeground(
                QColor(PAL["red"] if r["available"] == 0 else PAL["green"])
            )
            self._inv_table.setItem(i, 3, avail)

    def _do_restock(self):
        iface = self._get_iface()
        if not iface:
            QMessageBox.warning(self, "Aura", "No active kiosk.")
            return
        pid = self._pid.text().strip().upper()
        if not pid:
            QMessageBox.warning(self, "Aura", "Product ID required.")
            return
        result = iface.restockInventory(pid, self._qty.value())
        if result == "Restocked":
            QMessageBox.information(
                self, "Restock", f"✔  Added {self._qty.value()} units to {pid}."
            )
            self._log(f"RESTOCK: {pid} +{self._qty.value()}")
            self.refresh_inventory()
        else:
            QMessageBox.critical(self, "Error", f"Restock failed: {result}")


class AddProductPage(QWidget):
    def __init__(self, get_iface, log_fn, parent=None):
        super().__init__(parent)
        self._get_iface = get_iface
        self._log = log_fn
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)

        heading = QLabel("ADD NEW PRODUCT")
        heading.setStyleSheet(
            f"font-size:22px; font-weight:900; color:{PAL['accent']}; letter-spacing:3px;"
        )
        lay.addWidget(heading)
        sub = QLabel("Register a custom product into the active kiosk's inventory.")
        sub.setStyleSheet(f"color:{PAL['text_dim']}; font-size:12px;")
        lay.addWidget(sub)
        lay.addWidget(h_line())

        grp = QGroupBox("Product Details")
        form = QFormLayout(grp)
        form.setSpacing(12)
        self._pid = QLineEdit()
        self._pid.setPlaceholderText("e.g. CUSTOM-001")
        self._name = QLineEdit()
        self._name.setPlaceholderText("Product name")
        self._price = QDoubleSpinBox()
        self._price.setRange(0.01, 999999)
        self._price.setDecimals(2)
        self._price.setValue(50.0)
        self._cat = QLineEdit()
        self._cat.setText("general")
        self._qty = QSpinBox()
        self._qty.setRange(0, 9999)
        self._qty.setValue(20)
        self._ess = QComboBox()
        self._ess.addItems(["No", "Yes"])
        form.addRow("Product ID:", self._pid)
        form.addRow("Name:", self._name)
        form.addRow("Price ₹:", self._price)
        form.addRow("Category:", self._cat)
        form.addRow("Initial Stock:", self._qty)
        form.addRow("Essential item:", self._ess)
        lay.addWidget(grp)

        btn = make_btn("➕  ADD PRODUCT", "primary")
        btn.setFixedHeight(44)
        btn.clicked.connect(self._do_add)
        lay.addWidget(btn)
        lay.addStretch()

    def _do_add(self):
        iface = self._get_iface()
        if not iface:
            QMessageBox.warning(self, "Aura", "No active kiosk.")
            return
        pid = self._pid.text().strip().upper()
        name = self._name.text().strip()
        if not pid or not name:
            QMessageBox.warning(self, "Aura", "Product ID and Name are required.")
            return
        essential = self._ess.currentText() == "Yes"
        product = Product(
            pid,
            name,
            self._price.value(),
            self._cat.text().strip(),
            is_essential=essential,
        )
        try:
            iface.kiosk.inventory.add_product(product, self._qty.value())
            QMessageBox.information(
                self,
                "Added",
                f"✔  '{name}' ({pid}) added with {self._qty.value()} units.",
            )
            self._log(f"PRODUCT ADDED: {pid}  {name}  ₹{self._price.value():.2f}")
            self._pid.clear()
            self._name.clear()
        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))


class InventoryPage(QWidget):
    def __init__(self, get_iface, log_fn, parent=None):
        super().__init__(parent)
        self._get_iface = get_iface
        self._log = log_fn
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)

        heading = QLabel("INVENTORY")
        heading.setStyleSheet(
            f"font-size:22px; font-weight:900; color:{PAL['accent']}; letter-spacing:3px;"
        )
        lay.addWidget(heading)
        lay.addWidget(h_line())

        btn_row = QHBoxLayout()
        refresh_btn = make_btn("↻  Refresh")
        refresh_btn.clicked.connect(self.refresh)
        fault_btn = make_btn("⚡ Set HW Fault", "danger")
        fault_btn.clicked.connect(lambda: self._set_hw(False))
        restore_btn = make_btn("✔  Restore HW", "success")
        restore_btn.clicked.connect(lambda: self._set_hw(True))
        btn_row.addWidget(refresh_btn)
        btn_row.addWidget(fault_btn)
        btn_row.addWidget(restore_btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        self._table = QTableWidget(0, 8)
        self._table.setHorizontalHeaderLabels(
            [
                "ID",
                "Name",
                "Category",
                "Price ₹",
                "Total",
                "Reserved",
                "Available",
                "HW / Essential",
            ]
        )
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        lay.addWidget(self._table)

    def refresh(self):
        iface = self._get_iface()
        if not iface:
            return
        rows = iface.getInventory()
        self._table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self._table.setItem(i, 0, QTableWidgetItem(r["product_id"]))
            self._table.setItem(i, 1, QTableWidgetItem(r["name"]))
            p = iface.kiosk.inventory.get_product(r["product_id"])
            self._table.setItem(i, 2, QTableWidgetItem(p.category if p else ""))
            self._table.setItem(i, 3, QTableWidgetItem(f"₹{r['base_price']:.2f}"))
            self._table.setItem(i, 4, QTableWidgetItem(str(r["total_stock"])))
            self._table.setItem(i, 5, QTableWidgetItem(str(r["reserved"])))
            avail = QTableWidgetItem(str(r["available"]))
            avail.setForeground(
                QColor(
                    PAL["red"]
                    if r["available"] == 0
                    else (PAL["yellow"] if r["available"] <= 5 else PAL["green"])
                )
            )
            self._table.setItem(i, 6, avail)
            hw_txt = ("✔ HW" if r["hw_ok"] else "✘ FAULT") + (
                "  ★ Essential" if r["is_essential"] else ""
            )
            hw_item = QTableWidgetItem(hw_txt)
            hw_item.setForeground(QColor(PAL["green"] if r["hw_ok"] else PAL["red"]))
            self._table.setItem(i, 7, hw_item)

    def _set_hw(self, ok: bool):
        iface = self._get_iface()
        if not iface:
            return
        row = self._table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aura", "Select a product row first.")
            return
        pid = self._table.item(row, 0).text()
        iface.kiosk.inventory.set_hardware_ok(pid, ok)
        state = "OK" if ok else "FAULT"
        self._log(f"HW {state}: {pid}")
        self.refresh()


class StatePage(QWidget):
    def __init__(self, get_iface, log_fn, parent=None):
        super().__init__(parent)
        self._get_iface = get_iface
        self._log = log_fn
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)

        heading = QLabel("KIOSK STATE CONTROL")
        heading.setStyleSheet(
            f"font-size:22px; font-weight:900; color:{PAL['accent']}; letter-spacing:3px;"
        )
        lay.addWidget(heading)
        lay.addWidget(h_line())

        self._current_lbl = QLabel("Current state: —")
        self._current_lbl.setStyleSheet(f"font-size:16px; font-weight:700;")
        self._desc_lbl = QLabel("")
        self._desc_lbl.setStyleSheet(f"color:{PAL['text_dim']}; font-size:12px;")
        self._desc_lbl.setWordWrap(True)
        lay.addWidget(self._current_lbl)
        lay.addWidget(self._desc_lbl)
        lay.addSpacing(16)

        states = [
            (
                ActiveState,
                "ACTIVE",
                PAL["green"],
                "● ACTIVE",
                "Full operation. All purchases allowed.",
            ),
            (
                PowerSavingState,
                "POWER_SAVING",
                PAL["yellow"],
                "⚡ POWER SAVING",
                f"Qty limit: {PowerSavingState.MAX_QTY} per transaction.",
            ),
            (
                MaintenanceState,
                "MAINTENANCE",
                PAL["red"],
                "🔧 MAINTENANCE",
                "All purchases blocked. Technician required.",
            ),
            (
                EmergencyState,
                "EMERGENCY",
                "#FF2020",
                "🚨 EMERGENCY",
                f"Lockdown. Max {EmergencyState.MAX_QTY} units per purchase.",
            ),
        ]

        cards = QHBoxLayout()
        for StateCls, name, col, icon_label, desc in states:
            card = QPushButton()
            card.setMinimumHeight(130)
            card_lay = QVBoxLayout(card)
            il = QLabel(icon_label)
            il.setAlignment(Qt.AlignCenter)
            il.setStyleSheet(f"font-size:15px; font-weight:800; color:{col};")
            dl = QLabel(desc)
            dl.setWordWrap(True)
            dl.setAlignment(Qt.AlignCenter)
            dl.setStyleSheet(f"color:{PAL['text_dim']}; font-size:11px;")
            card_lay.addWidget(il)
            card_lay.addWidget(dl)
            card.setStyleSheet(
                f"QPushButton{{background:{PAL['surface2']}; border:2px solid {PAL['border']};"
                f" border-radius:10px; padding:8px;}}"
                f"QPushButton:hover{{border-color:{col}; background:{col}18;}}"
            )
            card.clicked.connect(
                lambda checked, SC=StateCls, n=name: self._set_state(SC, n)
            )
            cards.addWidget(card)
        lay.addLayout(cards)
        lay.addStretch()

    def _set_state(self, StateCls, name):
        iface = self._get_iface()
        if not iface:
            QMessageBox.warning(self, "Aura", "No active kiosk.")
            return
        st = StateCls()
        iface.setKioskState(st)
        col = STATE_COLOURS.get(name, PAL["text"])
        self._current_lbl.setText(f"Current state:")
        self._current_lbl.setStyleSheet(
            f"font-size:16px; font-weight:700; color:{col};"
        )
        self._current_lbl.setText(f"Current state:  {name}")
        self._desc_lbl.setText(st.describe())
        self._log(f"STATE → {name}: {st.describe()}")

    def refresh(self):
        iface = self._get_iface()
        if not iface:
            return
        st = iface.getCurrentState()
        col = STATE_COLOURS.get(st, PAL["text"])
        self._current_lbl.setText(f"Current state:  {st}")
        self._current_lbl.setStyleSheet(
            f"font-size:16px; font-weight:700; color:{col};"
        )
        self._desc_lbl.setText(iface.kiosk.get_state().describe())


class PricingPage(QWidget):
    def __init__(self, get_iface, log_fn, parent=None):
        super().__init__(parent)
        self._get_iface = get_iface
        self._log = log_fn
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)

        heading = QLabel("PRICING STRATEGY")
        heading.setStyleSheet(
            f"font-size:22px; font-weight:900; color:{PAL['accent']}; letter-spacing:3px;"
        )
        lay.addWidget(heading)
        lay.addWidget(h_line())

        self._current_lbl = QLabel("Current pricing: —")
        self._current_lbl.setStyleSheet(f"font-size:14px; color:{PAL['text_dim']};")
        lay.addWidget(self._current_lbl)

        options = [
            (StandardPricing(), "Standard", "Full price. No adjustments.", PAL["blue"]),
            (
                DiscountPricing(0.05),
                "Discount 5%",
                "5% off all products.",
                PAL["green"],
            ),
            (
                DiscountPricing(0.10),
                "Discount 10%",
                "10% off all products.",
                PAL["green"],
            ),
            (
                DiscountPricing(0.20),
                "Discount 20%",
                "20% off. Heavy discount season.",
                PAL["green"],
            ),
            (
                EmergencyPricing(),
                "Emergency",
                "Essential: −20%.  Non-essential: +15%.",
                PAL["red"],
            ),
        ]
        for strat, name, desc, col in options:
            btn = QPushButton(f"  {name}   —  {desc}")
            btn.setFixedHeight(54)
            btn.setStyleSheet(
                f"QPushButton{{background:{PAL['surface2']}; border:1px solid {PAL['border']}; border-left:4px solid {col};"
                f" border-radius:6px; text-align:left; padding:0 16px; color:{PAL['text']}; font-size:13px;}}"
                f"QPushButton:hover{{background:{col}18; border-left-color:{col};}}"
            )
            btn.clicked.connect(lambda checked, s=strat, n=name: self._set(s, n))
            lay.addWidget(btn)
        lay.addStretch()

    def _set(self, strategy, name):
        iface = self._get_iface()
        if not iface:
            QMessageBox.warning(self, "Aura", "No active kiosk.")
            return
        iface.setPricingStrategy(strategy)
        self._current_lbl.setText(f"Current pricing:  {name}")
        self._log(f"PRICING → {name}")

    def refresh(self):
        iface = self._get_iface()
        if iface:
            self._current_lbl.setText(f"Current pricing:  {iface.getCurrentPricing()}")


class PaymentPage(QWidget):
    def __init__(self, get_iface, log_fn, parent=None):
        super().__init__(parent)
        self._get_iface = get_iface
        self._log = log_fn
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)

        heading = QLabel("PAYMENT METHOD")
        heading.setStyleSheet(
            f"font-size:22px; font-weight:900; color:{PAL['accent']}; letter-spacing:3px;"
        )
        lay.addWidget(heading)
        lay.addWidget(h_line())

        self._current_lbl = QLabel("Current payment: —")
        self._current_lbl.setStyleSheet(f"font-size:14px; color:{PAL['text_dim']};")
        lay.addWidget(self._current_lbl)

        for PayCls, name, icon, col in [
            (UPIPayment, "UPI", "📱", PAL["blue"]),
            (CardPayment, "Card", "💳", PAL["purple"]),
            (WalletPayment, "Wallet", "👛", PAL["green"]),
        ]:
            btn = QPushButton(f"  {icon}  {name}")
            btn.setFixedHeight(70)
            btn.setStyleSheet(
                f"QPushButton{{background:{PAL['surface2']}; border:2px solid {PAL['border']}; border-radius:10px;"
                f" font-size:16px; font-weight:700; color:{col};}}"
                f"QPushButton:hover{{border-color:{col}; background:{col}18;}}"
            )
            btn.clicked.connect(lambda checked, PC=PayCls, n=name: self._set(PC, n))
            lay.addWidget(btn)
        lay.addStretch()

    def _set(self, PayCls, name):
        iface = self._get_iface()
        if not iface:
            QMessageBox.warning(self, "Aura", "No active kiosk.")
            return
        iface.setPaymentMethod(PayCls())
        self._current_lbl.setText(f"Current payment:  {name}")
        self._log(f"PAYMENT → {name}")

    def refresh(self):
        iface = self._get_iface()
        if iface:
            self._current_lbl.setText(
                f"Current payment:  {iface.kiosk.get_payment().get_name()}"
            )


class DiagnosticsPage(QWidget):
    def __init__(self, get_iface, log_fn, parent=None):
        super().__init__(parent)
        self._get_iface = get_iface
        self._log = log_fn
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        heading = QLabel("DIAGNOSTICS")
        heading.setStyleSheet(
            f"font-size:22px; font-weight:900; color:{PAL['accent']}; letter-spacing:3px;"
        )
        lay.addWidget(heading)
        lay.addWidget(h_line())

        refresh_btn = make_btn("↻  Run Diagnostics")
        refresh_btn.clicked.connect(self.refresh)
        lay.addWidget(refresh_btn)

        self._grid = QFormLayout()
        self._grid.setSpacing(10)
        self._fields = {}
        for key in ["Kiosk ID", "State", "Pricing", "Payment", "Inventory Items"]:
            val = QLabel("—")
            val.setStyleSheet(f"color:{PAL['text']}; font-weight:600;")
            self._grid.addRow(QLabel(f"{key}:"), val)
            self._fields[key] = val
        lay.addLayout(self._grid)
        lay.addWidget(h_line())

        # Inventory mini table
        self._inv_table = QTableWidget(0, 5)
        self._inv_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Price", "Available", "HW"]
        )
        self._inv_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._inv_table.setAlternatingRowColors(True)
        self._inv_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._inv_table.verticalHeader().setVisible(False)
        lay.addWidget(self._inv_table)

    def refresh(self):
        iface = self._get_iface()
        if not iface:
            QMessageBox.warning(self, "Aura", "No active kiosk.")
            return
        d = iface.runDiagnostics()
        st = d["state"]
        col = STATE_COLOURS.get(st, PAL["text"])
        rows = d["inventory_summary"]
        updates = {
            "Kiosk ID": d["kiosk_id"],
            "State": st,
            "Pricing": d["pricing"],
            "Payment": d["payment"],
            "Inventory Items": str(len(rows)),
        }
        for key, val in updates.items():
            lbl = self._fields[key]
            lbl.setText(val)
            if key == "State":
                lbl.setStyleSheet(f"color:{col}; font-weight:700;")

        self._inv_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self._inv_table.setItem(i, 0, QTableWidgetItem(r["product_id"]))
            self._inv_table.setItem(i, 1, QTableWidgetItem(r["name"]))
            self._inv_table.setItem(i, 2, QTableWidgetItem(f"₹{r['base_price']:.2f}"))
            avail = QTableWidgetItem(str(r["available"]))
            avail.setForeground(
                QColor(PAL["red"] if r["available"] == 0 else PAL["green"])
            )
            self._inv_table.setItem(i, 3, avail)
            hw = QTableWidgetItem("✔" if r["hw_ok"] else "✘ FAULT")
            hw.setForeground(QColor(PAL["green"] if r["hw_ok"] else PAL["red"]))
            self._inv_table.setItem(i, 4, hw)


class TransactionsPage(QWidget):
    def __init__(self, get_iface, log_fn, parent=None):
        super().__init__(parent)
        self._get_iface = get_iface
        self._log = log_fn
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        heading = QLabel("TRANSACTION HISTORY")
        heading.setStyleSheet(
            f"font-size:22px; font-weight:900; color:{PAL['accent']}; letter-spacing:3px;"
        )
        lay.addWidget(heading)
        lay.addWidget(h_line())

        refresh_btn = make_btn("↻  Refresh")
        refresh_btn.clicked.connect(self.refresh)
        lay.addWidget(refresh_btn)

        self._table = QTableWidget(0, 8)
        self._table.setHorizontalHeaderLabels(
            [
                "#",
                "Type",
                "Product ID",
                "Qty",
                "Amount ₹",
                "Pricing",
                "Payment",
                "Status",
            ]
        )
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        lay.addWidget(self._table)

    def refresh(self):
        iface = self._get_iface()
        if not iface:
            return
        history = iface.getTransactionHistory()
        self._table.setRowCount(len(history))
        for i, h in enumerate(history):
            self._table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self._table.setItem(i, 1, QTableWidgetItem(h["type"]))
            self._table.setItem(i, 2, QTableWidgetItem(h.get("product_id", "")))
            self._table.setItem(i, 3, QTableWidgetItem(str(h.get("qty", ""))))
            self._table.setItem(i, 4, QTableWidgetItem(f"₹{h.get('amount', 0):.2f}"))
            self._table.setItem(i, 5, QTableWidgetItem(h.get("pricing", "")))
            self._table.setItem(i, 6, QTableWidgetItem(h.get("payment", "")))
            status_item = QTableWidgetItem(h["status"])
            status_item.setForeground(
                QColor(PAL["green"] if h["status"] == "SUCCESS" else PAL["red"])
            )
            self._table.setItem(i, 7, status_item)


class EventLogPage(QWidget):
    def __init__(self, log_fn, parent=None):
        super().__init__(parent)
        self._log = log_fn
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        heading = QLabel("SYSTEM EVENT LOG")
        heading.setStyleSheet(
            f"font-size:22px; font-weight:900; color:{PAL['accent']}; letter-spacing:3px;"
        )
        lay.addWidget(heading)
        lay.addWidget(h_line())

        btn_row = QHBoxLayout()
        ref_btn = make_btn("↻  Refresh")
        ref_btn.clicked.connect(self.refresh)
        clear_btn = make_btn("🗑  Clear Display", "danger")
        clear_btn.clicked.connect(lambda: self._display.clear())
        btn_row.addWidget(ref_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        self._display = QTextEdit()
        self._display.setReadOnly(True)
        self._display.setStyleSheet(
            f"background:{PAL['surface']}; border:1px solid {PAL['border']}; border-radius:6px;"
            f" color:{PAL['text_dim']}; font-size:11px; font-family: Consolas, monospace;"
        )
        lay.addWidget(self._display)

    def refresh(self):
        reg = CentralRegistry.get_instance()
        logs = reg.get_event_log()
        self._display.clear()
        for entry in logs:
            colour = (
                PAL["red"]
                if "FAIL" in entry.upper() or "ERROR" in entry.upper()
                else (
                    PAL["yellow"]
                    if "WARN" in entry.upper() or "BLOCK" in entry.upper()
                    else PAL["green"] if "SUCCESS" in entry.upper() else PAL["text_dim"]
                )
            )
            self._display.append(f'<span style="color:{colour}">{entry}</span>')


class SavePage(QWidget):
    def __init__(self, get_iface, log_fn, parent=None):
        super().__init__(parent)
        self._get_iface = get_iface
        self._log = log_fn
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(16)

        heading = QLabel("SAVE / EXPORT")
        heading.setStyleSheet(
            f"font-size:22px; font-weight:900; color:{PAL['accent']}; letter-spacing:3px;"
        )
        lay.addWidget(heading)
        lay.addWidget(h_line())

        grp = QGroupBox("JSON Export Paths")
        form = QFormLayout(grp)
        self._inv_path = QLineEdit("data/inventory_export.json")
        self._txn_path = QLineEdit("data/transactions_export.json")
        form.addRow("Inventory file:", self._inv_path)
        form.addRow("Transactions file:", self._txn_path)
        lay.addWidget(grp)

        save_btn = make_btn("💾  Save to JSON", "primary")
        save_btn.setFixedHeight(48)
        save_btn.clicked.connect(self._do_save)
        lay.addWidget(save_btn)
        lay.addStretch()

    def _do_save(self):
        iface = self._get_iface()
        if not iface:
            QMessageBox.warning(self, "Aura", "No active kiosk.")
            return
        inv_path = self._inv_path.text().strip()
        txn_path = self._txn_path.text().strip()
        Storage.save_inventory(iface.getInventory(), inv_path)
        Storage.save_transactions(iface.getTransactionHistory(), txn_path)
        QMessageBox.information(
            self, "Saved", f"✔  Inventory → {inv_path}\n✔  Transactions → {txn_path}"
        )
        self._log(f"SAVED: inventory→{inv_path}  transactions→{txn_path}")


# ──────────────────────────────────────────────────────────────
# Main Window
# ──────────────────────────────────────────────────────────────


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aura Retail OS — Smart City Kiosk System")
        self.resize(1280, 820)
        self.setMinimumSize(1000, 680)

        self._iface: KioskInterface | None = None
        self._bus: EventBus | None = None

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        self._header = HeaderBar()
        root.addWidget(self._header)

        # Body: sidebar + content
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self._sidebar = Sidebar()
        body.addWidget(self._sidebar)

        # Content stack
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._stack = QStackedWidget()
        content_layout.addWidget(self._stack, 1)

        # Log panel at bottom
        self._log_panel = LogPanel()
        content_layout.addWidget(self._log_panel)

        body.addWidget(content_widget, 1)

        body_widget = QWidget()
        body_widget.setLayout(body)
        root.addWidget(body_widget, 1)

        # Status bar
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Ready — Create a kiosk to begin")

        # Build pages
        def get_iface():
            return self._iface

        self._setup_page = SetupPage(self._append_log)
        self._purchase_page = PurchasePage(get_iface, self._append_log)
        self._refund_page = RefundPage(get_iface, self._append_log)
        self._restock_page = RestockPage(get_iface, self._append_log)
        self._add_product_page = AddProductPage(get_iface, self._append_log)
        self._inventory_page = InventoryPage(get_iface, self._append_log)
        self._state_page = StatePage(get_iface, self._append_log)
        self._pricing_page = PricingPage(get_iface, self._append_log)
        self._payment_page = PaymentPage(get_iface, self._append_log)
        self._diag_page = DiagnosticsPage(get_iface, self._append_log)
        self._txn_page = TransactionsPage(get_iface, self._append_log)
        self._event_page = EventLogPage(self._append_log)
        self._save_page = SavePage(get_iface, self._append_log)

        for page in [
            self._setup_page,
            self._purchase_page,
            self._refund_page,
            self._restock_page,
            self._add_product_page,
            self._inventory_page,
            self._state_page,
            self._pricing_page,
            self._payment_page,
            self._diag_page,
            self._txn_page,
            self._event_page,
            self._save_page,
        ]:
            # Wrap in scroll area
            scroll = QScrollArea()
            scroll.setWidget(page)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setStyleSheet(f"background:{PAL['bg']};")
            self._stack.addWidget(scroll)

        # Signals
        self._sidebar.page_changed.connect(self._on_page_changed)
        self._setup_page.kiosk_created.connect(self._on_kiosk_created)

        # Auto-refresh timer
        self._timer = QTimer()
        self._timer.timeout.connect(self._periodic_refresh)
        self._timer.start(3000)

        self._append_log(
            "Aura Retail OS started. Go to Kiosk Setup to begin.", PAL["accent"]
        )

    def _append_log(self, msg: str, colour: str = PAL["text_dim"]):
        self._log_panel.append(msg, colour)

    def _on_kiosk_created(self, factory, kiosk_id: str):
        # Build event bus with all subscribers + GUI subscriber
        bus = EventBus()
        gui_sub = GUIEventSubscriber(lambda m: self._append_log(m, PAL["blue"]))
        for et in [
            EventType.PURCHASE_SUCCESS,
            EventType.PURCHASE_FAILED,
            EventType.REFUND_SUCCESS,
            EventType.RESTOCK_DONE,
            EventType.LOW_STOCK,
            EventType.HARDWARE_FAILURE,
            EventType.HARDWARE_RECALIBRATED,
            EventType.EMERGENCY_ACTIVATED,
            EventType.TRANSACTION_ROLLBACK,
            EventType.STATE_CHANGED,
            EventType.PRICING_CHANGED,
        ]:
            bus.subscribe(et, gui_sub)
        bus.subscribe(EventType.HARDWARE_FAILURE, MaintenanceServiceSubscriber())
        bus.subscribe(EventType.LOW_STOCK, SupplyChainSubscriber())
        bus.subscribe(EventType.EMERGENCY_ACTIVATED, CityMonitoringSubscriber())

        self._bus = bus
        self._iface = factory.create_kiosk(kiosk_id, bus)
        self._on_kiosk_ready(kiosk_id)

    def _on_kiosk_ready(self, kiosk_id: str):
        st = self._iface.getCurrentState()
        self._header.refresh(kiosk_id, st)
        self._status.showMessage(f"Active kiosk: {kiosk_id}  |  State: {st}")
        self._append_log(f"Kiosk '{kiosk_id}' is live.", PAL["green"])
        # Refresh data pages
        self._purchase_page.refresh_inventory()
        self._restock_page.refresh_inventory()
        self._inventory_page.refresh()
        self._state_page.refresh()
        self._pricing_page.refresh()
        self._payment_page.refresh()

    def _on_page_changed(self, index: int):
        self._stack.setCurrentIndex(index)
        # Refresh relevant pages on visit
        if not self._iface:
            return
        refresh_map = {
            1: self._purchase_page.refresh_inventory,
            2: self._refund_page.refresh_history,
            3: self._restock_page.refresh_inventory,
            5: self._inventory_page.refresh,
            6: self._state_page.refresh,
            7: self._pricing_page.refresh,
            8: self._payment_page.refresh,
            9: self._diag_page.refresh,
            10: self._txn_page.refresh,
            11: self._event_page.refresh,
        }
        if fn := refresh_map.get(index):
            fn()

    def _periodic_refresh(self):
        if not self._iface:
            return
        st = self._iface.getCurrentState()
        self._header.refresh(self._iface.kiosk.kiosk_id, st)
        self._status.showMessage(
            f"Kiosk: {self._iface.kiosk.kiosk_id}  |  State: {st}  |  "
            f"Pricing: {self._iface.getCurrentPricing()}  |  "
            f"Payment: {self._iface.kiosk.get_payment().get_name()}"
        )


# ──────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────


def main():
    CentralRegistry._instance = None
    CentralRegistry.get_instance().log("=== GUI Session Started ===")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)

    # Override palette for dark mode
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(PAL["bg"]))
    palette.setColor(QPalette.WindowText, QColor(PAL["text"]))
    palette.setColor(QPalette.Base, QColor(PAL["surface"]))
    palette.setColor(QPalette.AlternateBase, QColor(PAL["surface2"]))
    palette.setColor(QPalette.Text, QColor(PAL["text"]))
    palette.setColor(QPalette.Button, QColor(PAL["surface2"]))
    palette.setColor(QPalette.ButtonText, QColor(PAL["text"]))
    palette.setColor(QPalette.Highlight, QColor(PAL["accent"]))
    palette.setColor(QPalette.HighlightedText, QColor(PAL["bg"]))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

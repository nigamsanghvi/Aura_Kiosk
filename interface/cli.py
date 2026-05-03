# ============================================================
# Module: cli.py
# Role: Full interactive CLI — access every system feature
# ============================================================

from __future__ import annotations
import sys, os, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

# ── ANSI colours ──────────────────────────────────────────────
R = "\033[0m"
B = "\033[1m"
DIM = "\033[2m"
CY = "\033[96m"
GR = "\033[92m"
YL = "\033[93m"
RD = "\033[91m"
MG = "\033[95m"
BL = "\033[94m"
WH = "\033[97m"

STATE_COLOUR = {
    "ACTIVE": GR,
    "POWER_SAVING": YL,
    "MAINTENANCE": RD,
    "EMERGENCY": RD + B,
}

# ── Global session state ───────────────────────────────────────
session: dict = {}


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────


def cls():
    os.system("cls" if os.name == "nt" else "clear")


def banner():
    print(f"""
{CY}{B}╔══════════════════════════════════════════════════════════════╗
║           AURA RETAIL OS  ·  SMART CITY KIOSK SYSTEM         ║
║                  Interactive CLI Console                       ║
╚══════════════════════════════════════════════════════════════╝{R}""")


def status_bar():
    iface: KioskInterface = session.get("iface")
    if not iface:
        return
    st = iface.getCurrentState()
    sc = STATE_COLOUR.get(st, WH)
    ktype = session.get("ktype", "?")
    kid = session.get("kid", "?")
    pr = iface.getCurrentPricing()
    pay = iface.kiosk.get_payment().get_name()
    print(f"{DIM}─────────────────────────────────────────────────────────────{R}")
    print(
        f"  Kiosk {BL}{B}{kid}{R} ({BL}{ktype}{R})  "
        f"State: {sc}{B}{st}{R}  "
        f"Pricing: {MG}{pr}{R}  "
        f"Payment: {MG}{pay}{R}"
    )
    print(f"{DIM}─────────────────────────────────────────────────────────────{R}")


def pause():
    input(f"\n{DIM}  Press Enter to continue…{R}")


def ask(prompt: str, default: str = "") -> str:
    val = input(
        f"  {WH}{prompt}{R}{DIM}{'  ['+default+']' if default else ''}: {R}"
    ).strip()
    return val if val else default


def ask_int(prompt: str, default: int | None = None) -> int | None:
    raw = ask(prompt, str(default) if default is not None else "")
    try:
        return int(raw)
    except ValueError:
        print(f"  {RD}Invalid number.{R}")
        return None


def ask_float(prompt: str, default: float | None = None) -> float | None:
    raw = ask(prompt, str(default) if default is not None else "")
    try:
        return float(raw)
    except ValueError:
        print(f"  {RD}Invalid number.{R}")
        return None


def ok(msg):
    print(f"  {GR}✔  {msg}{R}")


def err(msg):
    print(f"  {RD}✘  {msg}{R}")


def info(msg):
    print(f"  {CY}ℹ  {msg}{R}")


def warn(msg):
    print(f"  {YL}⚠  {msg}{R}")


def pick_payment():
    print(f"\n  Payment method:")
    print(f"  {BL}1{R}. UPI    {BL}2{R}. Card    {BL}3{R}. Wallet")
    ch = ask("Choice", "1")
    return {"1": UPIPayment(), "2": CardPayment(), "3": WalletPayment()}.get(
        ch, UPIPayment()
    )


def pick_pricing():
    print(f"\n  Pricing strategy:")
    print(f"  {BL}1{R}. Standard    {BL}2{R}. Discount 10%    {BL}3{R}. Emergency")
    ch = ask("Choice", "1")
    return {
        "1": StandardPricing(),
        "2": DiscountPricing(0.10),
        "3": EmergencyPricing(),
    }.get(ch, StandardPricing())


def require_kiosk() -> bool:
    if not session.get("iface"):
        err("No kiosk active. Please create/select a kiosk first (option K).")
        return False
    return True


def show_inventory_table():
    iface: KioskInterface = session["iface"]
    rows = iface.getInventory()
    print(
        f"\n  {B}{'ID':<12}{'Name':<26}{'Price':>8}{'Total':>8}{'Avail':>8}{'HW':>6}{'Essential':>10}{R}"
    )
    print(f"  {'─'*78}")
    for r in rows:
        hw = f"{GR}OK{R}" if r["hw_ok"] else f"{RD}FAULT{R}"
        ess = f"{YL}✓{R}" if r["is_essential"] else ""
        avail_col = RD if r["available"] == 0 else (YL if r["available"] <= 5 else GR)
        print(
            f"  {CY}{r['product_id']:<12}{R}{r['name']:<26}"
            f"{r['base_price']:>8.2f}{r['total_stock']:>8}"
            f"  {avail_col}{r['available']:>5}{R}  {hw}  {ess:>8}"
        )


# ─────────────────────────────────────────────────────────────
# Menu sections
# ─────────────────────────────────────────────────────────────


def menu_select_kiosk():
    cls()
    banner()
    print(f"\n{B}  ╔═ SELECT / CREATE KIOSK ═══════════════════════════════╗{R}")
    print(f"  {BL}1{R}. Pharmacy Kiosk          (Card payments, Standard pricing)")
    print(f"  {BL}2{R}. Food Kiosk               (UPI payments, 5% discount)")
    print(f"  {BL}3{R}. Emergency Relief Kiosk   (Wallet payments, Emergency pricing)")
    print(f"  {BL}0{R}. Back")
    ch = ask("\n  Choose kiosk type", "1")
    if ch == "0":
        return
    factories = {
        "1": (PharmacyKioskFactory, "Pharmacy", "KIOSK-PH"),
        "2": (FoodKioskFactory, "Food", "KIOSK-FD"),
        "3": (EmergencyReliefKioskFactory, "EmergencyRelief", "KIOSK-ER"),
    }
    if ch not in factories:
        err("Invalid choice.")
        pause()
        return

    FactoryCls, ktype, default_id = factories[ch]
    kid = ask("Kiosk ID", default_id)

    # Event bus with all 3 built-in subscribers
    bus = EventBus()
    bus.subscribe(EventType.HARDWARE_FAILURE, MaintenanceServiceSubscriber())
    bus.subscribe(EventType.HARDWARE_RECALIBRATED, MaintenanceServiceSubscriber())
    bus.subscribe(EventType.LOW_STOCK, SupplyChainSubscriber())
    bus.subscribe(EventType.EMERGENCY_ACTIVATED, CityMonitoringSubscriber())
    bus.subscribe(EventType.TRANSACTION_ROLLBACK, CityMonitoringSubscriber())

    iface = FactoryCls().create_kiosk(kid, bus)
    session["iface"] = iface
    session["bus"] = bus
    session["kid"] = kid
    session["ktype"] = ktype

    ok(f"{ktype} kiosk '{kid}' is ready.")
    pause()


def menu_purchase():
    cls()
    banner()
    status_bar()
    if not require_kiosk():
        pause()
        return

    print(f"\n{B}  ╔═ PURCHASE ═══════════════════════════════════════════╗{R}")
    show_inventory_table()

    pid = ask("\n  Product ID").upper()
    qty = ask_int("Quantity", 1)
    if qty is None or qty <= 0:
        err("Quantity must be a positive integer.")
        pause()
        return
    uid = ask("User ID", "USER-001")
    pay = pick_payment()
    pric = pick_pricing()

    iface: KioskInterface = session["iface"]
    print()
    result = iface.purchaseItem(pid, qty, pay, pric, uid)

    if result.startswith("Success"):
        ok(f"Transaction complete: {result}")
    elif "OutOfStock" in result:
        err("Out of stock.")
    elif "Blocked" in result:
        warn(f"Purchase blocked by kiosk state: {result}")
    elif "HardwareFault" in result:
        warn(f"Hardware fault: {result}")
    else:
        err(f"Transaction failed / rolled back: {result}")
    pause()


def menu_refund():
    cls()
    banner()
    status_bar()
    if not require_kiosk():
        pause()
        return

    print(f"\n{B}  ╔═ REFUND ════════════════════════════════════════════╗{R}")
    iface: KioskInterface = session["iface"]

    history = iface.getTransactionHistory()
    purchases = [
        h for h in history if h["type"] == "PURCHASE" and h["status"] == "SUCCESS"
    ]
    if not purchases:
        info("No successful purchases to refund.")
        pause()
        return

    print(f"\n  {B}Recent purchases:{R}")
    for i, h in enumerate(purchases[-10:], 1):
        print(
            f"  {BL}{i:>2}{R}. {h['product_id']:<12} qty={h.get('qty','?'):>3}  "
            f"₹{h.get('amount',0):.2f}  txn={h.get('txn_id','')}"
        )

    pid = ask("\n  Product ID to refund").upper()
    qty = ask_int("Quantity to return", 1)
    if qty is None:
        pause()
        return
    amount = ask_float("Refund amount (₹)", 0.0)
    if amount is None:
        pause()
        return
    ref = ask("Reference/txn ID", "")

    result = iface.refundTransaction(pid, qty, amount or 0.0, ref)
    if result == "Success":
        ok(f"Refund of ₹{amount:.2f} processed for {pid}.")
    else:
        err(f"Refund failed: {result}")
    pause()


def menu_restock():
    cls()
    banner()
    status_bar()
    if not require_kiosk():
        pause()
        return

    print(f"\n{B}  ╔═ RESTOCK INVENTORY ════════════════════════════════╗{R}")
    show_inventory_table()

    pid = ask("\n  Product ID to restock").upper()
    qty = ask_int("Quantity to add", 10)
    if qty is None or qty <= 0:
        err("Quantity must be positive.")
        pause()
        return

    iface: KioskInterface = session["iface"]
    result = iface.restockInventory(pid, qty)
    if result == "Restocked":
        ok(f"Added {qty} units to {pid}.")
    else:
        err(f"Restock failed: {result}")
    pause()


def menu_add_product():
    cls()
    banner()
    status_bar()
    if not require_kiosk():
        pause()
        return

    print(f"\n{B}  ╔═ ADD NEW PRODUCT ══════════════════════════════════╗{R}")
    pid = ask("Product ID (e.g. CUSTOM-001)").upper()
    name = ask("Product name")
    price = ask_float("Base price (₹)", 50.0)
    if price is None:
        pause()
        return
    cat = ask("Category", "general")
    qty = ask_int("Initial stock", 10)
    if qty is None:
        pause()
        return
    ess_s = ask("Is this an essential item? (y/n)", "n")
    essential = ess_s.lower() in ("y", "yes")

    if not pid or not name:
        err("Product ID and name are required.")
        pause()
        return

    product = Product(pid, name, price, cat, is_essential=essential)
    iface: KioskInterface = session["iface"]
    try:
        iface.kiosk.inventory.add_product(product, qty)
        ok(f"Product '{name}' ({pid}) added with {qty} units.")
    except ValueError as e:
        err(str(e))
    pause()


def menu_inventory():
    cls()
    banner()
    status_bar()
    if not require_kiosk():
        pause()
        return

    print(f"\n{B}  ╔═ INVENTORY ════════════════════════════════════════╗{R}")
    show_inventory_table()

    print(f"\n  {B}Hardware controls:{R}")
    print(f"  {BL}1{R}. Set hardware FAULT on a product")
    print(f"  {BL}2{R}. Restore hardware OK on a product")
    print(f"  {BL}0{R}. Back")
    ch = ask("Choice", "0")
    if ch in ("1", "2"):
        pid = ask("Product ID").upper()
        iface: KioskInterface = session["iface"]
        iface.kiosk.inventory.set_hardware_ok(pid, ch == "2")
        state_label = "restored to OK" if ch == "2" else "set to FAULT"
        ok(f"Hardware for {pid} {state_label}.")
        if ch == "1":
            session["bus"].publish(
                EventType.HARDWARE_FAILURE,
                {"kiosk_id": session["kid"], "detail": f"Hardware fault on {pid}"},
            )
    pause()


def menu_state():
    cls()
    banner()
    status_bar()
    if not require_kiosk():
        pause()
        return

    iface: KioskInterface = session["iface"]
    print(f"\n{B}  ╔═ KIOSK STATE ══════════════════════════════════════╗{R}")
    print(
        f"  Current state: {STATE_COLOUR.get(iface.getCurrentState(), WH)}"
        f"{B}{iface.getCurrentState()}{R}"
    )
    print(f"\n  Set new state:")
    states = {
        "1": (ActiveState, "ACTIVE", GR),
        "2": (PowerSavingState, "POWER_SAVING", YL),
        "3": (MaintenanceState, "MAINTENANCE", RD),
        "4": (EmergencyState, "EMERGENCY", RD),
    }
    for k, (_, name, col) in states.items():
        print(f"  {BL}{k}{R}. {col}{name}{R}")
    print(f"  {BL}0{R}. Back")
    ch = ask("Choice", "0")
    if ch in states:
        StateCls, name, _ = states[ch]
        iface.setKioskState(StateCls())
        ok(f"State changed to {name}.")
        ok(iface.kiosk.get_state().describe())
    pause()


def menu_pricing():
    cls()
    banner()
    status_bar()
    if not require_kiosk():
        pause()
        return

    iface: KioskInterface = session["iface"]
    print(f"\n{B}  ╔═ PRICING STRATEGY ════════════════════════════════╗{R}")
    print(f"  Current pricing: {MG}{iface.getCurrentPricing()}{R}")
    print(f"\n  {BL}1{R}. Standard       (full price)")
    print(f"  {BL}2{R}. Discount 5%    (light discount)")
    print(f"  {BL}3{R}. Discount 10%   (medium discount)")
    print(f"  {BL}4{R}. Discount 20%   (heavy discount)")
    print(f"  {BL}5{R}. Emergency       (essential items discounted, others marked up)")
    print(f"  {BL}0{R}. Back")
    strategies = {
        "1": StandardPricing(),
        "2": DiscountPricing(0.05),
        "3": DiscountPricing(0.10),
        "4": DiscountPricing(0.20),
        "5": EmergencyPricing(),
    }
    ch = ask("Choice", "0")
    if ch in strategies:
        iface.setPricingStrategy(strategies[ch])
        ok(f"Pricing changed to: {iface.getCurrentPricing()}")
    pause()


def menu_payment():
    cls()
    banner()
    status_bar()
    if not require_kiosk():
        pause()
        return

    iface: KioskInterface = session["iface"]
    print(f"\n{B}  ╔═ PAYMENT METHOD ══════════════════════════════════╗{R}")
    print(f"  Current: {MG}{iface.kiosk.get_payment().get_name()}{R}")
    print(f"\n  {BL}1{R}. UPI     {BL}2{R}. Card     {BL}3{R}. Wallet")
    print(f"  {BL}0{R}. Back")
    methods = {"1": UPIPayment(), "2": CardPayment(), "3": WalletPayment()}
    ch = ask("Choice", "0")
    if ch in methods:
        iface.setPaymentMethod(methods[ch])
        ok(f"Payment method set to: {iface.kiosk.get_payment().get_name()}")
    pause()


def menu_diagnostics():
    cls()
    banner()
    status_bar()
    if not require_kiosk():
        pause()
        return

    iface: KioskInterface = session["iface"]
    d = iface.runDiagnostics()
    print(f"\n{B}  ╔═ DIAGNOSTICS ══════════════════════════════════════╗{R}")
    print(f"  Kiosk ID      : {CY}{d['kiosk_id']}{R}")
    print(f"  State         : {STATE_COLOUR.get(d['state'],WH)}{B}{d['state']}{R}")
    print(f"  State desc    : {d['state_desc']}")
    print(f"  Pricing       : {MG}{d['pricing']}{R}")
    print(f"  Payment       : {MG}{d['payment']}{R}")
    print(f"\n{B}  Inventory summary:{R}")
    show_inventory_table()
    pause()


def menu_history():
    cls()
    banner()
    status_bar()
    if not require_kiosk():
        pause()
        return

    iface: KioskInterface = session["iface"]
    history = iface.getTransactionHistory()
    print(f"\n{B}  ╔═ TRANSACTION HISTORY ══════════════════════════════╗{R}")
    if not history:
        info("No transactions yet.")
    else:
        print(
            f"\n  {B}{'#':<4}{'Type':<10}{'Product':<14}{'Qty':>5}{'Amount':>10}"
            f"{'Pricing':<14}{'Payment':<10}{'Status':<10}{'Time'}{R}"
        )
        print(f"  {'─'*90}")
        for i, h in enumerate(history, 1):
            st_col = GR if h["status"] == "SUCCESS" else RD
            print(
                f"  {i:<4}{h['type']:<10}{h.get('product_id',''):<14}"
                f"{str(h.get('qty',''))[:5]:>5}  "
                f"₹{h.get('amount',0):>7.2f}  "
                f"{h.get('pricing',''):<14}{h.get('payment',''):<10}"
                f"{st_col}{h['status']:<10}{R}{h.get('timestamp','')}"
            )
    pause()


def menu_event_log():
    cls()
    banner()
    print(f"\n{B}  ╔═ SYSTEM EVENT LOG ════════════════════════════════╗{R}")
    reg = CentralRegistry.get_instance()
    logs = reg.get_event_log()
    if not logs:
        info("Event log is empty.")
    else:
        show_n = ask_int("How many recent entries to show", 20) or 20
        for entry in logs[-show_n:]:
            print(f"  {DIM}{entry}{R}")
    pause()


def menu_persist():
    cls()
    banner()
    status_bar()
    if not require_kiosk():
        pause()
        return

    iface: KioskInterface = session["iface"]
    print(f"\n{B}  ╔═ SAVE TO JSON ════════════════════════════════════╗{R}")
    inv_file = ask("Inventory file path", "data/inventory_session.json")
    txn_file = ask("Transactions file path", "data/transactions_session.json")
    Storage.save_inventory(iface.getInventory(), inv_file)
    Storage.save_transactions(iface.getTransactionHistory(), txn_file)
    ok(f"Inventory saved  → {inv_file}")
    ok(f"Transactions saved → {txn_file}")
    pause()


def menu_failure_demo():
    cls()
    banner()
    status_bar()
    if not require_kiosk():
        pause()
        return

    print(f"\n{B}  ╔═ FAILURE HANDLER CHAIN DEMO ═══════════════════════╗{R}")
    print(f"  This demonstrates the Chain of Responsibility pattern.")
    print(f"  Type a failure description; the chain will handle it.\n")
    print(f"  Example issues:")
    print(f"    {DIM}• 'timeout occurred'    → RetryHandler catches it")
    print(f"    • 'motor jam detected'  → RecalibrateHandler catches it")
    print(f"    • 'unknown error xyz'   → AlertHandler escalates it{R}\n")

    issue = ask("Describe the failure", "timeout occurred")
    from failure.handler import build_default_chain

    chain = build_default_chain()
    print()
    result = chain.handle(issue)
    ok(f"Chain resolution: {result}")
    pause()


# ─────────────────────────────────────────────────────────────
# Main menu loop
# ─────────────────────────────────────────────────────────────

MENU_ITEMS = [
    ("K", "Select / Create Kiosk", menu_select_kiosk),
    ("P", "Purchase Item", menu_purchase),
    ("R", "Refund Transaction", menu_refund),
    ("S", "Restock Inventory", menu_restock),
    ("A", "Add New Product", menu_add_product),
    ("I", "View Inventory", menu_inventory),
    ("T", "Kiosk State", menu_state),
    ("C", "Pricing Strategy", menu_pricing),
    ("M", "Payment Method", menu_payment),
    ("D", "Diagnostics", menu_diagnostics),
    ("H", "Transaction History", menu_history),
    ("E", "System Event Log", menu_event_log),
    ("J", "Save Session to JSON", menu_persist),
    ("F", "Failure Handler Chain Demo", menu_failure_demo),
    ("Q", "Quit", None),
]


def main_menu():
    while True:
        cls()
        banner()
        status_bar() if session.get("iface") else print()
        print(f"\n{B}  Main Menu{R}\n")
        for key, label, _ in MENU_ITEMS:
            col = RD if key == "Q" else BL
            print(f"  {col}[{key}]{R}  {label}")
        print()
        ch = ask("Command").upper()
        for key, _, fn in MENU_ITEMS:
            if ch == key:
                if fn is None:
                    cls()
                    print(
                        f"\n{CY}{B}  Thank you for using Aura Retail OS. Goodbye!{R}\n"
                    )
                    sys.exit(0)
                fn()
                break
        else:
            err(f"Unknown command: '{ch}'")
            time.sleep(0.8)


if __name__ == "__main__":
    CentralRegistry._instance = None
    CentralRegistry.get_instance().log("=== CLI Session Started ===")
    cls()
    banner()
    print(f"\n{CY}  Welcome to the Aura Retail OS interactive console.{R}")
    print(f"  Start by pressing {BL}[K]{R} to create a kiosk.\n")
    pause()
    main_menu()

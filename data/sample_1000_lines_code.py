"""
================================================================================
LEGACY E-COMMERCE & PAYMENT GATEWAY MONOLITHIC MODULE (TEST FILE ~1000 LINES)
================================================================================
This monolithic Python file simulates a large, complex, and legacy enterprise
order processing engine with high branching, nested loops, and multiple dependencies.
"""

import os
import sys
import json
import time
import math
import hashlib
import random
import datetime
import urllib.parse
from typing import Dict, List, Any, Optional, Tuple

# ==============================================================================
# SECTION 1: GLOBAL CONFIGURATION & CONSTANTS
# ==============================================================================

MAX_RETRY_ATTEMPTS = 5
DEFAULT_CURRENCY = "USD"
SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "INR", "JPY", "CAD", "AUD"]
MIN_ORDER_VAL = 0.50
MAX_ORDER_VAL = 100000.00
FRAUD_RISK_THRESHOLD = 75.0

TAX_RATES_BY_STATE = {
    "CA": 0.0925, "NY": 0.08875, "TX": 0.0825, "FL": 0.0700, "WA": 0.0650,
    "IL": 0.0875, "PA": 0.0600, "OH": 0.0575, "GA": 0.0400, "NC": 0.0475,
    "MI": 0.0600, "NJ": 0.06625, "VA": 0.0530, "WA_LOCAL": 0.1010, "OR": 0.0000
}

DISCOUNT_TIERS = {
    "BRONZE": {"min_spend": 50.0, "rate": 0.05},
    "SILVER": {"min_spend": 200.0, "rate": 0.10},
    "GOLD": {"min_spend": 500.0, "rate": 0.15},
    "PLATINUM": {"min_spend": 1000.0, "rate": 0.20},
    "DIAMOND": {"min_spend": 5000.0, "rate": 0.25}
}

# ==============================================================================
# SECTION 2: UTILITY AND SANITIZATION FUNCTIONS
# ==============================================================================

def sanitize_string_input(val: Any) -> str:
    """Sanitizes user input string against malicious payloads."""
    if val is None:
        return ""
    s = str(val).strip()
    s = s.replace("<script>", "").replace("</script>", "")
    s = s.replace("'", "''").replace(";", "")
    return s

def format_currency_amount(amount: float, currency: str = "USD") -> str:
    """Formats numeric balance into standardized string representation."""
    if currency not in SUPPORTED_CURRENCIES:
        currency = DEFAULT_CURRENCY
    if amount < 0:
        return f"-{currency} {abs(amount):,.2f}"
    return f"{currency} {amount:,.2f}"

def generate_transaction_hash(user_id: str, order_id: str, amount: float, timestamp: float) -> str:
    """Generates cryptographic SHA-256 fingerprint for idempotency."""
    seed = f"{user_id}::{order_id}::{amount:.4f}::{timestamp}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()

def is_valid_email_address(email: str) -> bool:
    """Basic validation for customer email format."""
    if not email or "@" not in email or "." not in email:
        return False
    parts = email.split("@")
    if len(parts) != 2 or len(parts[0]) == 0 or len(parts[1]) < 3:
        return False
    return True

# ==============================================================================
# SECTION 3: INVENTORY AND STOCK VERIFICATION
# ==============================================================================

class InventoryManager:
    """Simulates warehouse inventory tracking and reservation locks."""

    def __init__(self):
        self.mock_inventory_db = {
            "PROD-001": {"name": "Mechanical Keyboard", "stock": 45, "price": 120.00, "weight_kg": 1.2},
            "PROD-002": {"name": "4K Ultra-wide Monitor", "stock": 12, "price": 450.00, "weight_kg": 6.8},
            "PROD-003": {"name": "USB-C Braided Cable", "stock": 500, "price": 15.00, "weight_kg": 0.1},
            "PROD-004": {"name": "Noise Cancelling Headphones", "stock": 30, "price": 280.00, "weight_kg": 0.4},
            "PROD-005": {"name": "Ergonomic Mesh Chair", "stock": 5, "price": 350.00, "weight_kg": 18.5}
        }
        self.reserved_items = {}

    def check_item_availability(self, item_id: str, requested_qty: int) -> Tuple[bool, str, float]:
        if not item_id or requested_qty <= 0:
            return False, "Invalid item request", 0.0
        
        if item_id not in self.mock_inventory_db:
            return False, f"Item {item_id} not found in catalog", 0.0
            
        item = self.mock_inventory_db[item_id]
        available_stock = item["stock"] - self.reserved_items.get(item_id, 0)
        
        if available_stock < requested_qty:
            return False, f"Insufficient stock for {item['name']}. Available: {available_stock}", item["price"]
            
        return True, "Item in stock", item["price"]

    def reserve_stock(self, order_id: str, item_id: str, qty: int) -> bool:
        avail, _, _ = self.check_item_availability(item_id, qty)
        if not avail:
            return False
        current_res = self.reserved_items.get(item_id, 0)
        self.reserved_items[item_id] = current_res + qty
        return True

    def release_reservation(self, order_id: str, item_id: str, qty: int) -> None:
        if item_id in self.reserved_items:
            self.reserved_items[item_id] = max(0, self.reserved_items[item_id] - qty)

# ==============================================================================
# SECTION 4: FRAUD DETECTION ENGINE (HIGH COMPLEXITY LOGIC)
# ==============================================================================

class FraudDetectionEngine:
    """Evaluates multi-variable risk signals for payment fraud."""

    def __init__(self):
        self.high_risk_countries = ["XX", "YY", "ZZ", "UNKNOWN"]
        self.velocity_cache = {}

    def compute_risk_score(
        self,
        user_id: str,
        user_ip: str,
        billing_country: str,
        shipping_country: str,
        order_amount: float,
        is_guest: bool,
        card_fingerprint: str,
        previous_chargebacks: int
    ) -> Dict[str, Any]:
        """
        Deep nested decision logic calculating an overall fraud score (0 to 100).
        High cyclomatic complexity and branching density.
        """
        risk_score = 10.0
        reasons = []

        # 1. IP and Geolocation Checks
        if billing_country != shipping_country:
            risk_score += 25.0
            reasons.append("Cross-border shipping address mismatch")
            if billing_country in self.high_risk_countries or shipping_country in self.high_risk_countries:
                risk_score += 30.0
                reasons.append("High-risk country destination")

        if user_ip.startswith("10.") or user_ip.startswith("192.168."):
            # Internal test network
            pass
        elif user_ip.startswith("172.") or user_ip.startswith("100."):
            risk_score += 15.0
            reasons.append("VPN / Data center proxy IP detected")

        # 2. Amount and Order Size Checks
        if order_amount > 5000.00:
            risk_score += 20.0
            reasons.append("Order amount exceeds standard threshold (> $5,000)")
            if is_guest:
                risk_score += 25.0
                reasons.append("Guest checkout for high-value order")
        elif order_amount < 1.00:
            risk_score += 35.0
            reasons.append("Micro-transaction card testing pattern (< $1.00)")

        # 3. User History & Chargebacks
        if previous_chargebacks > 0:
            penalty = previous_chargebacks * 30.0
            risk_score += penalty
            reasons.append(f"Customer has {previous_chargebacks} historical chargebacks recorded")

        # 4. Velocity Checks (Number of requests in short duration)
        now = time.time()
        user_history = self.velocity_cache.get(user_id, [])
        # Keep only events in last 300 seconds
        recent_events = [t for t in user_history if now - t < 300]
        recent_events.append(now)
        self.velocity_cache[user_id] = recent_events

        if len(recent_events) > 5:
            risk_score += 30.0
            reasons.append(f"High velocity trigger: {len(recent_events)} orders in 5 minutes")
        elif len(recent_events) > 3:
            risk_score += 10.0
            reasons.append("Moderate velocity warning")

        # Normalize score between 0.0 and 100.0
        final_score = min(100.0, max(0.0, risk_score))
        action = "DECLINE" if final_score >= FRAUD_RISK_THRESHOLD else ("MANUAL_REVIEW" if final_score >= 50.0 else "APPROVE")

        return {
            "fraud_score": round(final_score, 2),
            "action": action,
            "reasons": reasons,
            "is_flagged": final_score >= 50.0
        }

# ==============================================================================
# SECTION 5: TAX, SHIPPING, AND DISCOUNT CALCULATORS
# ==============================================================================

def calculate_state_sales_tax(subtotal: float, state: str, has_exemption: bool = False) -> float:
    """Calculates applicable US state sales tax."""
    if has_exemption or subtotal <= 0:
        return 0.0
    state_code = state.upper().strip() if state else "UNKNOWN"
    rate = TAX_RATES_BY_STATE.get(state_code, 0.05) # Default 5% for other states
    return round(subtotal * rate, 2)

def calculate_tiered_discount(subtotal: float, tier_name: str, coupon_code: Optional[str] = None) -> Tuple[float, str]:
    """Calculates user tier discounts and stackable promotional coupon codes."""
    if subtotal <= 0:
        return 0.0, "None"
        
    discount = 0.0
    applied_rules = []
    
    tier = tier_name.upper() if tier_name else "NONE"
    if tier in DISCOUNT_TIERS:
        tier_cfg = DISCOUNT_TIERS[tier]
        if subtotal >= tier_cfg["min_spend"]:
            tier_discount = subtotal * tier_cfg["rate"]
            discount += tier_discount
            applied_rules.append(f"{tier} Member ({int(tier_cfg['rate']*100)}%)")
            
    if coupon_code:
        code_clean = coupon_code.upper().strip()
        if code_clean == "WELCOME20" and subtotal >= 50.0:
            discount += subtotal * 0.20
            applied_rules.append("Coupon: 20% Off")
        elif code_clean == "FLAT50" and subtotal >= 300.0:
            discount += 50.00
            applied_rules.append("Coupon: $50 Flat Off")
        elif code_clean == "FREESHIP":
            applied_rules.append("Free Shipping Voucher")
            
    # Max discount cannot exceed 60% of total
    max_discount_allowed = subtotal * 0.60
    final_discount = min(discount, max_discount_allowed)
    
    return round(final_discount, 2), " + ".join(applied_rules) if applied_rules else "None"

def calculate_shipping_cost(total_weight_kg: float, distance_km: float, is_express: bool, is_fragile: bool) -> float:
    """Calculates courier freight cost based on distance and parcel specifications."""
    if total_weight_kg <= 0 or distance_km <= 0:
        return 0.0
        
    base_fee = 5.00
    weight_fee = total_weight_kg * 1.50
    distance_fee = (distance_km / 100.0) * 2.00
    
    total_shipping = base_fee + weight_fee + distance_fee
    
    if is_express:
        total_shipping *= 1.75
        
    if is_fragile:
        total_shipping += 8.50
        
    return round(total_shipping, 2)

# ==============================================================================
# SECTION 6: PAYMENT GATEWAY INTEGRATIONS & MOCK DRIVERS
# ==============================================================================

class PaymentGatewayStripe:
    """Simulates Stripe Payment Intent workflow."""

    def charge(self, amount: float, card_number: str, exp_month: int, exp_year: int, cvc: str) -> Dict[str, Any]:
        time.sleep(0.01) # Simulated network call
        if not card_number or len(card_number) < 13:
            return {"success": False, "code": "INVALID_CARD_NUMBER", "msg": "Card number format rejected"}
        if exp_year < 2026 or (exp_year == 2026 and exp_month < 10):
            return {"success": False, "code": "EXPIRED_CARD", "msg": "Card expiration is in the past"}
        if len(cvc) not in [3, 4]:
            return {"success": False, "code": "INVALID_CVC", "msg": "Security code invalid"}
            
        # Simulate gateway declines for specific test numbers
        if card_number.endswith("0000"):
            return {"success": False, "code": "INSUFFICIENT_FUNDS", "msg": "Issuer declined due to low balance"}
        if card_number.endswith("9999"):
            return {"success": False, "code": "CARD_LOST_OR_STOLEN", "msg": "Issuer flagged card as lost/stolen"}
            
        tx_id = f"ch_stripe_{int(time.time()*1000)}_{random.randint(100,999)}"
        return {"success": True, "transaction_id": tx_id, "amount_charged": amount, "gateway": "Stripe"}

class PaymentGatewayPayPal:
    """Simulates PayPal Express checkout workflow."""

    def process_order(self, paypal_payer_id: str, amount: float) -> Dict[str, Any]:
        if not paypal_payer_id or len(paypal_payer_id) < 5:
            return {"success": False, "code": "INVALID_PAYER_ID", "msg": "PayPal authentication missing"}
        if amount <= 0:
            return {"success": False, "code": "INVALID_AMOUNT", "msg": "Order amount zero or negative"}
            
        tx_id = f"PAYID-{hashlib.md5(str(time.time()).encode()).hexdigest()[:12].upper()}"
        return {"success": True, "transaction_id": tx_id, "amount_charged": amount, "gateway": "PayPal"}

# ==============================================================================
# SECTION 7: MONOLITHIC MASTER ORDER PROCESSOR (VERY HIGH COMPLEXITY)
# ==============================================================================

class MonolithicOrderProcessor:
    """
    Central orchestration engine for processing multi-item orders,
    running fraud detection, inventory locking, and payment capture.
    """

    def __init__(self):
        self.inventory = InventoryManager()
        self.fraud = FraudDetectionEngine()
        self.stripe_gw = PaymentGatewayStripe()
        self.paypal_gw = PaymentGatewayPayPal()
        self.order_audit_log = []

    def execute_complete_order(self, order_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Giant monolithic pipeline processing order end-to-end.
        High nesting, multiple conditional error trees, and branch interactions.
        """
        start_time = time.time()
        order_id = order_payload.get("order_id", f"ORD-{int(time.time())}")
        user_id = order_payload.get("user_id", "GUEST_USER")
        user_ip = order_payload.get("client_ip", "127.0.0.1")
        items = order_payload.get("items", [])
        shipping_info = order_payload.get("shipping_address", {})
        payment_info = order_payload.get("payment_info", {})
        coupon = order_payload.get("coupon_code", None)
        user_tier = order_payload.get("user_tier", "STANDARD")
        
        # 1. Basic Payload Validation
        if not items or len(items) == 0:
            return {"status": "FAILED", "order_id": order_id, "error": "Order item list cannot be empty"}
            
        if not shipping_info or not shipping_info.get("state") or not shipping_info.get("country"):
            return {"status": "FAILED", "order_id": order_id, "error": "Incomplete shipping destination address"}

        # 2. Inventory Check and Subtotal Calculation
        subtotal = 0.0
        total_weight = 0.0
        reserved_items_tracker = []
        
        for item_entry in items:
            item_id = item_entry.get("id")
            qty = item_entry.get("qty", 1)
            
            is_avail, msg, unit_price = self.inventory.check_item_availability(item_id, qty)
            if not is_avail:
                # Rollback any prior reservations
                for res_id, res_qty in reserved_items_tracker:
                    self.inventory.release_reservation(order_id, res_id, res_qty)
                return {"status": "FAILED", "order_id": order_id, "error": f"Inventory allocation error: {msg}"}
                
            self.inventory.reserve_stock(order_id, item_id, qty)
            reserved_items_tracker.append((item_id, qty))
            
            item_subtotal = unit_price * qty
            subtotal += item_subtotal
            # Mock weight: 1.5kg per item
            total_weight += 1.5 * qty

        # 3. Discount Calculations
        discount_amount, discount_details = calculate_tiered_discount(subtotal, user_tier, coupon)
        taxable_amount = max(0.0, subtotal - discount_amount)

        # 4. Tax Calculations
        state = shipping_info.get("state", "CA")
        is_tax_exempt = order_payload.get("is_tax_exempt", False)
        tax_amount = calculate_state_sales_tax(taxable_amount, state, is_tax_exempt)

        # 5. Shipping Cost
        shipping_dist = float(shipping_info.get("distance_km", 250.0))
        is_exp = bool(shipping_info.get("is_express", False))
        is_frag = bool(order_payload.get("contains_fragile_items", False))
        shipping_fee = calculate_shipping_cost(total_weight, shipping_dist, is_exp, is_frag)

        final_total = round(taxable_amount + tax_amount + shipping_fee, 2)

        # 6. Fraud Evaluation
        billing_country = payment_info.get("billing_country", shipping_info.get("country", "US"))
        shipping_country = shipping_info.get("country", "US")
        card_fingerprint = hashlib.md5(payment_info.get("card_number", "EMPTY").encode()).hexdigest()
        is_guest_user = user_id.startswith("GUEST")

        fraud_result = self.fraud.compute_risk_score(
            user_id=user_id,
            user_ip=user_ip,
            billing_country=billing_country,
            shipping_country=shipping_country,
            order_amount=final_total,
            is_guest=is_guest_user,
            card_fingerprint=card_fingerprint,
            previous_chargebacks=int(order_payload.get("user_chargebacks", 0))
        )

        if fraud_result["action"] == "DECLINE":
            for res_id, res_qty in reserved_items_tracker:
                self.inventory.release_reservation(order_id, res_id, res_qty)
            return {
                "status": "REJECTED_BY_FRAUD_SYSTEM",
                "order_id": order_id,
                "fraud_score": fraud_result["fraud_score"],
                "reasons": fraud_result["reasons"]
            }

        # 7. Payment Processing Execution
        payment_method = payment_info.get("method", "STRIPE").upper()
        payment_success = False
        payment_tx_id = ""
        payment_error_msg = ""

        if payment_method == "STRIPE":
            card_num = payment_info.get("card_number", "")
            exp_m = int(payment_info.get("exp_month", 12))
            exp_y = int(payment_info.get("exp_year", 2028))
            cvc_val = payment_info.get("cvc", "123")
            
            charge_res = self.stripe_gw.charge(final_total, card_num, exp_m, exp_y, cvc_val)
            if charge_res["success"]:
                payment_success = True
                payment_tx_id = charge_res["transaction_id"]
            else:
                payment_error_msg = f"Stripe decline: {charge_res['msg']} (Code: {charge_res['code']})"

        elif payment_method == "PAYPAL":
            payer_id = payment_info.get("paypal_payer_id", "")
            paypal_res = self.paypal_gw.process_order(payer_id, final_total)
            if paypal_res["success"]:
                payment_success = True
                payment_tx_id = paypal_res["transaction_id"]
            else:
                payment_error_msg = f"PayPal decline: {paypal_res['msg']}"
        else:
            payment_error_msg = f"Unsupported payment gateway provider: '{payment_method}'"

        # 8. Handling Payment Result
        if not payment_success:
            for res_id, res_qty in reserved_items_tracker:
                self.inventory.release_reservation(order_id, res_id, res_qty)
            return {
                "status": "PAYMENT_FAILED",
                "order_id": order_id,
                "error": payment_error_msg,
                "subtotal": subtotal,
                "attempted_charge": final_total
            }

        # 9. Final Order Confirmation & Audit Logging
        duration_ms = round((time.time() - start_time) * 1000, 2)
        audit_entry = {
            "order_id": order_id,
            "user_id": user_id,
            "total_amount": final_total,
            "transaction_id": payment_tx_id,
            "fraud_score": fraud_result["fraud_score"],
            "processed_in_ms": duration_ms,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        self.order_audit_log.append(audit_entry)

        return {
            "status": "COMPLETED",
            "order_id": order_id,
            "transaction_id": payment_tx_id,
            "pricing_summary": {
                "subtotal": subtotal,
                "discount_applied": discount_amount,
                "discount_description": discount_details,
                "tax_amount": tax_amount,
                "shipping_fee": shipping_fee,
                "final_total": final_total
            },
            "fraud_assessment": fraud_result,
            "processing_time_ms": duration_ms
        }

# ==============================================================================
# SECTION 8: AUTOMATED INTEGRATION TESTS (MODULE RUNNER)
# ==============================================================================

def run_sample_test_suite():
    """Runs a simulated batch test over the order processing monolith."""
    print("Initializing Monolithic Order Processor Test Run...")
    processor = MonolithicOrderProcessor()
    
    test_order = {
        "order_id": "ORD-998822",
        "user_id": "USER-4401",
        "client_ip": "172.56.21.9",
        "items": [
            {"id": "PROD-001", "qty": 2},
            {"id": "PROD-003", "qty": 3}
        ],
        "shipping_address": {
            "state": "NY",
            "country": "US",
            "distance_km": 420.0,
            "is_express": True
        },
        "payment_info": {
            "method": "STRIPE",
            "card_number": "4111222233334444",
            "exp_month": 11,
            "exp_year": 2029,
            "cvc": "789",
            "billing_country": "US"
        },
        "coupon_code": "WELCOME20",
        "user_tier": "GOLD",
        "user_chargebacks": 0
    }
    
    result = processor.execute_complete_order(test_order)
    print("\n--- Test Order Execution Result ---")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    run_sample_test_suite()

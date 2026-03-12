"""Travel policy tool handlers.

Stubs return mock data. Replace with real Itilite API calls.
"""
import json


_MOCK_POLICIES = {
    "flights": {
        "domestic": {
            "max_cost_per_segment": 8000,
            "currency": "INR",
            "allowed_classes": ["economy"],
            "advance_booking_days": 14,
            "preferred_carriers": ["IndiGo", "Air India", "Vistara"],
            "note": "Business class requires VP approval for domestic travel.",
        },
        "international": {
            "max_cost_per_segment": 80000,
            "currency": "INR",
            "allowed_classes": ["economy", "premium_economy"],
            "advance_booking_days": 21,
            "note": "Business class allowed for flights >8 hours with Director approval.",
        },
    },
    "hotels": {
        "metro_cities": {
            "max_per_night": 6000,
            "currency": "INR",
            "cities": ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune"],
        },
        "non_metro": {
            "max_per_night": 4000,
            "currency": "INR",
        },
        "note": "Breakfast included preferred. Book through Itilite portal for corporate rates.",
    },
    "car": {
        "max_per_day": 2500,
        "currency": "INR",
        "allowed_types": ["sedan", "hatchback"],
        "note": "SUV requires Manager approval.",
    },
    "per_diem": {
        "metro": {"daily_allowance": 1500, "currency": "INR"},
        "non_metro": {"daily_allowance": 1000, "currency": "INR"},
        "international": {"daily_allowance": 50, "currency": "USD"},
    },
    "general": {
        "approval_threshold": 20000,
        "currency": "INR",
        "booking_window": "All travel must be booked at least 7 days in advance unless emergency.",
        "receipt_required_above": 500,
        "travel_insurance": "Mandatory for international travel.",
    },
}


async def get_travel_policy(company_id: str, category: str) -> str:
    """Retrieve travel policy rules for a given category."""
    # TODO: call Itilite policy API for the specific company
    policy = _MOCK_POLICIES.get(category)
    if not policy:
        valid = list(_MOCK_POLICIES.keys())
        return json.dumps({"error": f"Unknown category '{category}'. Valid: {valid}"})
    return json.dumps({"company_id": company_id, "category": category, "policy": policy}, indent=2)


async def check_policy_compliance(
    company_id: str,
    segment_type: str,
    amount: float,
    currency: str = "USD",
    travel_class: str = "",
) -> str:
    """Check whether a booking complies with company policy."""
    # TODO: call Itilite compliance check API
    violations = []
    warnings = []

    if segment_type == "flight":
        limit = _MOCK_POLICIES["flights"]["domestic"]["max_cost_per_segment"]
        if amount > limit:
            violations.append(f"Flight cost {currency} {amount} exceeds policy limit of INR {limit}.")
        if travel_class and travel_class.lower() not in ["economy"]:
            warnings.append(f"Travel class '{travel_class}' requires additional approval for domestic flights.")

    elif segment_type == "hotel":
        limit = _MOCK_POLICIES["hotels"]["metro_cities"]["max_per_night"]
        if amount > limit:
            violations.append(f"Hotel nightly rate {currency} {amount} exceeds metro limit of INR {limit}.")

    elif segment_type == "car":
        limit = _MOCK_POLICIES["car"]["max_per_day"]
        if amount > limit:
            violations.append(f"Car rental cost {currency} {amount} exceeds daily limit of INR {limit}.")

    compliant = len(violations) == 0
    return json.dumps({
        "company_id": company_id,
        "segment_type": segment_type,
        "amount": amount,
        "currency": currency,
        "compliant": compliant,
        "violations": violations,
        "warnings": warnings,
        "message": "Booking is within policy." if compliant else "Booking violates policy. Approval required.",
    }, indent=2)

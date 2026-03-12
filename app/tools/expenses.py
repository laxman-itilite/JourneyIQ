"""Expense report tool handlers.

Stubs return mock data. Replace with real Itilite API calls.
"""
import json


async def get_expense_report(trip_id: str, employee_id: str) -> str:
    """Retrieve submitted expense reports for a trip."""
    # TODO: call Itilite expense API
    if trip_id != "TRP-003":
        return json.dumps({
            "trip_id": trip_id,
            "employee_id": employee_id,
            "expenses": [],
            "message": "No expense reports submitted for this trip yet.",
        })

    mock_report = {
        "trip_id": "TRP-003",
        "employee_id": employee_id,
        "status": "approved",
        "submitted_at": "2026-02-18T10:00:00Z",
        "approved_at": "2026-02-20T14:00:00Z",
        "total_claimed": 9800.00,
        "total_approved": 9300.00,
        "currency": "INR",
        "expenses": [
            {"category": "Flight", "amount": 4200.00, "status": "approved", "receipt": True},
            {"category": "Hotel", "amount": 4300.00, "status": "approved", "receipt": True},
            {"category": "Meals", "amount": 800.00, "status": "approved", "receipt": True},
            {"category": "Local Transport", "amount": 500.00, "status": "rejected", "receipt": False, "note": "No receipt attached"},
        ],
        "reimbursement_date": "2026-02-27",
    }
    return json.dumps(mock_report, indent=2)

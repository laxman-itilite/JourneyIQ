"""Approval workflow tool handlers.

Stubs return mock data. Replace with real Itilite API calls.
"""
import json


async def get_approval_status(entity_id: str, entity_type: str) -> str:
    """Get the approval workflow status for a trip or booking."""
    # TODO: call Itilite approvals API
    mock_approvals = {
        "TRP-001": {
            "entity_id": "TRP-001",
            "entity_type": "trip",
            "status": "approved",
            "approver": "Priya Sharma (Manager)",
            "approved_at": "2026-03-10T09:30:00Z",
            "comments": "Approved. Ensure hotel is within policy limits.",
        },
        "TRP-002": {
            "entity_id": "TRP-002",
            "entity_type": "trip",
            "status": "pending",
            "approver": "Priya Sharma (Manager)",
            "submitted_at": "2026-03-11T11:00:00Z",
            "comments": None,
            "message": "Waiting for manager review. Typically takes 1-2 business days.",
        },
    }

    result = mock_approvals.get(entity_id)
    if not result:
        return json.dumps({
            "entity_id": entity_id,
            "entity_type": entity_type,
            "status": "not_found",
            "message": f"No approval record found for {entity_type} {entity_id}.",
        })
    return json.dumps(result, indent=2)

"""FAQ search tool handler.

Stub returns mock answers. Replace with vector search or Itilite FAQ API.
"""
import json


_FAQ = [
    {
        "q": "how do i submit an expense",
        "a": "Go to Itilite → Expenses → New Expense. Upload receipts, categorize items, and submit for manager approval. Approved expenses are reimbursed within 7 business days.",
    },
    {
        "q": "how do i cancel a booking",
        "a": "Open the booking in Itilite, click 'Cancel Booking', and confirm. Refunds follow the vendor's cancellation policy. Check the booking details for the free cancellation deadline.",
    },
    {
        "q": "what is the hotel policy",
        "a": "For metro cities the cap is INR 6,000/night. Non-metro cap is INR 4,000/night. Book through the Itilite portal to access corporate rates. Breakfast-inclusive options are preferred.",
    },
    {
        "q": "how do i get approval for my trip",
        "a": "Trips over INR 20,000 require manager approval. Create the trip in Itilite and it will automatically enter the approval workflow. You'll be notified by email once approved.",
    },
    {
        "q": "can i book business class",
        "a": "Business class for domestic flights requires VP approval. For international flights over 8 hours, Director approval is needed. Economy / premium economy is the default.",
    },
    {
        "q": "how do i raise a travel request",
        "a": "Go to Itilite → New Trip → fill in destination, dates, purpose, and cost estimate → submit. The system will route it for approval based on your company policy.",
    },
    {
        "q": "what documents do i need for international travel",
        "a": "Valid passport (6+ months validity), visa for destination country, travel insurance (mandatory via Itilite), and any health documentation required by the destination.",
    },
    {
        "q": "how do i change my flight",
        "a": "Open the booking in Itilite → 'Modify Booking'. Date changes may incur airline fees. Major changes (route, passenger) require cancellation and rebooking.",
    },
]


async def search_faq(query: str) -> str:
    """Search FAQ for answers to Itilite platform questions."""
    # TODO: replace with vector search or Itilite FAQ API
    query_lower = query.lower()
    matches = []
    for entry in _FAQ:
        # Simple keyword overlap scoring
        q_words = set(entry["q"].split())
        query_words = set(query_lower.split())
        overlap = len(q_words & query_words)
        if overlap > 0 or any(word in entry["q"] for word in query_words):
            matches.append({"score": overlap, "question": entry["q"], "answer": entry["a"]})

    matches.sort(key=lambda x: x["score"], reverse=True)
    top = matches[:2] if matches else []

    if not top:
        return json.dumps({
            "query": query,
            "results": [],
            "message": "No matching FAQ entries found. Please contact your HR/travel admin.",
        })

    return json.dumps({
        "query": query,
        "results": [{"question": m["question"], "answer": m["answer"]} for m in top],
    }, indent=2)

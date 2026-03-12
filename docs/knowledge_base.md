# Itilite API — Knowledge Base

Domain rules, ID conventions, and non-obvious API behaviours discovered during development.
Add entries here whenever you learn something that isn't obvious from reading the code.

---

## ID Conventions

### Trip ID
Format: `{client_id_padded}-{sequence}` e.g. `0600-1241`

| Part | Example | Rule |
|---|---|---|
| Prefix | `0600` | Client ID zero-padded to 4 digits |
| Suffix | `1241` | Sequential trip number |

**Derive client_id from trip_id:**
```python
client_id = str(int(trip_id.split("-")[0]))  # "0600-1241" → "600"
```
The leading zero is stripped — the API expects `600`, not `0600`.

### Leg Request ID
Opaque MongoDB ObjectId string (e.g. `696decd6a90d231111c0d7eb`). Used to identify individual flight/hotel/car legs within a trip.

### Cancellation Detail ID
Returned by the cancellation-details API (`_id` field). Must be passed verbatim to the cancellation-request POST.

### User ID
The authenticated user's email address (e.g. `Filus@yopmail.com`). Stored as `user_id` in the JWT payload.

---

## API Base URLs

| URL | Used for |
|---|---|
| `https://stream-api-qa.iltech.in` | Trip itinerary, trips list (`API_BASE_URL`) |
| `https://fast-api-qa.iltech.in` | Hotel static, hotel room details, flight cancellation (`HOTEL_STATIC_BASE_URL`) |

---

## Required Headers by Endpoint Group

### Itinerary / Trips (`stream-api-qa`)
```
Authorization: Bearer <token>
```

### Hotel Static / Room Details (`fast-api-qa`)
```
Authorization: Bearer <token>
Content-Type: application/json
```

### Flight Cancellation (`fast-api-qa /v1/trip-modify/*`)
```
Authorization: Bearer <token>
client-id: <client_id>          ← derived from trip_id prefix
role: traveler
Content-Type: application/json
```
The `client-id` and `role` headers are **required** or the API returns 4xx.

---

## Authentication

- All APIs use a short-lived JWT (`Bearer` token).
- Token is hardcoded in `config.py → get_user_access_token()` for now.
- `user_id` is the email in the JWT payload (`payload["user_id"]`).
- Token expiry is at `payload["exp"]` (Unix timestamp). Decode with base64 to check.
- **TODO:** Replace with per-user token from Socket.IO auth handshake.

---

## Flight Cancellation Flow

Three-step process — each step depends on the previous:

```
Step 1: GET  /v1/trip-modify/cancellation-details?trip_id=
        → Returns: cancellation_detail_id, eligible legs, refund estimates

Step 2: POST /v1/trip-modify/cancellation-request
        Body: { cancellation_detail_id, trip_id, leg_details }
        → leg_details must include flight_get_can_details from Step 1
        → Returns: cancellation_request_id

Step 3: GET  /v1/trip-modify/cancellation-request?cancellation_request_id=&trip_id=
        → Returns: status of the cancellation (async, may take time)
```

Our tool `submit_flight_cancellation` internally re-fetches Step 1 to build the POST body,
so Claude only needs to pass `trip_id` + `leg_request_ids`.

---

## Hotel Cancellation vs Flight Cancellation

These are **different APIs**:

| | Hotel | Flight |
|---|---|---|
| Cancel endpoint | `/hotels/{booking_id}/cancel` (stream-api) | `/v1/trip-modify/cancellation-request` (fast-api) |
| Key identifier | `booking_id` | `leg_request_id` from cancellation-details |
| Flow | Single call | 3-step flow |
| Extra headers | None | `client-id`, `role` |

---

## Pax (Passenger) IDs

Numeric IDs (e.g. `20807`). Stored as integers in the API but should be passed as strings in cancellation requests (`pax_list: ["20807"]`).

---

## QA Environment

All current endpoints point to QA (`-qa.iltech.in`). Production domains will differ — update `API_BASE_URL` and `HOTEL_STATIC_BASE_URL` in `config.py` when switching.

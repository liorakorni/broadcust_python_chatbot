# User profile API (server-to-server)

Two **POST** endpoints touch Gemini-backed enrichment. Your backend (not the browser) should call them with the **same** shared secret as today’s profile APIs.

## Which endpoint should the client call?

| Situation | Call |
|-----------|------|
| User **just submitted** the onboarding form (you have `UserID`, contact fields, and raw questionnaire text) | **`POST /add-user-profile`** |
| Row **already exists** in DynamoDB with `RawBizChar` filled (migration, old users, or retry) | **`POST /backfill-user-biz-profile`** |
| **`/add-user-profile`** returned **5xx** with “enrichment failed” but **`userId`** is present (raw row was saved) | **`POST /backfill-user-biz-profile`** with that `UserID` |
| You changed **`RawBizChar`** in DB and want **new** copy + suggestions | **`POST /backfill-user-biz-profile`** with **`"force": true`** |
| You only need to **read** the stored item (`OptBizChar`, `InitialBizSugg`, etc.) | **`GET /get-user-profile?UserID=...`** (unchanged; see below) |

**Summary:** Use **`/add-user-profile`** once per **new** submission (creates/overwrites the item and runs Gemini). Use **`/backfill-user-biz-profile`** when the user **already has** a stored profile and you only need to **generate or refresh** `OptBizChar` / `InitialBizSugg` from existing `RawBizChar`.

Do **not** call both for every form submit—only **`/add-user-profile`** on submit. Use backfill for batch migration, retries, or forced refresh.

---

## Authentication

Both POST endpoints expect header:

```http
x-api-key: <SERVER_API_KEY>
```

Use the same server API key configured for `add_user_profile` (`server_api_key` in `conf.py` / your Lambda env). Never expose this key in frontend code.

---

## Base URL

After `serverless deploy`, copy the HTTP API host from the deploy output (API Gateway HTTP API). Examples use placeholders:

```bash
export API_BASE="https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com"
export API_KEY="YOUR_SERVER_API_KEY"
```

Adjust region if your stack is not `us-east-1`.

---

## `POST /add-user-profile`

**When:** New profile from form submit.

**Body (JSON):**

| Field | Required | Description |
|-------|----------|-------------|
| `UserID` | yes | Stable user identifier |
| `Mobile` | yes | Phone (at least 9 digits) |
| `Email` | yes | Valid email |
| `RawBizChar` | yes | Raw “business characterization” questionnaire text |

**Note:** `OptBizChar` is **not** sent by the client; the service generates it with Gemini.

**Example:**

```bash
curl -sS -X POST "${API_BASE}/add-user-profile" \
  -H "Content-Type: application/json" \
  -H "x-api-key: ${API_KEY}" \
  -d '{
    "UserID": "user-123",
    "Mobile": "+972501234567",
    "Email": "owner@example.com",
    "RawBizChar": "תיאור גולמי של העסק מהטופס..."
  }' | jq .
```

**Success (200):** JSON includes `initialBizSugg`, `optBizChar`, `userId`.

**Partial failure (500):** If Gemini fails after the row was written, body includes `userId` and a hint to call backfill.

---

## `POST /backfill-user-biz-profile`

**When:** Existing DynamoDB row with non-empty `RawBizChar`; migration, retry, or refresh.

**Body (JSON):**

| Field | Required | Description |
|-------|----------|-------------|
| `UserID` | yes | Which profile to enrich |
| `force` | no (default `false`) | If `true`, regenerate even when `OptBizChar` and `InitialBizSugg` are already filled |

**Example (migration / first-time enrichment):**

```bash
curl -sS -X POST "${API_BASE}/backfill-user-biz-profile" \
  -H "Content-Type: application/json" \
  -H "x-api-key: ${API_KEY}" \
  -d '{
    "UserID": "user-legacy-456"
  }' | jq .
```

**Example (force refresh after editing `RawBizChar` or changing prompts):**

```bash
curl -sS -X POST "${API_BASE}/backfill-user-biz-profile" \
  -H "Content-Type: application/json" \
  -H "x-api-key: ${API_KEY}" \
  -d '{
    "UserID": "user-123",
    "force": true
  }' | jq .
```

**Responses:**

- **200 + `"skipped": true`:** Profile already had both `OptBizChar` and `InitialBizSugg` non-empty; no Gemini call (unless you use `force: true`).
- **200 + `"skipped": false`:** Generated and updated; body includes `initialBizSugg`, `optBizChar`.
- **404:** Unknown `UserID`.
- **400:** Missing or empty `RawBizChar` on the stored item.

---

## `GET /get-user-profile` (read-only)

Fetch the full item (including `RawBizChar`, `OptBizChar`, `InitialBizSugg`, `BizCharGeneratedAt` when present).

```bash
curl -sS "${API_BASE}/get-user-profile?UserID=user-123" | jq .
```

(This endpoint is unchanged from your existing setup; confirm whether your deployment restricts it.)

---

## DynamoDB fields (reference)

| Attribute | Meaning |
|-----------|---------|
| `RawBizChar` | Raw form text (input to Gemini) |
| `OptBizChar` | Prompt 1 output (“כרטיס ביקור אסטרטגי”) |
| `InitialBizSugg` | Prompt 2 output (marketing headline suggestions) |
| `BizCharGeneratedAt` | ISO timestamp of last successful enrichment update |

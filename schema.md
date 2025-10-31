# Mine Safety Analysis - MongoDB Schema

This document specifies the schema for documents stored in the MongoDB collection. These documents are parsed from DGMS Safety Alert PDFs/HTMLs by `mine_safety/parser.py`.

- Database: `MONGODB_DB` (default: `mine_safety`)
- Collection: `MONGODB_COLLECTION` (default: `dgms_reports`)
- Unique index: `{ report_id: 1 }` (if present)

## Document Schema

```json
{
  "_id": "ObjectId",                 // Created by MongoDB
  "report_id": "SA-21-2025",        // Derived from the alert number/year if found
  "date_reported": "2025-08-22",    // YYYY-MM-DD, date the alert/report was issued
  "accident_date": "2025-07-23T02:15:00", // ISO date/time if time known; otherwise YYYY-MM-DD
  "mine_details": {
    "name": "Gevra Opencast Mine",
    "owner": "M/s S.E.C.Ltd.",
    "district": "Korba",
    "state": "Chhattisgarh",
    "mineral": "Coal"
  },
  "incident_details": {
    "location": "Haul Road (NIT-522 Naraibodh OB Patch), Gevra Project of M/s SECL",
    "fatalities": [
      {
        "name": "Shri Rajan Rana Magar",
        "designation": "Driller’s Helper",
        "age": 25,
        "experience": "2 months"
      }
    ],
    "injuries": [],
    "brief_cause": "A contractual workman (Driller’s helper)..."
  },
  "best_practices": [
    "Pedestrians shall not be allowed to travel on haul roads...",
    "A designated place shall be provided on haul roads for crossing.",
    "Crossing of haul roads may be done only by conveyance vehicles at designated places."
  ],
  "source_url": "https://www.dgms.gov.in/.../Fatal_Accident_Gevra_2025.pdf",
  "summary": "",                     // Intentionally left empty; no summarization needed
  "created_at": "2025-10-31T19:35:00Z", // UTC timestamp set at ingestion

  "_raw_title": "SAFETY ALERT : 21/2025 ...", // Preserved for auditing/debugging
  "_raw_text": "...full extracted text..."     // Up to ~6000 chars for storage
}
```

Notes:
- Fields may be empty strings (`""`), nulls (`null`), or empty arrays (`[]`) if information is not present in the source.
- `report_id` may not be derivable for every document; when absent, upserts will fall back to inserting a new document.
- `created_at` is set to the UTC time when the document is processed.

## Field Types

- `report_id`: string
- `date_reported`: string (YYYY-MM-DD)
- `accident_date`: string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
- `mine_details`: object
  - `name`: string
  - `owner`: string
  - `district`: string
  - `state`: string
  - `mineral`: string
- `incident_details`: object
  - `location`: string
  - `fatalities`: array of objects
    - `name`: string
    - `designation`: string
    - `age`: integer or null
    - `experience`: string
  - `injuries`: array of objects (currently empty in most cases)
  - `brief_cause`: string
- `best_practices`: array of strings
- `source_url`: string (URL)
- `summary`: string
- `created_at`: string (ISO8601 UTC)
- `_raw_title`: string
- `_raw_text`: string

## Indexes

- A unique index is created on `report_id` to prevent duplicates when the `report_id` is present:

```js
// Mongo shell example
// db.dgms_reports.createIndex({ report_id: 1 }, { unique: true })
```

## Example Document

```json
{
  "report_id": "SA-21-2025",
  "date_reported": "2025-08-22",
  "accident_date": "2025-07-23T02:15:00",
  "mine_details": {
    "name": "Gevra Opencast Mine",
    "owner": "M/s S.E.C.Ltd.",
    "district": "Korba",
    "state": "Chhattisgarh",
    "mineral": "Coal"
  },
  "incident_details": {
    "location": "Haul Road (NIT-522 Naraibodh OB Patch), Gevra Project of M/s SECL",
    "fatalities": [
      {
        "name": "Shri Rajan Rana Magar",
        "designation": "Driller’s Helper",
        "age": 25,
        "experience": "2 months"
      }
    ],
    "injuries": [],
    "brief_cause": "A contractual workman (Driller’s helper), while trying to cross a haul road in an opencast coal mine, was hit by an empty truck and later succumbed during treatment."
  },
  "best_practices": [
    "Pedestrians shall not be allowed to travel on the haul roads made for trucks, tippers and dumpers or other mobile machinery.",
    "A designated place shall be provided on haul roads for crossing.",
    "Crossing of haul roads, if required, may be done only by conveyance vehicles at the designated places."
  ],
  "source_url": "https://www.dgms.gov.in/.../Fatal_Accident_Gevra_2025.pdf",
  "summary": "",
  "created_at": "2025-10-31T19:35:00Z",
  "_raw_title": "SAFETY ALERT : 21/2025 ...",
  "_raw_text": "..."
}
```

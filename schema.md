# Mine Safety Analysis - MongoDB Schema

This document specifies the schema for documents stored in the MongoDB collection. These documents are parsed from DGMS Safety Alert PDFs/HTMLs and news articles.

- Database: `MONGODB_DB` (default: `mine_safety`)
- Collection: `MONGODB_COLLECTION` (default: `dgms_reports`)
- Unique index: `{ "metadata.report_id": 1 }`

## Document Schema

The schema is designed to be flexible to accommodate data from both structured DGMS reports and unstructured news articles.

```json
{
  "_id": "ObjectId",
  "summary": "A summary of the incident...",
  "incident_details": {
    "date_of_incident": "2025-07-23T02:15:00Z",
    "location": "Gevra Opencast Mine, Haul Road",
    "district": "Korba",
    "state": "Chhattisgarh",
    "brief_cause": "A contractual workman was hit by a dumper while crossing the haul road.",
    "cause_code": "3.2 - Dumper",
    "place_of_accident": "Belowground",
    "nature_of_accident": "Struck by object",
    "type_of_accident": "Fatal",
    "victim_details": [
      {
        "name": "Shri Rajan Rana Magar",
        "age": 25,
        "sex": "Male",
        "occupation": "Driller’s Helper",
        "status": "Fatal"
      }
    ]
  },
  "actions_taken": {
    "violations_observed": "Pedestrians were allowed to travel on haul roads.",
    "recommendations": "Provide designated crossing points for pedestrians on haul roads."
  },
  "metadata": {
    "source_url": "https://www.dgms.gov.in/.../Fatal_Accident_Gevra_2025.pdf",
    "scraped_at": "2025-11-04T10:00:00Z",
    "report_id": "DGMS-SA-21-2025",
    "source_type": "DGMS Report",
    "_raw_text": "...full extracted text of the report..."
  },
  "embeddings": {
    "summary_embedding": [0.1, 0.2, ...],
    "full_text_embedding": [0.3, 0.4, ...]
  }
}
```

## Field Descriptions

- **`summary`** (string): A concise, LLM-generated summary of the incident.
- **`incident_details`** (object): Detailed structured information about the incident.
  - **`date_of_incident`** (string, ISO 8601 format): The date when the incident occurred.
  - **`location`** (string): The specific location of the incident (e.g., "Mine No. 5").
  - **`district`** (string, optional): The district where the mine is located.
  - **`state`** (string, optional): The state where the mine is located.
  - **`brief_cause`** (string): A short, unstructured description of the cause of the incident, extracted directly from the source text.
  - **`cause_code`** (string, optional): A structured cause code (e.g., "1.1 - Fall of roof") mapped from the `brief_cause` using the cause code vector database.
  - **`place_of_accident`** (string, optional): A structured code for the place of the accident.
  - **`nature_of_accident`** (string, optional): A description of the nature of the accident.
  - **`type_of_accident`** (string, optional): The type of accident.
  - **`victim_details`** (array of objects): Information about the victims.
    - **`name`** (string): Name of the victim.
    - **`age`** (integer): Age of the victim.
    - **`sex`** (string): Sex of the victim.
    - **`occupation`** (string): Occupation of the victim.
    - **`status`** (string): "Fatal" or "Serious".
- **`actions_taken`** (object): Actions taken after the incident.
  - **`violations_observed`** (string): Any violations that were observed.
  - **`recommendations`** (string): Recommendations to prevent future incidents.
- **`metadata`** (object): Metadata about the document.
  - **`source_url`** (string): The URL where the report was found.
  - **`scraped_at`** (string, ISO 8601 format): The timestamp when the data was scraped.
  - **`report_id`** (string): A unique identifier for the report, often generated from the source.
  - **`source_type`** (string): "DGMS Report" or "News Article".
  - **`_raw_text`** (string): The full raw text extracted from the source, stored for archival and re-processing purposes.
- **`embeddings`** (object, optional): Vector embeddings for the document, used for similarity searches.
  - **`summary_embedding`** (array of floats): Embedding of the `summary` field.
  - **`full_text_embedding`** (array of floats): Embedding of the `_raw_text` field.

## Indexes

- A unique index is created on `metadata.report_id` to prevent duplicate documents.

```javascript
// Mongo shell command to create the index
db.getCollection('dgms_reports').createIndex({ "metadata.report_id": 1 }, { unique: true, sparse: true });
```
*Note: The `sparse: true` option ensures the unique constraint only applies to documents that have the `metadata.report_id` field.*

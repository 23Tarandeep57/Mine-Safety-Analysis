from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Fatality(BaseModel):
    name: Optional[str] = None
    designation: Optional[str] = None
    age: Optional[int] = None
    experience: Optional[str] = None

class Injury(BaseModel):
    name: Optional[str] = None
    designation: Optional[str] = None
    age: Optional[int] = None
    experience: Optional[str] = None

class IncidentDetails(BaseModel):
    location: Optional[str] = None
    fatalities: List[Fatality] = []
    injuries: List[Injury] = []
    brief_cause: Optional[str] = None

class MineDetails(BaseModel):
    name: Optional[str] = None
    owner: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    mineral: Optional[str] = None

class Verification(BaseModel):
    status: str
    timestamp: datetime
    articles: List[str] = []

class Report(BaseModel):
    report_id: Optional[str] = None
    date_reported: Optional[str] = None
    accident_date: Optional[str] = None
    mine_details: MineDetails
    incident_details: IncidentDetails
    best_practices: List[str] = []
    source_url: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    verification: Optional[Verification] = None
    raw_title: Optional[str] = Field(alias="_raw_title")
    raw_text: Optional[str] = Field(alias="_raw_text")

    class Config:
        populate_by_name = True

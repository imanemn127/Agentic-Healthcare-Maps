"""
Pydantic v2 schemas for the Agentic Healthcare Maps pipeline.
Every module imports from here — this is the single source of truth for data shapes.
"""

from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field


class RawFacilityRecord(BaseModel):
    """Mirrors the columns in raw_facilities.xlsx exactly."""
    row_id: int
    facility_name: Optional[str] = None
    facility_type: Optional[str] = None
    address_raw: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None
    beds: Optional[str] = None          # kept as string — may be "~200" or "approx 120"
    specialties: Optional[str] = None   # comma-separated, may have typos
    ownership: Optional[str] = None
    accreditation: Optional[str] = None
    operational_status: Optional[str] = None
    emergency_services: Optional[str] = None
    source_note: Optional[str] = None


FacilityTypeEnum = Literal[
    "hospital", "clinic", "PHC", "CHC", "dispensary",
    "nursing_home", "diagnostic_center", "unknown"
]
OwnershipEnum = Literal["government", "private", "trust", "NGO", "unknown"]
TrustTierEnum = Literal["high", "medium", "low", "unverified"]


class ExtractedFacility(BaseModel):
    """Output of the Gemini extraction step."""
    row_id: int
    facility_name: str = "Unknown"
    facility_type: FacilityTypeEnum = "unknown"
    city: str = ""
    district: str = ""
    state: str = ""
    pincode: Optional[str] = None
    beds_count: Optional[int] = None
    specialties: list[str] = Field(default_factory=list)
    ownership: OwnershipEnum = "unknown"
    accreditation: list[str] = Field(default_factory=list)
    is_operational: Optional[bool] = None
    has_emergency: Optional[bool] = None
    evidence_sentences: list[str] = Field(default_factory=list)
    extraction_confidence: float = 0.0
    contradictions_found: list[str] = Field(default_factory=list)


class TrustScore(BaseModel):
    """Output of the trust scoring step."""
    row_id: int
    completeness_score: float = 0.0
    consistency_score: float = 0.0
    geocode_score: float = 0.5          # placeholder until geocode runs
    validation_score: float = 0.0
    final_trust_score: float = 0.0
    trust_tier: TrustTierEnum = "unverified"
    correction_applied: bool = False
    validator_notes: str = ""


class GeocodedFacility(BaseModel):
    """
    Final merged record combining extraction + trust score + geocode.
    This is what gets written to geocoded_facilities.csv and used by
    the map generator, query agent, and Streamlit app.
    """
    # --- from ExtractedFacility ---
    row_id: int
    facility_name: str = "Unknown"
    facility_type: FacilityTypeEnum = "unknown"
    city: str = ""
    district: str = ""
    state: str = ""
    pincode: Optional[str] = None
    beds_count: Optional[int] = None
    specialties: list[str] = Field(default_factory=list)
    ownership: OwnershipEnum = "unknown"
    accreditation: list[str] = Field(default_factory=list)
    is_operational: Optional[bool] = None
    has_emergency: Optional[bool] = None
    evidence_sentences: list[str] = Field(default_factory=list)
    extraction_confidence: float = 0.0
    contradictions_found: list[str] = Field(default_factory=list)

    # --- from TrustScore ---
    completeness_score: float = 0.0
    consistency_score: float = 0.0
    geocode_score: float = 0.0
    validation_score: float = 0.0
    final_trust_score: float = 0.0
    trust_tier: TrustTierEnum = "unverified"
    correction_applied: bool = False
    validator_notes: str = ""

    # --- from Geocoder ---
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geocode_source: str = "pending"
    geocode_confidence: str = "none"


class QueryResult(BaseModel):
    """Returned by the query agent."""
    query_text: str
    interpreted_intent: str = ""
    filters_applied: dict = Field(default_factory=dict)
    results: list[dict] = Field(default_factory=list)   # list of GeocodedFacility dicts
    distance_km: Optional[float] = None
    evidence_trail: list[str] = Field(default_factory=list)
    answer_summary: str = ""
    result_count: int = 0
